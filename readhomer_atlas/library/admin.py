from django.contrib import admin

from .models import AlignmentChunk, Book, Line, Version, VersionAlignment


@admin.register(Version)
class VersionAdmin(admin.ModelAdmin):
    list_display = ("id", "urn", "name", "metadata")
    search_fields = ("name",)


@admin.register(VersionAlignment)
class VersionAlignmentAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug", "metadata", "version")
    list_filter = ("version",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ["name"]}


@admin.register(AlignmentChunk)
class AlignmentChunkAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "citation",
        "metadata",
        "idx",
        "version",
        "alignment",
        "start",
        "end",
    )
    list_filter = ("version", "alignment")
    raw_id_fields = ("start", "end")
    exclude = ("contains",)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("id", "position", "idx", "version")
    list_filter = ("version",)


@admin.register(Line)
class LineAdmin(admin.ModelAdmin):
    list_display = ("id", "text_content", "position", "idx", "book", "version")
    list_filter = ("book", "version")
    raw_id_fields = ("book", "version")
