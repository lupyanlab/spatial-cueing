from collections import OrderedDict
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
    the bounds of four rectangular masks, presented left, right, above, and
    below of fixation. For some participants, the masks will be flashing
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
        gutter = 440  # distance between L/R and U/D centroids
        self.location_map = {
            'left': (-gutter/2, 0),
            'right': (gutter/2, 0),
            'up': (0, gutter/2),
            'down': (0, -gutter/2)
        }
        self.masks = [DynamicMask(pos=p, **mask_kwargs)
                      for p in self.location_map.values()]

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
                                  opacity=0.8, fillColor='white')

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
        # Set mask type
        for mask in self.masks:
            mask.is_flicker = (trial.mask_type == 'mask')
            mask.pick_new_mask()

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
            sound_options = self.sounds[trial.cue_dir].values()
            auditory_cue = random.choice(sound_options)
        else:
            msg = 'cue type %s not implemented' % trial.cue_type
            raise NotImplementedError(msg)

        # Set the position of the target
        target_pos = self.location_map[trial.target_loc]
        x, y = self.jitter(target_pos)
        self.target.setPos((x, y))

        fps = 120 # frames per second of testing computers
        def to_n_frames(time_in_seconds):
            return int(fps * time_in_seconds)

        # Fixation frames
        n_fixation_frames = to_n_frames(
            self.times_in_seconds['fixation_duration']
        )
        n_cue_frames = to_n_frames(
            self.times_in_seconds['cue_duration']
        )
        # Fixation offset to cue onset frames
        n_pre_cue_frames = to_n_frames(
            self.times_in_seconds['fixation_offset_to_cue_onset']
        )
        # Cue offset to target onset frames
        interval = self.times_in_seconds['cue_onset_to_target_onset'] - \
            self.times_in_seconds['cue_duration']
        n_interval_frames = to_n_frames(interval)
        # Jitter the soa by a maximum of 50 ms in either direction
        max_soa_jitter = int(fps * 0.05)
        soa_jitter = random.choice(range(-max_soa_jitter, max_soa_jitter + 1))
        n_interval_frames += soa_jitter

        n_target_frames = to_n_frames(self.times_in_seconds['target_duration'])

        self.timer.reset()
        # ----------------------------------------------------------------------
        # Start of trial presentation

        # Fixation
        for _ in range(n_fixation_frames):
            self.draw_masks()
            self.fix.draw()
            self.window.flip()

        # Fixation offset to cue onset
        for _ in range(n_pre_cue_frames):
            self.draw_masks()
            self.window.flip()

        # Start the auditory cue before entering cue loop
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
            self.fix.draw()
            self.window.flip()

        # Draw the target on top of the masks
        target_onset = self.timer.getTime()
        for _ in range(n_target_frames):
            self.draw_masks()
            self.target.draw()
            self.fix.draw()
            self.window.flip()

        # Clear the target from the masks before showing the prompt
        self.draw_masks()
        self.fix.draw()
        self.window.flip()

        # Draw the prompt and wait for a response
        self.prompt.draw()
        self.window.flip()
        responses = event.waitKeys(
            keyList=self.response_map.keys(),
            maxWait=self.times_in_seconds['response_window']
        )
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
        trial_data = OrderedDict()
        for key, value in zip(trial._fields, trial):
            trial_data[key] = value

        # Add variables determined at runtime to trial data
        trial_data['soa'] = n_interval_frames / float(fps)
        trial_data['target_loc_x'] = x
        trial_data['target_loc_y'] = y

        # Add response variables to trial data
        trial_data['rt'] = rt * 1000
        trial_data['response_type'] = response_type
        trial_data['is_correct'] = is_correct

        # ITI
        core.wait(self.times_in_seconds['inter_trial_interval'])

        return trial_data

    def draw_masks(self):
        for mask in self.masks:
            mask.draw()

    def show_instructions(self, mask_type):
        texts = self.texts['instructions']

        # Show the masks in the instructions that will be
        # used in the experiment.
        for mask in self.masks:
            mask.is_flicker = (mask_type == 'mask')
            mask.pick_new_mask()

        title = visual.TextStim(
            self.window, text='Welcome to the SPC Experiment', height=60,
            font='Consolas', color='black', pos=[0,200], wrapWidth=1000,
        )

        text_kwargs = dict(wrapWidth=900, height=20, color='black',
                           font='Consolas')

        instructions = visual.TextStim(self.window, **text_kwargs)

        # Instructions 1
        title.draw()
        instructions.setText(texts[1])
        instructions.draw()
        self.window.flip()
        response = event.waitKeys()[0]
        if response == 'q':
            core.quit()

        # Instructions 2
        instructions.setText(texts[2])
        instructions.setPos([0,200])

        target_pos = self.location_map['left']
        x, y = self.jitter(target_pos)
        self.target.setPos((x, y))

        footer_kwargs = dict(text_kwargs)
        footer_kwargs['wrapWidth'] = 220
        footer = visual.TextStim(self.window, pos=[0,0], **footer_kwargs)
        footer.setText('The target is present. Do you see it?')

        instructions.draw()
        self.window.flip()
        event.waitKeys()

        for _ in range(5):
            self.draw_masks()
            self.window.flip()
            core.wait(0.5)

        for n in range(10):
            if n == 9:
                # Last frame
                footer.setText('Press the SPACEBAR to continue.')
            footer.draw()
            self.draw_masks()
            self.target.draw()
            self.window.flip()
            core.wait(0.5)

        response = event.waitKeys()[0]
        if response == 'q':
            core.quit()

        # Instructions 3
        instructions.setText(texts[3])
        instructions.draw()
        self.window.flip()
        response = event.waitKeys()[0]
        if response == 'q':
            core.quit()

        # Instructions 4
        instructions.setText(texts[4])
        instructions.draw()
        self.window.flip()
        response = event.waitKeys()[0]
        if response == 'q':
            core.quit()

        # Instructions 5
        instructions.setText(texts[5])
        instructions.draw()
        self.window.flip()
        response = event.waitKeys()[0]
        if response == 'q':
            core.quit()

    def show_end_of_practice_screen(self):
        self.show_text(self.texts['end_of_practice'])

    def show_break_screen(self):
        self.show_text(self.texts['break_screen'])

    def show_end_screen(self):
        self.show_text(self.texts['end_of_experiment'])

if __name__ == '__main__':
    participant = SpatialCueingParticipant.from_yaml('participant.yaml')
    participant.get_subj_info()

    trial_list_kwargs = participant.get_trial_list_kwargs()
    random.seed(trial_list_kwargs['seed'])
    trial_list = SpatialCueingTrialList.from_kwargs(**trial_list_kwargs)

    experiment = SpatialCueingExperiment('experiment.yaml')
    experiment.show_instructions(mask_type = participant['mask_type'])

    with open(participant['data_filename'], 'w') as data_file:
        data_file.write(trial_list.header())
        data_file.flush()

        block = 0
        for trial in trial_list:
            # Before starting new block, show the break screen
            if trial.block > block:
                if block == 0:
                    # Just finished the practice trials
                    experiment.show_end_of_practice_screen()
                else:
                    experiment.show_break_screen()
                block = trial.block
            trial_data = experiment.run_trial(trial)
            trial_str = ','.join(map(str, trial_data.values())) + '\n'
            data_file.write(trial_str)
            data_file.flush()

    experiment.show_end_screen()

    import socket
    import webbrowser
    survey_url_prepop = 'https://docs.google.com/forms/d/1cKhnV2chvnpxg9Oy6beFVfaoMQy46Epoht2DA0epFRU/viewform?entry.1000000={}&entry.1000001={}'
    room = socket.gethostname()
    survey_url = survey_url_prepop.format(participant['subj_id'], room)
    webbrowser.open(survey_url)
