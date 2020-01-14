import json
import os
import re
import sys
from collections import defaultdict

from django.conf import settings

from .models import Node


LIBRARY_DATA_PATH = os.path.join(settings.PROJECT_ROOT, "data", "library")
LIBRARY_METADATA_PATH = os.path.join(LIBRARY_DATA_PATH, "metadata.json")


class CTSImporter:
    """
    urn:cts:CTSNAMESPACE:WORK:PASSAGE
    https://cite-architecture.github.io/ctsurn_spec
    """

    CTS_URN_SCHEME = ["nid", "namespace", "textgroup", "work", "version"]

    def __init__(self, version_data, nodes=dict()):
        self.version_data = version_data
        self.nodes = nodes
        self.urn = self.version_data["urn"].strip()
        self.metadata = self.version_data["metadata"]
        self.citation_scheme = self.metadata["citation_scheme"]
        self.name = self.metadata["work_title"]
        self.idx_lookup = defaultdict(int)

    def get_node_idx(self, kind):
        idx = self.idx_lookup[kind]
        self.idx_lookup[kind] += 1
        return idx

    def urn_has_exemplar(self, node_urn):
        return len(node_urn.rsplit(":")[-2].split(".")) == 4

    def get_urn_scheme(self, node_urn):
        if self.urn_has_exemplar(node_urn):
            return [*self.CTS_URN_SCHEME, "exemplar", *self.citation_scheme]
        return [*self.CTS_URN_SCHEME, *self.citation_scheme]

    def destructure_node(self, node_urn, tokens):
        split = ["urn:cts", ":", *re.split(r"([:|.])", node_urn)[4:]]
        nodes = [node for idx, node in enumerate(split) if idx % 2 == 0]
        delimiters = [delimiter for idx, delimiter in enumerate(split) if idx % 2 == 1]
        zipped = zip(self.get_urn_scheme(node_urn), nodes)

        node_data = []
        for idx, (kind, node) in enumerate(zipped):
            parts = nodes[: idx + 1]
            joins = [*delimiters[:idx], ""]
            urn = "".join(item for pair in zip(parts, joins) for item in pair)
            if kind in self.CTS_URN_SCHEME:
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
        full_content_path = os.path.join(
            LIBRARY_DATA_PATH, self.version_data["content_path"]
        )
        with open(full_content_path, "r") as f:
            for line in f:
                self.generate_branch(line)

        created_count = Node.objects.get(
            urn=self.version_data["urn"]
        ).get_descendant_count()
        print(f"{self.name}: {created_count + 1} nodes.", file=sys.stderr)


def import_versions():
    Node.objects.filter(kind="nid").delete()
    library_metadata = json.load(open(LIBRARY_METADATA_PATH))
    nodes = {}
    for version_data in library_metadata["versions"]:
        CTSImporter(version_data, nodes).apply()
    print(f"{Node.objects.count()} total nodes on the tree.", file=sys.stderr)
