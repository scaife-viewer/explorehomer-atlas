import logging

from django.utils.text import slugify

from tqdm import tqdm

from ..models import TOC, NamedEntity


logger = logging.getLogger(__name__)


def create_root_toc():
    root_toc = TOC.objects.create(
        urn="urn:cite2:exploreHomer:toc.v1.root", title="Named Entities"
    )
    entries = [
        ("Catalog of Ships", "urn:cts:greekLit:tlg0012.tlg001.perseus-eng4:2.480"),
        (
            "Persons in Chapter 1",
            "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.1-1.25",
        ),
    ]
    for title, uri in entries:
        root_toc.entries.create(toc=root_toc, title=title, uri=uri)


def create_entity_entry_title(entity):
    return f"{entity.entity}"


def create_entry_title(line):
    # strip out hemis from text content
    return line.sanitized_text_content


def create_entity_toc(parent, entity, lines):
    urn = f"{parent.urn}-{slugify(entity.tag)}"
    title = create_entity_entry_title(entity)
    parent.entries.create(toc=parent, title=title, uri=urn)
    entity_toc = TOC.objects.create(title=title, urn=urn)
    for line in lines:
        entity_toc.entries.create(
            toc=entity_toc, title=create_entry_title(line), uri=line.idx_urn
        )


def create_toc_for_category(category, en, ar):
    urn = f"urn:cite:dsp-dar:toc.{en.lower()}"
    category_toc = TOC.objects.create(urn=urn, title=ar)
    entities = (
        NamedEntity.objects.filter(category=category)
        .exclude(lines=None)
        .order_by("tag")
    )
    logger.info(f'Creating "{en}"')
    for entity in tqdm(entities):
        lines = entity.lines.select_related("work", "section").order_by("work", "idx")
        create_entity_toc(category_toc, entity, lines)


def create_tocs(reset=False):
    if reset:
        TOC.objects.all().delete()

    create_root_toc()
    # @@@ create additional tocs here
    # for category, en_title, ar_title in [
    #     (constants.NE_CATEGORY_EVENT, "Events", EVENTS_AR),
    #     (constants.NE_CATEGORY_PERSON, "Persons", PERSONS_AR),
    # ]:
    #     create_toc_for_category(category, en_title, ar_title)

    msg = f"Created TOCs [count={TOC.objects.count()}]"
    logger.info(msg)
