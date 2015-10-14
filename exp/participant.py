from labtools.participant import Participant

class SpatialCueingParticipant(Participant):
    def get_trial_list_kwargs(self):
        """ Get a subset of variables to pass to the trial list creator. """
        keys_to_copy = ['subj_id', 'experimenter', 'sona_experiment_code',
                        'cue_contrast', 'mask_type']
        kwargs = {k: self[k] for k in keys_to_copy}

        # Interpret any signifiers here
        cue_contrast_map = {'word_arrow': ['visual_word', 'visual_arrow'],
                            'visual_auditory': ['visual_word', 'auditory_word']}
        kwargs['cue_type'] = cue_contrast_map[self['cue_contrast']]

        return kwargs
