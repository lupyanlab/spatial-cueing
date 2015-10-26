from collections import namedtuple

from UserList import UserList

class TrialList(UserList):
    @classmethod
    def from_dataframe(cls, dataframe):
        Trial = namedtuple('Trial', dataframe.columns)
        data = [Trial(*trial[1:]) for trial in dataframe.itertuples()]
        return cls(data)
