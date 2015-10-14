import yaml
from collections import OrderedDict
import numpy as np
from numpy.random import choice
import random
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
    is compared to performance with a cue. Cues can be spatial or auditory.

    - Spatial cues are "X"s presented in the location of the target.
    - Auditory cues are the spoken words "left" or "right".

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
            exp_name = 'spatial-cueing-final',
            options = subj_info_fields,
            exp_dir = './',
            data_dir = './data/')

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
            'interval',
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
        self.screen = SpatialCueing(self.window, self.hub)
        self.intertrial = ClearScreen(self, timeout = 0.5)

        # Begin the experiment
        # --------------------
        self.show_instructions()

        accuracy_in_practice_trials = 0.0
        while accuracy_in_practice_trials < 0.7:
            accuracy_in_practice_trials = self.run_practice_trials(
                    num_trials = 10,
                    target_opacity = 1.0)

            if accuracy_in_practice_trials < 0.7:
                details = self.text_info['low_accuracy']
                self.screen.show_text(details)

        ready = self.text_info['ready']
        self.screen.show_text(ready)

        # Don't try to calibrate the critical opacity because
        # performance is just too noisy and it's not worth it.
        # Instead, run participants in both cueing conditions
        # in random order
        critical_opacity = 1.0
        self.test_cueing_effect(critical_opacity = critical_opacity)

        self.end_experiment()

    def run_trial(self, target_present, target_opacity, cue_type = None):
        """ Prepare the trial, run it, and save the data to disk

        On target present trials, randomly assigns targets to the left
        or right mask, and selects a location within that mask. Target
        opacity is provided.

        On cue present trials, assign cue location (and position, for
        spatial cues). If a cue and a target are both present on the
        same trial, the cue is always valid.
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
            if cue_type == 'frame':
                if target_present:
                    cue_pos = self.screen.location_map[target_loc]
                else:
                    cue_pos = self.screen.location_map[cue_loc]
                cue_pos_x, cue_pos_y = cue_pos

        self.trial_data['cue_present'] = int(cue_present)
        self.trial_data['cue_type'] = cue_type
        self.trial_data['cue_loc'] = cue_loc
        self.trial_data['cue_pos_x'] = cue_pos_x
        self.trial_data['cue_pos_y'] = cue_pos_y

        # set interval for the trial
        # this interval is the only difference between spatial-cueing.py
        # and short-delay-with-interference.py
        self.trial_data['interval'] = 0.100

        self.trial_data = self.screen.run_trial(self.trial_data)

        row = '\t'.join(map(str, self.trial_data.values()))
        self.data_file.write(row + '\n')

        self.intertrial.switchTo()

    def show_instructions(self):
        for screen in ['welcome', 'target', 'practice']:
            details = self.text_info[screen]
            self.screen.show_text(details)

    def run_practice_trials(self, num_trials = 20, target_opacity = 1.0):
        """ Run a few practice trials with highly visible targets """
        current_performance = []
        self.trial_data['part'] = 'practice'
        for trial_ix in range(num_trials):
            target_present = choice([True, False], p = [0.8, 0.2])

            self.trial_data['trial_ix'] = trial_ix
            self.run_trial(target_present, target_opacity, cue_type = None)

            current_performance.append(self.trial_data['is_correct'])

        current_accuracy = np.array(current_performance).mean()
        return current_accuracy

    def test_cueing_effect(self, critical_opacity):
        """ Determine the effect of cueing on near-threshold detection """
        self.trial_data['part'] = 'cueing_effect'
        for trial_ix in range(360):
            target_present = choice([True, False], p = [0.85, 0.15])

            cue_present = choice([True, False], p = [0.667, 0.333])
            if cue_present:
                cue_type = choice(['frame', 'sound'])
            else:
                cue_type = None

            self.trial_data['trial_ix'] = trial_ix
            self.run_trial(target_present, critical_opacity, cue_type)

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
