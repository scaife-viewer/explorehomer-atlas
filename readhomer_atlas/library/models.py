from django.conf import settings
from django.db import models

# @@@ https://code.djangoproject.com/ticket/12990
from django_extensions.db.fields.json import JSONField
from treebeard.mp_tree import MP_Node


class Node(MP_Node):
    # @@@ used to pivot siblings; may be possible if we hook into path field
    idx = models.IntegerField(help_text="0-based index", blank=True, null=True)
    # @@@ if we expose kind, can access some GraphQL enumerations
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
    def position(self):
        return list(self.get_siblings()).index(self)

    @property
    def rank(self):
        # TODO: What should this be now?
        raise NotImplementedError()
