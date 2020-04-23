from django.db.models import Q
from django.utils.functional import cached_property

from ..library.models import Node, TextAlignmentChunk
from ..library.utils import (
    extract_version_urn_and_ref,
    get_textparts_from_passage_reference,
)
from .utils import preferred_folio_urn


class AlignmentsShim:
    """
    Shim to allow us to retrieve alignment data indirectly from the database
    eventually, we'll likely want to write out bonding box info as standoff annotation
    and ship to explorehomer directly.
    """

    def __init__(self, folio_urn):
        self.folio_urn = preferred_folio_urn(folio_urn)

    @cached_property
    def folio_lines(self):
        return Node.objects.filter(urn__startswith=self.folio_urn).filter(kind="line")

    @cached_property
    def line_urns(self):
        return [l.urn for l in self.folio_lines]

    def get_ref(self):
        first = self.line_urns[0].rsplit(":", maxsplit=1)[1]
        last = self.line_urns[-1].rsplit(":", maxsplit=1)[1]
        # @@@ strip folios
        first = first.split(".", maxsplit=1)[1]
        last = last.split(".", maxsplit=1)[1]
        if first == last:
            return first
        return f"{first}-{last}"

    def get_alignment_data(self, idx=None, fields=None):
        if fields is None:
            fields = ["idx", "items", "citation"]

        ref = self.get_ref()
        version_urn = "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:"
        passage_reference = f"{version_urn}{ref}"

        # @@@ add as a Node manager method
        version_urn, ref = extract_version_urn_and_ref(passage_reference)
        try:
            version = Node.objects.get(urn=version_urn)
        except Node.DoesNotExist:
            raise Exception(f"{version_urn} was not found.")

        textparts_queryset = get_textparts_from_passage_reference(
            passage_reference, version
        )
        alignments = TextAlignmentChunk.objects.filter(
            Q(start__in=textparts_queryset) | Q(end__in=textparts_queryset)
        ).values(*fields)
        return list(alignments)
