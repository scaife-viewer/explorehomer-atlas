import os

from django.utils.functional import cached_property

import requests

from ..library.models import Node
from .utils import preferred_folio_urn


class AlignmentsShim:
    """
    Shim to allow us to retrieve alignment data from explorehomer;
    eventually, we'll likely want to write out bonding box info as standoff annotation
    and ship to explorehomer directly.
    """

    GRAPHQL_ENDPOINT = os.environ.get(
        "ATLAS_GRAPHQL_ENDPOINT",
        "https://explorehomer-atlas-dev.herokuapp.com/graphql/",
    )

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
        # @@@ hardcoded version urn
        # @@@ add the ability to get a count from an edge
        reference = f"urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:{ref}"
        predicate = f'reference:"{reference}"'
        if idx:
            predicate = f"{predicate} idx: {idx}"
        resp = requests.post(
            self.GRAPHQL_ENDPOINT,
            json={
                "query": """
                {
                    textAlignmentChunks(%s) {
                        edges {
                            node {
                                %s
                            }
                        }
                    }
                }"""
                % (predicate, "\n".join(fields))
            },
        )
        data = []
        for edge in resp.json()["data"]["textAlignmentChunks"]["edges"]:
            data.append(edge["node"])
        return data
