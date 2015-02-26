from psychopy import visual
from psychopy.iohub import ioHubExperimentRuntime, EventConstants
from psychopy.iohub.util import (ScreenState, TimeTrigger, 
                                 DeviceEventTrigger)

from util import DynamicMask

class TargetDetection(ScreenState):
    """
    Visuals
    -------
    fix: fixation cross presented at trial start
    masks: two masks, one for each side of the screen.
    cue: the thing to present before the target
    target: circle to detect, appears overlapping with left or right mask
    """
    def __init__(self, experimentRuntime):
        super(TargetDetection).__init__(self, experimentRuntime)

        window = self.experimentRuntime().window

        mask_kwargs = {'window': window, 'width': 80, 'height': 80}
        masks = {}
        masks['left']  = DynamicMask(pos = (-200, 0), **mask_kwargs)
        masks['right'] = DynamicMask(pos = (200, 0), **mask_kwargs)
        self.stim.update(masks)
        self.stimNames.extend(['left', 'right'])

        fix = visual.TextStim(window, text = '+', font = 'Consolas',
                height = 10)
        self.stim.update({'fix': fix})
        self.stimNames.append('fix')

        target = visual.Circle(window, radius = 10)
        self.stim.update({'target': target})
        self.stimNames.append('target')

        keyboard = self.experimentRuntime().keyboard
        responder = DeviceEventTrigger(device = keyboard,
            event_type = EventConstants.KEYBOARD_PRESS,
            event_attribute_conditions = {'key': ['f', 'j']})
        self.addEventTrigger(responder)
