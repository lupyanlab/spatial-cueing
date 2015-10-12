import random
import yaml

import unipath

from psychopy import visual, core, event

from labtools.participant import Participant
from labtools.trial_list import TrialList
from labtools.psychopy_helper import load_sounds
from labtools.dynamicmask import DynamicMask

from trials import spatial_cueing_trial_list


class SpatialCueingExperiment(object):
    """ Measure spatial cueing effects when targets are hard to see.

    On each trial, participants wait for a target to appear within
    the bounds of two rectangular masks, presented to the left and right
    of fixation.

    Before the target, participants get one of the following cues:
        - visual_arrow
        - visual_word
        - auditory_word

    Cues are valid, invalid, or neutral.
    """
    def __init__(self, experiment_yaml):
        with open(experiment_yaml, 'r') as f:
            self.experiment_info = yaml.load(f)

        self.window = visual.Window(fullscr=True, units='pix', allowGUI=False)

        # global params
        gutter = 400
        left = (-gutter/2, 0)
        right = (gutter/2, 0)
        self.location_map = {'left': left, 'right': right}

        self.mask_size = 200

        self._make_masks()
        self._make_fixation_and_prompt()
        self._make_visual_cues()
        self._make_sounds()
        self._make_target()

    def _make_masks(self):
        mask_kwargs = {
            'win': self.window,
            'size': [self.mask_size, self.mask_size],
            'opacity': 0.8,
        }
        left_mask = DynamicMask(pos=self.location_map['left'], **mask_kwargs)
        right_mask = DynamicMask(pos=self.location_map['right'], **mask_kwargs)
        self.masks = [left_mask, right_mask]

    def draw_masks(self):
        for mask in self.masks:
            mask.draw()

    def _make_fixation_and_prompt(self):
        text_kwargs = {'height': 40, 'font': 'Consolas', 'color': 'black'}
        self.fix = visual.TextStim(self.window, text='+', **text_kwargs)
        self.prompt = visual.TextStim(self.window, text='?', **text_kwargs)

    def _make_visual_cues(self):
        self.cues = {}
        self.cues['arrow'] = visual.ImageStim(self.window, 'stimuli/arrow.png')
        self.cues['word'] = visual.TextStim(self.window, text='')

        self.arrow_orientation_map = {
            'left': -90,
            'right': 90,
            'up': 0,
            'down': 180,
        }

    def _make_sounds(self):
        stim_dir = unipath.Path('stimuli/')
        self.sounds = {}
        self.sounds['left'] = load_sounds(stim_dir, '*left*.wav')
        self.sounds['right'] = load_sounds(stim_dir, '*right*.wav')
        self.sounds['up'] = load_sounds(stim_dir, '*up*.wav')
        self.sounds['down'] = load_sounds(stim_dir, '*down*.wav')
        self.sounds['feedback'] = load_sounds(stim_dir, 'feedback*.wav')

    def _make_target(self):
        target_size = 80
        target_kwargs = {
            'win': self.window,
            'size': [target_size, target_size],
            'fillColor': 'white',
        }
        self.target = visual.Rect(opacity=0.0, **target_kwargs)

        # create a jitter function for target positions
        edge_buffer = target_size/6
        outer_edge = self.mask_size/2
        inner_edge = outer_edge - target_size/2 - edge_buffer
        self.jitter = lambda p: (
            p[0] + random.uniform(-inner_edge/2, inner_edge/2),
            p[1] + random.uniform(-inner_edge/2, inner_edge/2)
        )

    def configure_for_participant(self, participant):
        trial_list_kwargs = {}

        mask_condition = participant['mask_condition']
        if mask_condition == 'nomask':
            # Turn off flicker
            for mask in self.masks:
                mask.is_flicker = False
        trial_list_kwargs['mask_type'] = mask_condition

        cue_contrast = participant['cue_contrast']
        if cue_contrast == 'word_arrow':
            cue_types = ['visual_word', 'visual_arrow']
        elif cue_contrast == 'visual_auditory':
            cue_types = ['visual_word', 'auditory_word']
        else:
            raise NotImplementedError('cue contrast not implemented')
        trial_list_kwargs['cue_type'] = cue_types

        return trial_list_kwargs

    def show_instructions(self):
        instructions = "test 123"
        text = visual.TextStim(self.window, text=instructions)
        text.draw()
        self.window.flip()

    def run_trial(self, trial):
        """ Prepare the trial, run it, and return the trial data. """
        visual_cue, auditory_cue = self._set_cue_for_trial(trial.cue_type,
                                                           trial.cue_dir)

        self._set_target_pos(trial.target_loc)

        refresh_rate = self.experiment_info['refresh_rate']
        fixation_duration = self.experiment_info['fixation_duration']
        cue_duration = self.experiment_info['cue_duration']
        cue_onset_to_target_onset = self.experiment_info[
            'cue_onset_to_target_onset'
        ]
        target_duration = self.experiment_info['target_duration']

        timer = core.Clock()
        timer.reset()

        trial_onset = timer.getTime()
        while timer.getTime() - trial_onset < fixation_duration:
            self.draw_masks()
            self.fix.draw()
            self.window.flip()
            core.wait(refresh_rate)

        cue_onset = timer.getTime()
        while timer.getTime() - cue_onset < cue_duration:
            self.draw_masks()

            if visual_cue:
                visual_cue.draw()

            # Play auditory cue once
            if auditory_cue:
                auditory_cue.play()
                auditory_cue = None

            self.window.flip()
            core.wait(refresh_rate)

        while timer.getTime() - cue_onset < cue_onset_to_target_onset:
            self.draw_masks()
            self.window.flip()
            core.wait(refresh_rate)

        target_onset = timer.getTime()
        while timer.getTime() - target_onset < target_duration:
            self.draw_masks()
            self.target.draw()
            self.window.flip()
            core.wait(refresh_rate)

        self.draw_masks()
        self.window.flip()
        core.wait(refresh_rate)

        self.prompt.draw()
        self.window.flip()
        response = event.waitKeys(['f', 'j'])
        return response

    def _set_cue_for_trial(self, cue_type, cue_dir):
        visual_cue = None
        auditory_cue = None

        if cue_type == 'visual_arrow':
            visual_cue = self.cues['arrow']
            visual_cue.setOri(self.arrow_orientation_map[cue_dir])
        elif cue_type == 'visual_word':
            visual_cue = self.cues['word']
            visual_cue.setText(cue_dir)
        elif trial.cue_type == 'auditory_word':
            sound_options = self.sounds[cue_dir]
            auditory_cue = random.choice(sound_options)
        else:
            raise NotImplementedError('cue type %s not implemented' % cue_type)

        return visual_cue, auditory_cue

    def _set_target_pos(self, target_loc):
        target_pos = self.location_map[target_loc]
        x, y = self.jitter(target_pos)
        self.target.setPos((x, y))

    def show_break_screen(self):
        pass

    def write_trial(self, trial_data):
        self.experiment_info, self.participant_info

if __name__ == '__main__':
    participant = Participant.from_yaml('participant.yaml')
    participant.get_subj_info()

    experiment = SpatialCueingExperiment('experiment.yaml')
    trial_list_kwargs = experiment.configure_for_participant(participant)

    trial_frame = spatial_cueing_trial_list(**trial_list_kwargs)
    trial_list = TrialList.from_dataframe(trial_frame)

    experiment.show_instructions()

    cur_block = 1
    for trial in trial_list:
        if trial.block > cur_block:
            experiment.show_break_screen()
            cur_block = trial.block
        trial_data = experiment.run_trial(trial)
        print trial_data
        core.quit()
        # participant.write_trial_data(trial_data)

    experiment.show_end_screen()
