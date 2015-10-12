import random

import pandas

from labtools.trials_functions import (counterbalance, extend, add_block,
                                       simple_shuffle)

dir_reverser = {'left': 'right', 'right': 'left'}

def determine_cue_dir(trial):
    target_loc = trial['target_loc']
    if trial['cue_validity'] == 'valid':
        return target_loc
    else:
        return dir_reverser[target_loc]

def spatial_cueing_trial_list(cue_type, mask_type, seed=None):
    random.seed(seed)

    trials = counterbalance({
        'target_loc': ['left', 'right'],
        'cue_type': cue_type,
        'mask_type': mask_type,
        'cue_validity': ['valid', 'invalid'],
    })

    trials['cue_dir'] = trials.apply(determine_cue_dir, axis=1)

    trials = extend(trials, max_length=300)

    block_size = 100
    trials = add_block(trials, size=block_size, id_col='cue_validity',
                       start_at=2)

    baseline_trials = counterbalance({
        'target_loc': ['left', 'right'],
        'cue_type': cue_type,
        'mask_type': mask_type,
        'cue_validity': 'neutral',
    })
    baseline_trials['block'] = 1
    baseline_trials = extend(baseline_trials, max_length=100)

    neutral_dirs = ['up', 'down'] * 50
    random.shuffle(neutral_dirs)
    baseline_trials['cue_dir'] = neutral_dirs

    trials = pandas.concat([baseline_trials, trials])
    trials = simple_shuffle(trials, block='block', seed=seed)
    trials = trials.reset_index(drop=True)

    trials.index.name = 'trial'
    trials = trials.reset_index(drop=True)

    return trials


if __name__ == '__main__':
    cue_type = ['visual_arrow', 'visual_word']
    mask_type = ['mask', ]
    trials = spatial_cueing_trial_list(cue_type, mask_type, seed=639)
    trials.to_csv('trials.csv', index=False)
