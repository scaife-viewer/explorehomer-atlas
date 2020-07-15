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
