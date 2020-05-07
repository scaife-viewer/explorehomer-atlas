from django.utils.functional import cached_property

from ..library.models import AudioAnnotation, Node, Token
from ..library.utils import (
    extract_version_urn_and_ref,
    filter_alignments_by_textparts,
    get_textparts_from_passage_reference,
)
from .utils import preferred_folio_urn


class FolioShimBase:
    version_urn = "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:"

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

    def get_textparts_queryset(self):
        ref = self.get_ref()
        passage_reference = f"{self.version_urn}{ref}"

        # @@@ add as a Node manager method
        version_urn, ref = extract_version_urn_and_ref(passage_reference)
        try:
            version = Node.objects.get(urn=version_urn)
        except Node.DoesNotExist:
            raise Exception(f"{version_urn} was not found.")

        return get_textparts_from_passage_reference(passage_reference, version)


class AlignmentsShim(FolioShimBase):
    """
    Shim to allow us to retrieve alignment data indirectly from the database
    eventually, we'll likely want to write out bonding box info as standoff annotation
    and ship to explorehomer directly.
    """

    def get_object_list(self, idx=None, fields=None):
        if fields is None:
            fields = ["idx", "items", "citation"]
        textparts_queryset = self.get_textparts_queryset()
        alignments = filter_alignments_by_textparts(textparts_queryset).values(*fields)
        return list(alignments)


class NamedEntitiesShim(FolioShimBase):
    def get_object_list(self, idx=None, fields=None):
        textparts_queryset = self.get_textparts_queryset()

        named_entities = []
        # @@@ fake idx
        idx = 0
        tokens = Token.objects.filter(
            text_part__in=textparts_queryset
        ).prefetch_related("named_entities")
        for token in tokens:
            for named_entity in token.named_entities.all():
                print(idx)
                named_entities.append(
                    {"token": token, "named_entity_obj": named_entity, "idx": idx}
                )
                idx += 1
        return named_entities


class AudioAnnotationsShim(FolioShimBase):
    version_urn = "urn:cts:greekLit:tlg0012.tlg001.msA:"

    def get_object_list(self, idx=None, fields=None):
        textparts_queryset = self.get_textparts_queryset()
        return [
            {"idx": pos, "obj": obj}
            for pos, obj in enumerate(
                AudioAnnotation.objects.filter(text_parts__in=textparts_queryset)
            )
        ]
