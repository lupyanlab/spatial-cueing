import yaml
from collections import OrderedDict
from numpy.random import choice
import random
from unipath import Path

from psychopy import visual, core
from psychopy.data import QuestHandler
from psychopy.iohub import ioHubExperimentRuntime, EventConstants
from psychopy.iohub.util import DeviceEventTrigger, ClearScreen

from util.psychopy_helper import enter_subj_info
from util.screenstates import SpatialCueing2

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
        exp_info = yaml.load(open('spatial-cueing-no-calibration.yaml', 'r'))
        subj_info_fields = exp_info['subj_info']
        self.text_info = exp_info['texts']

        # Get the session info
        # --------------------
        self.subj_info, self.data_file = enter_subj_info(
            exp_name = 'spatial-cueing-no-calibration', options = subj_info_fields,
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


        # the same screenstate runs the trials and shows instructions
        self.screen = SpatialCueing2(self.window, self.hub)
        self.intertrial = ClearScreen(self, timeout = 0.5)

        self.show_instructions()
        self.run_practice_trials(num_trials = 10, target_opacity = 1.0,
                text_when_done = 'harder')
        self.run_practice_trials(num_trials = 10, target_opacity = 0.6,
                text_when_done = 'ready')

        # Don't try to calibrate the critical opacity because
        # performance is just too noisy and it's not worth it.
        # Instead, run participants in both cueing conditions
        # in random order
        critical_opacity = 0.6
        possible_orders = [('dot', 'sound', 'dot', 'sound', 'dot', 'sound'),
                           ('sound', 'dot', 'sound', 'dot', 'dot', 'sound')]
        selected_order = random.choice(possible_orders)

        for current_block in selected_order:
            self.test_cueing_effect(
                    cue_type = current_block,
                    critical_opacity = critical_opacity)

        self.end_experiment()

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

    def show_instructions(self):
        for screen in ['welcome', 'target', 'practice']:
            details = self.text_info[screen]
            self.screen.show_text(details)

    def run_practice_trials(self, num_trials = 20, target_opacity = 1.0,
            text_when_done = 'ready'):
        """ Run a few practice trials with highly visible targets """
        self.trial_data['part'] = 'practice'
        for trial_ix in range(num_trials):
            target_present = choice([True, False], p = [0.6, 0.4])

            self.trial_data['trial_ix'] = trial_ix
            self.run_trial(target_present, target_opacity, cue_type = None)

        if text_when_done:
            text_details = self.text_info[text_when_done]
            self.screen.show_text(text_details)

    def test_cueing_effect(self, cue_type, critical_opacity):
        """ Determine the effect of cueing on near-threshold detection """
        introduce_cue = self.text_info['cue']
        self.screen.show_text(introduce_cue)

        self.trial_data['part'] = 'cueing_effect'
        for trial_ix in range(60):
            target_present = choice([True, False], p = [0.5, 0.5])
            cue_present = choice([True, False])
            cue_this_trial = cue_type if cue_present else None

            self.trial_data['trial_ix'] = trial_ix
            self.run_trial(target_present, critical_opacity, cue_this_trial)

            if trial_ix > 0 and trial_ix % 30 == 0:
                break_details = self.text_info['break']
                self.screen.show_text(break_details)

    def end_experiment(self):
        end_details = self.text_info['end_of_experiment']
        self.screen.show_text(end_details)
        self.data_file.close()

if __name__ == '__main__':
    from psychopy.iohub import module_directory
    module = module_directory(SpatialCueingExperiment.run)
    runtime = SpatialCueingExperiment(module, 'experiment_config.yaml')
    runtime.start()

