import weakref
import time
import yaml
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

# Overwrite psychopy.iohub.util.visualUtil InstructionScreen class to
# use the modified ScreenState class, above
class InstructionScreen(ScreenState):
    def __init__(self, window, hubServer, eventTriggers = list(),
                timeout = 10 * 60.0, background_color = (255, 255, 255)):
        super(InstructionScreen, self).__init__(window, hubServer,
                eventTriggers, timeout, background_color)

        l, t, r, b = self.experimentRuntime().devices.display.getBounds()
        self.stim['TEXTLINE'] = visual.TextStim(self.window(), text=text,
                    pos=text_pos, height=text_height, color=text_color,
                    colorSpace='rgb255', alignHoriz='center',
                    alignVert='center', units='pix', wrapWidth=(r-l)*.9)
        self.stimNames.append('TEXTLINE')

    def setText(self, text):
        self.stim['TEXTLINE'].setText(text)
        self.dirty = True

    def setTextColor(self, rgbColor):
        self.stim['TEXTLINE'].setColor(rgbColor, 'rgb255')
        self.dirty = True

    def setTextSize(self,size):
        self.stim['TEXTLINE'].setSize(size)
        self.dirty = True

    def setTextPosition(self, pos):
        self.stim['TEXTLINE'].setPos(pos)

    def flip(self, text=''):
        if text is None:
            text = "INSTRUCT_SCREEN SYNC: [%s] [%s] "%(self.stim['TEXTLINE'].text[0:30], text)
        return ScreenState.flip(self, text)

class RefreshTrigger(TimeTrigger):
    """ TimeTrigger every X msec """
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

        # RefreshTrigger functionality:
        # Count delay from time of last trigger (not from state start time)
        ct = getTime()

        if not self._last_triggered_time:
            self._last_triggered_time = start_time
        if ct-self._last_triggered_time >= delay:
            self._last_triggered_time = ct
            self._last_triggered_event = ct
            self.triggered_count += 1
            return True
        return False

    def resetLastTriggeredInfo(self):
        self._last_triggered_event = None
        # don't reset self._last_triggered_event

class TargetDetection(ScreenState):
    """
    Variable delays
    ---------------
    start : self.getStateStartTime()
    delay : [fixation, cue, ..., prompt]
    """
    def __init__(self, window, hubServer, keys = ['y', 'n'], 
            eventTriggers = list(), timeout = 60.0):
        """
        Visual objects
        --------------
        masks (2)
        fixation: text stim "+"
        cue - dot: rect stim
            - arrow: pic stim, rotated as needed
            - word: text stim "left" or "right"
        target: rect stim, presented in the left or right mask
        prompt: text stim "?" presented centrally after the target

        Timer objects
        -------------
        refresh: to redraw the masks, should be close to refresh rate
        delay: when changes in the visuals should occur
        """
        super(TargetDetection, self).__init__(window, hubServer,
                eventTriggers = eventTriggers, timeout = timeout)

        # Visual objects
        # ==============
        self.exp = Path(__file__).absolute().ancestor(2)
        stim = Path(self.exp, 'stimuli')

        # masks
        # -----
        gutter = 300
        left = (-gutter, 0)
        right = (gutter, 0)
        self.location_map = {'left': left, 'right': right}
        ## location_map also used for dot cues and targets

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
        target_kwargs = {'radius': 25, 'fillColor': 'white'}
        target = visual.Circle(self.window, opacity = 0.0, **target_kwargs)
        self.stim.update({'target': target})

        # cues
        # ----
        self.cues = {}
        self.cues['dot'] = visual.Circle(self.window, **target_kwargs)
        #self.cues['arrow'] = visual.ImageStim(self.window, Path(stim, 'arrow.png'))
        self.cues['word'] = visual.TextStim(self.window, **text_kwargs)
        # cues added to self.stim on switchTo

        mask_names = ['left', 'right']
        self.visuals = {}
        self.visuals['fixation'] = mask_names + ['fix', ]
        self.visuals['cue']      = mask_names + ['cue', ]
        self.visuals['interval'] = mask_names
        self.visuals['target']   = mask_names + ['target', ]
        self.visuals['prompt']   = mask_names + ['prompt', ]

        # Timer objects
        # =============
        self.triggers = {}  # like self.stim, but for triggers

        # refresh
        # -------
        REFRESH_RATE = 0.02
        refresh_trig = RefreshTrigger(self.getStateStartTime,
                delay = REFRESH_RATE, trigger_function = self.refresh,
                repeat_count = -1)
        self.triggers['refresh_trig'] = refresh_trig
        self.addEventTrigger(refresh_trig) # by default, add refresh

        # delay
        # -----
        self.delays = OrderedDict()
        self.delays['fixation'] = 0.5
        self.delays['cue']      = 0.2
        self.delays['interval'] = 0.5
        self.delays['target']   = 0.5
        self.delays['prompt']   = 2.0

        delay_trig = RefreshTrigger(self.getStateStartTime,
                delay = self.get_delay, # callable, force update
                trigger_function = self.transition, repeat_count = -1)
        self.addEventTrigger(delay_trig)

        # Responses
        # ---------
        responder = DeviceEventTrigger(device = hubServer.devices.keyboard,
                event_type = EventConstants.KEYBOARD_PRESS,
                event_attribute_conditions = {'key': keys},
                trigger_function = self.response)
        self.triggers['response_trig'] = responder
        self.addEventTrigger(responder)

    def refresh(self, *args, **kwargs):
        """ Redraw the screen to update the masks """
        self.dirty = True
        self.flip()
        return False

    def get_delay(self):
        """ Return the current delay """
        return self.current_state_delay

    def transition(self, *args, **kwargs):
        """ Update the stimuli on the screen """
        self.delays.pop(self.state)  # done with current state

        try:
            self.state = next(iter(self.delays))
        except StopIteration:
            # trial has timed out without a response
            return True

        self.stimNames = self.visuals[self.state]
        self.current_state_delay = self.delays[self.state]
        self.dirty = True
        self.flip()
        return False

    def response(self, *args, **kwargs):
        """ User hit one of the response keys """
        if self.state in ['target', 'prompt']:
            return True
        else:
            return False

    def prepare_trial(self, location_name, opacity = 0.0,
                 cue_type = None, cue_location = None):
        """ Set the target opacity and run the trial. """
        if cue_type == 'dot':
            self.cues[cue_type].setPos(self.location_map[cue_location])
        elif cue_type == 'word':
            self.cues[cue_type].setText(cue_location)
        else:
            # no cue trial
            cue_type = 'dot'
            self.cues[cue_type].setOpacity(0.0)

        self.stim['cue'] = self.cues[cue_type]

        if location_name:
            # target present trial
            location = self.location_map[location_name]
        else:
            # target absent trial
            # still draw it, but invisibly
            opacity = 0.0
            location = (0, 0)

        self.stim['target'].setPos(location)
        self.stim['target'].setOpacity(opacity)

        self.state = 'fixation'
        self.stimNames = self.visuals[self.state]
        self.current_state_delay = self.delays[self.state]

class TargetDetectionInstructions(TargetDetection):
    def __init__(self, window, hubServer, eventTriggers = list()):
        super(TargetDetectionInstructions, self).__init__(window, 
                hubServer, eventTriggers = eventTriggers, timeout = 60.0)

        (l, t, r, b) = hubServer.devices.display.getBounds()
        title_y = -(t - b)/2 - 40
        text_y = -(t - b)/2 - 100
        text_kwargs = {'win': window, 'wrapWidth': (r - l) * 0.5, 
                'color': 'black', 'alignVert': 'top'}
        self.stim['title'] = visual.TextStim(pos = (0,title_y), height = 40,
                **text_kwargs)
        self.stim['text'] = visual.TextStim(pos = (0,text_y), height = 20,
                **text_kwargs)

        advance_trig = DeviceEventTrigger(hubServer.devices.keyboard,
                event_type = EventConstants.KEYBOARD_PRESS,
                event_attribute_conditions = {'key': [' ', ]})
        self.triggers['advance_trig'] = advance_trig
        
        spc_yaml = Path(self.exp, 'spatial-cueing.yaml')
        self.instructions = yaml.load(open(spc_yaml, 'r'))
    
    def prepare_instructions(self, screen_name):
        details = self.instructions[screen_name]

        self.stim['title'].setText(details['title'])
        self.stim['text'].setText(details['text'])

        if screen_name == 'target':
            self.stim['target'].setPos(self.location_map['left'])
            self.stim['target'].setOpacity(1.0)
        elif screen_name == 'cue':
            self.cues['word'].setText('left')
            self.stim['cue'] = self.cues['word']
        
        self.stimNames = details['visuals']
        self.event_triggers = [self.triggers[trig_name] \
                for trig_name in details['triggers']]

if __name__ == '__main__':
    import argparse
    from psychopy.iohub import launchHubServer

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest = 'view')

    trial_parser = subparsers.add_parser('trial', 
            help = 'Show a sample trial')
    trial_parser.add_argument('target', choices = ['left', 'right'],
            default = 'left', help = 'Where should the target be shown')
    trial_parser.add_argument('-o', '--opacity', type = float,
            default = 1.0, help = 'Opacity of the target')
    trial_parser.add_argument('-cue', choices = ['dot', 'arrow', 'word'],
            help = 'Which cue should be used.')
    trial_parser.add_argument('-loc', '--location', 
            choices = ['left', 'right'],
            help = 'Which version of the cue should be shown')

    instruct_parser = subparsers.add_parser('instruct',
            help = 'Show the instructions')
    possible_screen_names = ['welcome', 'target', 'cue', 'ready']
    instruct_parser.add_argument('screen_name',
            choices = possible_screen_names + ['all', ],
            default = 'all', help = 'Which screen should be shown')

    args = parser.parse_args() 
   
    io = launchHubServer()
    display = io.devices.display
    window = visual.Window(display.getPixelResolution(),
            monitor = display.getPsychopyMonitorName(),
            units = display.getCoordinateType(),
            fullscr = True, allowGUI = False,
            screen = display.getIndex())

    if args.view == 'trial':
        args.location = args.location or args.target

        keys = ['y', 'n']
        detect_target = TargetDetection(hubServer=io, window=window, keys=keys)
        detect_target.prepare_trial(args.target, args.opacity,
                cue_type = args.cue, cue_location = args.location)
        _,rt,event = detect_target.switchTo()
        print rt, event.key
    else:  # view == 'instruct'
        instructions = TargetDetectionInstructions(window, io)
        if args.screen_name == 'all':
            for screen_name in possible_screen_names:
                instructions.prepare_instructions(screen_name)
                instructions.switchTo()
        else:
            instructions.prepare_instructions(args.screen_name)
            instructions.switchTo()
