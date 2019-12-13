import json
import os
from collections import defaultdict

from django.conf import settings

from .models import Node


LIBRARY_DATA_PATH = os.path.join(settings.PROJECT_ROOT, "data", "library")
LIBRARY_METADATA_PATH = os.path.join(LIBRARY_DATA_PATH, "metadata.json")


def _destructure_ref(reference):
    """
    NODE_HIERARCHY = ('A', 'B', 'C', 'D', 'E',)
    assert _destructure_ref('1.2.3.a.5') == [
        ('A', '1'),
        ('B', '1.2'),
        ('C', '1.2.3'),
        ('D', '1.2.3.a'),
        ('E', '1.2.3.a.5')
    ]
    """
    components = reference.split(".")
    return [
        (kind, ".".join(components[: idx + 1]))
        for idx, kind in enumerate(settings.NODE_HIERARCHY)
    ]


def _get_node_idx(kind, idx_lookup):
    idx = idx_lookup[kind]
    idx_lookup[kind] += 1
    return idx


def _generate_branch(line, nodes, root_node, idx_lookup):
    ref, tokens = line.strip().split(maxsplit=1)
    _, textpart_ref = ref.split(".", maxsplit=1)

    refs = _destructure_ref(textpart_ref)
    for idx, key in enumerate(refs):
        parent = root_node if idx == 0 else nodes.get(refs[idx - 1])
        node = nodes.get(key)
        if node is None:
            kind, ref = key
            data = {
                "kind": kind,
                "urn": f"{root_node.urn}{ref}",
                "ref": ref,
                "idx": _get_node_idx(kind, idx_lookup),
            }
            if key == refs[-1]:
                data.update({"text_content": tokens})
            node = parent.add_child(**data)
            nodes[key] = node


def _import_version(data):
    root_node = Node.add_root(
        kind="Version", urn=data["urn"], metadata=data["metadata"]
    )

    nodes = {}
    idx_counters = defaultdict(int)
    full_content_path = os.path.join(LIBRARY_DATA_PATH, data["content_path"])
    with open(full_content_path, "r") as f:
        for line in f:
            _generate_branch(line, nodes, root_node, idx_counters)

    created_count = root_node.get_descendant_count()
    print(f"{root_node.name}: created {created_count + 1} nodes")


def import_versions():
    Node.objects.filter(kind="Version").delete()

    library_metadata = json.load(open(LIBRARY_METADATA_PATH))
    for version_data in library_metadata["versions"]:
        _import_version(version_data)
