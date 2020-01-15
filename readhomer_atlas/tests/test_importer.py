import copy
from unittest import mock

from readhomer_atlas.library.importers import CTSImporter
from readhomer_atlas.tests import constants


def test_destructure():
    node_urn = "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.1"
    tokens = "Some tokens"

    assert CTSImporter(constants.VERSION_DATA).destructure_node(node_urn, tokens) == [
        {"kind": "nid", "urn": "urn:cts:"},
        {"kind": "namespace", "urn": "urn:cts:greekLit:"},
        {"kind": "textgroup", "urn": "urn:cts:greekLit:tlg0012:"},
        {"kind": "work", "urn": "urn:cts:greekLit:tlg0012.tlg001:"},
        {
            "kind": "version",
            "urn": "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:",
            "metadata": constants.VERSION_DATA["metadata"],
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
    version_data = copy.deepcopy(constants.VERSION_DATA)
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
    read_data=constants.PASSAGE,
)
@mock.patch("readhomer_atlas.library.importers.Node")
def test_importer(mock_node, mock_open):
    CTSImporter(constants.VERSION_DATA, {}).apply()

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
    read_data=constants.PASSAGE,
)
@mock.patch("readhomer_atlas.library.importers.Node")
def test_importer_exemplar(mock_node, mock_open):
    version_data = copy.deepcopy(constants.VERSION_DATA)
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
