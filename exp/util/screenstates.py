import weakref
import time
from unipath import Path
from collections import OrderedDict

from psychopy import visual, core
from psychopy.iohub import ioHubExperimentRuntime, EventConstants
from psychopy.iohub.util import Trigger, TimeTrigger, DeviceEventTrigger
from psychopy.iohub.util import win32MessagePump

from util.dynamicmask import DynamicMask

getTime = core.getTime

# Overwrite psychopy.iohub.util.visualUtil ScreenState class so that
# ScreenStates can be viewed using iohub's quick launch.
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

class RefreshTrigger(Trigger):
    """
    TimeTrigger's are used by ScreenState objects. A TimeTrigger
    associates a delay from the provided start_time parameter to when
    the classes triggered() method returns True. start_time and delay can be
    sec.msec float, or a callable object (that takes no parameters).
    """
    __slots__=['startTime', 'delay', '_start_time']
    def __init__(self, start_time, delay, repeat_count=0,
                 trigger_function = lambda a, b, c: True==True, user_kwargs={}):
        Trigger.__init__(self, trigger_function, user_kwargs, repeat_count)

        self._start_time = start_time

        if start_time is None or not callable(start_time):
            def startTimeFunc():
                if self._start_time is None:
                    self._start_time = getTime()
                return self._start_time
            self.startTime = startTimeFunc
        else:
            self.startTime = start_time

        self.delay = delay
        if not callable(delay):
            def delayFunc():
                return delay
            self.delay = delayFunc

    def triggered(self, **kwargs):
        if Trigger.triggered(self) is False:
            return False

        if self.startTime is None:
            start_time = kwargs.get('start_time')
        else:
            start_time = self.startTime()

        if self.delay is None:
            delay = kwargs.get('delay')
        else:
            delay = self.delay()

        ct = getTime()
        if not self._last_triggered_time:
            self._last_triggered_time = start_time
        if ct-self._last_triggered_time >= delay:
            self._last_triggered_time = ct
            self._last_triggered_event = ct
            self.triggered_count += 1
            return True
        return False

    def resetTrigger(self):
        self.resetLastTriggeredInfo()
        self.triggered_count = 0
        self._start_time = None

class TargetDetection(ScreenState):
    """
    ┌────────┐     ┌────────┐     ┌────────┐     ┌────────┐     ┌────────┐
    │        │     │        │     │        │     │        │     │        │
    │fixation│─────│  cue   │─────│interval│─────│ target │─────│ prompt │
    │        │     │        │     │        │     │        │     │        │
    └────────┘     └────────┘     └────────┘     └────────┘     └────────┘
                                                 ┼─── response time ──▶
    Variable delays
    ---------------
    start : self.getStateStartTime()
    delay : [fixation, cue, ..., prompt]
    """
    def __init__(self, window, hubServer, eventTriggers = list()):
        """
        Visual Objects
        --------------
        masks (2)
        fixation : text stim "+"
        cue - dot : rect stim
            - arrow : pic stim, rotated as needed
            - word : text stim "left" or "right"
        target : rect stim, presented in the left or right mask
        prompt : text stim "?" presented centrally after the target

        Timer Objects
        -------------
        refresh : to redraw the masks, should be close to refresh rate
        delay : when changes in the visuals should occur
        """
        super(TargetDetection, self).__init__(window, hubServer,
                eventTriggers = eventTriggers, timeout = 60.0)

        # Visual Objects
        # ==============
        exp = Path(__file__).absolute().ancestor(2)
        stim = Path(exp, 'stimuli')

        # masks
        # -----
        gutter = 300
        left = (-gutter, 0)
        right = (gutter, 0)
        self.location_map = {'left': left, 'right': right}

        size = 200
        mask_kwargs = {'win': self.window, 'size': [size,size], 'opacity': 0.8}
        masks = {}
        masks['left']  = DynamicMask(pos = left,  **mask_kwargs)
        masks['right'] = DynamicMask(pos = right, **mask_kwargs)
        self.stim.update(masks)

        # fixation and prompt
        # -------------------
        text_kwargs = {'height': 40, 'font': 'Consolas', 'color': 'black'}
        fix    = visual.TextStim(self.window, text = '+', **text_kwargs)
        prompt = visual.TextStim(self.window, text = '?', **text_kwargs)
        self.stim.update({'fix': fix, 'prompt': prompt})

        # target
        # ------
        target_kwargs = {'radius': 15, 'fillColor': 'white'}
        target = visual.Circle(self.window, opacity = 0.0, **target_kwargs)
        self.stim.update({'target': target})

        # cues
        # ----
        self.cues = {}
        self.cues['dot'] = visual.Circle(self.window, **target_kwargs)
        self.cues['arrow'] = visual.ImageStim(self.window, Path(stim, 'arrow.png'))
        self.cues['word'] = visual.TextStim(self.window, **text_kwargs)
        # cues added to self.stim on switchTo

        mask_names = ['left', 'right']
        self.visuals = {}
        self.visuals['fixation'] = mask_names + ['fix', ]
        self.visuals['cue'] = mask_names + ['cue', ]
        self.visuals['interval'] = mask_names
        self.visuals['target'] = mask_names + ['target', ]
        self.visuals['prompt'] = mask_names + ['prompt', ]

        # Timer Objects
        # =============

        # refresh
        # -------
        REFRESH_RATE = 0.02
        refresh = RefreshTrigger(start_time = self.getStateStartTime,
                delay = REFRESH_RATE, repeat_count = -1,
                trigger_function = self.refresh)
        self.addEventTrigger(refresh)

        # delay
        # -----
        self.durations = OrderedDict()
        self.durations['fixation'] = 0.5
        self.durations['cue'] = 0.2
        self.durations['interval'] = 0.5
        self.durations['target'] = 0.5
        self.durations['prompt'] = 2.0

        delay = TimeTrigger(start_time = self.getStateStartTime,
                delay = self.state_duration, # callable, force update
                repeat_count = -1, trigger_function = self.transition)
        self.addEventTrigger(delay)

    def refresh(self, *args, **kwargs):
        self.dirty = True
        self.delays['refresh'] += self.flip()
        return False

    def delay(self):
        return self.durations[self.state]

    def transition(self, *args, **kwargs):
        self.durations.pop(self.state)  # done with current state

        try:
            self.state = next(iter(self.durations))
        except StopIteration:
            # trial timeout
            return True

        self.stimNames = self.visuals[self.state]
        self.dirty = True
        self.flip()
        return False

    def switchTo(self, opacity, location_name,
                 cue_type = None, cue_location = None):
        """ Set the target opacity and run the trial. """
        if cue_type:
            self.stim['cue'] = self.cues[cue_type]

            if cue_type == 'dot':
                self.stim['cue'].setPos(self.location_map[cue_location])
            elif cue_type == 'word':
                self.stim['cue'].setText(cue_location)

        if location_name:
            # target present trial
            self.target_opacity = opacity
            location = self.location_map[location_name]
        else:
            # target absent trial
            # still draw it, but invisibly
            self.target_opacity = 0.0
            location = (0, 0)

        self.stim['target'].setPos(location)

        self.state = 'fixation'
        self.stimNames = self.visuals[self.state]
        return super(TargetDetection, self).switchTo()

if __name__ == '__main__':
    import argparse
    from psychopy.iohub import launchHubServer

    parser = argparse.ArgumentParser()
    parser.add_argument('target', choices = ['left', 'right'],
            default = 'left', help = 'Where should the target be shown')
    parser.add_argument('-o', '--opacity', type = float,
            default = 1.0, help = 'Opacity of the target')
    parser.add_argument('-cue', choices = ['dot', 'arrow', 'word'],
            help = 'Which cue should be used.')
    parser.add_argument('-loc', '--location', choices = ['left', 'right'],
            help = 'Which version of the cue should be shown')

    args = parser.parse_args()
    args.location = args.location or args.target

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

    _,rt,event = detect_target.switchTo(opacity = args.opacity,
            location_name = args.target,
            cue_type = args.cue, cue_location = args.location)
    print rt, event.key
