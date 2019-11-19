from django.core.management.base import BaseCommand

from lemma_content_atlas.library import importers


class Command(BaseCommand):
    """
    Prepares the database
    """

    help = "Prepares the database"

    def handle(self, *args, **options):
        self.stdout.write("--[Loading versions]--")
        importers.import_versions()
