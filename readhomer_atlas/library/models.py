from django.conf import settings
from django.db import models

# @@@ https://code.djangoproject.com/ticket/12990
from django_extensions.db.fields.json import JSONField
from treebeard.mp_tree import MP_Node


class Node(MP_Node):
    kind = models.CharField(max_length=255)
    urn = models.CharField(max_length=255, unique=True)
    ref = models.CharField(max_length=255, blank=True, null=True)
    text_content = models.TextField(blank=True, null=True)
    metadata = JSONField(default=dict, blank=True, null=True)

    alphabet = settings.NODE_ALPHABET

    def __str__(self):
        return f"{self.kind}: {self.urn}"

    @property
    def name(self):
        return self.metadata.get("work_title")

    @property
    def idx(self):
        qs = self.get_root().get_descendants().filter(depth=self.depth)
        return list(qs).index(self)

    @property
    def position(self):
        return list(self.get_siblings()).index(self)

    @property
    def rank(self):
        return self.depth - 1
