import random
import time
import weakref
import yaml

from unipath import Path
from collections import OrderedDict

from psychopy import visual, core
from psychopy.iohub import ioHubExperimentRuntime, EventConstants
from psychopy.iohub.util import Trigger, TimeTrigger, DeviceEventTrigger
from psychopy.iohub.util import win32MessagePump

from util.dynamicmask import DynamicMask
from util.psychopy_helper import load_sounds

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

class SpatialCueing(ScreenState):
    def __init__(self, window, hubServer):
        """ Create all visual stims and event triggers """
        super(SpatialCueing, self).__init__(window, hubServer,
                eventTriggers = list(), timeout = 60.0)

        # Visual stims
        # ============
        self.exp = Path(__file__).absolute().ancestor(2)
        stim = Path(self.exp, 'stimuli')

        # masks
        # -----
        gutter = 400
        left = (-gutter/2, 0)
        right = (gutter/2, 0)
        # location_map also used for targets
        self.location_map = {'left': left, 'right': right}

        mask_size = 200
        mask_kwargs = {
            'win': self.window,
            'size': [mask_size, mask_size],
            'opacity': 0.8,
        }
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
        target_size = 80
        target_kwargs = {
            'win': self.window,
            'size': [target_size, target_size],
            'fillColor': 'white',
        }
        target = visual.Rect(opacity = 0.0, **target_kwargs)
        self.stim.update({'target': target})

        # create a jitter function for target positions
        edge_buffer = target_size/6
        outer_edge = mask_size/2
        inner_edge = outer_edge - target_size/2 - edge_buffer
        self.jitter = lambda p: (p[0] + random.uniform(-inner_edge/2, inner_edge/2),
                                 p[1] + random.uniform(-inner_edge/2, inner_edge/2))

        # cues
        # ----
        self.cues = {}
        self.cues['dot'] = visual.TextStim(self.window, text = 'x', **text_kwargs)
        self.cues['text'] = visual.TextStim(self.window, **text_kwargs)
        # self.cues['arrow'] = visual.ImageStim(self.window, Path(stim, 'arrow.png'))
        self.cues['nocue'] = visual.Rect(opacity = 0.0, **target_kwargs)

        self.sounds = {}
        self.sounds['left'] = load_sounds(stim, '*left*.wav')
        self.sounds['right'] = load_sounds(stim, '*right*.wav')

        # texts
        # -----
        (l, t, r, b) = hubServer.devices.display.getBounds()
        top = -(t - b)/2 - 60
        mid = -(t - b)/2 - 140
        bot =  (t - b)/2 + 150
        text_kwargs = {'win': window, 'wrapWidth': (r - l) * 0.5,
                'color': 'black', 'alignVert': 'top'}
        texts = {}
        texts['title'] = visual.TextStim(pos=(0,top), height=40, **text_kwargs)
        texts['body'] = visual.TextStim(pos =(0,mid), height=20, **text_kwargs)
        texts['footer'] =visual.TextStim(pos=(0,bot), height=20, **text_kwargs)
        self.stim.update(texts)

        # Event triggers
        # ==============
        self.triggers = {}  # like self.stim

        # responses
        # ---------
        self.response_map = {'y': 'present', 'u': 'absent'}
        responder = DeviceEventTrigger(device = hubServer.devices.keyboard,
                event_type = EventConstants.KEYBOARD_PRESS,
                event_attribute_conditions = {'key': self.response_map.keys()}, trigger_function = self.response)
        self.triggers['response'] = responder

        advance_trig = DeviceEventTrigger(hubServer.devices.keyboard,
                event_type = EventConstants.KEYBOARD_PRESS,
                event_attribute_conditions = {'key': ' '})
        self.triggers['advance'] = advance_trig

        # refresh
        # -------
        REFRESH_RATE = 0.0166
        refresh_trig = RefreshTrigger(self.getStateStartTime,
                delay = REFRESH_RATE, trigger_function = self.refresh,
                repeat_count = -1)
        self.triggers['refresh'] = refresh_trig

        # delay
        # -----
        delay_trig = RefreshTrigger(self.getStateStartTime,
                delay = self.get_delay, # callable, force update
                trigger_function = self.delay_reached, repeat_count = -1)
        self.triggers['delay'] = delay_trig

        self.trial_parts = OrderedDict()
        self.trial_parts['fixation'] = {
            'duration': 0.750,
            'stim': ['left', 'right', 'fix'],
            'trig': ['response', 'refresh', ]}  # triggers have to be present at state start
        self.trial_parts['cue'] = {
            'duration': 0.2,
            'stim': ['left', 'right', 'cue'],
            'trig': ['refresh', ]}
        self.trial_parts['interval'] = {
            'duration': 0.750,
            'stim': ['left', 'right'],
            'trig': ['refresh', ]}
        self.trial_parts['target'] = {
            'duration': 0.066,
            'stim': ['left', 'right', 'target'],
            'trig': ['response', 'refresh', ]}
        self.trial_parts['prompt'] = {
            'duration': 2.0,
            'stim': ['left', 'right', 'prompt'],
            'trig': ['response']}

    def show_text(self, details):
        for text_stim in ['title', 'body', 'footer']:
            if text_stim in details:
                self.stim[text_stim].setText(details[text_stim])
        if 'target' in details['visuals']:
            self.stim['target'].setPos(self.location_map['left'])
            self.stim['target'].setOpacity(0.8)
        self.prepare(details['visuals'], details['triggers'])
        self.switchTo()

    def run_trial(self, settings):
        """
        Required settings
        -----------------
        target_pos_x, target_pos_y
        target_opacity
        cue_type
        cue_loc
        cue_pos_x, cue_pos_y
        """
        if settings['target_loc']:
            target_pos = (settings['target_pos_x'], settings['target_pos_y'])
            target_opacity = settings['target_opacity']
        else:
            target_pos = (0,0)
            target_opacity = 0.0
        self.stim['target'].setPos(target_pos)
        self.stim['target'].setOpacity(target_opacity)

        cue_type = settings['cue_type']
        cue_loc = settings['cue_loc']
        if cue_type == 'dot':
            dot_pos = (settings['cue_pos_x'], settings['cue_pos_y'])
            self.cues['dot'].setPos(dot_pos)
        elif cue_type == 'text':
            self.cues['text'].setText(cue_loc)
        elif cue_type == 'sound':
            sound_options = self.sounds[cue_loc].values()
            sound_version = random.choice(sound_options)
            sound_version.reset()
            self.cues['sound'] = sound_version
        # elif cue_type == 'arrow':
        #     cue_loc = settings['cue_loc']
        #     angle_from_name = {'left': -90, 'right': 90}
        #     arrow_ori = angle_from_name[cue_loc]
        #     self.cues['arrow'].setOri(arrow_ori)
        else:
            assert cue_type == '', cue_type + ' not implemented'
            cue_type = 'nocue'
        self.stim['cue'] = self.cues[cue_type]

        self.state = 'fixation'
        start_part = self.trial_parts[self.state]
        self.current_state_delay = start_part['duration']
        self.prepare(start_part['stim'], start_part['trig'] + ['delay', ])

        self.target_onset = None
        stateStartTime, stateDuration, triggeringEvent = self.switchTo()

        try:
            rt = stateDuration - self.target_onset
        except TypeError:
            rt = 0.0
        rt = rt * 1000
        try:
            key = triggeringEvent.key
            response = self.response_map[key]
        except AttributeError:
            key = ''
            response = 'timeout'

        grader = {'present': 1, 'absent': 0, 'timeout': -1}
        is_correct = int(grader[response] == settings['target_present'])

        response_vars = {
            'rt': rt,
            'key': key,
            'response': response,
            'is_correct': is_correct,
        }
        settings.update(response_vars)
        return settings

    def prepare(self, stimNames, trigNames):
        self.stimNames = stimNames
        self.event_triggers = [self.triggers[name] \
                for name in trigNames]

    def response(self, *args, **kwargs):
        if self.state != 'fixation':
            return True
        else:
            return False

    def refresh(self, *args, **kwargs):
        """ Redraw the screen to update the masks """
        self.dirty = True
        self.flip()
        return False

    def get_delay(self):
        """ Return the delay for the current state """
        return self.current_state_delay

    def delay_reached(self, *args, **kwargs):
        """ Update the stimuli on the screen """
        print 'Finished state:', self.state, '; trigger args:', args
        ordered_parts = self.trial_parts.keys()
        next_part_ix = ordered_parts.index(self.state) + 1
        try:
            self.state = ordered_parts[next_part_ix]
        except IndexError:
            return True

        next_part = self.trial_parts[self.state]
        self.current_state_delay = next_part['duration']
        self.prepare(next_part['stim'], next_part['trig'] + ['delay', ])
        self.dirty = True
        flip_time = self.flip()
        print 'Starting state:', self.state, 'at time:', flip_time
        if self.state == 'target' and not self.target_onset:
            self.target_onset = flip_time - self._start_time
        return False


class SpatialCueing2(SpatialCueing):
    def __init__(self, *args, **kwargs):
        super(SpatialCueing2, self).__init__(*args, **kwargs)
        
        # refresh (adjusted)
        # ------------------
        REFRESH_RATE = 0.0166 * 2
        refresh_trig = RefreshTrigger(self.getStateStartTime,
                delay = REFRESH_RATE, trigger_function = self.refresh,
                repeat_count = -1)
        self.triggers['refresh'] = refresh_trig

        self.trial_parts['target'] = {
            'duration': 0.066 * 2,
            'stim': ['left', 'right', 'target'],
            'trig': ['response', 'refresh']}

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
    trial_parser.add_argument('-cue', choices = ['dot', 'text', 'sound'],
            help = 'Which cue should be used.')
    trial_parser.add_argument('-loc', '--location',
            choices = ['left', 'right'],
            help = 'Which version of the cue should be shown')

    instruct_parser = subparsers.add_parser('instruct',
            help = 'Show the instructions')
    instruct_parser.add_argument('screen_name',
            choices = ['welcome', 'target', 'cue', 'ready'],
            default = 'all', help = 'Which screen should be shown')

    args = parser.parse_args()

    io = launchHubServer()
    display = io.devices.display
    window = visual.Window(display.getPixelResolution(),
            monitor = display.getPsychopyMonitorName(),
            units = display.getCoordinateType(),
            fullscr = True, allowGUI = False,
            screen = display.getIndex())

    screen = SpatialCueing(window = window, hubServer = io)

    if args.view == 'trial':
        target_loc = args.target
        target_pos_x, target_pos_y = screen.location_map[target_loc]
        cue_type = args.cue or ''
        if args.location:
            cue_loc = args.location
        elif cue_type:
            print 'setting cue to target'
            cue_loc = target_loc
        else:
            cue_loc = ''
        cue_pos_x = ''
        cue_pos_y = ''
        if args.cue == 'dot':
            cue_pos_x, cue_pos_y = screen.location_map[cue_loc]

        settings = {
            'target_present': 'present',
            'target_loc': target_loc,
            'target_pos_x': target_pos_x,
            'target_pos_y': target_pos_y,
            'target_opacity': args.opacity,
            'cue_type': cue_type,
            'cue_loc': args.location,
            'cue_pos_x': cue_pos_x,
            'cue_pos_y': cue_pos_y,
        }
        print screen.run_trial(settings)
    else:  # view == 'instruct'
        texts = yaml.load(open('spatial-cueing.yaml', 'r'))['texts']
        screen.show_text(texts[args.screen_name])
