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
        super(TargetDetection, self).__init__(experimentRuntime, timeout = 10.0,
		eventTriggers = eventTriggers)

        window = experimentRuntime.window

	gutter = -300  # x-distance between left and right locations
	self.location_map = {'left': (-gutter, 0), 'right': (gutter, 0)}
        mask_kwargs = {'win': window, 'size': [200, 200]}
        masks = {}
        masks['left']  = DynamicMask(pos = self.location_map['left'], 
			**mask_kwargs)
        masks['right'] = DynamicMask(pos = self.location_map['right'],
			**mask_kwargs)
        self.stim.update(masks)
        self.stimNames.extend(['left', 'right'])

        fix = visual.TextStim(window, text = '+', height = 40,
			font = 'Consolas', color = 'black')
        self.stim.update({'fix': fix})
        self.stimNames.append('fix')

        target = visual.Circle(window, radius = 10, pos = (-300, 0), 
			fillColor = 'white', opacity = 0.0)
        self.stim.update({'target': target})
        self.stimNames.append('target')

	refresh = TimeTrigger(start_time = self.interval,
			delay = REFRESH_RATE,
			repeat_count = -1,
			trigger_function = self.refresh)
	self.addEventTrigger(refresh)
	self.last_frame = None

	self.target_opacity = None  # will be set on switch
	target_onset = 1.0 # TEMPORARY
	onset = TimeTrigger(start_time = self.getStateStartTime,
			delay = target_onset, repeat_count = 1,
			trigger_function = self.reveal)
	self.addEventTrigger(onset)

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

    def reveal(self, *args, **kwargs):
	""" Triggered when it's been target_onset since switching. """
	self.stim['target'].setOpacity(self.target_opacity)
	self.refresh()

    def switchTo(self, opacity, location_name):
        """ Set the target opacity and run the trial """
	if location_name: # target present trial
	    self.target_opacity = opacity
	    location = self.location_map[location_name]
	else:        # target absent trial
	    self.target_opactiy = 0.0
	    location = (0, 0)

	self.stim['target'].setPos(location)
	self.stim['target'].setOpacity(0.0)  # start with target hidden
	return super(TargetDetection, self).switchTo()
