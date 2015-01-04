#!/usr/bin/env python
import unittest

import trials
import mechanics

class TestTrialsGenerator(unittest.TestCase):

    def test_coerce_pandas_to_trialhandler(self):
        t = trials.Trials()

class TestTrialsIntervals(unittest.TestCase):

    def test_correct_number_of_trials_in_each_interval(self):
        expected = 10
        generated = trials.uniform_intervals(0, 100, 10, expected, var_name = 'isi')
        self.assertTrue(all(generated.groupby('bin').size() == expected))


    def test_two_trials_for_each_isi(self):
        duplicated = trials.add_cued_trials(0, 100, 10, 10, var_name = 'isi')
        self.assertTrue(all(duplicated.groupby('isi').size() == 2))


    @unittest.skip('Trials functions havent yet been updated')
    def test_make_trials_with_fixed_isi(self):
        fixed = trials.make_trials(cue_type = ['dot', 'none'])

class TestMechanicsStaircase(unittest.TestCase):

    def setUp(self):
        self.range = [0, 100]
        self.intervals = trials.uniform_intervals(
            self.range[0], self.range[1], 10, 10
        )

    def tearDown(self):
        pass


    def test_generator_methods(self):
        """ Ensures that the generator has next() like functionality """
        generator = mechanics.Staircase(self.intervals)
        self.assertGreaterEqual(generator.next(), self.range[0])
        self.assertLessEqual(generator.next(), self.range[1])


    def test_staircase_decreases_contrast_after_successful_hits(self):
        starting_contrast = 1.0
        generator = mechanics.Staircase(self.intervals, starting_contrast)

        step_width = 10

        self.assertTrue(generator.contrast, starting_contrast)

        responses = [1 for _ in range(step_width)]
        for r in responses:
            isi = generator.next()
            generator.record_response(r)

        generator.update_if_greater_than(0.8)

        self.assertTrue(generator.contrast, starting_contrast)
