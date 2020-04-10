def preferred_folio_urn(urn):
    """
    # @@@ we've been exposing the CITE urn, but maybe
    we should just expose the folio instead
    """
    if not urn.startswith("urn:cite2:hmt:msA.v1:"):
        return urn
    _, ref = urn.rsplit(":", maxsplit=1)
    # @@@ hardcoded version
    return f"urn:cts:greekLit:tlg0012.tlg001.msA-folios:{ref}"


def as_zero_based(int_val):
    """
    https://www.w3.org/TR/annotation-model/#model-35
    The relative position of the first Annotation in the items list, relative to the Annotation Collection. The first entry in the first page is considered to be entry 0.
    Each Page should have exactly 1 startIndex, and must not have more than 1. The value must be an xsd:nonNegativeInteger.

    JHU seems to be using zero-based pagination too, so we're matching that.
    """
    return int_val - 1
