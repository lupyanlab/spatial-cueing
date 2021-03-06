import random

import pandas

from labtools.trial_list import TrialList
from labtools.trials_functions import (counterbalance, expand, extend,
                                       add_block, simple_shuffle)


def spatial_cueing_trial_list(cue_type, mask_type, **participant_kwargs):
    trials = counterbalance({
        'target_loc': ['left', 'right'],
        'cue_type': cue_type,
        'mask_type': mask_type,
    })

    seed = participant_kwargs.get('seed')
    random.seed(seed)

    # Determine cue validity, starting with the smallest group
    # 66.6% valid, 25% invalid, 8.3% neutral
    trials = expand(trials, 'cue_validity', values=['invalid', 'neutral'],
                    ratio=0.75, seed=seed)

    trials = expand(trials, 'tmp_cue_valid', values=[1,0], ratio=0.7, seed=seed)
    trials.loc[trials.tmp_cue_valid == 1, 'cue_validity'] = 'valid'
    del trials['tmp_cue_valid']

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
        else:
            msg = 'cue validity %s not implemented' % trial['cue_validity']
            raise NotImplementedError(msg)
    trials['cue_dir'] = trials.apply(determine_cue_dir, axis=1)

    # Save a copy of the practice trials
    practice_trials = trials.copy()
    practice_trials['block'] = 0

    # Ensure that there are some up/down targets in the practice trials
    practice_trial_invalid_ix = practice_trials.ix[
        practice_trials.cue_validity == 'invalid',
    ].index
    practice_trial_target_loc = [random.choice(['up', 'down'])
                                 for _ in practice_trial_invalid_ix]
    practice_trials.ix[practice_trial_invalid_ix, 'target_loc'] = \
        practice_trial_target_loc

    # Select a subset of trials for practice
    num_practice_trials = 15
    sampled_trials = random.sample(practice_trials.index, num_practice_trials)
    practice_trials = practice_trials.ix[sampled_trials]
    practice_trials.reset_index(drop=True)

    # Duplicate unique trials evenly to reach max
    # 320 trials ~ 20 trials in each within subject cell
    trials = extend(trials, max_length=320)

    # Set target location for catch trials
    invalid_trial_ix = trials.ix[trials.cue_validity == 'invalid',].index
    catch_trial_ix = random.sample(invalid_trial_ix, len(invalid_trial_ix)/2)
    catch_trial_target_loc = [random.choice(['up', 'down'])
                              for _ in catch_trial_ix]
    trials.ix[catch_trial_ix, 'target_loc'] = catch_trial_target_loc

    # Assign block randomly
    block_size = 80
    trials = add_block(trials, size=block_size, id_col='cue_validity',
                       start_at=1, seed=seed)

    # Join the practice trials
    trials = pandas.concat([practice_trials, trials])

    # Shuffle by block
    trials = simple_shuffle(trials, block='block', seed=seed)
    trials = trials.reset_index(drop=True)

    # Label trial number
    trials.insert(0, 'trial', range(len(trials)))

    # Rearrange columns
    participant_keys = [
        'subj_id',
        'seed',
        'sona_experiment_code',
        'experimenter',
        'cue_contrast',
    ]
    for p in participant_keys:
        if p not in trials.columns:
            trials[p] = ''

    col_order = participant_keys + [
        'block',
        'trial',
        'mask_type',
        'cue_type',
        'cue_validity',
        'cue_dir',
        'target_loc',
    ]
    assert all([c in trials.columns for c in col_order])
    trials = trials[col_order]

    # Fill columns decided at runtime
    trials['soa'] = ''
    trials['target_loc_x'] = ''
    trials['target_loc_y'] = ''

    # Fill response columns
    trials['rt'] = ''
    trials['response_type'] = ''
    trials['is_correct'] = ''

    return trials


class SpatialCueingTrialList(TrialList):
    @classmethod
    def from_kwargs(cls, **kwargs):
        trials_frame = spatial_cueing_trial_list(**kwargs)
        return cls.from_dataframe(trials_frame)

    def header(self):
        return ','.join(self[0]._fields) + '\n'


if __name__ == '__main__':
    cue_type = ['visual_arrow', 'visual_word']
    mask_type = ['mask', ]
    trials = spatial_cueing_trial_list(cue_type, mask_type, seed=100)
    trials.to_csv('sample_trials.csv', index=False)
