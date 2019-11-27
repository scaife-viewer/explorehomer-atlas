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
    def ref(self):
        return f"{self.position}"

    @property
    def urn(self):
        return f"{self.version.urn}{self.ref}"

    @property
    def label(self):
        return self.label

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
    def urn(self):
        return f"{self.version.urn}{self.ref}"

    @property
    def label(self):
        return self.ref

    def __str__(self):
        return f"{self.version} [line_num={self.label}]"
