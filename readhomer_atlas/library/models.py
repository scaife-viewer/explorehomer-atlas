from django.db import models

# @@@ https://code.djangoproject.com/ticket/12990
from django_extensions.db.fields.json import JSONField


class Version(models.Model):
    """
    urn:cts:greekLit:tlg0012.tlg001.perseus-grc2
    """

    urn = models.CharField(max_length=255)
    name = models.CharField(blank=True, null=True, max_length=255)
    metadata = JSONField(default=dict, blank=True)
    """
    {
        "work_urn": "urn:cts:greekLit:tlg0012.tlg001",
        "work_title": "Iliad",
        "type": "edition"
    }
    """

    class Meta:
        ordering = ["urn"]

    def __str__(self):
        return self.name


class VersionAlignment(models.Model):
    name = models.CharField(blank=True, null=True, max_length=255)
    slug = models.SlugField()
    metadata = JSONField(default=dict, blank=True)

    version = models.ForeignKey(
        "library.Version", related_name="alignments", on_delete=models.CASCADE
    )

    def __str__(self):
        return self.name


class AlignmentChunk(models.Model):
    # denormed from start / end
    citation = models.CharField(max_length=13)
    items = JSONField(default=list, blank=True)
    metadata = JSONField(default=dict, blank=True)
    idx = models.IntegerField(help_text="0-based index")

    version = models.ForeignKey(
        "library.Version", related_name="alignment_chunks", on_delete=models.CASCADE
    )
    alignment = models.ForeignKey(
        "library.VersionAlignment",
        related_name="alignment_chunks",
        on_delete=models.CASCADE,
    )
    start = models.ForeignKey(
        "library.Line", related_name="+", on_delete=models.CASCADE
    )
    end = models.ForeignKey("library.Line", related_name="+", on_delete=models.CASCADE)
    # denormed from start/end
    contains = models.ManyToManyField("library.Line", related_name="alignment_chunks")

    class Meta:
        ordering = ["idx"]

    def __str__(self):
        return f"{self.version} || {self.alignment} [citation={self.citation}]"


class Book(models.Model):
    """
    urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1
    """

    position = models.IntegerField()
    idx = models.IntegerField(help_text="0-based index")

    version = models.ForeignKey(
        "library.Version", related_name="books", on_delete=models.CASCADE
    )

    class Meta:
        ordering = ["idx"]

    @property
    def label(self):
        return f"{self.position}"

    def __str__(self):
        return f"{self.version} [book={self.position}]"


class Line(models.Model):
    """
    urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.1
    """

    text_content = models.TextField()

    position = models.IntegerField()
    book_position = models.IntegerField()
    idx = models.IntegerField(help_text="0-based index")

    book = models.ForeignKey(
        "library.Book", related_name="lines", on_delete=models.CASCADE
    )
    version = models.ForeignKey(
        "library.Version", related_name="lines", on_delete=models.CASCADE
    )

    class Meta:
        ordering = ["idx"]

    @property
    def ref(self):
        return f"{self.book_position}.{self.position}"

    @property
    def label(self):
        return self.ref

    def __str__(self):
        return f"{self.version} [line_num={self.label}]"
