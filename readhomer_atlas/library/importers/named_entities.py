import csv

from ..models import NamedEntity, Node


def apply_named_entities(reset=True):
    if reset:
        NamedEntity.objects.all().delete()

    named_entites_path = "data/annotations/named-entities/raw/named_entities.csv"
    lookup = {}
    with open(named_entites_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            named_entity, _ = NamedEntity.objects.get_or_create(
                urn=row["urn"],
                defaults={
                    "title": row["label"],
                    "description": row["description"],
                    "url": row["link"],
                },
            )
            lookup[named_entity.urn] = named_entity

    iliad_path = "data/annotations/named-entities/raw/tlg0012.tlg001.perseus-grc2.csv"
    with open(iliad_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            named_entity = lookup[row["named_entity_urn"]]
            text_part = Node.objects.get(urn=row["ref"])
            position = int(row["token_position"])
            tokens = text_part.tokens.filter(position__in=[position])
            named_entity.tokens.add(*tokens)
