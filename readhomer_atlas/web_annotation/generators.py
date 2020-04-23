from django.db.models import Q
from django.shortcuts import Http404
from django.urls import reverse_lazy
from django.utils.functional import cached_property

from ..iiif import IIIFResolver
from ..library.models import ImageROI, Node
from .shortcuts import build_absolute_url
from .utils import preferred_folio_urn


def map_dimensions_to_integers(dimensions):
    """
    FragmentSelector requires percentages expressed as integers.

    https://www.w3.org/TR/media-frags/#naming-space
    """
    int_dimensions = {}
    for k, v in dimensions.items():
        int_dimensions[k] = round(v)
    return int_dimensions


class TranslationAlignmentGenerator:
    slug = "translation-alignment"

    def __init__(self, folio_urn, alignment):
        self.urn = folio_urn
        self.alignment = alignment
        self.idx = alignment["idx"]

    @cached_property
    def folio_image_urn(self):
        folio = Node.objects.get(urn=preferred_folio_urn(self.urn))
        return folio.image_annotations.first().urn

    @property
    def greek_lines(self):
        return self.alignment["items"][0]

    @property
    def english_lines(self):
        return self.alignment["items"][1]

    def as_text(self, lines):
        return "\n".join([f"{l[0]}) {l[1]}" for l in lines])

    def as_html(self, lines):
        # @@@ this could be rendered via Django if we need fancier HTML
        return "<ul>" + "".join([f"<li>{l[0]}) {l[1]}</li>" for l in lines]) + "</ul>"

    @property
    def alignment_urn(self):
        # @@@ what if we have multiple alignments covering a single line?
        # @@@ we can use the idx, but no too helpful downstream
        version_urn = "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:"
        return f'{version_urn}{self.alignment["citation"]}'

    def get_urn_coordinates(self, urns):
        # first convert urns to folio exmplar URNS
        predicate = Q()
        for urn in urns:
            _, ref = urn.rsplit(":", maxsplit=1)
            predicate.add(Q(urn__endswith=f".{ref}"), Q.OR)

        # retrieve folio exemplar URNs
        text_parts = Node.objects.filter(
            urn__startswith="urn:cts:greekLit:tlg0012.tlg001.msA-folios:"
        ).filter(predicate)

        # @@@ order of these ROIs is really important; do we ensure it?
        roi_qs = ImageROI.objects.filter(text_parts__in=text_parts)
        if not roi_qs:
            # @@@ we should handle this further up the chain;
            # this ensures we don't serve a 500 when we're missing
            # bounding box data
            raise Http404
        coordinates = []
        for roi_obj in roi_qs:
            if roi_obj.data["urn:cite2:hmt:va_dse.v1.surface:"] != self.urn:
                # @@@ validates that the URNs are found within the current folio
                # @@@ prefer we don't look at data to handle that
                continue
            coords = [float(part) for part in roi_obj.coordinates_value.split(",")]
            coordinates.append(coords)
        return coordinates

    def get_bounding_box_dimensions(self, coords):
        dimensions = {}
        y_coords = []
        for x, y, w, h in coords:
            dimensions["x"] = min(dimensions.get("x", 100.0), x * 100)
            dimensions["y"] = min(dimensions.get("y", 100.0), y * 100)
            dimensions["w"] = max(dimensions.get("w", 0.0), w * 100)
            y_coords.append(y * 100)

        dimensions["h"] = y_coords[-1] - y_coords[0] + h * 100
        return dimensions

    @cached_property
    def common_obj(self):
        cite_version_urn = "urn:cts:greekLit:tlg0012.tlg001.msA:"
        urns = []
        # @@@ this is a giant hack, would be better to resolve the citation ref
        for ref, _, _ in self.greek_lines:
            urns.append(f"{cite_version_urn}{ref}")
        urn_coordinates = self.get_urn_coordinates(urns)
        precise_bb_dimensions = self.get_bounding_box_dimensions(urn_coordinates)
        bb_dimensions = map_dimensions_to_integers(precise_bb_dimensions)

        dimensions_str = ",".join(
            [
                str(bb_dimensions["x"]),
                str(bb_dimensions["y"]),
                str(bb_dimensions["w"]),
                str(bb_dimensions["h"]),
            ]
        )
        fragment_selector_val = f"xywh=percent:{dimensions_str}"

        image_urn = self.folio_image_urn
        iiif_obj = IIIFResolver(image_urn)
        image_api_selector_region = iiif_obj.get_region_by_pct(bb_dimensions)

        return {
            "@context": "http://www.w3.org/ns/anno.jsonld",
            "type": "Annotation",
            "target": [
                self.alignment_urn,
                {
                    "type": "SpecificResource",
                    "source": {"id": f"{iiif_obj.canvas_url}", "type": "Canvas"},
                    "selector": {
                        "type": "FragmentSelector",
                        "region": fragment_selector_val,
                    },
                },
                {
                    "type": "SpecificResource",
                    "source": {"id": f"{iiif_obj.identifier}", "type": "Image"},
                    "selector": {
                        "type": "ImageApiSelector",
                        "region": image_api_selector_region,
                    },
                },
                iiif_obj.build_image_request_url(region=image_api_selector_region),
            ],
        }

    def get_textual_bodies(self, body_format):
        bodies = [
            {"type": "TextualBody", "language": "el"},
            {"type": "TextualBody", "language": "en"},
        ]
        if body_format == "text":
            for body, lines in zip(bodies, [self.greek_lines, self.english_lines]):
                body["format"] = "text/plain"
                body["value"] = self.as_text(lines)
        elif body_format == "html":
            for body, lines in zip(bodies, [self.greek_lines, self.english_lines]):
                body["format"] = "text/plain"
                body["value"] = self.as_html(lines)
        return bodies

    def get_absolute_url(self, body_format):
        url = reverse_lazy(
            "serve_web_annotation",
            kwargs={
                "urn": self.urn,
                "annotation_kind": self.slug,
                "idx": self.idx,
                "format": body_format,
            },
        )
        return build_absolute_url(url)

    def get_object_for_body_format(self, body_format):
        obj = {
            "body": self.get_textual_bodies(body_format),
            "id": self.get_absolute_url(body_format),
        }
        obj.update(self.common_obj)
        return obj

    @property
    def text_obj(self):
        return self.get_object_for_body_format("text")

    @property
    def html_obj(self):
        return self.get_object_for_body_format("html")


class NamedEntitiesGenerator:
    slug = "named-entities"

    def __init__(self, folio_urn, named_entity):
        self.urn = folio_urn
        self.named_entity = named_entity
        # @@@
        self.idx = named_entity["idx"]

    # @@@ factor this out
    @cached_property
    def folio_image_urn(self):
        folio = Node.objects.get(urn=preferred_folio_urn(self.urn))
        return folio.image_annotations.first().urn

    def get_absolute_url(self, body_format):
        url = reverse_lazy(
            "serve_web_annotation",
            kwargs={
                "urn": self.urn,
                "annotation_kind": self.slug,
                "idx": self.idx,
                "format": body_format,
            },
        )
        return build_absolute_url(url)

    @property
    def compound_obj(self):
        image_urn = self.folio_image_urn
        iiif_obj = IIIFResolver(image_urn)
        work_label = "Venetus A"
        return {
            "id": self.get_absolute_url("compound"),
            "@context": [
                "http://www.w3.org/ns/anno.jsonld",
                # @@@ do we need this?
                {
                    "prezi": "http://iiif.io/api/presentation/2#",
                    "Canvas": "prezi:Canvas",
                    "Manifest": "prezi:Manifest",
                },
            ],
            "type": "Annotation",
            "label": f'Named Entity data for {work_label} {iiif_obj.munged_image_path} text "{self.named_entity["token"].word_value}"',
            "creator": "https://scaife-viewer.org/",
            "body": [
                {
                    "purpose": "commenting",
                    "type": "TextualBody",
                    "value": f'{self.named_entity["named_entity_obj"].title}',
                    "format": "text/plain",
                },
                {
                    "purpose": "identifying",
                    "source": f'{self.named_entity["named_entity_obj"].url}',
                    "format": "text/html",
                },
            ],
            "target": [
                {
                    "type": "SpecificResource",
                    "partOf": [
                        {"id": iiif_obj.collection_manifest_url, "type": "Manifest"}
                    ],
                    "source": {"id": f"{iiif_obj.canvas_url}", "type": "Canvas"},
                },
                # @@@ URI / ASCII requirements and our subpaths
                f'{self.named_entity["token"].text_part.urn}@{self.named_entity["token"].subref_value}',
            ],
        }


class WebAnnotationCollectionGenerator:
    def __init__(self, generator_class, urn, objects, format):
        self.generator_class = generator_class
        self.objects = objects
        self.format = format
        self.urn = urn
        self.item_list = []

    def append_to_item_list(self, data):
        # strip @context key
        # @@@@
        data.pop("@context", None)
        self.item_list.append(data)

    @property
    def items(self):
        for obj in self.objects:
            wa = self.generator_class(self.urn, obj)
            if self.format == "html":
                self.append_to_item_list(wa.html_obj)
            elif self.format == "text":
                self.append_to_item_list(wa.text_obj)
            elif self.format == "compound":
                self.append_to_item_list(wa.compound_obj)
        return self.item_list


def get_generator_for_kind(annotation_kind):
    return {
        "translation-alignment": TranslationAlignmentGenerator,
        "named-entities": NamedEntitiesGenerator,
    }[annotation_kind]
