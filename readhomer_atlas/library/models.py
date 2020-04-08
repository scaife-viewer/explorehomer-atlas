import json
import re
from collections import Counter

from django.conf import settings
from django.core import serializers
from django.db import models

# @@@ https://code.djangoproject.com/ticket/12990
from django_extensions.db.fields.json import JSONField
from graphene_django.utils import camelize
from treebeard.mp_tree import MP_Node

from readhomer_atlas import constants


class Node(MP_Node):
    # @@@ used to pivot siblings; may be possible if we hook into path field
    idx = models.IntegerField(help_text="0-based index", blank=True, null=True)
    # @@@ if we expose kind, can access some GraphQL enumerations
    kind = models.CharField(max_length=255)
    urn = models.CharField(max_length=255, unique=True)
    ref = models.CharField(max_length=255, blank=True, null=True)
    rank = models.IntegerField(blank=True, null=True)
    text_content = models.TextField(blank=True, null=True)
    metadata = JSONField(default=dict, blank=True, null=True)

    alphabet = settings.NODE_ALPHABET

    def __str__(self):
        return f"{self.kind}: {self.urn}"

    @property
    def name(self):
        return self.metadata.get("work_title")

    @classmethod
    def dump_tree(cls, root=None, up_to=None, to_camel=True):
        """Dump a tree or subtree for serialization rendering all
        fieldnames as camelCase by default.

        Extension of django-treebeard.treebeard.mp_tree `dump_bulk` for
        finer-grained control over the initial queryset and resulting value.
        """
        if up_to and up_to not in constants.CTS_URN_NODES:
            raise ValueError(f"Invalid CTS node identifier for: {up_to}")

        qs = cls._get_serializable_model().get_tree(parent=root)
        if up_to:
            depth = constants.CTS_URN_DEPTHS[up_to]
            qs = qs.exclude(depth__gt=depth)

        tree, index = [], {}
        for pyobj in serializers.serialize("python", qs):
            fields = pyobj["fields"]
            path = fields["path"]
            depth = int(len(path) / cls.steplen)
            del fields["depth"]
            del fields["path"]
            del fields["numchild"]

            metadata = json.loads(fields["metadata"])
            if to_camel:
                fields = camelize(fields)
                metadata = camelize(metadata)
            fields.update({"metadata": metadata})

            newobj = {"data": fields}

            if (not root and depth == 1) or (root and len(path) == len(root.path)):
                tree.append(newobj)
            else:
                parentpath = cls._get_basepath(path, depth - 1)
                parentobj = index[parentpath]
                if "children" not in parentobj:
                    parentobj["children"] = []
                parentobj["children"].append(newobj)
            index[path] = newobj
        return tree


class Token(models.Model):
    text_part = models.ForeignKey(
        "Node", related_name="tokens", on_delete=models.CASCADE
    )

    value = models.CharField(max_length=255)

    # @@@ consider JSON or EAV to store / filter attrs
    word_value = models.CharField(max_length=255, blank=True, null=True)
    subref_value = models.CharField(max_length=255, blank=True, null=True)
    uuid = models.CharField(max_length=255, blank=True, null=True)
    lemma = models.CharField(max_length=255, blank=True, null=True)
    gloss = models.CharField(max_length=255, blank=True, null=True)
    part_of_speech = models.CharField(max_length=255, blank=True, null=True)
    tag = models.CharField(max_length=255, blank=True, null=True)
    case = models.CharField(max_length=255, blank=True, null=True)
    mood = models.CharField(max_length=255, blank=True, null=True)
    named_entity = models.CharField(max_length=255, blank=True, null=True)

    position = models.IntegerField()
    idx = models.IntegerField(help_text="0-based index")

    @staticmethod
    def get_word_value(value):
        return re.sub(r"[^\w]", "", value)

    @classmethod
    def tokenize(cls, text_part_node, counters):
        pieces = text_part_node.text_content.split()
        to_create = []
        # @@@ compare with scaife-viewer/scaife-viewer
        # see discussion on https://github.com/scaife-viewer/scaife-viewer/issues/162
        subref_counter = Counter()
        for pos, piece in enumerate(pieces):
            word_value = cls.get_word_value(piece)

            subref_counter[word_value] += 1
            subref_value = f"{word_value}[{subref_counter[word_value]}]"

            to_create.append(
                cls(
                    text_part=text_part_node,
                    value=piece,
                    word_value=word_value,
                    position=pos + 1,
                    # @@@ not a true uuid
                    uuid=f"t{text_part_node.ref}_{pos}",
                    idx=counters["token_idx"],
                    subref_value=subref_value,
                )
            )
            counters["token_idx"] += 1
        return to_create

    def __str__(self):
        return f"{self.text_part.urn} :: {self.value}"


class NamedEntity(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    kind = models.CharField(max_length=6, choices=constants.NAMED_ENTITY_KINDS)
    url = models.URLField(max_length=200)

    idx = models.IntegerField(help_text="0-based index", blank=True, null=True)
    urn = models.CharField(max_length=255, unique=True)

    # @@@ we may also want to this over to URNs
    tokens = models.ManyToManyField("library.Token", related_name="named_entities")
