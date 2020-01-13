import copy
from unittest import mock

import hypothesis

from readhomer_atlas.library.importers import CTSImporter
from readhomer_atlas.tests.strategies import URNs


# fmt: off
PASSAGE = """
    Il.1.1 μῆνιν ἄειδε θεὰ Πηληϊάδεω Ἀχιλῆος
    Il.1.2 οὐλομένην, ἣ μυρίʼ Ἀχαιοῖς ἄλγεʼ ἔθηκε,
    Il.1.3 πολλὰς δʼ ἰφθίμους ψυχὰς Ἄϊδι προΐαψεν
    Il.1.4 ἡρώων, αὐτοὺς δὲ ἑλώρια τεῦχε κύνεσσιν
    Il.1.5 οἰωνοῖσί τε πᾶσι, Διὸς δʼ ἐτελείετο βουλή,
    Il.1.6 ἐξ οὗ δὴ τὰ πρῶτα διαστήτην ἐρίσαντε
    Il.1.7 Ἀτρεΐδης τε ἄναξ ἀνδρῶν καὶ δῖος Ἀχιλλεύς.
""".strip("\n")
# fmt: on


VERSION_DATA = {
    "urn": "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:",
    "content_path": "tlg0012.tlg001.perseus-grc2.txt",
    "metadata": {
        "work_title": "Iliad",
        "work_urn": "urn:cts:greekLit:tlg0012.tlg001:",
        "type": "edition",
        "first_passage_urn": "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.1-1.7",
        "citation_scheme": ["rank_1", "rank_2"],
    },
}


@hypothesis.given(URNs.cts_urns())
def test_destructure__property(node_urn):
    # TODO: I realise this code is on the uglier side of things but I
    # anticipate that when we develop our base URN abstraction as discussed it
    # should become easier and cleaner for us to make general statements and
    # assertions about the characteristics any particular URN during
    # property-based testing and then we can refactor the noisier parts below.
    # I'm also looking for a naming convention for distinguishing
    # property-based test cases but haven't come up with any good ones yet.
    tokens = "Some tokens"
    _, work, passage = node_urn.rsplit(":", maxsplit=2)
    scheme = [f"rank_{idx + 1}" for idx, _ in enumerate(passage.split("."))]
    version_data = copy.deepcopy(VERSION_DATA)
    version_data["metadata"].update({"citation_scheme": scheme})

    nodes = CTSImporter(version_data).destructure_node(node_urn, tokens)

    has_exemplar = len(work.split(".")) == 4
    if has_exemplar:
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


def test_destructure():
    node_urn = "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.1"
    tokens = "Some tokens"

    assert CTSImporter(VERSION_DATA).destructure_node(node_urn, tokens) == [
        {"kind": "nid", "urn": "urn:cts:"},
        {"kind": "namespace", "urn": "urn:cts:greekLit:"},
        {"kind": "textgroup", "urn": "urn:cts:greekLit:tlg0012:"},
        {"kind": "work", "urn": "urn:cts:greekLit:tlg0012.tlg001:"},
        {
            "kind": "version",
            "urn": "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:",
            "metadata": VERSION_DATA["metadata"],
        },
        {
            "kind": "rank_1",
            "urn": "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1",
            "ref": "1",
            "rank": 1,
        },
        {
            "kind": "rank_2",
            "urn": "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.1",
            "ref": "1.1",
            "text_content": tokens,
            "rank": 2,
        },
    ]


def test_destructure_alphanumeric():
    node_urn = "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.2.a.3"
    scheme = ["rank_1", "rank_2", "rank_3", "rank_4"]
    tokens = "Some tokens"
    version_data = copy.deepcopy(VERSION_DATA)
    version_data["metadata"].update({"citation_scheme": scheme})

    assert CTSImporter(version_data).destructure_node(node_urn, tokens) == [
        {"kind": "nid", "urn": "urn:cts:"},
        {"kind": "namespace", "urn": "urn:cts:greekLit:"},
        {"kind": "textgroup", "urn": "urn:cts:greekLit:tlg0012:"},
        {"kind": "work", "urn": "urn:cts:greekLit:tlg0012.tlg001:"},
        {
            "kind": "version",
            "urn": "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:",
            "metadata": version_data["metadata"],
        },
        {
            "kind": "rank_1",
            "urn": "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1",
            "ref": "1",
            "rank": 1,
        },
        {
            "kind": "rank_2",
            "urn": "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.2",
            "ref": "1.2",
            "rank": 2,
        },
        {
            "kind": "rank_3",
            "urn": "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.2.a",
            "ref": "1.2.a",
            "rank": 3,
        },
        {
            "kind": "rank_4",
            "urn": "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.2.a.3",
            "ref": "1.2.a.3",
            "text_content": tokens,
            "rank": 4,
        },
    ]


@mock.patch(
    "readhomer_atlas.library.importers.open",
    new_callable=mock.mock_open,
    read_data=PASSAGE,
)
@mock.patch("readhomer_atlas.library.importers.Node")
def test_importer(mock_node, mock_open):
    CTSImporter(VERSION_DATA, {}).apply()

    assert mock_node.mock_calls == [
        mock.call.add_root(kind="nid", urn="urn:cts:", idx=0),
        mock.call.add_root().add_child(
            kind="namespace", urn="urn:cts:greekLit:", idx=0
        ),
        mock.call.add_root()
        .add_child()
        .add_child(kind="textgroup", urn="urn:cts:greekLit:tlg0012:", idx=0),
        mock.call.add_root()
        .add_child()
        .add_child()
        .add_child(kind="work", urn="urn:cts:greekLit:tlg0012.tlg001:", idx=0),
        mock.call.add_root()
        .add_child()
        .add_child()
        .add_child()
        .add_child(
            kind="version",
            urn="urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:",
            metadata={
                "work_title": "Iliad",
                "work_urn": "urn:cts:greekLit:tlg0012.tlg001:",
                "type": "edition",
                "first_passage_urn": "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.1-1.7",
                "citation_scheme": ["rank_1", "rank_2"],
            },
            idx=0,
        ),
        mock.call.add_root()
        .add_child()
        .add_child()
        .add_child()
        .add_child()
        .add_child(
            kind="rank_1",
            urn="urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1",
            ref="1",
            rank=1,
            idx=0,
        ),
        mock.call.add_root()
        .add_child()
        .add_child()
        .add_child()
        .add_child()
        .add_child()
        .add_child(
            kind="rank_2",
            urn="urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.1",
            ref="1.1",
            rank=2,
            text_content="μῆνιν ἄειδε θεὰ Πηληϊάδεω Ἀχιλῆος",
            idx=0,
        ),
        mock.call.add_root()
        .add_child()
        .add_child()
        .add_child()
        .add_child()
        .add_child()
        .add_child(
            kind="rank_2",
            urn="urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.2",
            ref="1.2",
            rank=2,
            text_content="οὐλομένην, ἣ μυρίʼ Ἀχαιοῖς ἄλγεʼ ἔθηκε,",
            idx=1,
        ),
        mock.call.add_root()
        .add_child()
        .add_child()
        .add_child()
        .add_child()
        .add_child()
        .add_child(
            kind="rank_2",
            urn="urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.3",
            ref="1.3",
            rank=2,
            text_content="πολλὰς δʼ ἰφθίμους ψυχὰς Ἄϊδι προΐαψεν",
            idx=2,
        ),
        mock.call.add_root()
        .add_child()
        .add_child()
        .add_child()
        .add_child()
        .add_child()
        .add_child(
            kind="rank_2",
            urn="urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.4",
            ref="1.4",
            rank=2,
            text_content="ἡρώων, αὐτοὺς δὲ ἑλώρια τεῦχε κύνεσσιν",
            idx=3,
        ),
        mock.call.add_root()
        .add_child()
        .add_child()
        .add_child()
        .add_child()
        .add_child()
        .add_child(
            kind="rank_2",
            urn="urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.5",
            ref="1.5",
            rank=2,
            text_content="οἰωνοῖσί τε πᾶσι, Διὸς δʼ ἐτελείετο βουλή,",
            idx=4,
        ),
        mock.call.add_root()
        .add_child()
        .add_child()
        .add_child()
        .add_child()
        .add_child()
        .add_child(
            kind="rank_2",
            urn="urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.6",
            ref="1.6",
            rank=2,
            text_content="ἐξ οὗ δὴ τὰ πρῶτα διαστήτην ἐρίσαντε",
            idx=5,
        ),
        mock.call.add_root()
        .add_child()
        .add_child()
        .add_child()
        .add_child()
        .add_child()
        .add_child(
            kind="rank_2",
            urn="urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.7",
            ref="1.7",
            rank=2,
            text_content="Ἀτρεΐδης τε ἄναξ ἀνδρῶν καὶ δῖος Ἀχιλλεύς.",
            idx=6,
        ),
        mock.call.objects.get(urn="urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:"),
        mock.call.objects.get().get_descendant_count(),
        mock.ANY,
        mock.ANY,
    ]


@mock.patch(
    "readhomer_atlas.library.importers.open",
    new_callable=mock.mock_open,
    read_data=PASSAGE,
)
@mock.patch("readhomer_atlas.library.importers.Node")
def test_importer_exemplar(mock_node, mock_open):
    version_data = copy.deepcopy(VERSION_DATA)
    version_data.update({"urn": "urn:cts:greekLit:tlg0013.tlg001.perseus-grc2.card:"})
    CTSImporter(version_data, {}).apply()

    assert mock_node.mock_calls == [
        mock.call.add_root(kind="nid", urn="urn:cts:", idx=0),
        mock.call.add_root().add_child(
            kind="namespace", urn="urn:cts:greekLit:", idx=0
        ),
        mock.call.add_root()
        .add_child()
        .add_child(kind="textgroup", urn="urn:cts:greekLit:tlg0013:", idx=0),
        mock.call.add_root()
        .add_child()
        .add_child()
        .add_child(kind="work", urn="urn:cts:greekLit:tlg0013.tlg001:", idx=0),
        mock.call.add_root()
        .add_child()
        .add_child()
        .add_child()
        .add_child(
            kind="version",
            urn="urn:cts:greekLit:tlg0013.tlg001.perseus-grc2:",
            metadata={
                "work_title": "Iliad",
                "work_urn": "urn:cts:greekLit:tlg0012.tlg001:",
                "type": "edition",
                "first_passage_urn": "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.1-1.7",
                "citation_scheme": ["rank_1", "rank_2"],
            },
            idx=0,
        ),
        mock.call.add_root()
        .add_child()
        .add_child()
        .add_child()
        .add_child()
        .add_child(
            kind="exemplar",
            urn="urn:cts:greekLit:tlg0013.tlg001.perseus-grc2.card",
            idx=0,
        ),
        mock.call.add_root()
        .add_child()
        .add_child()
        .add_child()
        .add_child()
        .add_child()
        .add_child(
            kind="rank_1",
            urn="urn:cts:greekLit:tlg0013.tlg001.perseus-grc2.card:1",
            ref="1",
            rank=1,
            idx=0,
        ),
        mock.call.add_root()
        .add_child()
        .add_child()
        .add_child()
        .add_child()
        .add_child()
        .add_child()
        .add_child(
            kind="rank_2",
            urn="urn:cts:greekLit:tlg0013.tlg001.perseus-grc2.card:1.1",
            ref="1.1",
            rank=2,
            text_content="μῆνιν ἄειδε θεὰ Πηληϊάδεω Ἀχιλῆος",
            idx=0,
        ),
        mock.call.add_root()
        .add_child()
        .add_child()
        .add_child()
        .add_child()
        .add_child()
        .add_child()
        .add_child(
            kind="rank_2",
            urn="urn:cts:greekLit:tlg0013.tlg001.perseus-grc2.card:1.2",
            ref="1.2",
            rank=2,
            text_content="οὐλομένην, ἣ μυρίʼ Ἀχαιοῖς ἄλγεʼ ἔθηκε,",
            idx=1,
        ),
        mock.call.add_root()
        .add_child()
        .add_child()
        .add_child()
        .add_child()
        .add_child()
        .add_child()
        .add_child(
            kind="rank_2",
            urn="urn:cts:greekLit:tlg0013.tlg001.perseus-grc2.card:1.3",
            ref="1.3",
            rank=2,
            text_content="πολλὰς δʼ ἰφθίμους ψυχὰς Ἄϊδι προΐαψεν",
            idx=2,
        ),
        mock.call.add_root()
        .add_child()
        .add_child()
        .add_child()
        .add_child()
        .add_child()
        .add_child()
        .add_child(
            kind="rank_2",
            urn="urn:cts:greekLit:tlg0013.tlg001.perseus-grc2.card:1.4",
            ref="1.4",
            rank=2,
            text_content="ἡρώων, αὐτοὺς δὲ ἑλώρια τεῦχε κύνεσσιν",
            idx=3,
        ),
        mock.call.add_root()
        .add_child()
        .add_child()
        .add_child()
        .add_child()
        .add_child()
        .add_child()
        .add_child(
            kind="rank_2",
            urn="urn:cts:greekLit:tlg0013.tlg001.perseus-grc2.card:1.5",
            ref="1.5",
            rank=2,
            text_content="οἰωνοῖσί τε πᾶσι, Διὸς δʼ ἐτελείετο βουλή,",
            idx=4,
        ),
        mock.call.add_root()
        .add_child()
        .add_child()
        .add_child()
        .add_child()
        .add_child()
        .add_child()
        .add_child(
            kind="rank_2",
            urn="urn:cts:greekLit:tlg0013.tlg001.perseus-grc2.card:1.6",
            ref="1.6",
            rank=2,
            text_content="ἐξ οὗ δὴ τὰ πρῶτα διαστήτην ἐρίσαντε",
            idx=5,
        ),
        mock.call.add_root()
        .add_child()
        .add_child()
        .add_child()
        .add_child()
        .add_child()
        .add_child()
        .add_child(
            kind="rank_2",
            urn="urn:cts:greekLit:tlg0013.tlg001.perseus-grc2.card:1.7",
            ref="1.7",
            rank=2,
            text_content="Ἀτρεΐδης τε ἄναξ ἀνδρῶν καὶ δῖος Ἀχιλλεύς.",
            idx=6,
        ),
        mock.call.objects.get(urn="urn:cts:greekLit:tlg0013.tlg001.perseus-grc2.card:"),
        mock.call.objects.get().get_descendant_count(),
        mock.ANY,
        mock.ANY,
    ]
