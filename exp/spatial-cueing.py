import random

from psychopy import visual, core
from psychopy.data import StairHandler
from psychopy.iohub import ioHubExperimentRuntime, EventConstants
from psychopy.iohub.util import DeviceEventTrigger, InstructionScreen

from util.screenstates import TargetDetection

class SpatialCueing(ioHubExperimentRuntime):

    def run(self, *args, **kwargs):
        self.running = True 

        display = self.hub.devices.display
        self.window = visual.Window(display.getPixelResolution(),
                monitor = display.getPsychopyMonitorName(),
                units = display.getCoordinateType(),
                fullscr = True, allowGUI = False,
                screen = display.getIndex())


        self.keyboard = self.hub.devices.keyboard
        advance = DeviceEventTrigger(device = self.keyboard,
                event_type = EventConstants.KEYBOARD_PRESS,
                event_attribute_conditions = {'key': ' '})
        quit = DeviceEventTrigger(device = self.keyboard,
                event_type = EventConstants.KEYBOARD_PRESS,
                event_attribute_conditions = {'key': 'q'},
                trigger_function = self.request_quit)
        instructions = InstructionScreen(self, timeout = 1 * 60.0,
                eventTriggers = [advance, quit],
                text = "Press SPACEBAR to advance, or press 'q' to quit.")

	response_keys = {'y': 'present', 'n': 'absent'}
        responder = DeviceEventTrigger(device = self.keyboard,
		event_type = EventConstants.KEYBOARD_PRESS,
		event_attribute_conditions = {'key': response_keys.keys()})
	detect_target = TargetDetection(self, 
		eventTriggers = [responder, quit])

        instructions.switchTo()
	if not self.running: return

        staircase = StairHandler(0.5, stepSizes = 0.1,
                nTrials = 10, nUp = 2, nDown = 2, stepType = 'lin',
                minVal = 0.0, maxVal = 1.0)

        for current_opacity in staircase:
            # first arg is start time, which we don't care about
	    opacity = staircase.next()
	    print "Using opacity:", opacity
	    
	    # will want to update this to control percentages
	    present = random.choice(['present', 'absent'])

	    if present == 'present':
		location_name = random.choice(['left', 'right'])
	    else:
		location_name = None
	    
            _, rt, event = detect_target.switchTo(
			opacity = opacity, location_name = location_name)

	    if not self.running: break

	    response = response_keys[event.key]
	    graded = (response == present)
	    print "Grade:", graded
	    staircase.addResponse(graded)
	    core.wait(1.0)

    def request_quit(self, *args, **kwargs):
        """ User requested to quit the experiment. """
        self.running = False
	print "Quit requested..."
        return True  # exits the screenstate

if __name__ == '__main__':
    from psychopy.iohub import module_directory
    module = module_directory(SpatialCueing.run)
    runtime = SpatialCueing(module, "experiment_config.yaml")
    runtime.start()
