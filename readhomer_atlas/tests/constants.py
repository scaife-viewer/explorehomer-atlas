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
    "path": "data/library/tlg0012/tlg001/tlg0012.tlg001.perseus-grc2.txt",
    "urn": "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:",
    "nodeKind": "version",
    "versionKind": "edition",
    "firstPassageUrn": "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.1-1.7",
    "citationScheme": ["book", "line"],
    "title": [{"lang": "eng", "value": "Iliad, Homeri Opera"}],
    "description": [
        {
            "lang": "eng",
            "value": "Homer, creator; Monro, D. B. (David Binning), 1836-1905, creator; Monro, D. B. (David Binning), 1836-1905, editor; Allen, Thomas W. (Thomas William), b. 1862, editor",
        }
    ],
}

VERSION_METADATA = {
    "citation_scheme": ["book", "line"],
    "work_title": "Iliad",
    "first_passage_urn": "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.1-1.7",
}

LIBRARY_DATA = {
    "text_groups": {
        "urn:cts:greekLit:tlg0012:": {
            "urn": "urn:cts:greekLit:tlg0012:",
            "nodeKind": "textgroup",
            "name": [{"lang": "eng", "value": "Homer"}],
        }
    },
    "works": {
        "urn:cts:greekLit:tlg0012.tlg001:": {
            "urn": "urn:cts:greekLit:tlg0012.tlg001:",
            "groupUrn": "urn:cts:greekLit:tlg0012:",
            "nodeKind": "work",
            "lang": "grc",
            "title": [{"lang": "eng", "value": "Iliad"}],
            "versions": [
                {
                    "urn": "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:",
                    "nodeKind": "version",
                    "versionKind": "edition",
                    "firstPassageUrn": "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.1-1.7",
                    "citationScheme": ["book", "line"],
                    "title": [{"lang": "eng", "value": "Iliad, Homeri Opera"}],
                    "description": [
                        {
                            "lang": "eng",
                            "value": "Homer, creator; Monro, D. B. (David Binning), 1836-1905, creator; Monro, D. B. (David Binning), 1836-1905, editor; Allen, Thomas W. (Thomas William), b. 1862, editor",
                        }
                    ],
                }
            ],
        },
        "urn:cts:greekLit:tlg0012.tlg002:": {
            "urn": "urn:cts:greekLit:tlg0012.tlg002:",
            "groupUrn": "urn:cts:greekLit:tlg0012:",
            "nodeKind": "work",
            "lang": "grc",
            "title": [{"lang": "eng", "value": "Odyssey"}],
            "versions": [
                {
                    "urn": "urn:cts:greekLit:tlg0012.tlg002.perseus-grc2:",
                    "nodeKind": "version",
                    "versionKind": "edition",
                    "firstPassageUrn": "urn:cts:greekLit:tlg0012.tlg002.perseus-grc2:1.1-1.10",
                    "citationScheme": ["book", "line"],
                    "title": [
                        {"lang": "eng", "value": "Odyssey, Loeb classical library"}
                    ],
                    "description": [
                        {
                            "lang": "eng",
                            "value": "Homer, creator; Murray, A. T. (Augustus Taber), 1866-1940, editor",
                        }
                    ],
                }
            ],
        },
    },
    "versions": {
        "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:": {
            "path": "/Users/jwegner/Data/development/repos/scaife-viewer/explorehomer-atlas/data/library/tlg0012/tlg001/tlg0012.tlg001.perseus-grc2.txt",
            "urn": "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:",
            "nodeKind": "version",
            "versionKind": "edition",
            "firstPassageUrn": "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.1-1.7",
            "citationScheme": ["book", "line"],
            "title": [{"lang": "eng", "value": "Iliad, Homeri Opera"}],
            "description": [
                {
                    "lang": "eng",
                    "value": "Homer, creator; Monro, D. B. (David Binning), 1836-1905, creator; Monro, D. B. (David Binning), 1836-1905, editor; Allen, Thomas W. (Thomas William), b. 1862, editor",
                }
            ],
        },
        "urn:cts:greekLit:tlg0012.tlg002.perseus-grc2:": {
            "path": "/Users/jwegner/Data/development/repos/scaife-viewer/explorehomer-atlas/data/library/tlg0012/tlg002/tlg0012.tlg002.perseus-grc2.txt",
            "urn": "urn:cts:greekLit:tlg0012.tlg002.perseus-grc2:",
            "nodeKind": "version",
            "versionKind": "edition",
            "firstPassageUrn": "urn:cts:greekLit:tlg0012.tlg002.perseus-grc2:1.1-1.10",
            "citationScheme": ["book", "line"],
            "title": [{"lang": "eng", "value": "Odyssey, Loeb classical library"}],
            "description": [
                {
                    "lang": "eng",
                    "value": "Homer, creator; Murray, A. T. (Augustus Taber), 1866-1940, editor",
                }
            ],
        },
    },
}
