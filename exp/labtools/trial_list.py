from collections import namedtuple

from UserList import UserList

class TrialList(UserList):
    @classmethod
    def from_dataframe(cls, dataframe):
        Trial = namedtuple('Trial', dataframe.columns)
        data = [Trial(*trial[1:]) for trial in dataframe.itertuples()]
        return cls(data, column_order=dataframe.columns)

    def __init__(self, data, column_order=None):
        self.column_order = column_order
        return super(TrialList, self).__init__(data)
