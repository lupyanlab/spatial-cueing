import yaml
from collections import OrderedDict
from numpy.random import choice
from unipath import Path

from psychopy import visual, core
from psychopy.data import QuestHandler
from psychopy.iohub import ioHubExperimentRuntime, EventConstants
from psychopy.iohub.util import DeviceEventTrigger, ClearScreen

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

    The presence of a cue does not predict whether or not a target will
    be presented on the trial. Cue direction is never invalid, e.g.,
    there are no trial in which the subject is cued to the right and
    the target is presented to the left.
    """
    def run(self, *args, **kwargs):
        # Load the experiment info
        # ------------------------
        exp_info = yaml.load(open('spatial-cueing.yaml', 'r'))
        subj_info_fields = exp_info['subj_info']
        text_screen_states = exp_info['texts']

        # Get the session info
        # --------------------
        self.subj_info, self.data_file = enter_subj_info(
            exp_name = 'spatial-cueing', options = subj_info_fields,
            exp_dir = './spatial-cueing/', data_dir = './spatial-cueing/data/')

        # Set the structure of data file
        # ------------------------------
        # session_vars: variables that are fixed for each subject
        # trial_vars: variables that vary from trial to trial
        # response_vars: variables generated based on the subject's response
        self.trial_data = OrderedDict()

        session_vars = [
            'subj_id',
            'date',
            'computer',
            'experimenter',
        ]
        for session_var in session_vars:
            self.trial_data[session_var] = self.subj_info[session_var]

        trial_vars = [
            'part',
            'trial_ix',
            'cue_present',
            'cue_type',
            'cue_loc',
            'target_present',
            'target_loc',
            'target_pos_x',
            'target_pos_y',
            'target_opacity',
        ]
        for trial_var in trial_vars:
            self.trial_data[trial_var] = ''

        response_vars = [
            'rt',
            'key',
            'response',
            'is_correct',
        ]
        for response_var in response_vars:
            self.trial_data[response_var] = ''

        # write header to each subject's data file
        row = '\t'.join(self.trial_data.keys())
        self.data_file.write(row + '\n')

        # Create experiment screens
        # -------------------------
        display = self.hub.devices.display
        self.window = visual.Window(display.getPixelResolution(),
                monitor = display.getPsychopyMonitorName(),
                units = display.getCoordinateType(),
                fullscr = True, allowGUI = False,
                screen = display.getIndex())

        self.text_screen = TargetDetectionInstructions(self.window, self.hub)
        self.detect_target = TargetDetection(self.window, self.hub)
        self.intertrial = ClearScreen(self, timeout = 0.5)

        # Show instructions
        # -----------------
        for screen in ['welcome', 'target']:
            details = text_screen_states[screen]
            self.text_screen.show_text(details)

        # Run practice trials
        # -------------------
        self.text_screen.show_text('practice')
        self.run_practice_trials()
        if not self.running:
            return

        # Calibrate target opacity
        # ------------------------
        self.text_screen.show_text('ready')
        critical_opacity = self.calibrate_target_opacity()
        if not self.running:
            return

        # Test cueing effect
        # ------------------
        self.text_screen.show_text('cue')
        cue_type = self.subj_info['cue_type']
        self.test_cueing_effect(cue_type, critical_opacity)
        if not self.running:
            return

        # End of experiment
        # -----------------
        self.text_screen.show_text('end_of_experiment')
        self.data_file.close()

    def run_trial(self, target_present, cue_present, target_opacity,
            cue_type = None):
        """ Prepare the trial, run it, and save the data to disk

        If it's a target present trial, pick a location at random. If it's
        a cue present trial, pick a location based on where the target is.
        """
        if target_present:
            target_location_name = choice(['left', 'right'])
        else:
            target_location_name = ''

        if cue_present:
            cue_location_name = target_location_name \
                or choice(['left', 'right'])
        else:
            cue_location_name = ''

        trial_vars = self.detect_target.prepare_trial(
                target_location_name = target_location_name,
                target_opacity = target_opacity,
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

    def run_practice_trials(self):
        """ Run a few practice trials with highly visible targets """
        self.trial_data['part'] = 'practice'
        for trial_ix in range(10):
            target_present = choice([True, False], p = [0.8, 0.2])
            cue_present = False

            self.trial_data['trial_ix'] = trial_ix
            self.run_trial(target_present, cue_present, target_opacity = 1.0)

    def calibrate_target_opacity(self):
        """ Adjust the target opacity until performance is around 50% """
        self.trial_data['part'] = 'calibration'

        staircase = QuestHandler(startVal = 0.8,
            startValSd = 0.4,
            pThreshold = 0.63,   # bring them close to threshold
            nTrials = 100,       # run 100 trials (don't use stopInterval)
            stopInterval = None,
            method = 'quantile',
            stepType = 'lin',
            minVal = 0.01, maxVal = 1.0)

        for target_opacity in staircase:
            target_present = choice([True, False], p = [0.8, 0.2])
            cue_present = False

            self.trial_data['trial_ix'] = staircase.thisTrialN
            self.run_trial(target_present, cue_present,
                    target_opacity = target_opacity)

            if target_present:
                staircase.addResponse(self.trial_data['is_correct'])

            trial_ix = self.trial_data['trial_ix']
            if trial_ix > 0 and trial_ix % 40 == 0:
                self.text_screen.show_text('break')

        if not self.running:
            return

        # use quantile
        critical_opacity = staircase.quantile()
        print 'Using final_opacity: ', critical_opacity
        return critical_opacity

    def test_cueing_effect(self, cue_type, critical_opacity):
        """ Determine the effect of cueing on near-threshold detection """
        self.trial_data['part'] = 'cueing_effect'
        for trial_ix in range(200):
            target_present = choice([True, False], p = [0.8, 0.2])
            cue_present = choice([True, False])

            self.trial_data['trial_ix'] = trial_ix
            self.run_trial(target_present, cue_present,
                    target_opacity = critical_opacity, cue_type = cue_type)

            if not self.running:
                return

            if trial_ix > 0 and trial_ix % 40 == 0:
                self.text_screen.show_text('break')

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
