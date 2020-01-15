import os


class URN:
    """
    Provides a subset of functionality from `MyCapytain.common.reference.URN`
    """

    NAMESPACE = 0
    TEXTGROUP = 1
    WORK = 2
    VERSION = 3
    EXEMPLAR = 4
    NO_PASSAGE = 5
    WORK_COMPONENT_LABELS = {
        TEXTGROUP: "textgroup",
        WORK: "work",
        VERSION: "version",
        EXEMPLAR: "exemplar",
    }

    def __str__(self):
        return self.urn

    def __init__(self, urn):
        self.urn = urn
        self.parsed = self.parse_urn(urn)

    def parse_urn(self, urn):
        parsed = {}
        for v in self.WORK_COMPONENT_LABELS.values():
            parsed[v] = None

        components = urn.split(":")
        try:
            _, _, namespace_component, work_component = components[:4]
        except ValueError:
            raise ValueError("Invalid URN")
        passage_component = next(iter(components[4:]), None)
        work_components = work_component.split(".")
        parsed.update({"namespace": namespace_component, "ref": passage_component})
        for constant, value in enumerate(work_components, 1):
            key = self.WORK_COMPONENT_LABELS[constant]
            parsed[key] = value
        return parsed

    def to_namespace(self):
        return f'urn:cts:{self.parsed["namespace"]}'

    def to_textgroup(self):
        return f'{self.to_namespace()}:{self.parsed["textgroup"]}'

    def to_work(self):
        return f'{self.to_textgroup()}.{self.parsed["work"]}'

    def to_version(self):
        return f'{self.to_textgroup()}.{self.parsed["version"]}'

    def to_exemplar(self):
        return f'{self.to_textgroup()}.{self.parsed["exemplar"]}'

    def to_no_passage(self):
        if self.parsed["ref"]:
            return self.urn.rsplit(":", maxsplit=1)[0]
        return self.urn

    def upTo(self, key):
        if key == self.NAMESPACE:
            return self.to_namespace()
        elif key == self.TEXTGROUP and self.parsed["textgroup"]:
            return self.to_textgroup()
        elif key == self.WORK and self.parsed["work"]:
            return self.to_work()
        elif key == self.VERSION and self.parsed["version"]:
            return self.to_version()
        elif key == self.EXEMPLAR and self.parsed["exemplar"]:
            return self.to_exemplar()
        elif key == self.NO_PASSAGE and self.parsed["work"]:
            return self.to_no_passage()
        else:
            raise KeyError("Provided key is not recognized.")
