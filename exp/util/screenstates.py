import weakref
import time

from psychopy import visual, core
from psychopy.iohub import ioHubExperimentRuntime, EventConstants
from psychopy.iohub.util import Trigger, TimeTrigger, DeviceEventTrigger
from psychopy.iohub.util import win32MessagePump

from util.dynamicmask import DynamicMask

REFRESH_RATE = 0.01 # delay between screen flips during mask

getTime = core.getTime

class ScreenState(object):
    _currentState = None
    experimentRuntime = None
    window = None

    def __init__(self, hubServer, window, eventTriggers = None, 
            timeout = None, background_color = (255, 255, 255)):
        self.hub = hubServer
        self.window = window

        w, h = self.window.size
        self._screen_background_fill = visual.Rect(self.window, w, h,
                                                   lineColor=background_color,
                                                   lineColorSpace='rgb255',
                                                   fillColor=background_color,
                                                   fillColorSpace='rgb255',
                                                   units='pix',
                                                   name='BACKGROUND',
                                                   opacity=1.0,
                                                   interpolate=False)
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
        #self.window().setColor(rgbColor,'rgb255')
        self._screen_background_fill.setFillColor(color=rgbColor,
                                                  colorSpace='rgb255')
        self._screen_background_fill.setLineColor(color=rgbColor,
                                                  colorSpace='rgb255')
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

    # switches to screen state (draws and flips)
    # records flip time as start time for timer if timeout has been specified.
    # monitors the device.getEvents function ptrs that are available and if any events are returned,
    # checks the events against the event masks dict provided. If an event matches, it causes method to return
    # then, if no event masks are provided and an event is received, it will cause the method to return regardless
    # of event type for that device.
    # Otherwise method does not reurn until timeout seconds has passed.
    # Returns: [flip_time, time_since_flip, event]
    #          all elements but flip_time may be None. All times are in sec.msec
    def switchTo(self,clearEvents=True, msg=None):
        """
        Switches to the screen state defined by the class instance. The screen
        stim are built and a flip occurs.

        Three conditions can cause the switchTo method to then return,
        based on whether a timeout and / or DeviceEventTriggers
        have been set with the Screen state when switchTo is called. In all cases
        a tuple of three values is returned, some elements of which may be None
        depending on what resulted in the state exit. The three conditions are:

            #. If no timeout or DeviceEventTriggers have been specified with the ScreenState, switchto() returns after the window.flip() with::

                    (stateStartTime, None, None)

               where stateStartTime is the time the call to flip() returned.

            #. If a timeout has been specified, and that amount of time elapses from the startStartTime, then switchTo() returns with::

                    (stateStartTime, stateDuration, None)

               where:

                      * stateStartTime is the time the call to flip() returned.
                      * stateDuration is the time switchTo() returned minus
                      * stateStartTime; so it should be close to the timeout specified. It may be rounded to the next flip() time interval if something in the state is causing the screen to be updated each frame.

            #. If 1 - N DeviceEventTriggers have been set with the ScreenState, they are monitored to determine if any have triggered.
               If a DeviceEventTrigger has triggered, the triggering event and the triggers callback function are retrieved.
               The deviceEventTrigger is then reset, and the callback is called.

        If a callback returns True, the ScreenState is exited, returning (stateStartTime, stateDuration, exitTriggeringEvent), where:

                * **stateStartTime** is the time the call to flip() returned.
                * **stateDuration** is the time switchTo() returned minus stateStartTime; so it should be close to the timeout specified. It may be rounded to the next flip() time interval if something in the state is causing the screen to be updated each frame.
                * **exitTriggeringEvent** is the Device event (in dict form) that caused the ScreenState to exit.

        If the callback returns False, the ScreenState is not exited, and the the timeout period and DeviceEventTriggers cintinue to be checked.
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
    def __init__(self, experimentRuntime = None, eventTriggers = [], 
            hubServer = None, window = None,
            timeout = 60.0, background_color = (255, 255, 255)):
        hubServer = hubServer or experimentRuntime.hub
        window = window or experimentRuntime.window
        super(TargetDetection, self).__init__(hubServer, window,
                timeout = 10.0, eventTriggers = eventTriggers)

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

        text_kwargs = {'height': 40, 'font': 'Consolas', 'color': 'black'}
        fix = visual.TextStim(self.window, text = '+', **text_kwargs)
        self.stim.update({'fix': fix})

        target_kwargs = {'radius': 10, 'fillColor': 'white'}

        cues = {}
        # make the dot just like the target
        cues['dot'] = visual.Circle(self.window, **target_kwargs)
        # cues['arrow'] = visual.ImageStim()
        cues['word'] = visual.TextStim(self.window, **text_kwargs)

        target = visual.Circle(self.window, opacity = 0.0, **target_kwargs)
        self.stim.update({'target': target})

        # probe for response
        probe = visual.TextStim(self.window, text = '?', **text_kwargs)
        self.stim.update({'probe': probe})

        self.last_frame = None
        refresh = TimeTrigger(start_time = self.interval,
                delay = REFRESH_RATE, repeat_count = -1,
                trigger_function = self.refresh)
        self.addEventTrigger(refresh)

        self.target_opacity = None  # will be set on switch
        target_onset = 0.5          # TEMPORARY
        onset = TimeTrigger(start_time = self.getStateStartTime,
                delay = target_onset, repeat_count = 1,
                trigger_function = self.reveal)
        self.addEventTrigger(onset)

        probe_onset = 1.0
        probe_for_response = TimeTrigger(start_time=self.getStateStartTime,
                delay = probe_onset, repeat_count = 1,
                trigger_function = self.probe)
        self.addEventTrigger(probe_for_response)

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

    def reveal(self, *args, **kwargs):
        """ TimeTriggered when it's been target_onset since screen start. """
        self.stim['target'].setOpacity(self.target_opacity)
        return self.refresh()

    def probe(self, *args, **kwargs):
        """ Hide the masks, show the probe """
        self.stimNames = ['left', 'right', 'probe']
        return self.refresh()

    def switchTo(self, opacity, location_name,
                cue_type = None, cue_location = None):
        """ Set the target opacity and run the trial. """
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
