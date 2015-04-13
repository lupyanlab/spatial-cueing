#!/usr/bin/env python
import numpy as np

class Staircase(object):
    """
    Generator for ISIs during staircase calibration of stimulus contrast.
    """
    def __init__(self, intervals, contrast = 0.0, step_height = 0.5,
        var_name = 'cue_offset_to_target_onset'):
        self.generator = intervals[var_name].iteritems()
        self._contrast = contrast
        self.step_height = step_height
        self.response_queue = []

    def next(self):
        return self.generator.next()[1]

    def record_response(self, response):
        self.response_queue.append(response)

    def _mean_response(self):
        return np.array(self.response_queue).mean()

    @property
    def contrast(self):
        return self._contrast

    def update_if_greater_than(self, threshold):
        if self._mean_response() > threshold:
            self._contrast -= self.step_height
