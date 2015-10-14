import random

import pandas

from labtools.trial_list import TrialList
from labtools.trials_functions import (counterbalance, extend, add_block,
                                       simple_shuffle)

def spatial_cueing_trial_list(cue_type, mask_type, **participant_kwargs):
    # - determine cue validity here
    trials = counterbalance({
        'target_loc': ['left', 'right'],
        'cue_type': cue_type,
        'mask_type': mask_type,
        'cue_validity': ['valid', 'invalid'],
    })

    # baseline_trials = counterbalance({
    #     'target_loc': ['left', 'right'],
    #     'cue_type': cue_type,
    #     'mask_type': mask_type,
    #     'cue_validity': 'neutral',
    # })
    # baseline_trials['block'] = 1
    # baseline_trials = extend(baseline_trials, max_length=100)
    #
    # neutral_dirs = ['up', 'down'] * 50
    # random.shuffle(neutral_dirs)
    # baseline_trials['cue_dir'] = neutral_dirs


    # Take anything given by the participant and put it in the trial list
    for col_name, subj_info in participant_kwargs.items():
        trials[col_name] = subj_info

    # Target was determined, now determine cue dir based on cue validity
    direction_reverser = {'left': 'right', 'right': 'left'}
    def determine_cue_dir(trial):
        target_loc = trial['target_loc']
        if trial['cue_validity'] in 'valid':
            return target_loc
        elif trial['cue_validity'] == 'invalid':
            return direction_reverser[target_loc]
        elif trial['cue_validity'] == 'neutral':
            return 'neutral'
    trials['cue_dir'] = trials.apply(determine_cue_dir, axis=1)

    # Duplicate unique trials evenly to reach 300 trials
    trials = extend(trials, max_length=300)

    # Assign block randomly
    block_size = 100
    trials = add_block(trials, size=block_size, id_col='cue_validity',
                       start_at=2)

    # Shuffle by block
    trials = simple_shuffle(trials, block='block')
    trials = trials.reset_index(drop=True)

    trials.index.name = 'trial'
    trials = trials.reset_index(drop=False)  # will be inserted as first column

    return trials


class SpatialCueingTrialList(TrialList):
    @classmethod
    def from_kwargs(cls, **kwargs):
        trials_frame = spatial_cueing_trial_list(**kwargs)
        return cls.from_dataframe(trials_frame)

    def compose(self, trial_data):
        trial_data_args = [trial_data[key] for key in self.column_order]
        return ','.join(map(str, trial_data_args))


if __name__ == '__main__':
    cue_type = ['visual_arrow', 'visual_word']
    mask_type = ['mask', ]
    trials = spatial_cueing_trial_list(cue_type, mask_type)
    trials.to_csv('trials.csv', index=False)
