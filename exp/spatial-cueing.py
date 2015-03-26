import yaml
from collections import OrderedDict
from numpy import array
from numpy.random import choice
from unipath import Path

from psychopy import visual, core
from psychopy.data import QuestHandler
from psychopy.iohub import ioHubExperimentRuntime, EventConstants
from psychopy.iohub.util import (DeviceEventTrigger, InstructionScreen,
        ClearScreen)

from util.psychopy_helper import enter_subj_info
from util.screenstates import TargetDetection, TargetDetectionInstructions

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

        # Load experiment information
        # ---------------------------
        self.exp_info = yaml.load(open('spatial-cueing.yaml', 'r'))

        # Get session variables
        # ---------------------
        subj_info_fields = self.exp_info['subj_info']
        self.subj_info, self.data_file = enter_subj_info(
            exp_name = 'spatial-cueing', options = subj_info_fields,
            exp_dir = './', data_dir = './spatial-cueing/data/')

        # Determine structure of data file
        # --------------------------------
        self.trial_data = OrderedDict()

        # session vars
        session_vars = ['subj_id', 'date', 'computer', 'experimenter']
        for session_var in session_vars:
            self.trial_data[session_var] = self.subj_info[session_var]

        # trial vars
        trial_vars = ['part', 'trial_ix',
                      'cue_type', 'cue_loc',
                      'target_loc', 'target_pos', 'target_opacity']
        for trial_var in trial_vars:
            self.trial_data[trial_var] = ''

        # response vars
        response_vars = ['rt', 'key', 'response', 'is_correct']
        for response_var in response_vars:
            self.trial_data[response_var] = ''

        # write header to each subject's data file
        row = '\t'.join(self.trial_data.keys())
        self.data_file.write(row + '\n')

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

        # Create experiment screens
        # -------------------------
        loaded_instructions = self.exp_info['instructions']
        instructions = TargetDetectionInstructions(self.window, self.hub,
                eventTriggers = [advance, quit],
                instructions = loaded_instructions)

        self.response_keys = {'y': 'present', 'n': 'absent'}
        self.detect_target = TargetDetection(self.window, self.hub,
                keys = self.response_keys, eventTriggers = [quit, ])
        self.intertrial = ClearScreen(self, timeout = 0.5)

        self.break_screen = InstructionScreen(self,
                eventTriggers = [advance, quit],
                text = self.exp_info['break_screen'])

        # Show instructions
        # -----------------
        instructions.switchTo('all')
        if not self.running:
            return

        # Calibrate target opacity
        # ------------------------
        critical_opacity = self.calibrate_target_opacity()

        if not self.running:
            return

        # Test cueing effect
        # ------------------
        cue_type = self.subj_info['cue_type']
        self.test_cueing_effect(cue_type, critical_opacity)

        if not self.running:
            return

        # End of experiment
        # -----------------
        end_of_experiment = self.exp_info['end_of_experiment']
        self.break_screen.setText(end_of_experiment)
        self.break_screen.switchTo()
        self.data_file.close()

    def calibrate_target_opacity(self):
        starting_opacity = 0.8
        desired_accuracy = 0.63  # bring them close to threshold
        nTrials = 100            # run 100 trials (don't use stopInterval)

        staircase = QuestHandler(startVal = starting_opacity,
                startValSd = 0.4,
                pThreshold = desired_accuracy,
                nTrials = nTrials, stopInterval = None,
                method = 'quantile', stepType = 'lin',
                minVal = 0.01, maxVal = 1.0)

        self.trial_data['part'] = 'calibration'
        for target_opacity in staircase:
            target_present = choice([True, False], p = [0.8, 0.2])

            if target_present:
                target_location_name = choice(['left', 'right'])
            else:
                target_location_name = None

            self.trial_data['trial_ix'] = staircase.thisTrialN
            trial_vars = self.detect_target.prepare_trial(
                    target_location_name = target_location_name,
                    target_opacity = target_opacity)
            self.trial_data.update(trial_vars)

            expected_response = 'present' if target_present else 'absent'
            response_vars = self.detect_target.run_trial(expected_response)
            self.trial_data.update(response_vars)

            if not self.running:
                return

            # only update the opacity staircase if opacity was
            # relevant to the trial
            if target_present:
                staircase.addResponse(response_vars['is_correct'])

            row = '\t'.join(map(str, self.trial_data.values()))
            self.data_file.write(row + '\n')

            self.intertrial.switchTo()

            trial_ix = self.trial_data['trial_ix']
            if trial_ix > 0 and trial_ix % 40 == 0:
                self.break_screen.switchTo()

        if not self.running:
            return

        # use quantile
        critical_opacity = staircase.quantile()
        print 'Using final_opacity: ', critical_opacity
        return critical_opacity

    def test_cueing_effect(self, cue_type, critical_opacity):
        self.trial_data['part'] = 'cueing_effect'
        for trial_ix in range(200):
            target_present = choice([True, False], p = [0.8, 0.2])

            if target_present:
                target_location_name = choice(['left', 'right'])
            else:
                target_location_name = None

            # select a cue location
            # cues are present on half of all trials
            cue_present = choice([True, False])
            if cue_present:
                # if the cue is present, it points to the target if
                # there is one, otherwise it is selected at random
                # in other words: cues never point to the incorrect location
                cue_location_name = target_location_name \
                    or choice(['left', 'right'])
            else:
                cue_location_name = None

            self.trial_data['trial_ix'] = trial_ix
            trial_vars = self.detect_target.prepare_trial(
                    target_location_name = target_location_name,
                    target_opacity = critical_opacity,
                    cue_type = cue_type,
                    cue_location_name = cue_location_name)
            self.trial_data.update(trial_vars)

            expected_response = 'present' if target_present else 'absent'
            response_vars = self.detect_target.run_trial(expected_response)
            self.trial_data.update(response_vars)

            if not self.running:
                return

            row = '\t'.join(map(str, self.trial_data.values()))
            self.data_file.write(row + '\n')

            self.intertrial.switchTo()

            if trial_ix > 0 and trial_ix % 40 == 0:
                self.break_screen.switchTo()

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
