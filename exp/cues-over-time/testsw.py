#!/usr/bin/env python
import unittest
import os

import trials
import experiment

class SmallWindowTests(unittest.TestCase):

    def setUp(self):
        self.posner = experiment.Posner()
        self.test_trials = trials.add_cued_trials(0.1, 0.5, 5, 1)

    def tearDown(self):
        self.posner.close()
        try:
            os.remove(self.posner.data_file_name)
        except OSError:
            pass

    def test_visuals(self):
        self.posner.present_trial()


    def test_instructions(self):
        text_key = 1
        self.posner.load_text(text_key, "Hello world!")
        self.posner.show_text(text_key)


    def test_make_trials_and_run_a_few(self):
        self.posner.run_trials(self.test_trials.head(3))


    def test_trial_vars_not_in_default_throws_error(self):
        self.test_trials['var_not_in_default_trial'] = 'xxx'
        with self.assertRaises(AssertionError):
            self.posner.run_trials(self.test_trials)


    def test_getting_input_vars(self):
        """ Open up an input box and store the variables """
        self.posner.get_session_inputs()
        if not self.posner.session_inputs:
            self.fail()


    def test_experiment_window_can_start_from_scratch(self):
        """ Restart the window and redraw all objects during the experiment """
        self.posner.run_trials(self.test_trials.head(1))
        self.posner.get_session_inputs()
        self.posner.run_trials(self.test_trials.tail(1))


    def test_get_key_press(self):
        """ Saves a response to a file """
        test_data_file = 'test-key-press.txt'
        self.posner.open_data_file(test_data_file)
        self.posner.run_trials(self.test_trials.head(1))
        self.assertTrue(os.path.isfile(test_data_file))


    def test_can_quit_experiment_during_text(self):
        """ Should be able to quit during any instructions screen """
        text_key = 1
        self.posner.load_text(text_key, "Press Q to quit")
        with self.assertRaises(experiment.QuitException):
            self.posner.show_text(text_key)


class FullWindowTests(unittest.TestCase):

    def setUp(self):
        self.posner = experiment.Posner(fullscr = True)
        self.test_trials = trials.add_cued_trials(0.1, 0.5, 5, 1)

    def tearDown(self):
        self.posner.close()
        try:
            os.remove(self.posner.data_file_name)
        except OSError:
            pass


    def test_getting_popup_input_over_full_screen(self):
        self.posner.run_trials(self.test_trials.head(1))
        self.posner.get_session_inputs()
        self.posner.run_trials(self.test_trials.tail(1))

class SessionTests(unittest.TestCase):

    def setUp(self):
        self.files_to_delete = []

    def tearDown(self):
        if self.files_to_delete:
            for f in self.files_to_delete:
                try:
                    os.remove(f)
                except OSError:
                    pass

    def test_empty_data_file_deletes_on_close(self):
        """ Empty data files get deleted when the experiment closes """
        empty_data_file = 'empty.txt'
        user1 = experiment.Posner()
        self.assertFalse(os.path.isfile(empty_data_file))
        user1.open_data_file(empty_data_file)
        self.assertTrue(os.path.isfile(empty_data_file))
        user1.close()
        self.assertFalse(os.path.isfile(empty_data_file))


    def test_filled_data_doesnt_delete(self):
        filled_data_file = 'filled.txt'
        user1 = experiment.Posner()
        self.assertFalse(os.path.isfile(filled_data_file))
        user1.open_data_file(filled_data_file)
        self.files_to_delete.append(filled_data_file)
        user1.data_file.write('my\tdata\t')
        user1.close()
        self.assertTrue(os.path.isfile(filled_data_file))


    def test_two_users_cant_have_same_data_file(self):
        same_data_file = 'same-data-file.txt'

        user1 = experiment.Posner()
        user1.open_data_file(same_data_file)
        self.files_to_delete += [same_data_file, ]

        user2 = experiment.Posner()
        with self.assertRaises(experiment.ExistingDataFileException):
            user2.open_data_file(same_data_file)

        user1.close()


    def test_opening_a_data_file_writes_header_if_it_doesnt_exist(self):
        test_experiment_name = 'test-name-for-header'
        test_experiment_header = '.'+test_experiment_name
        self.assertFalse(os.path.isfile(test_experiment_header))
        user1 = experiment.Posner(test_experiment_name)
        user1.make_header()
        self.files_to_delete += ['filled-2.txt', '.test-name-for-header']
        self.assertTrue(os.path.isfile(test_experiment_header))
