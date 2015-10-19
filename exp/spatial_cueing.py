import functools
import random
import yaml

import unipath

from psychopy import visual, core, event, sound

from labtools.psychopy_helper import load_sounds
from labtools.dynamicmask import DynamicMask
from labtools.experiment import Experiment

from participant import SpatialCueingParticipant
from trial_list import SpatialCueingTrialList

class SpatialCueingExperiment(Experiment):
    """ Measure spatial cueing effects when targets are hard to see.

    On each trial, participants wait for a target to appear within
    the bounds of two rectangular masks, presented to the left and right
    of fixation. For some participants, the masks will be flashing
    continuously over the course of the trial. For others, the masks
    will be static.

    Before the target appears, participants receive one of the following cues:
        - visual_arrow
        - visual_word
        - auditory_word

    Cues are valid, invalid, or neutral.
    """
    def __init__(self, experiment_yaml):
        self.window = visual.Window(fullscr=True, units='pix', allowGUI=False)

        # Save any info in the yaml file to the experiment object
        with open(experiment_yaml, 'r') as f:
            self.config = yaml.load(f)
        self.texts = self.config.pop('texts')
        self.times_in_seconds = self.config.pop('times_in_seconds')
        self.response_map = self.config.pop('response_map')

        # Create the fixation and prompt
        text_kwargs = {'height': 40, 'font': 'Consolas', 'color': 'black'}
        self.fix = visual.TextStim(self.window, text='+', **text_kwargs)
        self.prompt = visual.TextStim(self.window, text='?', **text_kwargs)

        # Create the masks
        mask_size = 200
        mask_kwargs = {'win': self.window, 'size': [mask_size, mask_size]}
        gutter = 400  # distance between left right centroids
        self.location_map = {'left': (-gutter/2, 0), 'right': (gutter/2, 0)}
        self.masks = [DynamicMask(pos=self.location_map[d], **mask_kwargs)
                      for d in ['left', 'right']]

        # Stimuli directory
        STIM_DIR = unipath.Path('stimuli')
        assert STIM_DIR.isdir(), "stimuli directory not found"

        # Create the arrow cues
        self.arrows = {}
        for direction in ['left', 'right', 'neutral']:
            arrow_png = unipath.Path(STIM_DIR, 'arrow-%s.png' % direction)
            assert arrow_png.exists(), "%s not found" % arrow_png
            arrow_png = str(arrow_png)  # psychopy doesn't like unipath.Path's
            self.arrows[direction] = visual.ImageStim(self.window, arrow_png)

        # Create the visual word cue using same kwargs as fixation and prompt
        self.word = visual.TextStim(self.window, text='', **text_kwargs)

        # Load the sound cues
        # There are multiple versions of each sound, so pick one like this:
        # >>> random.choice(self.sounds['left']).play()
        self.sounds = {}
        for direction in ['left', 'right', 'neutral']:
            sounds_re = '%s-*.wav' % direction
            self.sounds[direction] = load_sounds(STIM_DIR, sounds_re)

        # Create the target
        target_size = 80
        self.target = visual.Rect(self.window, size=[target_size, target_size],
                                  opacity=0.6, fillColor='white')

        # Create the stimuli for feedback
        incorrect_wav = unipath.Path(STIM_DIR, 'feedback-incorrect.wav')
        correct_wav = unipath.Path(STIM_DIR, 'feedback-correct.wav')
        self.feedback = {}
        self.feedback[0] = sound.Sound(incorrect_wav)
        self.feedback[1] = sound.Sound(correct_wav)

        # Create a closure function to jitter target positions with the
        # bounds of the mask
        no_edge_to_edge_buffer = target_size/6
        amount = mask_size - target_size - no_edge_to_edge_buffer
        def jitter(pos):
            """ For jittering the target. """
            return (p + random.uniform(-amount/2, amount/2) for p in pos)
        self.jitter = jitter

        # Attach timer to experiment
        self.timer = core.Clock()

    def run_trial(self, trial):
        """ Prepare the trial, run it, and return the trial data.

        trial is a namedtuple with attributes for each item in the trials list.
        """
        # Determine which cue will be shown on this trial
        visual_cue = None
        auditory_cue = None

        if trial.cue_type == 'visual_arrow':
            visual_cue = self.arrows[trial.cue_dir]
        elif trial.cue_type == 'visual_word':
            visual_cue = self.word
            if trial.cue_dir == 'neutral':
                visual_cue.setText('XXXXX')
            else:
                visual_cue.setText(trial.cue_dir)
        elif trial.cue_type == 'auditory_word':
            sound_options = self.sounds[trial.cue_dir]
            auditory_cue = random.choice(sound_options)
        else:
            raise NotImplementedError('cue type %s not implemented' % cue_type)

        # Set the position of the target
        target_pos = self.location_map[trial.target_loc]
        x, y = self.jitter(target_pos)
        self.target.setPos((x, y))

        # Shortcuts for config variables
        fps = 120  # frames per second of testing computers
        n_fixation_frames = int(fps * self.times_in_seconds['fixation_duration'])
        n_cue_frames = int(fps * self.times_in_seconds['cue_duration'])

        # - jitter soa here
        n_interval_frames = int(fps * \
            (self.times_in_seconds['cue_onset_to_target_onset'] -
             self.times_in_seconds['cue_duration']))
        n_target_frames = int(fps * self.times_in_seconds['target_duration'])

        self.timer.reset()
        # ----------------------------------------------------------------------
        # Start of trial presentation

        # Fixation
        for _ in range(n_fixation_frames):
            self.draw_masks()
            self.fix.draw()
            self.window.flip()

        # Play the auditory cue before entering cue loop
        if auditory_cue:
            auditory_cue.play()

        # Draw the masks and visual cue, if present
        for _ in range(n_cue_frames):
            self.draw_masks()
            if visual_cue:
                visual_cue.draw()
            self.window.flip()

        # Draw the masks between the cue and target
        for _ in range(n_interval_frames):
            self.draw_masks()
            self.window.flip()

        # Draw the target on top of the masks
        target_onset = self.timer.getTime()
        for _ in range(n_target_frames):
            self.draw_masks()
            self.target.draw()
            self.window.flip()

        # Clear the target from the masks before showing the prompt
        self.draw_masks()
        self.window.flip()

        # Draw the prompt and wait for a response
        self.prompt.draw()
        self.window.flip()
        responses = event.waitKeys(keyList=self.response_map.keys(),
                                   maxWait=2.0)
        rt = self.timer.getTime() - target_onset

        # Figure out how they responded
        try:
            response = responses[0]
        except TypeError:
            response_type = 'timeout'
        else:
            response_type = self.response_map[response]

        is_correct = int(response_type == trial.target_loc)

        # Give auditory feedback
        self.feedback[is_correct].play()

        # Pause the experiment after a timeout trial
        if response_type == 'timeout':
            self.show_text(self.texts['timeout_screen'])

        # End of trial presentation
        # ----------------------------------------------------------------------

        # Create a writable copy of the trial
        trial_data = dict(zip(trial._fields, trial))

        # Add response variables to trial data
        trial_data['rt'] = rt
        trial_data['response_type'] = response_type
        trial_data['is_correct'] = is_correct

        return trial_data

    def draw_masks(self):
        for mask in self.masks:
            mask.draw()

    def show_instructions(self):
        self.show_text(self.texts['instructions'])

    def show_break_screen(self):
        self.show_text(self.texts['break_screen'])

    def show_end_screen(self):
        self.show_text(self.texts['end_of_experiment'])

if __name__ == '__main__':
    participant = SpatialCueingParticipant.from_yaml('participant.yaml')
    participant.get_subj_info()

    trial_list_kwargs = participant.get_trial_list_kwargs()
    trial_list = SpatialCueingTrialList.from_kwargs(**trial_list_kwargs)

    experiment = SpatialCueingExperiment('experiment.yaml')
    experiment.show_instructions()

    with open(participant['data_filename'], 'w') as data_file:
        block = 1
        for trial in trial_list:
            # Before starting new block, show the break screen
            if trial.block > block:
                experiment.show_break_screen()
                block = trial.block
            trial_data = experiment.run_trial(trial)
            trial_str = trial_list.compose(trial_data)
            data_file.write(trial_str)

    experiment.show_end_screen()