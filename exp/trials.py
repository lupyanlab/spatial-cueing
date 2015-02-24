#!/usr/bin/env python
import pandas as pd
import numpy as np

from psychopy.data import TrialHandler

import labtools

def uniform_intervals(low, high, num_bins, samples_per, seed = 100,
        var_name = 'cue_offset_to_target_onset'):
    """
    Sample values so that each bin has the same number of samples
    """
    prng = np.random.RandomState(seed)

    interval = (high - low)/float(num_bins)
    bins = {}
    for b in range(num_bins):
        current_low = low + b * interval
        current_high = low + (b + 1) * interval
        bins[b] = prng.uniform(current_low, current_high, samples_per)

    frame = pd.melt(pd.DataFrame(bins), var_name = 'bin', value_name = var_name)

    # round isi
    frame[var_name] = np.round(frame[var_name], 2)

    return frame

def add_cued_trials(low, high, num_bins, samples_per, var_name = 'cue_offset_to_target_onset'):
    """
    Create trials of each cue type for each ISI at the given ratio.

    Defaults to simply doubling the trials
    """
    same_seed = 100
    no_cue = uniform_intervals(low, high, num_bins, samples_per, same_seed, var_name)
    cue = uniform_intervals(low, high, num_bins, samples_per, same_seed, var_name)
    doubled = pd.concat([no_cue, cue],
        keys = ['no_cue', 'cue'],
        names = ['cue_type', 'ix']
    )
    doubled.reset_index('cue_type', inplace = True)

    return doubled

class Trials(object):

    def __init__(self):
        default_trial = pd.DataFrame({
            'cue_type': ['dot', 'arrow'],
            'cue_loc': ['right', 'left'],
            'isi': [0.5, 0.6],
            'target_loc': ['right', 'left'],
            'target_contrast': [1.0, 0.5],
        })

        for_handler = [row.to_dict() for _, row in default_trial.iterrows()]
        self._trials = TrialHandler(for_handler, nReps = 1)

    def __iter__(self):
        return self

    def next(self):
        if True:
            pass
        else:
            raise StopIteration()
