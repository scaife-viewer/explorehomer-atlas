import copy
import io
from unittest import mock

import hypothesis
import pytest

from readhomer_atlas.library.importers import CTSImporter
from readhomer_atlas.library.models import Node
from readhomer_atlas.tests.strategies import URNs


VERSION_DATA = {
    "urn": "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:",
    "content_path": "tlg0012.tlg001.perseus-grc2.txt",
    "metadata": {
        "work_title": "Iliad",
        "work_urn": "urn:cts:greekLit:tlg0012.tlg001:",
        "type": "edition",
        "first_passage_urn": "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.1-1.7",
        "citation_scheme": ["book", "line"],
    },
}

# fmt: off
PASSAGE = io.StringIO("""
    Il.1.1 μῆνιν ἄειδε θεὰ Πηληϊάδεω Ἀχιλῆος
    Il.1.2 οὐλομένην, ἣ μυρίʼ Ἀχαιοῖς ἄλγεʼ ἔθηκε,
    Il.1.3 πολλὰς δʼ ἰφθίμους ψυχὰς Ἄϊδι προΐαψεν
    Il.1.4 ἡρώων, αὐτοὺς δὲ ἑλώρια τεῦχε κύνεσσιν
    Il.1.5 οἰωνοῖσί τε πᾶσι, Διὸς δʼ ἐτελείετο βουλή,
    Il.1.6 ἐξ οὗ δὴ τὰ πρῶτα διαστήτην ἐρίσαντε
    Il.1.7 Ἀτρεΐδης τε ἄναξ ἀνδρῶν καὶ δῖος Ἀχιλλεύς.
""".strip("\n"))
# fmt: on


@hypothesis.given(URNs.cts_urns())
def test_destructure__property(node_urn):
    tokens = "Some tokens"
    _, passage = node_urn.rsplit(":", maxsplit=1)
    scheme = [f"x{idx + 1}" for idx, _ in enumerate(passage.split("."))]
    version_data = copy.deepcopy(VERSION_DATA)
    version_data["metadata"].update({"citation_scheme": scheme})
    nodes = CTSImporter(version_data).destructure_node(node_urn, tokens)

    raise NotImplementedError()


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
            "kind": "book",
            "urn": "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1",
            "ref": "1",
            "rank": 1,
        },
        {
            "kind": "line",
            "urn": "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.1",
            "ref": "1.1",
            "text_content": tokens,
            "rank": 2,
        },
    ]


def test_destructure_alphanumeric():
    node_urn = "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.2.a.3"
    scheme = ["a", "b", "c", "d"]
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
            "kind": "a",
            "urn": "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1",
            "ref": "1",
            "rank": 1,
        },
        {
            "kind": "b",
            "urn": "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.2",
            "ref": "1.2",
            "rank": 2,
        },
        {
            "kind": "c",
            "urn": "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.2.a",
            "ref": "1.2.a",
            "rank": 3,
        },
        {
            "kind": "d",
            "urn": "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.2.a.3",
            "ref": "1.2.a.3",
            "text_content": tokens,
            "rank": 4,
        },
    ]


@mock.patch("builtins.open", new_callable=mock.mock_open)
@mock.patch("readhomer_atlas.library.importers.Node.objects.get")
@mock.patch.object(Node, "add_child")
@pytest.mark.django_db
def test_importer(mock_add, mock_get, mock_open):
    mock_open.side_effect = [PASSAGE]
    CTSImporter(VERSION_DATA).apply()

    assert mock_add.mock_calls == [
        mock.call(idx=0, kind="namespace", urn="urn:cts:greekLit:"),
        mock.call().add_child(idx=0, kind="textgroup", urn="urn:cts:greekLit:tlg0012:"),
        mock.call()
        .add_child()
        .add_child(idx=0, kind="work", urn="urn:cts:greekLit:tlg0012.tlg001:"),
        mock.call()
        .add_child()
        .add_child()
        .add_child(
            idx=0,
            kind="version",
            metadata={
                "work_title": "Iliad",
                "work_urn": "urn:cts:greekLit:tlg0012.tlg001:",
                "type": "edition",
                "first_passage_urn": "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.1-1.7",
                "citation_scheme": ["book", "line"],
            },
            urn="urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:",
        ),
        mock.call()
        .add_child()
        .add_child()
        .add_child()
        .add_child(
            idx=0,
            kind="book",
            ref="1",
            rank=1,
            urn="urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1",
        ),
        mock.call()
        .add_child()
        .add_child()
        .add_child()
        .add_child()
        .add_child(
            idx=0,
            kind="line",
            ref="1.1",
            rank=2,
            text_content="μῆνιν ἄειδε θεὰ Πηληϊάδεω Ἀχιλῆος",
            urn="urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.1",
        ),
        mock.call()
        .add_child()
        .add_child()
        .add_child()
        .add_child()
        .add_child(
            idx=1,
            kind="line",
            ref="1.2",
            rank=2,
            text_content="οὐλομένην, ἣ μυρίʼ Ἀχαιοῖς ἄλγεʼ ἔθηκε,",
            urn="urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.2",
        ),
        mock.call()
        .add_child()
        .add_child()
        .add_child()
        .add_child()
        .add_child(
            idx=2,
            kind="line",
            ref="1.3",
            rank=2,
            text_content="πολλὰς δʼ ἰφθίμους ψυχὰς Ἄϊδι προΐαψεν",
            urn="urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.3",
        ),
        mock.call()
        .add_child()
        .add_child()
        .add_child()
        .add_child()
        .add_child(
            idx=3,
            kind="line",
            ref="1.4",
            rank=2,
            text_content="ἡρώων, αὐτοὺς δὲ ἑλώρια τεῦχε κύνεσσιν",
            urn="urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.4",
        ),
        mock.call()
        .add_child()
        .add_child()
        .add_child()
        .add_child()
        .add_child(
            idx=4,
            kind="line",
            ref="1.5",
            rank=2,
            text_content="οἰωνοῖσί τε πᾶσι, Διὸς δʼ ἐτελείετο βουλή,",
            urn="urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.5",
        ),
        mock.call()
        .add_child()
        .add_child()
        .add_child()
        .add_child()
        .add_child(
            idx=5,
            kind="line",
            ref="1.6",
            rank=2,
            text_content="ἐξ οὗ δὴ τὰ πρῶτα διαστήτην ἐρίσαντε",
            urn="urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.6",
        ),
        mock.call()
        .add_child()
        .add_child()
        .add_child()
        .add_child()
        .add_child(
            idx=6,
            kind="line",
            ref="1.7",
            rank=2,
            text_content="Ἀτρεΐδης τε ἄναξ ἀνδρῶν καὶ δῖος Ἀχιλλεύς.",
            urn="urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.7",
        ),
    ]
    assert mock_get.mock_calls[0] == mock.call(urn=VERSION_DATA["urn"])
    assert mock_get.mock_calls[1] == mock.call().get_descendant_count()
