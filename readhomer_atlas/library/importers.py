import json
import os
import re
import sys
from collections import defaultdict

from django.conf import settings

from .models import Node
from .urn import URN


LIBRARY_DATA_PATH = os.path.join(settings.PROJECT_ROOT, "data", "library")


class LibraryDataResolver:
    def __init__(self, data_dir_path):
        self.text_groups = {}
        self.works = {}
        self.versions = {}

        self.resolved = self.resolve_data_dir_path(data_dir_path)

    def populate_versions(self, dirpath, data):
        for version in data:
            version_part = version["urn"].rsplit(":", maxsplit=2)[1]
            version_path = os.path.join(dirpath, f"{version_part}.txt")

            if not os.path.exists(version_path):
                raise FileNotFoundError(version_path)

            self.versions[version["urn"]] = {"path": version_path, **version}

    def resolve_data_dir_path(self, data_dir_path):
        for dirpath, dirnames, filenames in os.walk(data_dir_path):
            if "metadata.json" not in filenames:
                continue

            metadata = json.load(open(os.path.join(dirpath, "metadata.json")))
            assert metadata["node_kind"] in ["textgroup", "work"]

            if metadata["node_kind"] == "textgroup":
                self.text_groups[metadata["urn"]] = metadata
            elif metadata["node_kind"] == "work":
                self.works[metadata["urn"]] = metadata
                self.populate_versions(dirpath, metadata["versions"])

        return self.text_groups, self.works, self.versions


class Library:
    def __init__(self, text_groups, works, versions):
        self.text_groups = text_groups
        self.works = works
        self.versions = versions


class CTSImporter:
    """
    urn:cts:CTSNAMESPACE:WORK:PASSAGE
    https://cite-architecture.github.io/ctsurn_spec
    """

    CTS_URN_SCHEME = ["nid", "namespace", "textgroup", "work", "version"]
    CTS_URN_SCHEME_EXEMPLAR = CTS_URN_SCHEME + ["exemplar"]

    def get_version_metadata(self):
        return {
            # @@@ how much of the `metadata.json` do we
            # "pass through" via GraphQL vs
            # apply to particular node kinds in the heirarchy
            "citation_scheme": self.citation_scheme,
            "work_title": self.name,
            "first_passage_urn": self.version_data["first_passage_urn"],
        }

    def __init__(self, library, version_data, nodes=dict()):
        self.library = library
        self.version_data = version_data
        self.nodes = nodes
        self.urn = self.version_data["urn"].strip()
        self.work_urn = URN(self.urn).up_to(URN.WORK)
        self.name = get_first_value_for_language(
            self.library.works[self.work_urn]["title"], "eng"
        )
        self.citation_scheme = self.version_data["citation_scheme"]
        self.metadata = self.get_version_metadata()
        self.idx_lookup = defaultdict(int)

    def get_node_idx(self, kind):
        idx = self.idx_lookup[kind]
        self.idx_lookup[kind] += 1
        return idx

    # @@@ refactor with URN class
    def urn_has_exemplar(self, node_urn):
        return len(node_urn.rsplit(":")[-2].split(".")) == 4

    # @@@ refactor with URN class
    def get_urn_scheme(self, node_urn):
        if self.urn_has_exemplar(node_urn):
            return [*self.CTS_URN_SCHEME_EXEMPLAR, *self.citation_scheme]
        return [*self.CTS_URN_SCHEME, *self.citation_scheme]

    def destructure_node(self, node_urn, tokens):
        # @@@ refactor with URN class
        split = ["urn:cts", ":", *re.split(r"([:|.])", node_urn)[4:]]
        nodes = [node for idx, node in enumerate(split) if idx % 2 == 0]
        delimiters = [delimiter for idx, delimiter in enumerate(split) if idx % 2 == 1]
        zipped = zip(self.get_urn_scheme(node_urn), nodes)

        node_data = []
        for idx, (kind, node) in enumerate(zipped):
            parts = nodes[: idx + 1]
            joins = [*delimiters[:idx], ""]
            urn = "".join(item for pair in zip(parts, joins) for item in pair)
            if kind in self.CTS_URN_SCHEME_EXEMPLAR:
                urn = f"{urn}:"
            data = {"kind": kind, "urn": urn}

            if kind == "version":
                data.update({"metadata": self.metadata})

            if kind in self.citation_scheme:
                ref_index = self.citation_scheme.index(kind)
                ref = ".".join(nodes[-len(self.citation_scheme) :][: ref_index + 1])
                data.update({"ref": ref, "rank": ref_index + 1})
                if kind == self.citation_scheme[-1]:
                    data.update({"text_content": tokens})

            node_data.append(data)

        return node_data

    def generate_branch(self, line):
        ref, tokens = line.strip().split(maxsplit=1)
        _, passage = ref.split(".", maxsplit=1)
        node_data = self.destructure_node(f"{self.urn}{passage}", tokens)
        for idx, data in enumerate(node_data):
            node = self.nodes.get(data["urn"])
            if node is None:
                data.update({"idx": self.get_node_idx(data["kind"])})
                if idx == 0:
                    node = Node.add_root(**data)
                else:
                    parent = self.nodes.get(node_data[idx - 1]["urn"])
                    node = parent.add_child(**data)
                self.nodes[data["urn"]] = node

    def apply(self):
        full_content_path = self.library.versions[self.urn]["path"]
        with open(full_content_path, "r") as f:
            for line in f:
                self.generate_branch(line)
        created_count = Node.objects.get(
            urn=self.version_data["urn"]
        ).get_descendant_count()
        print(f"{self.name}: {created_count + 1} nodes.", file=sys.stderr)


def resolve_library():
    text_groups, works, versions = LibraryDataResolver(LIBRARY_DATA_PATH).resolved
    return Library(text_groups, works, versions)


def get_first_value_for_language(values, lang):
    return next(iter(filter(lambda x: x["lang"] == lang, values)), None).get("value")


def import_versions():
    Node.objects.filter(kind="nid").delete()

    library = resolve_library()

    nodes = {}
    for _, version_data in library.versions.items():
        CTSImporter(library, version_data, nodes).apply()
    print(f"{Node.objects.count()} total nodes on the tree.", file=sys.stderr)
