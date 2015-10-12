import yaml
import pandas as pd

from psychopy import visual, core, misc

from labtools.participant import Participant
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
    def __init__(self, experiment_yaml, participant):
        with open(experiment_yaml, 'r') as f:
            self.experiment_info = yaml.load(f)

        self.participant_info = participant.subj_info

        self.window = visual.Window()

        gutter = 400
        left = (-gutter/2, 0)
        right = (gutter/2, 0)
        self.location_map = {'left': left, 'right': right}

        self._make_masks()
        self._make_fixation_and_prompt()
        self._make_visual_cues()
        self._make_sounds()
        self._make_target()

    def trial_list_kwargs(self):
        return {
            'cue_type': ['visual_arrow', 'visual_word']
        }

    def _make_masks(self):
        is_flicker_on = True
        mask_size = 200
        mask_kwargs = {
            'win': self.window,
            'size': [mask_size, mask_size],
            'opacity': 0.8,
            'flicker': is_mask_flicker_on,
        }
        self.masks = {}
        self.masks['left']  = DynamicMask(pos=self.location_map['left'],
                                          **mask_kwargs)
        self.masks['right'] = DynamicMask(pos=self.location_map['right'],
                                          **mask_kwargs)

    def _make_fixation_and_prompt(self):
        text_kwargs = {'height': 40, 'font': 'Consolas', 'color': 'black'}
        self.fix    = visual.TextStim(self.window, text='+', **text_kwargs)
        self.prompt = visual.TextStim(self.window, text='?', **text_kwargs)

    def _make_visual_cues(self):
        self.cues = {}
        self.cues['arrow'] = visual.ImageStim(self.window, 'stimuli/arrow.png')
        self.cues['word'] = visual.TextSteim(self.window, text='')

        self.arrow_orientation_map = {
            'left': -90,
            'right': 90,
            'up': 0,
            'down': 180,
        }

    def _make_sounds(self):
        self.sounds = {}
        self.sounds['left'] = load_sounds(stim, '*left*.wav')
        self.sounds['right'] = load_sounds(stim, '*right*.wav')
        self.sounds['up'] = load_sounds(stim, '*up*.wav')
        self.sounds['down'] = load_sounds(stim, '*down*.wav')
        self.sounds['feedback'] = load_sounds(stim, 'feedback*.wav')

    def _make_target(self):
        target_size = 80
        target_kwargs = {
            'win': self.window,
            'size': [target_size, target_size],
            'fillColor': 'white',
        }
        self.target = visual.Rect(opacity = 0.0, **target_kwargs)

        # create a jitter function for target positions
        edge_buffer = target_size/6
        outer_edge = mask_size/2
        inner_edge = outer_edge - target_size/2 - edge_buffer
        self.jitter = lambda p: (
            p[0] + random.uniform(-inner_edge/2, inner_edge/2),
            p[1] + random.uniform(-inner_edge/2, inner_edge/2)
        )

    def show_instructions(self):
        instructions = "test 123"
        text = visual.TextStim(self.window, text=instructions)
        text.draw()
        win.flip()

    def run_trial(self, trial):
        """ Prepare the trial, run it, and save the data to disk. """
        trial = dict(trial)

        if trial['cue_modality'] == 'visual':
            auditory_cue = None
            if trial['cue_type'] == 'visual_arrow':
                visual_cue = self.cues['arrow']
                visual_cue.setOri(self.arrow_orientation_map(trial['cue_direction']))
            elif trial['cue_type'] == 'visual_word':
                visual_cue = self.cues['word']
                visual_cue.setText(trial['cue_direction'])
            else:
                msg = 'cue_type %s not found'
                raise AssertionError(msg)
        else:
            visual_cue = None
            sound_options = self.sounds[trial['cue_direction']]
            auditory_cue = random.choice(sound_options)

        target_loc = trial['target_loc']
        target_pos = self.location_map[target_loc]
        x, y = self.jitter(target_pos)
        self.target.setPos((x,y))
        self.trial['target_pos_x'] = x
        self.trial['target_pos_y'] = y

        timer = core.Clock()
        timer.reset()

        while timer.getTime() < END_OF_FIXATION:
            for mask in self.masks.values():
                mask.draw()
            self.fix.draw()
            self.window.flip()
            core.wait(REFRESH_RATE)

        timer.reset()
        while timer.getTime() < END_OF_CUE:
            for mask in self.masks.values():
                mask.draw()

            if visual_cue:
                visual_cue.draw()

            # Play auditory cue once
            if auditory_cue:
                auditory_cue.play()
                auditory_cue = None

        timer.reset()
        while timer.getTime() < END_OF_INTERVAL:
            for mask in self.masks.values():
                mask.draw()
            core.wait(REFRESH_RATE)

        timer.reset()
        while timer.getTime() < END_OF_TARGET:
            for mask in self.masks.values():
                mask.draw()
            self.target.draw()
            core.wait(REFRESH_RATE)

        timer.rest()
        while timer.getTime() < POST_TARGET:
            for mask in self.masks.values():
                mask.draw()
            core.wait(REFRESH_RATE)

        self.prompt.draw()
        self.window.flip()
        response = event.waitKeys(['f', 'j'])

    def show_break_screen(self):
        pass

    def write_trial(self, trial_data):
        self.experiment_info, self.participant_info

if __name__ == '__main__':
    participant = Participant.from_yaml('participant.yaml')
    participant.get_subj_info()

    experiment = SpatialCueingExperiment('experiment.yaml')
    experiment.configure_for_participant(participant)

    trial_frame = spatial_cueing_trial_list(experiment.trial_list_kwargs())
    trial_list = TrialList.from_dataframe(trial_frame)

    for trial in trial_list:
        experiment.run_trial(trial)
