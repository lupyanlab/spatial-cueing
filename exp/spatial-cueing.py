from psychopy import visual
from psychopy.iohub import ioHubExperimentRuntime, EventConstants
from psychopy.iohub.util import DeviceEventTrigger, InstructionScreen

from util.screenstates import TargetDetection

class SpatialCueing(ioHubExperimentRuntime):

    def run(self, *args, **kwargs):
        self.running = True 

        # conditions = importConditions('trial_conditions.xlsx')
        # trials = TrialHandler(conditions, 1)
        # self.hub.createTrialHandlerRecordTable(trials)

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

	detect_target = TargetDetection(self)

        instructions.switchTo()
	if not self.running: return

	start, duration, event = detect_target.switchTo()
	print start
	print duration
	print event

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
