import weakref
import time

from psychopy import visual, core
from psychopy.iohub import ioHubExperimentRuntime, EventConstants
from psychopy.iohub.util import Trigger, TimeTrigger, DeviceEventTrigger
from psychopy.iohub.util import win32MessagePump

from util.dynamicmask import DynamicMask

REFRESH_RATE = 0.01       # delay between screen flips during mask
FIXATION_DURATION = 0.5   # duration of fixation cross prior to cue/target
CUE_DURATION = 0.2        # duration of cueing interval
CUE_TARGET_INTERVAL = 0.5 # duration between cue offset and target onset
## start of RT timer
TARGET_DURATION = 0.5     # duration target visible
RESPONSE_WINDOW = 2.0

getTime = core.getTime

class ScreenState(object):
    _currentState = None

    def __init__(self, window, hubServer, eventTriggers = list(),
            timeout = None, background_color = (255, 255, 255)):
        self.window = window
        self.hub = hubServer

        w, h = self.window.size
        self._screen_background_fill = visual.Rect(self.window, w, h,
               lineColor = background_color, lineColorSpace = 'rgb255',
               fillColor = background_color, fillColorSpace = 'rgb255',
               units = 'pix', name = 'BACKGROUND', opacity = 1.0,
               interpolate = False)

        self.stim = dict()
        self.stimNames = []

        if isinstance(eventTriggers, Trigger):
            eventTriggers=[eventTriggers, ]
        elif eventTriggers is None:
            eventTriggers = []

        self.event_triggers = eventTriggers
        self._start_time = None
        self.timeout = timeout
        self.dirty = True

    def setScreenColor(self, rgbColor):
        self._screen_background_fill.setFillColor(color = rgbColor,
                                                  colorSpace = 'rgb255')
        self._screen_background_fill.setLineColor(color = rgbColor,
                                                  colorSpace = 'rgb255')
        self.dirty = True

    def setEventTriggers(self, triggers):
        self.event_triggers = []
        if isinstance(triggers, Trigger):
            triggers = [triggers, ]
        self.event_triggers = triggers

    def addEventTrigger(self, trigger):
        if isinstance(trigger, Trigger):
            self.event_triggers.append(trigger)
        else:
            raise ValueError("Triggers added to a screen state object"
                             "must be of type DeviceEventTrigger.")

    def getStateStartTime(self):
        return self._start_time

    def getEventTriggers(self):
        return self.event_triggers

    def setTimeout(self, timeout):
        self.timeout = timeout

    def switchTo(self, clearEvents = True, msg = None):
        """ Show the screen state.

        Stimuli are drawn and a flip occurs. Three conditions cause the
        switchTo method to return. In all cases, a tuple of three values
        is returned, some elements of which may be None.

            1. Nothing to monitor (no timeout or DeviceEventTriggers)::

                (stateStartTime, None, None)

            2. Reached timeout::

                (stateStartTime, stateDuration, None)

            3. DeviceEventTrigger returned True::

                (startStartTime, stateDuration, exitTriggeringEvent)
        """
        # ER = self.experimentRuntime()
        localClearEvents = self.hub.clearEvents
        if clearEvents is False:
            localClearEvents = lambda clearEvents: clearEvents is None

        event_triggers = self.event_triggers

        for trigger in event_triggers:
            trigger.resetTrigger()

        lastMsgPumpTime = 0
        self.build()
        self._start_time = self.flip(text=msg)
        endTime = self._start_time+self.timeout
        localClearEvents('all')

        if event_triggers and len(event_triggers) > 0:
            while getTime()+0.002 < endTime:
                for trigger in event_triggers:
                    if trigger.triggered() is True:

                        event = trigger.getTriggeringEvent()
                        functionToCall, kwargs = trigger.getTriggeredStateCallback()

                        trigger.resetLastTriggeredInfo()

                        if functionToCall:
                            exitState = functionToCall(self._start_time,
                                                    getTime()-self._start_time,
                                                    event, **kwargs)
                            if exitState is True:
                                localClearEvents('all')
                                Trigger.clearEventHistory()
                                return (self._start_time,
                                        getTime()-self._start_time, event)
                        break

                Trigger.clearEventHistory()

                tempTime = getTime()
                if tempTime+0.002 < endTime:
                    time.sleep(0.001)

                    if tempTime-lastMsgPumpTime > 0.5:
                        win32MessagePump()
                        lastMsgPumpTime = tempTime

            localClearEvents('all')
            while getTime() < endTime:
                pass
            return self._start_time, getTime()-self._start_time, None

        elif self.timeout is not None:
            self.hub.wait(self.timeout-0.002)
            localClearEvents('all')

            while getTime() < endTime:
                pass

            return self._start_time, getTime()-self._start_time, None

        return self._start_time, None, None

    def build(self):
        self._screen_background_fill.draw()
        for stimName in self.stimNames:
            self.stim[stimName].draw()
        self.dirty = False

    def flip(self, text=None):
        if self.dirty:
            self.build()
        ftime = self.window.flip()
        ScreenState._currentState = self
        if text is not None:
            self.sendMessage(text, ftime)
        return ftime

    def sendMessage(self, text, mtime = None):
        if mtime is None:
            mtime = getTime()
        mtext = text
        try:
            tracker = self.hub.getDevice('tracker')
            if tracker is not None and tracker.isConnected() is True:
                mtext = "%s : tracker_time [%.6f]"%(mtext, tracker.trackerSec())
                tracker.sendMessage(mtext)
            else:
                print '----------------------'
                print 'Warning: eyetracker is not connected.'
                print 'Msg not sent to eyetracker datafile: '
                print mtext
                print '----------------------'
        except:
            pass
        self.hub.sendMessageEvent(mtext, sec_time=mtime)

    @classmethod
    def getCurrentScreenState(cls):
        return cls._currentState

class TargetDetection(ScreenState):
    """
    Visuals
    -------
    fix: fixation cross presented at trial start
    masks: two masks, one for each side of the screen.
    cue: the thing to present before the target
    target: circle to detect, appears overlapping with left or right mask
    """
    def __init__(self, window, hubServer, eventTriggers = list()):
        super(TargetDetection, self).__init__(window, hubServer,
                eventTriggers = eventTriggers, timeout = 60.0)

        gutter = 300  # distance from centroid to left/right locations
        left = (-gutter, 0)
        right = (gutter, 0)
        self.location_map = {'left': left, 'right': right}

        mask_size = 200
        mask_kwargs = {'win': self.window, 'size': [mask_size, mask_size]}
        masks = {}
        masks['left']  = DynamicMask(pos = left, **mask_kwargs)
        masks['right'] = DynamicMask(pos = right, **mask_kwargs)
        self.stim.update(masks)

        # refresh timer draws a new mask image every REFRESH_RATE ms
        self.last_frame = None
        refresh = TimeTrigger(start_time = self.interval,
                delay = REFRESH_RATE, repeat_count = -1,
                trigger_function = self.refresh)
        self.addEventTrigger(refresh)

        # text args apply to fixation, word cue, and prompt objects
        text_kwargs = {'height': 40, 'font': 'Consolas', 'color': 'black'}

        # fixation cross is shown for the first FIXATION_DURATION of trial
        fix = visual.TextStim(self.window, text = '+', **text_kwargs)
        self.stim.update({'fix': fix})
        self.end_fixation = TimeTrigger(start_time = self.getStateStartTime,
                delay = FIXATION_DURATION, repeat_count = 1,
                trigger_function = self.cue)
        self.addEventTrigger(self.end_fixation)

        # target args apply to cue and target
        target_kwargs = {'radius': 10, 'fillColor': 'white'}

        cues = {}
        # make the dot just like the target
        cues['dot'] = visual.Circle(self.window, **target_kwargs)
        # cues['arrow'] = visual.ImageStim()
        cues['word'] = visual.TextStim(self.window, **text_kwargs)
        self.stim.update({'dot': cues['dot'], 'word': cues['word']})

        # timer for cue duration
        self.cue_onset = None  ## needs to get set when fix ended
        self.end_cueing = TimeTrigger(start_time = self.cue_onset,
                delay = CUE_DURATION, repeat_count = 1,
                trigger_function = self.wait)
        ## don't add to eventTriggers until fixation is ended

        # timer for interstimulus interval
        self.target_opacity = None  # will be set on switch
        self.cue_offset = None  ## needs to get set when cue ended
        self.end_interval = TimeTrigger(start_time = self.cue_offset,
                delay = CUE_TARGET_INTERVAL, repeat_count = 1,
                trigger_function = self.reveal)
        ## don't add to eventTriggers until cue is ended

        target = visual.Circle(self.window, opacity = 0.0, **target_kwargs)
        self.stim.update({'target': target})

        # probe for response
        probe = visual.TextStim(self.window, text = '?', **text_kwargs)
        self.stim.update({'probe': probe})

        self.target_onset = None ## needs to be set when target is revealed
        self.end_target = TimeTrigger(start_time = self.target_onset,
                delay = TARGET_DURATION, repeat_count = 1,
                trigger_function = self.probe)
        ## don't add until target_onset is set

    def interval(self):
        """ Return the time of the last flip.

        For the first interval, start when the ScreenState flips. For
        subsequent intervals, return the last_frame variable which is 
        updated when the screen is rebuilt.
        """
        if self.last_frame == None:
            self.last_frame = self.getStateStartTime()
        return self.last_frame

    def refresh(self, *args, **kwargs):
        """ TimeTriggered when it's been REFRESH_RATE since last_frame. """
        self.dirty = True
        self.last_frame = self.flip()
        return False

    ## not sure what the TimeTrigger returns
    def cue(self, stateStart, stateDuration, nullEvent = None):
        """ TimeTriggered when it's been FIXATION_DURATION since start. """
        self.event_triggers.remove(self.end_fixation)
        self.stimNames.remove('fix')

        if self.cue_name:
            self.stimNames.append(self.cue_name)

        # save cue_onset time which determines when to end cueing
        self.cue_onset = stateStart + stateDuration
        self.addEventTrigger(self.end_cueing)
        return self.refresh()

    def wait(self, stateStart, stateDuration, nullEvent = None):
        """ TimeTriggered when it's been CUE_DURATION since cue_onset. """
        self.event_triggers.remove(self.end_cueing)
        if self.cue_name:
            self.stimNames.remove(self.cue_name)

        # save cue_offset time which determines when to end the interval
        self.cue_offset = stateStart + stateDuration
        self.addEventTrigger(self.end_interval)
        return self.refresh()

    def reveal(self, stateStart, stateDuration, nullEvent = None):
        """ TimeTriggered when it's been target_onset since screen start """
        self.event_triggers.remove(self.end_interval)
        self.stim['target'].setOpacity(self.target_opacity)

        self.target_onset = stateStart + stateDuration
        self.addEventTrigger(self.end_target)
        return self.refresh()

    def probe(self, *args, **kwargs):
        """ Hide the masks, show the probe """
        self.event_triggers.remove(self.end_target)

        self.stimNames.remove('target')
        self.stimNames.append('probe')
        return self.refresh()

    def switchTo(self, opacity, location_name,
                cue_type = None, cue_location = None):
        """ Set the target opacity and run the trial. """
        self.cue_name = 'word'
        self.stim[self.cue_name].setText('left')

        if location_name:
            # target present trial
            self.target_opacity = opacity
            location = self.location_map[location_name]
        else:
            # target absent trial
            self.target_opacity = 0.0
            location = (0, 0)

        self.stim['target'].setPos(location)
        self.stim['target'].setOpacity(0.0)  # start with target hidden
        
        # start trial with masks, fixation, and invisible target
        self.stimNames = ['left', 'right', 'fix', 'target']
        
        return super(TargetDetection, self).switchTo()

if __name__ == '__main__':
    from psychopy.iohub import launchHubServer
    io = launchHubServer()

    display = io.devices.display
    window = visual.Window(display.getPixelResolution(),
            monitor = display.getPsychopyMonitorName(),
            units = display.getCoordinateType(),
            fullscr = True, allowGUI = False,
            screen = display.getIndex())

    responder_keys = {'y': 'present', 'n':'absent'}
    responder = DeviceEventTrigger(device = io.devices.keyboard,
            event_type = EventConstants.KEYBOARD_PRESS,
            event_attribute_conditions = {'key': responder_keys.keys()})

    detect_target = TargetDetection(eventTriggers = [responder, ],
            hubServer = io, window = window)

    _,rt,event = detect_target.switchTo(opacity = 1.0,
            location_name = 'right')
    print rt, event.key
