from numpy import array
from numpy.random import choice
from unipath import Path

from psychopy import visual, core
from psychopy.data import StairHandler
from psychopy.iohub import ioHubExperimentRuntime, EventConstants
from psychopy.iohub.util import (DeviceEventTrigger, InstructionScreen,
        ClearScreen)

from util.psychopy_helper import enter_subj_info
from util.screenstates import TargetDetection

class SpatialCueing(ioHubExperimentRuntime):
    """ Measure spatial cueing effects when targets are hard to see

    On each trial, participants are looking for a target to appear within
    the bounds of two rectangular masks, presented to the left and right
    of fixation.

    Baseline performance (ability to detect the target without any cues)
    is compared to performance with a cue. Cues can be spatial, symbolic,
    or auditory symbolic.

    - Spatial cues are identical to the target.
    - Symbolic cues are arrows, pointing to the left or the right mask.
    - Auditory symbolic cues are the spoken words "left" or "right".
    """
    def run(self, *args, **kwargs):
        self.running = True  # flags whether the user is trying to quit

        # iohub devices
        # -------------
        display = self.hub.devices.display
        self.window = visual.Window(display.getPixelResolution(),
                monitor = display.getPsychopyMonitorName(),
                units = display.getCoordinateType(),
                fullscr = True, allowGUI = False,
                screen = display.getIndex())
        self.keyboard = self.hub.devices.keyboard

        # iohub device triggers
        # ---------------------
        advance = DeviceEventTrigger(device = self.keyboard,
                event_type = EventConstants.KEYBOARD_PRESS,
                event_attribute_conditions = {'key': ' '})

        quit = DeviceEventTrigger(device = self.keyboard,
                event_type = EventConstants.KEYBOARD_PRESS,
                event_attribute_conditions = {'key': 'q'},
                trigger_function = self.request_quit)

        # Load experiment information
        # ---------------------------
        self.exp_info = yaml.load(open('spatial-cueing.yaml', 'r'))

        # Create experiment screens
        # -------------------------
        loaded_instructions = self.exp_info['instructions']
        instructions = TargetDetectionInstruction(self.window, self.hub,
                eventTriggers = [advance, quit],
                instructions = loaded_instructions)

        self.keys = {'y': 'present', 'n': 'absent'}
        self.detect_target = TargetDetection(self.window, self.hub,
                keys = self.keys.keys(), eventTriggers = [quit, ])
        self.intertrial = ClearScreen(self, timeout = 0.5)

        self.breakscreen = InstructionScreen(self,
                eventTriggers = [advance, quit],
                text = self.exp_info['break_screen'])

        # Get session variables
        # ---------------------
        subj_info_fields = self.exp_info['subj_info']
        self.subj_info, self.data_file = enter_subj_info(
            exp_name = 'spatial-cueing', options = subj_info_fields,
            exp_dir = './', data_dir = 'spatial-cueing-data')

        # Show instructions
        # -----------------
        instructions.switchTo('all')
        if not self.running:
            return

        # Calibrate target opacity
        # ------------------------
        critical_opacity = self.calibrate_target_opacity(subj_code)

        if not self.running:
            return

        # Test cueing effect
        # ------------------
        cue_type = self.subj_info['cue_type']
        self.test_cueing_effect(subj_code, critical_opacity, cue_type)

        if not self.running:
            return

        # End of experiment
        # -----------------
        end_of_experiment = self.exp_info['end_of_experiment']
        self.break_screen.setText(end_of_experiment)
        self.break_screen.switchTo()

    def calibrate_target_opacity(self, subj_code):
        output_name = Path('spatial-cueing', 'calibration', subj_code+'.txt')
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

            self.detect_target.prepare_trial(target_location, opacity)
            trial_data = self.detect_target.run_trial()
            trial_data.update({})
            # write trial_data to self.data_file
            

            _,rt,event = self.detect_target.switchTo(opacity,location_name)

            if not self.running:
                return

            response = self.keys[event.key]
            graded = (response == present_or_absent)

            # only update the opacity staircase if opacity was
            # relevant to the trial
            if present_or_absent == 'present':
                staircase.addResponse(graded)

            trial = [
                subj_code,
                staircase.thisTrialN,
                present_or_absent,
                opacity,
                location_name,
                response,
                rt,
                int(graded),
            ]

            row = '\t'.join(map(str, trial))
            output.write(row + '\n')

            self.intertrial.switchTo()

        output.close()

        if not self.running:
            return

        final_opacity = array(staircase.intensities[-10:]).mean()
        return final_opacity

    def test_cueing_effect(self, subj_code, opacity, cue_type):
        output_name = Path('spatial-cueing', 'testing', subj_code+'.txt')
        output = open(output_name, 'wb')

        for trial_ix in range(200):
            present_or_absent = choice(['present','absent'], p = [0.8,0.2])

            if present_or_absent == 'present':
                target_location_name = choice(['left', 'right'])
            else:
                target_location_name = None

            # select a cue location
            # cues are present on half of all trials
            cue_present_or_absent = choice(['present', 'absent'])
            if cue_present_or_absent == 'present':
                # if the cue is present, it points to the target if
                # there is one, otherwise it is selected at random
                # in other words: cues never point to the incorrect location
                cue_location_name = target_location_name or choice(['left', 'right'])
            else:
                cue_location_name = None

            self.detect_target.prepare_trial(
                target_location_name = target_location_name,
                opacity = opacity,
                cue_type = cue_type,
                cue_location_name = cue_location_name,
            )
            _, rt, event = self.detect_target.switchTo()

            if not self.running:
                return

            response = self.keys[event.key]
            graded = (response == present_absent)

            trial = [
                subj_code,
                trialN,
                cue_type,
                cue_location_name,
                present_or_absent,
                opacity,
                target_location_name,
                response,
                rt,
                int(graded),
            ]

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
