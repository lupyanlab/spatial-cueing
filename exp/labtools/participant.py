import yaml
from UserDict import UserDict

import unipath

from psychopy import gui, misc, data, core


class Participant(UserDict):
    """ Identifiers and files for this participant. """
    @classmethod
    def from_yaml(cls, participant_yaml):
        with open(participant_yaml, 'r') as f:
            data = yaml.load(f)
            data['participant_yaml'] = participant_yaml
        return cls(data)

    def get_subj_info(self):
        requirements = ['subj_info_options', 'participant_yaml',
                        'sona_experiment_code', 'data_dir']
        assert all([req in self for req in requirements])

        subj_info = self['subj_info_options']
        fields = [info for _, info in sorted(subj_info.items())]

        # Determine order and tips
        ordered_names = [info['name'] for info in fields]
        dlg_tips = {info['name']: info['prompt'] for info in fields}

        # Load the last participant's options or use the defaults
        last_dlg_data = self['participant_yaml'] + '.pickle'
        try:
            dlg_data = misc.fromFile(last_dlg_data)
        except IOError:
            dlg_data = {info['name']: info['default'] for info in fields}

        # Set fixed fields
        dlg_data['date'] = data.getDateStr()
        dlg_data['sona_experiment_code'] = self['sona_experiment_code']
        fixed_fields = ['date', 'sona_experiment_code']

        while True:
            # Bring up the dialogue
            dlg = gui.DlgFromDict(dlg_data, order=ordered_names,
                                  fixed=fixed_fields, tip=dlg_tips)

            if not dlg.OK:
                core.quit()

            subj_info = dict(dlg_data)
            data_filename = unipath.Path(self['data_dir'],
                                         subj_info['subj_id'] + '.csv')
            if data_filename.exists():
                print 'that data file already exists'
            else:
                misc.toFile(last_dlg_data, dlg_data)
                break

        open(data_filename, 'w')
        subj_info['data_filename'] = data_filename
        self.update(subj_info)
