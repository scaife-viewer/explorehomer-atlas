import csv
import json
import os

from django.conf import settings

from .models import Book, Line, Version


LIBRARY_DATA_PATH = os.path.join(settings.PROJECT_ROOT, "data", "library")
LEMMA_CONTENT_DATA_PATH = os.path.join(
    LIBRARY_DATA_PATH, "annotations", "lemma-content"
)
LIBRARY_METADATA_PATH = os.path.join(LIBRARY_DATA_PATH, "metadata.json")


def _prepare_line_obj(version_obj, book_lookup, book_idx, line, line_idx):
    ref, tokens = line.strip().split(maxsplit=1)
    _, passage_ref = ref.split(".", maxsplit=1)
    book_ref, line_ref = passage_ref.split(".", maxsplit=1)

    book_obj = book_lookup.get(book_ref)
    if book_obj is None:
        book_obj, _ = Book.objects.get_or_create(
            version=version_obj, position=int(book_ref), idx=book_idx
        )
        book_lookup[book_ref] = book_obj
        book_idx += 1
    return Line(
        text_content=tokens,
        position=int(line_ref),
        idx=line_idx,
        book=book_obj,
        book_position=book_obj.position,
        version=version_obj,
    )


def _import_version(data):
    version_obj, _ = Version.objects.update_or_create(
        urn=data["urn"],
        defaults=dict(name=data["metadata"]["work_title"], metadata=data["metadata"]),
    )

    book_lookup = {}
    book_idx = 0
    lines_to_create = []

    full_content_path = os.path.join(LIBRARY_DATA_PATH, data["content_path"])
    with open(full_content_path, "r") as f:
        for line_idx, line in enumerate(f):
            line_obj = _prepare_line_obj(
                version_obj, book_lookup, book_idx, line, line_idx
            )
            lines_to_create.append(line_obj)
    created_count = len(Line.objects.bulk_create(lines_to_create))
    assert created_count == line_idx + 1


def import_versions(reset=False):
    if reset:
        # delete all previous Version instances
        Version.objects.all().delete()

    library_metadata = json.load(open(LIBRARY_METADATA_PATH))
    for version_data in library_metadata["versions"]:
        _import_version(version_data)
        _import_lemmas(version_data)


def _import_lemmas(version_data):
    version_obj = Version.objects.get(urn=version_data["urn"])

    lemma_content_path = os.path.join(
        LEMMA_CONTENT_DATA_PATH, version_data["lemma_content_path"]
    )
    if not os.path.exists(lemma_content_path):
        return

    lookup = {}
    with open(lemma_content_path, "r") as f:
        for row in csv.DictReader(f):
            lookup[row["text_part"]] = row["lemma_content"].strip()
    to_update = []
    for line in version_obj.lines.all():
        line.lemma_content = lookup.get(line.label, "")
        to_update.append(line)
    Line.objects.bulk_update(to_update, ["lemma_content"], batch_size=500)
