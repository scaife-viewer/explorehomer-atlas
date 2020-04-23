import json
import re
from collections import defaultdict

from django.conf import settings
from django.core import serializers
from django.db import models

# @@@ https://code.djangoproject.com/ticket/12990
from django_extensions.db.fields.json import JSONField
from graphene_django.utils import camelize
from sortedm2m.fields import SortedManyToManyField
from treebeard.mp_tree import MP_Node

from readhomer_atlas import constants


class TextAlignment(models.Model):
    name = models.CharField(blank=True, null=True, max_length=255)
    slug = models.SlugField()
    metadata = JSONField(default=dict, blank=True)

    # @@@
    version = models.ForeignKey(
        "library.Node", related_name="text_alignments", on_delete=models.CASCADE
    )

    def __str__(self):
        return self.name


class TextAlignmentChunk(models.Model):
    # denormed from start / end
    citation = models.CharField(max_length=13)
    items = JSONField(default=list, blank=True)
    metadata = JSONField(default=dict, blank=True)
    idx = models.IntegerField(help_text="0-based index")

    # @@@
    version = models.ForeignKey(
        "library.Node", related_name="text_alignment_chunks", on_delete=models.CASCADE
    )
    alignment = models.ForeignKey(
        "library.TextAlignment",
        related_name="text_alignment_chunks",
        on_delete=models.CASCADE,
    )
    start = models.ForeignKey(
        "library.Node", related_name="+", on_delete=models.CASCADE
    )
    end = models.ForeignKey("library.Node", related_name="+", on_delete=models.CASCADE)

    class Meta:
        ordering = ["idx"]

    def __str__(self):
        return f"{self.version} || {self.alignment} [citation={self.citation}]"

    @property
    def contains(self):
        text_part_kind = self.start.kind
        return (
            self.version.get_descendants()
            .filter(kind=text_part_kind)
            .filter(idx__gte=self.start.idx)
            .filter(idx__lte=self.end.idx)
        )


TEXT_ANNOTATION_KIND_SCHOLIA = "scholia"
TEXT_ANNOTATION_KIND_CHOICES = ((TEXT_ANNOTATION_KIND_SCHOLIA, "Scholia"),)


class TextAnnotation(models.Model):
    kind = models.CharField(
        max_length=7,
        default=TEXT_ANNOTATION_KIND_SCHOLIA,
        choices=TEXT_ANNOTATION_KIND_CHOICES,
    )
    data = JSONField(default=dict, blank=True)
    idx = models.IntegerField(help_text="0-based index")

    text_parts = SortedManyToManyField("library.Node", related_name="text_annotations")

    urn = models.CharField(max_length=255, blank=True, null=True)

    def resolve_references(self):
        if "references" not in self.data:
            print(f'No references found [urn="{self.urn}"]')
            return
        desired_urns = set(self.data["references"])
        reference_objs = list(Node.objects.filter(urn__in=desired_urns))
        resolved_urns = set([r.urn for r in reference_objs])
        delta_urns = desired_urns.symmetric_difference(resolved_urns)

        if delta_urns:
            print(
                f'Could not resolve all references, probably due to bad data in the CEX file [urn="{self.urn}" unresolved_urns="{",".join(delta_urns)}"]'
            )
        self.text_parts.set(reference_objs)


IMAGE_ANNOTATION_KIND_CANVAS = "canvas"
IMAGE_ANNOTATION_KIND_CHOICES = ((IMAGE_ANNOTATION_KIND_CANVAS, "Canvas"),)


class ImageAnnotation(models.Model):
    kind = models.CharField(
        max_length=7,
        default=IMAGE_ANNOTATION_KIND_CANVAS,
        choices=IMAGE_ANNOTATION_KIND_CHOICES,
    )
    data = JSONField(default=dict, blank=True)
    # @@@ denormed from data
    image_identifier = models.CharField(max_length=255, blank=True, null=True)
    canvas_identifier = models.CharField(max_length=255, blank=True, null=True)
    idx = models.IntegerField(help_text="0-based index")

    text_parts = SortedManyToManyField("library.Node", related_name="image_annotations")

    urn = models.CharField(max_length=255, blank=True, null=True)


class ImageROI(models.Model):
    data = JSONField(default=dict, blank=True)

    # @@@ denormed from data; could go away when Django's SQLite backend has proper
    # JSON support
    image_identifier = models.CharField(max_length=255)
    # @@@ this could be structured
    coordinates_value = models.CharField(max_length=255)
    # @@@ idx
    image_annotation = models.ForeignKey(
        "library.ImageAnnotation", related_name="roi", on_delete=models.CASCADE
    )

    text_parts = SortedManyToManyField("library.Node", related_name="roi")
    text_annotations = SortedManyToManyField(
        "library.TextAnnotation", related_name="roi"
    )


class AudioAnnotation(models.Model):
    data = JSONField(default=dict, blank=True)
    asset_url = models.URLField(max_length=200)
    idx = models.IntegerField(help_text="0-based index")

    text_parts = SortedManyToManyField("library.Node", related_name="audio_annotations")

    urn = models.CharField(max_length=255, blank=True, null=True)

    def resolve_references(self):
        if "references" not in self.data:
            print(f'No references found [urn="{self.urn}"]')
            return
        desired_urns = set(self.data["references"])
        reference_objs = list(Node.objects.filter(urn__in=desired_urns))
        resolved_urns = set([r.urn for r in reference_objs])
        delta_urns = desired_urns.symmetric_difference(resolved_urns)

        if delta_urns:
            print(
                f'Could not resolve all references, probably due to bad data in the CEX file [urn="{self.urn}" unresolved_urns="{",".join(delta_urns)}"]'
            )
        self.text_parts.set(reference_objs)


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
        # @@@ compare with passage-based tokenization on
        # scaife-viewer/scaife-viewer.  See discussion on
        # https://github.com/scaife-viewer/scaife-viewer/issues/162
        #
        # For this implementation, we always calculate the index
        # within the text part, _not_ the passage. Also see
        # http://www.homermultitext.org/hmt-doc/cite/cts-subreferences.html
        idx = defaultdict(int)
        pieces = text_part_node.text_content.split()
        to_create = []
        for pos, piece in enumerate(pieces):
            # @@@ the word value will discard punctuation or
            # whitespace, which means we only support "true"
            # subrefs for word tokens
            w = cls.get_word_value(piece)
            wl = len(w)
            for wk in (w[i : j + 1] for i in range(wl) for j in range(i, wl)):
                idx[wk] += 1
            subref_idx = idx[w]
            subref_value = f"{w}[{subref_idx}]"

            to_create.append(
                cls(
                    text_part=text_part_node,
                    value=piece,
                    word_value=w,
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

    # @@@ we may also want structure these references using URNs
    tokens = models.ManyToManyField("library.Token", related_name="named_entities")

    def __str__(self):
        return f"{self.urn} :: {self.title }"
