from numpy.random import choice

from psychopy import visual, core
from psychopy.data import StairHandler
from psychopy.iohub import ioHubExperimentRuntime, EventConstants
from psychopy.iohub.util import DeviceEventTrigger, InstructionScreen

from util.screenstates import TargetDetection

class SpatialCueing(ioHubExperimentRuntime):

    def run(self, *args, **kwargs):
        self.running = True

        # visuals
        display = self.hub.devices.display
        self.window = visual.Window(display.getPixelResolution(),
                monitor = display.getPsychopyMonitorName(),
                units = display.getCoordinateType(),
                fullscr = True, allowGUI = False,
                screen = display.getIndex())

        # devices
        self.keyboard = self.hub.devices.keyboard

        ## for advancing the screen past the instructions
        advance = DeviceEventTrigger(device = self.keyboard,
                event_type = EventConstants.KEYBOARD_PRESS,
                event_attribute_conditions = {'key': ' '})
        ## for trying to quit the experiment
        quit = DeviceEventTrigger(device = self.keyboard,
                event_type = EventConstants.KEYBOARD_PRESS,
                event_attribute_conditions = {'key': 'q'},
                trigger_function = self.request_quit)
        ## for responding if the target was present or absent
        self.response_keys = {'y': 'present', 'n': 'absent'}
        responder = DeviceEventTrigger(device = self.keyboard,
                event_type = EventConstants.KEYBOARD_PRESS,
                event_attribute_conditions = {'key': response_keys.keys()})

        # screens
        instructions = InstructionScreen(self, timeout = 1 * 60.0,
                eventTriggers = [advance, quit],
                text = "Press SPACEBAR to advance, or press 'q' to quit.")
        self.detect_target = TargetDetection(self,
                eventTriggers = [responder, quit])

        # Show instructions
        # -----------------
        instructions.switchTo()

        if not self.running:
            return

        # Calibrate
        # ---------
        critical = self.calibrate()

        # Test
        # ----
        pass

    def calibrate(self):
        staircase = StairHandler(0.5,
                nReversals = 2, stepSizes = [0.1, 0.05], stepType = 'log',
                nTrials = 10, nUp = 2, nDown = 2, minVal = 0.0, maxVal = 1.0)

        for opacity in staircase:
            present_or_absent = choice(['present', 'absent'], p = [0.8, 0.2])

            if present_or_absent == 'present':
                location_name = choice(['left', 'right'])
            else:
                location_name = None

            _, rt, event = self.detect_target.switchTo(opacity, location_name)

            if not self.running:
                break

            response = self.response_keys[event.key]
            graded = (response == present_or_absent)
            staircase.addResponse(graded)

            core.wait(1.0)

        if not self.running:
            return

        return staircase.calculateNextIntensity()

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
