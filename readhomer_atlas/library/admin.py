from django.contrib import admin

from .models import Version, Book, Line


@admin.register(Version)
class VersionAdmin(admin.ModelAdmin):
    list_display = ("id", "urn", "name", "metadata")
    search_fields = ("name",)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("id", "position", "idx", "version")
    list_filter = ("version",)


@admin.register(Line)
class LineAdmin(admin.ModelAdmin):
    list_display = ("id", "text_content", "position", "idx", "book", "version")
    list_filter = ("book", "version")
