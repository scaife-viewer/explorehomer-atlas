class Passage:
    def __init__(self, start, end=None):
        self.start = start
        self.end = end

    @staticmethod
    def get_ranked_ancestors(obj):
        return list(obj.get_ancestors().filter(rank__gt=0)) + [obj]

    @staticmethod
    def extract_human_readable_part(kind, ref):
        return f"{kind.title()} {ref}"

    @property
    def human_readable_reference(self):
        """
        refs https://github.com/scaife-viewer/scaife-viewer/issues/69
        Book 1 Line 1 to Book 1 Line 30
        Book 1 Line 1 to Line 30
        Book 1 to Book 2

        Folio 12r Book 1 Line 1 to Line 6
        """
        start_objs = self.get_ranked_ancestors(self.start)

        if self.end is None:
            end_objs = start_objs
        else:
            end_objs = self.get_ranked_ancestors(self.end)

        start_pieces = []
        end_pieces = []
        for start, end in zip(start_objs, end_objs):
            start_pieces.append(
                self.extract_human_readable_part(start.kind, start.lowest_citable_part)
            )
            if start.ref != end.ref:
                end_pieces.append(
                    self.extract_human_readable_part(end.kind, end.lowest_citable_part)
                )
        start_fragment = " ".join(start_pieces).strip()
        end_fragment = " ".join(end_pieces).strip()
        if end_fragment:
            return " to ".join([start_fragment, end_fragment])
        return start_fragment


class PassageSiblingMetadata:
    def __init__(self, passage, previous_objects=None, next_objects=None):
        self.passage = passage
        self.previous_objects = previous_objects
        self.next_objects = next_objects

    @staticmethod
    def get_siblings_in_range(siblings, start, end, field_name="idx"):
        for sibling in siblings:
            if sibling[field_name] >= start and sibling[field_name] <= end:
                yield sibling

    @property
    def all(self):
        text_part_siblings = self.passage.start.get_siblings()
        data = []
        for tp in text_part_siblings.values("ref", "urn", "idx"):
            lcp = tp["ref"].split(".").pop()
            data.append({"lcp": lcp, "urn": tp.get("urn"), "idx": tp["idx"]})
        if len(data) == 1:
            # don't return
            data = []
        return data

    @property
    def selected(self):
        return list(
            self.get_siblings_in_range(
                self.all, self.passage.start.idx, self.passage.end.idx
            )
        )

    @property
    def previous(self):
        if self.previous_objects:
            return list(
                self.get_siblings_in_range(
                    self.all,
                    self.previous_objects[0]["idx"],
                    self.previous_objects[-1]["idx"],
                )
            )
        return []

    @property
    def next(self):
        if self.next_objects:
            return list(
                self.get_siblings_in_range(
                    self.all, self.next_objects[0]["idx"], self.next_objects[-1]["idx"],
                )
            )
        return []
