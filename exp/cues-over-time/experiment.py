#!/usr/bin/env python
import os
import yaml

from psychopy import visual, core, gui, event

class Posner(object):
    FIXATION_DURATION = 1.0
    FIXATION_OFFSET_TO_CUE_ONSET = 1.0
    CUE_DURATION = 1.0

    def __init__(self, name = 'Posner', fullscr = False):
        self.name = name

        self.win_params = {'fullscr': fullscr}
        self.win = None

        # generator for experiment info
        # must be saved in order
        experiment_info = yaml.load_all(open('experiment.yaml', 'r'))
        self.session_inputs = experiment_info.next()
        self.response_info = experiment_info.next()
        self.quit_status = experiment_info.next()

        self.texts = {}

        self.trials = None

        self.data_file_name = ""  ## TODO reformat as key-dict object
        self.data_file = None

        self.stimuli = {}

        self.default_trial = {
            'cue_type': 'dot',
            'cue_loc': 'right',
            'isi': 0.5,
            'target_loc': 'right',
            'target_contrast': 1.0,
        }

        self.variable_order = self.session_inputs.keys() + self.default_trial.keys()

    def make_header(self):
        with open('.{}'.format(self.name), 'w') as header_file:
            header_file.write('\t'.join(self.variable_order))

    def make_win(self):
        if self.win:
            self.win.close()

        self.win_params.update({
            'size': [800, 800],
            'units': 'pix',
            'winType': 'pyglet'
        })

        self.win = visual.Window(**self.win_params)

    def make_stimuli(self):
        self.stimuli = {}
        self.stimuli['fixation'] = visual.TextStim(self.win,
            text = '+', height = 80, color = 'black')
        self.stimuli['cue'] = visual.TextStim(self.win,
            text = '.', height = 80, color = 'black')
        self.stimuli['target'] = visual.TextStim(self.win,
            text = '*', height = 50, color = 'black')

    def get_session_inputs(self):
        if self.win:
            self.win.close()
            self.win = None

        inputs_dlg = gui.DlgFromDict(self.session_inputs)
        if not inputs_dlg.OK:
            print 'User canceled'

    def open_data_file(self, name):
        self.data_file_name = name
        if os.path.isfile(self.data_file_name):
            raise ExistingDataFileException("Already data file with that name")
        self.data_file = open(name, 'w')

    def load_text(self, key, text):
        if not self.win:
            self.make_win()

        self.texts[key] = visual.TextStim(self.win, text = text)

    def show_text(self, key):
        if not self.win:
            self.make_win()

        self.texts[key].draw()
        self.win.flip()
        response = event.waitKeys(
            keyList = self.response_info['keys'].keys() + [self.quit_status['quit_key'],],
            timeStamped = core.Clock()
        )[0]
        pressed_key = response[0]
        if pressed_key == self.quit_status['quit_key']:
            raise QuitException('The quit key was pressed')
            self.close()

        answer = self.response_info['keys'][pressed_key]
        return answer

    def run_trials(self, trials):
        # check that the trials are valid
        for col in trials:
            if col not in self.default_trial:
                raise AssertionError(col + ' not found in default_trial dict')

        for _, row in trials.iterrows():
            if not self.win:
                self.make_win()
                self.make_stimuli()
            trial = dict(self.default_trial.items() + row.to_dict().items())
            self.present_trial(trial)

    def present_trial(self, trial = None):
        # passing trial = None is really only useful for testing
        if not trial:
            self.make_win()
            self.make_stimuli()
            trial = self.default_trial.copy()

        self.stimuli['fixation'].draw()
        self.win.flip()
        core.wait(self.FIXATION_DURATION)

        self.win.flip()
        core.wait(self.FIXATION_OFFSET_TO_CUE_ONSET)

        self.stimuli['cue'].draw()
        self.win.flip()
        core.wait(self.CUE_DURATION)

        self.win.flip()
        core.wait(trial['isi'])

        self.stimuli['target'].draw()
        self.win.flip()

        # responses come in [(key, time), ] bundles
        response_bundle = event.waitKeys(
            maxWait = self.response_info['timeout'],
            keyList = self.response_info['keys'].keys(),
            timeStamped = core.Clock()
        )

        if response_bundle:
            key, rt = response_bundle[0]
            answer = self.response_info['keys'][key]
            rt *= 1000
        else:
            answer = 'timeout'
            rt = self.response_info['timeout'] * 1000

        data_line = '\t'.join([answer, str(rt)])
        try:
            self.data_file.write(data_line)
        except AttributeError:
            print data_line

    def close(self):
        if self.data_file:
            self.data_file.close()

            if os.stat(self.data_file_name)[6] == 0:  ## delete empty files
                os.remove(self.data_file_name)

            self.data_file = None
        if self.win:
            self.win.close()
            self.win = None

class QuitException(Exception):
    pass

class ExistingDataFileException(Exception):
    pass

if __name__ == '__main__':
    posner = Posner()
    posner.present_trial()
