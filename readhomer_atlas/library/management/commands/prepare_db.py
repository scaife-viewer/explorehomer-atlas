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
        importers.versions.import_versions(reset=True)

        self.stdout.write("--[Loading text annotations]--")
        importers.text_annotations.import_text_annotations(reset=True)

        self.stdout.write("--[Loading metrical annotations]--")
        importers.metrical_annotations.import_metrical_annotations(reset=True)

        self.stdout.write("--[Loading image annotations]--")
        importers.image_annotations.import_image_annotations(reset=True)

        self.stdout.write("--[Loading audio annotations]--")
        importers.audio_annotations.import_audio_annotations(reset=True)

        self.stdout.write("--[Tokenizing versions/exemplars]--")
        tokenizers.tokenize_all_text_parts(reset=True)

        self.stdout.write("--[Loading token annotations]--")
        importers.token_annotations.apply_token_annotations()

        self.stdout.write("--[Loading named entity annotations]--")
        importers.named_entities.apply_named_entities(reset=True)

        self.stdout.write("--[Loading alignments]--")
        # @@@ don't push the old alignments at all
        # importers.alignments.import_alignments(reset=True)

        # @@@
        importers.alignments.process_cex(
            "data/annotations/text-alignments/raw/tlg0012.tlg001.word_alignment.cex"
        )

        importers.alignments.process_cex(
            "data/annotations/text-alignments/raw/tlg0012.tlg001.sentence_alignment.cex"
        )
