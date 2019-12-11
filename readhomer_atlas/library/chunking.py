import abc


class ChunkingProxy(abc.ABC):
    """Take an entire tree of nodes ingested with the standard ATLAS chunking
    method ('linear', 'bibliographic', ?), and expose a mirror of a subset of
    the tree manipulation API able to derive new projections and alternate
    chunkings over the data. Each concrete proxy instance needs to implement
    some TBD, minimum, uniform interface.
    """

    def __init__(self, root):
        # The root of an ATLAS node tree.
        self.root = root

    @abc.abstractmethod
    def get_ancestors(self, urn):
        pass

    @abc.abstractmethod
    def get_siblings(self, urn):
        pass

    @abc.abstractmethod
    def get_descendants(self, urn):
        pass

    # ...etc.


class CardChunkingProxy(ChunkingProxy):
    """
    urn:cts:greekLit:tlg0012.tlg001.perseus-grc2.card:
    """

    chunking = "card"

    # ...Implement the abstract interface.
