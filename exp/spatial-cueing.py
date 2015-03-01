from numpy import array
from numpy.random import choice
from unipath import Path

from psychopy import visual, core
from psychopy.data import StairHandler
from psychopy.iohub import ioHubExperimentRuntime, EventConstants
from psychopy.iohub.util import (DeviceEventTrigger, InstructionScreen,
        ClearScreen)

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
        self.keys = {'y': 'present', 'n': 'absent'}
        responder = DeviceEventTrigger(device = self.keyboard,
                event_type = EventConstants.KEYBOARD_PRESS,
                event_attribute_conditions = {'key': self.keys.keys()})

        # screens
        instructions = InstructionScreen(self, timeout = 1 * 60.0,
                eventTriggers = [advance, quit],
                text = "Press SPACEBAR to advance, or press 'q' to quit.")
        self.detect_target = TargetDetection(self,
                eventTriggers = [responder, quit])
        self.intertrial = ClearScreen(self, timeout = 0.5)

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
        subj_code = 'SPC101'
        output_name = Path('spatial-cueing','calibration',subj_code+'.txt')
        output = open(output_name, 'wb')

        desired_accuracy = 0.5
        nDown = desired_accuracy * 10
        nUp = 10 - desired_accuracy * 10

        starting_opacity = 0.8
        stepSizes = [0.2, 0.1, 0.06, 0.03]
        nTrials = 100

        staircase = StairHandler(starting_opacity, minVal=0.01, maxVal=1.0,
                stepSizes = stepSizes, stepType = 'lin',
                nTrials = nTrials, nUp = nUp, nDown = nDown)

        for opacity in staircase:
            present_or_absent = choice(['present','absent'], p = [0.8,0.2])

            if present_or_absent == 'present':
                location_name = choice(['left', 'right'])
            else:
                location_name = None

            _,rt,event = self.detect_target.switchTo(opacity,location_name)

            if not self.running:
                return

            response = self.keys[event.key]
            graded = (response == present_or_absent)

            # only update the opacity staircase if opacity was
            # relevant to the trial
            if present_or_absent == 'present':
                staircase.addResponse(graded)

            trial = [subj_code,
                    staircase.thisTrialN,
                    present_or_absent,
                    opacity,
                    location_name,
                    response,
                    rt,
                    int(graded)]

            row = '\t'.join(map(str, trial))
            output.write(row + '\n')

            self.intertrial.switchTo()

        output.close()

        if not self.running:
            return

        final_opacity = array(staircase.intensities[-10:]).mean()
        return final_opacity

    def test(self, subj_code, opacity):
        output_name = Path('spatial-cueing', 'testing', subj_code+'.txt')
        output = open(output_name, 'wb')

        _,rt,event = self.detect_target.switchTo(opacity, 'left')

        if not self.running:
            return

        response = self.keys[event.key]
        graded = (response == present_absent)

        trial = [subj_code,
                trialN,
                cue_type,
                cue_dir,
                present_or_absent,
                opacity,
                location_name,
                response,
                rt,
                int(graded)]

        row = '\t'.join(map(str, trial))
        output.write(row + '\n')

        self.intertrial.switchTo()
   
        output.close()

        if not self.running:
            return

    def request_quit(self, *args, **kwargs):
        """ User requested to quit the experiment. """
        self.running = False
        print "Quit requested..."
        return True  # exits the screenstate

if __name__ == '__main__':
    from psychopy.iohub import module_directory
    module = module_directory(SpatialCueing.run)
    runtime = SpatialCueing(module, 'experiment_config.yaml')
    runtime.start()
