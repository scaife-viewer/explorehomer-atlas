import time
import hashlib

from django.core.management.base import BaseCommand
from redis import StrictRedis

from lemma_content_atlas.library.models import Line


class Command(BaseCommand):
    """
    Seeds the lemma content to the KV store
    """

    help = "Seeds the lemma content to the KV store"

    def handle(self, *args, **options):
        start = time.time()
        client = StrictRedis()
        for line in Line.objects.all().select_related("version"):
            urn = f"{line.version.urn}:{line.label}"

            # generate sha for text content
            summer = hashlib.md5()
            summer.update(line.text_content.encode("utf-8"))
            sha = summer.hexdigest()

            pipe = client.pipeline()
            pipe.set(urn, sha)
            pipe.set(f"lemma_content_for_sha:{sha}", line.lemma_content)
            pipe.set(f"urn_for_sha:{sha}", urn)
            pipe.execute()
        end = time.time()
        duration = end - start
        self.stdout.write(str(duration))
