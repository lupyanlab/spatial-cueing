from psychopy import visual
from psychopy.iohub import ioHubExperimentRuntime, EventConstants
from psychopy.iohub.util import (ScreenState, TimeTrigger,
                                 DeviceEventTrigger)

from util.dynamicmask import DynamicMask

REFRESH_RATE = 0.01 # delay between screen flips during mask

class TargetDetection(ScreenState):
    """
    Visuals
    -------
    fix: fixation cross presented at trial start
    masks: two masks, one for each side of the screen.
    cue: the thing to present before the target
    target: circle to detect, appears overlapping with left or right mask
    """
    def __init__(self, experimentRuntime, eventTriggers):
        super(TargetDetection, self).__init__(experimentRuntime,
                timeout = 10.0, eventTriggers = eventTriggers)

        window = experimentRuntime.window

        gutter = 300  # distance from centroid to left/right locations
        left = (-gutter, 0)
        right = (gutter, 0)
        self.location_map = {'left': left, 'right': right}

        mask_kwargs = {'win': window, 'size': [200, 200]}
        masks = {}
        masks['left']  = DynamicMask(pos = left, **mask_kwargs)
        masks['right'] = DynamicMask(pos = right, **mask_kwargs)
        self.stim.update(masks)

        text_kwargs = {'height': 40, 'font': 'Consolas', 'color': 'black'}
        fix = visual.TextStim(window, text = '+', **text_kwargs)
        self.stim.update({'fix': fix})

        target = visual.Circle(window, radius = 10, pos = (-300, 0),
                fillColor = 'white', opacity = 0.0)
        self.stim.update({'target': target})

        # probe for response
        probe = visual.TextStim(window, text = '?', **text_kwargs)
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

    def switchTo(self, opacity, location_name):
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

    responder_keys = {'y': 'present', 'n':'absent'}
    responder = DeviceEventTrigger(device = io.devices.keyboard,
            event_type = EventConstants.KEYBOARD_PRESS,
            event_attribute_conditions = {'key': responder_keys.keys()})

    detect_target = TargetDetect(io, eventTriggers = [responder, ])

    _,rt,event = detect_target.switchTo(opacity = 1.0,
            location_name = 'right')
    print rt, event.key
