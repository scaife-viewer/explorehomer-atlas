import os
import csv
import hashlib
import time

from django.core.management.base import BaseCommand

from redis import StrictRedis

from lemma_content_atlas.library.models import Version


class Command(BaseCommand):
    """
    Dumps the lemma content from the KV store

    python manage.py dump_kv_store data/library/annotations/lemma-content
    """

    help = "Dumps the lemma content from the KV store"

    def add_arguments(self, parser):
        parser.add_argument("output_dir", help="Path to write kv store output")

    def dump_lemma_content(self, version, output_dir):
        start = time.time()
        text_parts = []
        client = StrictRedis()
        pipeline = client.pipeline()
        for line in version.lines.all():
            summer = hashlib.md5()
            summer.update(line.text_content.encode("utf-8"))
            sha = summer.hexdigest()
            pipeline.get(f"lemma_content_for_sha:{sha}")
            text_parts.append(line.label)

        path = os.path.join(output_dir, f'{version.urn.rsplit(":", maxsplit=1)[-1]}.csv')
        f = open(path, "w")
        writer = csv.writer(f)
        writer.writerow(["text_part", "lemma_content"])

        results = []
        for r in pipeline.execute():
            if not r:
                results.append("")
            else:
                results.append(r.decode("utf-8"))

        for text_part, lemma_content in zip(text_parts, results):
            writer.writerow([text_part, lemma_content])
        end = time.time()
        duration = end - start
        self.stdout.write(f"{version.urn} [duration={duration:.2f}]")
        f.close()

    def handle(self, *args, **options):
        output_dir = options["output_dir"]
        os.makedirs(output_dir, exist_ok=True)

        for version in Version.objects.all():
            self.dump_lemma_content(version, output_dir)
