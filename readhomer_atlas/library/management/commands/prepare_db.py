import os

from django.core.management import call_command
from django.core.management.base import BaseCommand

from readhomer_atlas.library import importers, tokenizers


class Command(BaseCommand):
    """
    Prepares the database
    """

    help = "Prepares the database"

    def handle(self, *args, **options):
        if os.path.exists("db.sqlite3"):
            os.remove("db.sqlite3")
            self.stdout.write("--[Removed existing database]--")

        self.stdout.write("--[Creating database]--")
        call_command("migrate")

        self.stdout.write("--[Loading versions]--")
        importers.versions.import_versions()

        self.stdout.write("--[Loading alignments]--")
        importers.alignments.import_alignments(reset=True)

        self.stdout.write("--[Loading text annotations]--")
        importers.text_annotations.import_text_annotations(reset=True)

        self.stdout.write("--[Tokenizing versions/exemplars]--")
        tokenizers.tokenize_all_text_parts(reset=True)

        self.stdout.write("--[Loading named entity annotations]--")
        importers.named_entities.apply_named_entities(reset=True)
