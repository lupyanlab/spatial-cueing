import functools
import random
import yaml

import unipath

from psychopy import visual, core, event

from labtools.participant import Participant
from labtools.trial_list import TrialList
from labtools.experiment import Experiment
from labtools.psychopy_helper import load_sounds
from labtools.dynamicmask import DynamicMask

from trials import spatial_cueing_trial_list


def jitter(amount, pos):
    """ For jittering the target. """
    return (p + random.uniform(-amount/2, amount/2) for p in pos)

class SpatialCueingExperiment(Experiment):
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
        self.window = visual.Window(fullscr=True, units='pix', allowGUI=False)

        # Save any info in the yaml file to the experiment object
        with open(experiment_yaml, 'r') as f:
            self.experiment_info = yaml.load(f)

        # Create the fixation and prompt
        text_kwargs = {'height': 40, 'font': 'Consolas', 'color': 'black'}
        self.fix = visual.TextStim(self.window, text='+', **text_kwargs)
        self.prompt = visual.TextStim(self.window, text='?', **text_kwargs)

        # Create the masks
        mask_size = 200
        mask_kwargs = {'win': self.window, 'size': [mask_size, mask_size],
                       'opacity': 0.8}
        gutter = 400  # distance between left right centroids
        self.location_map = {'left': (-gutter/2, 0), 'right': (gutter/2, 0)}
        self.masks = [DynamicMask(pos=self.location_map[d], **mask_kwargs)
                      for d in ['left', 'right']]

        stim_dir = unipath.Path('stimuli')

        # Create the arrow cues
        self.arrows = {}
        for direction in ['left', 'right', 'neutral']:
            img = unipath.Path(stim_dir, 'arrow-%s.png' % direction)
            self.arrows[direction] = visual.ImageStim(self.window, img)

        # Create the visual word cue
        self.word = visual.TextStim(self.window, text='', **text_kwargs)

        # Create the sound cues
        self.sounds = {}
        self.sounds['left'] = load_sounds(stim_dir, '*left*.wav')
        self.sounds['right'] = load_sounds(stim_dir, '*right*.wav')

        # Create the target
        target_size = 80
        self.target = visual.Rect(self.window, size=[target_size, target_size],
                                  opacity=1.0, fillColor='white')

        # Create the stimuli for feedback
        incorrect_wav = unipath.Path(stim_dir, 'feedback-incorrect.wav')
        correct_wav = unipath.Path(stim_dir, 'feedback-correct.wav')
        self.feedback = {}
        self.feedback[0] = sound.Sound(incorrect_wav)
        self.feedback[1] = sound.Sound(correct_wav)

        # Create a function to jitter target positions
        amount = mask_size - target_size
        self.jitter = functools.partial(jitter, amount)

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
            self._draw_masks()
            self.fix.draw()
            self.window.flip()
            core.wait(refresh_rate)

        cue_onset = timer.getTime()
        while timer.getTime() - cue_onset < cue_duration:
            self._draw_masks()

            if visual_cue:
                visual_cue.draw()

            # Play auditory cue once
            if auditory_cue:
                auditory_cue.play()
                auditory_cue = None

            self.window.flip()
            core.wait(refresh_rate)

        while timer.getTime() - cue_onset < cue_onset_to_target_onset:
            self._draw_masks()
            self.window.flip()
            core.wait(refresh_rate)

        target_onset = timer.getTime()
        while timer.getTime() - target_onset < target_duration:
            self._draw_masks()
            self.target.draw()
            self.window.flip()
            core.wait(refresh_rate)

        self._draw_masks()
        self.window.flip()
        core.wait(refresh_rate)

        self.prompt.draw()
        self.window.flip()
        response = event.waitKeys(['f', 'j'])
        return response

    def _draw_masks(self):
        for mask in self.masks:
            mask.draw()

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

    def show_instructions(self):
        self.show_text(self.experiment_info['instructions'])

    def show_break_screen(self):
        self.show_text(self.experiment_info['break_text'])

    def show_end_screen(self):
        self.show_text(self.experiment_info['end_of_experiment'])

if __name__ == '__main__':
    participant = Participant.from_yaml('participant.yaml')
    participant.get_subj_info()

    experiment = SpatialCueingExperiment('experiment.yaml')
    trial_list_kwargs = experiment.trial_list_kwargs(participant)
    trial_frame = spatial_cueing_trial_list(**trial_list_kwargs)
    trial_list = TrialList.from_dataframe(trial_frame)

    experiment.show_instructions()

    with open(participant.data_file, 'w') as data_file:
        data_file.write(trial_list.header())

        cur_block = 1
        for trial in trial_list:
            if trial.block > cur_block:
                experiment.show_break_screen()
                cur_block = trial.block
            trial_data = experiment.run_trial(trial)
            print trial_data
            core.quit()
            # data_file.write(trial_data)

    experiment.show_end_screen()
