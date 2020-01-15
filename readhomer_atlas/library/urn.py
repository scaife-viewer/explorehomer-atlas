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
            (
                nid,
                protocol,
                namespace_component,
                work_component,
                passage_component,
            ) = components[:5]
        except ValueError:
            raise ValueError("Invalid URN")
        work_components = work_component.split(".")
        parsed.update(
            {
                "nid": nid,
                "protocol": protocol,
                "namespace": namespace_component,
                "ref": passage_component,
            }
        )
        for constant, value in enumerate(work_components, 1):
            key = self.WORK_COMPONENT_LABELS[constant]
            parsed[key] = value
        return parsed

    @property
    def to_namespace(self):
        return ":".join(
            [self.parsed["nid"], self.parsed["protocol"], self.parsed["namespace"]]
        )

    @property
    def to_textgroup(self):
        return ":".join([self.to_namespace, self.parsed["textgroup"]])

    @property
    def to_work(self):
        return ".".join([self.to_textgroup, self.parsed["work"]])

    @property
    def to_version(self):
        return ".".join([self.to_work, self.parsed["version"]])

    @property
    def to_exemplar(self):
        return ".".join([self.to_version, self.parsed["exemplar"]])

    @property
    def to_no_passage(self):
        if self.parsed["ref"]:
            return self.urn.rsplit(":", maxsplit=1)[0]
        return self.urn

    def up_to(self, key):
        if key == self.NO_PASSAGE:
            label = "no_passage"
        else:
            label = self.WORK_COMPONENT_LABELS.get(key, None)
        if label is None:
            raise KeyError("Provided key is not recognized.")

        attr_name = f"to_{label}"
        try:
            value = getattr(self, attr_name)
        except TypeError:
            raise ValueError(f'URN has no "{label}" component')

        if key == self.NO_PASSAGE and self.parsed["work"]:
            return value

        # from https://cite-architecture.github.io/ctsurn_spec/specification.html#overall-structure-of-a-cts-urn
        # The value of the passage component may be a null string;
        # in this case, the work component must still be separated
        # from the null string by a colon.
        return f"{value}:"
