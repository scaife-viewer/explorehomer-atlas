import copy

import hypothesis

from readhomer_atlas.library.importers import CTSImporter
from readhomer_atlas.library.urn import URN
from readhomer_atlas.tests import constants
from readhomer_atlas.tests.strategies import URNs


@hypothesis.given(URNs.cts_urns())
def test_destructure(node_urn):
    # TODO: I realise this code is on the uglier side of things but I
    # anticipate that when we develop our base URN abstraction as discussed it
    # should become easier and cleaner for us to make general statements and
    # assertions about the characteristics any particular URN during
    # property-based testing and then we can refactor the noisier parts below.
    tokens = "Some tokens"
    parsed = URN(node_urn).parsed
    passage = parsed["ref"]
    scheme = [f"rank_{idx + 1}" for idx, _ in enumerate(passage.split("."))]
    version_data = copy.deepcopy(constants.VERSION_DATA)
    version_data["metadata"].update({"citation_scheme": scheme})

    nodes = CTSImporter(version_data).destructure_node(node_urn, tokens)

    if parsed["exemplar"]:
        assert len(nodes) - len(scheme) == 6
    else:
        assert len(nodes) - len(scheme) == 5

    urn_root, _ = node_urn.rsplit(":", maxsplit=1)
    passage_nodes = nodes[-len(scheme) :]
    for idx, node in enumerate(passage_nodes):
        assert node["urn"] == f"{urn_root}:{node['ref']}"
        assert node["rank"] == idx + 1
        assert node["kind"] == scheme[idx]
        if idx > 0:
            assert node["ref"].startswith(f"{passage_nodes[idx - 1]['ref']}.")
        if idx == passage_nodes.index(passage_nodes[-1]):
            assert node["text_content"] == tokens
        else:
            assert "text_content" not in node
