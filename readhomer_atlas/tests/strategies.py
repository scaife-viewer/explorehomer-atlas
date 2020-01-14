from hypothesis import strategies

from readhomer_atlas import constants


class URNs:
    @classmethod
    def cite_urns(cls, example=False):
        raise NotImplementedError()

    @classmethod
    def cts_urns(cls, example=False):
        strategy = strategies.from_regex(constants.CTS_URN)
        return strategy.example() if example else strategy
