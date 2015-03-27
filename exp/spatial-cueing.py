import yaml
from collections import OrderedDict
from numpy.random import choice
from unipath import Path

from psychopy import visual, core
from psychopy.data import QuestHandler
from psychopy.iohub import ioHubExperimentRuntime, EventConstants
from psychopy.iohub.util import DeviceEventTrigger, ClearScreen

from util.psychopy_helper import enter_subj_info
from util.screenstates import SpatialCueing

class SpatialCueingExperiment(ioHubExperimentRuntime):
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
        self.text_info = exp_info['texts']

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
            'cue_pos_x',
            'cue_pos_y',
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

        # runs trials and shows instructions
        self.screen = SpatialCueing(self.window, self.hub)
        self.intertrial = ClearScreen(self, timeout = 0.5)

        # Show instructions
        # -----------------
        for screen in ['welcome', 'target', 'practice']:
            details = self.text_info[screen]
            self.screen.show_text(details)

        # Run practice trials
        # -------------------
        self.run_practice_trials()

        # Calibrate target opacity
        # ------------------------
        ready_text_details = self.text_info['ready']
        self.screen.show_text(ready_text_details)
        critical_opacity = self.calibrate_target_opacity()

        # Introduce cue
        # -------------
        cue_type = self.subj_info['cue_type']
        introduce_cue = self.text_info['cue']
        self.screen.show_text(introduce_cue)
        
        # Test cueing effect: easy_block
        # ------------------------------
        #easy_block = self.text_info['easy']
        #self.screen.show_text(easy_block)
        self.test_cueing_effect(cue_type, 0.8)

        # Test cueing effect: hard block
        # ------------------------------
        #hard_block = self.text_info['hard']
        #self.screen.show_text(hard_block)
        self.test_cueing_effect(cue_type, critical_opacity)

        # Test cueing effect: easy block
        # ------------------------------
        #self.screen.show_text(easy_block)
        self.test_cueing_effect(cue_type, 0.8)

        # Test cueing effect: hard block
        # ------------------------------
        #self.screen.show_text(hard_block)
        self.text_cueing_effect(cue_type, critical_opacity)

        # End of experiment
        # -----------------
        end_details = self.text_info['end_of_experiment']
        self.screen.show_text(end_details)
        self.data_file.close()

    def run_trial(self, target_present, target_opacity, cue_type = None):
        """ Prepare the trial, run it, and save the data to disk

        On target present trials, randomly assigns targets to the left or
        right mask, and selects a location within that mask. Target opacity
        is provided.

        On cue present trials, assign cue location (and position, for spatial
        cues). If a cue and a target are both present on the same trial,
        the cue is always valid.
        """
        if target_present:
            target_loc = choice(['left', 'right'])
            target_pos = self.screen.location_map[target_loc]
            target_pos_x, target_pos_y = self.screen.jitter(target_pos)
        else:
            target_loc = ''
            target_pos_x, target_pos_y = '', ''
            target_opacity = ''

        self.trial_data['target_present'] = int(target_present)
        self.trial_data['target_loc'] = target_loc
        self.trial_data['target_pos_x'] = target_pos_x
        self.trial_data['target_pos_y'] = target_pos_y
        self.trial_data['target_opacity'] = target_opacity

        cue_pos_x = ''
        cue_pos_y = ''
        if not cue_type:
            cue_present = False
            cue_loc = ''
            cue_type = ''
        else:
            cue_present = True
            cue_loc = target_loc or choice(['left', 'right'])
            if cue_type == 'dot':
                if target_present:
                    cue_pos_x, cue_pos_y = target_pos_x, target_pos_y
                else:
                    cue_pos = self.screen.location_map[cue_loc]
                    cue_pos_x, cue_pos_y = cue_pos  # show dot cue centrally

        self.trial_data['cue_present'] = int(cue_present)
        self.trial_data['cue_type'] = cue_type
        self.trial_data['cue_loc'] = cue_loc
        self.trial_data['cue_pos_x'] = cue_pos_x
        self.trial_data['cue_pos_y'] = cue_pos_y

        self.trial_data = self.screen.run_trial(self.trial_data)

        row = '\t'.join(map(str, self.trial_data.values()))
        self.data_file.write(row + '\n')

        if self.trial_data['response'] == 'timeout':
            self.screen.show_text(self.text_info['timeout'])
        else:
            self.intertrial.switchTo()

    def run_practice_trials(self):
        """ Run a few practice trials with highly visible targets """
        self.trial_data['part'] = 'practice'
        for trial_ix in range(10):
            target_present = choice([True, False], p = [0.8, 0.2])

            self.trial_data['trial_ix'] = trial_ix
            self.run_trial(target_present, 1.0, cue_type = None)

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

            self.trial_data['trial_ix'] = staircase.thisTrialN
            print "Using target opacity", target_opacity
            self.run_trial(target_present, target_opacity, cue_type = None)

            if target_present:
                staircase.addResponse(self.trial_data['is_correct'])

            trial_ix = self.trial_data['trial_ix']
            if trial_ix > 0 and trial_ix % 40 == 0:
                self.screen.show_text(self.text_info['break'])

        # use quantile
        critical_opacity = staircase.quantile()
        print 'Using final_opacity: ', critical_opacity
        return critical_opacity

    def test_cueing_effect(self, cue_type, critical_opacity):
        """ Determine the effect of cueing on near-threshold detection """
        self.trial_data['part'] = 'cueing_effect'
        for trial_ix in range(80):
            target_present = choice([True, False], p = [0.8, 0.2])
            cue_present = choice([True, False])
            cue_this_trial = cue_type if cue_present else None

            self.trial_data['trial_ix'] = trial_ix
            self.run_trial(target_present, critical_opacity, cue_this_trial)

            if trial_ix > 0 and trial_ix % 40 == 0:
                break_details = self.text_info['break']
                self.screen.show_text(break_details)

if __name__ == '__main__':
    from psychopy.iohub import module_directory
    module = module_directory(SpatialCueingExperiment.run)
    runtime = SpatialCueingExperiment(module, 'experiment_config.yaml')
    runtime.start()
