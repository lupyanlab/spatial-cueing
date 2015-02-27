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
    def __init__(self, experimentRuntime):
        super(TargetDetection, self).__init__(experimentRuntime, timeout = 10.0)

        window = experimentRuntime.window

        mask_kwargs = {'win': window, 'size': [80, 80]}
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

	refresh = TimeTrigger(start_time = self.interval,
			delay = REFRESH_RATE,
			repeat_count = -1,
			trigger_function = self.refresh)
	self.addEventTrigger(refresh)
	self.last_frame = None

        keyboard = experimentRuntime.keyboard
        responder = DeviceEventTrigger(device = keyboard,
            event_type = EventConstants.KEYBOARD_PRESS,
            event_attribute_conditions = {'key': ['f', 'j']})
        self.addEventTrigger(responder)

    def interval(self):
	""" Return the time of the last flip.

	For the first interval, start when the ScreenState flips. For subsequent
	intervals, return the last_frame variable which is updated when the 
	screen is rebuilt.
	"""
	if self.last_frame == None:
	    self.last_frame = self.getStateStartTime()
	return self.last_frame

    def refresh(self, *args, **kwargs):
	""" Triggered when it's been REFRESH_RATE since last flip. """
	self.dirty = True
	self.last_frame = self.flip()
	return False
