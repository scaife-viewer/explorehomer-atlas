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


class FolioImageAnnotationMixin:
    @cached_property
    def folio_image_urn(self):
        folio = Node.objects.get(urn=preferred_folio_urn(self.urn))
        return folio.image_annotations.first().urn

    def get_absolute_url(self):
        url = reverse_lazy(
            "serve_web_annotation",
            kwargs={"urn": self.urn, "annotation_kind": self.slug, "idx": self.idx},
        )
        return build_absolute_url(url)

    @cached_property
    def iiif_obj(self):
        image_urn = self.folio_image_urn
        return IIIFResolver(image_urn)


class FolioBoundingBoxAnnotationMixin(FolioImageAnnotationMixin):
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

    def get_bounding_boxes_for_urns(self, urns):
        urn_coordinates = self.get_urn_coordinates(urns)
        precise_bb_dimensions = self.get_bounding_box_dimensions(urn_coordinates)
        return map_dimensions_to_integers(precise_bb_dimensions)

    # @@@
    def get_references_for_bounding_box(self):
        raise NotImplementedError("Subclasses must implement this method")

    @cached_property
    def bb_dimensions(self):
        references = self.get_references_for_bounding_box()
        return self.get_bounding_boxes_for_urns(references)

    @cached_property
    def fragment_selector_value(self):
        dimensions_str = ",".join(
            [
                str(self.bb_dimensions["x"]),
                str(self.bb_dimensions["y"]),
                str(self.bb_dimensions["w"]),
                str(self.bb_dimensions["h"]),
            ]
        )
        return f"xywh=percent:{dimensions_str}"

    @cached_property
    def image_api_selector_region(self):
        return self.iiif_obj.get_region_by_pct(self.bb_dimensions)

    @cached_property
    def canvas_target_obj(self):
        return {
            "type": "SpecificResource",
            "source": {"id": f"{self.iiif_obj.canvas_url}", "type": "Canvas"},
            "selector": {
                "type": "FragmentSelector",
                "region": self.fragment_selector_value,
            },
        }

    @cached_property
    def image_target_obj(self):
        return {
            "type": "SpecificResource",
            "source": {"id": f"{self.iiif_obj.identifier}", "type": "Image"},
            "selector": {
                "type": "ImageApiSelector",
                "region": self.image_api_selector_region,
            },
        }

    @cached_property
    def image_request_url(self):
        return self.iiif_obj.build_image_request_url(
            region=self.image_api_selector_region
        )


class TranslationAlignmentGenerator(FolioBoundingBoxAnnotationMixin):
    slug = "translation-alignment"

    def __init__(self, folio_urn, alignment):
        self.urn = folio_urn
        self.alignment = alignment
        self.idx = alignment["idx"]

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

    def get_references_for_bounding_box(self):
        cite_version_urn = "urn:cts:greekLit:tlg0012.tlg001.msA:"
        references = []
        # @@@ this is a giant hack, would be better to resolve the citation ref
        for ref, _ in self.greek_lines:
            references.append(f"{cite_version_urn}{ref}")
        return references

    def get_textual_bodies(self):
        bodies = [
            {"type": "TextualBody", "language": "grc"},
            {"type": "TextualBody", "language": "en"},
        ]
        for body, lines in zip(bodies, [self.greek_lines, self.english_lines]):
            body["format"] = "text/plain"
            body["value"] = self.as_html(lines)
        return bodies

    @cached_property
    def obj(self):
        return {
            "@context": "http://www.w3.org/ns/anno.jsonld",
            "type": "Annotation",
            "id": self.get_absolute_url(),
            "target": [
                self.alignment_urn,
                self.canvas_target_obj,
                self.image_target_obj,
                self.image_request_url,
            ],
            "body": self.get_textual_bodies(),
        }


class NamedEntitiesGenerator(FolioImageAnnotationMixin):
    slug = "named-entities"

    def __init__(self, folio_urn, named_entity):
        self.urn = folio_urn
        self.named_entity = named_entity
        # @@@
        self.idx = named_entity["idx"]

    @property
    def obj(self):
        work_label = "Venetus A"
        return {
            "id": self.get_absolute_url(),
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
            "label": f'Named Entity data for {work_label} {self.iiif_obj.munged_image_path} text "{self.named_entity["token"].word_value}"',
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
                        {
                            "id": self.iiif_obj.collection_manifest_url,
                            "type": "Manifest",
                        }
                    ],
                    "source": {"id": f"{self.iiif_obj.canvas_url}", "type": "Canvas"},
                },
                # @@@ URI / ASCII requirements and our subpaths
                f'{self.named_entity["token"].text_part.urn}@{self.named_entity["token"].subref_value}',
            ],
        }


class AudioAnnotationsGenerator(FolioBoundingBoxAnnotationMixin):
    slug = "audio-annotations"

    def __init__(self, folio_urn, audio_annotation):
        self.urn = folio_urn
        self.audio_annotation = audio_annotation["obj"]
        # @@@
        self.idx = audio_annotation["idx"]

    @cached_property
    def annotation_references(self):
        return list(self.audio_annotation.text_parts.values_list("urn", flat=True))

    def get_references_for_bounding_box(self):
        return self.annotation_references

    @property
    def body(self):
        return {
            "id": self.audio_annotation.asset_url,
            # @@@ retrieve this from individual annotations
            "rights": "https://creativecommons.org/licenses/by/4.0/",
            "creator": {
                "id": "http://hypotactic.com/",
                "name": "David Chamberlain",
                "type": "Person",
            },
            "format": "audio/mp4",
            "language": "grc",
        }

    @property
    def obj(self):
        return {
            "id": self.get_absolute_url(),
            "@context": "http://www.w3.org/ns/anno.jsonld",
            "type": "Annotation",
            "target": [
                self.annotation_references[0],
                self.canvas_target_obj,
                self.image_target_obj,
                self.image_request_url,
            ],
            "body": self.body,
        }


class WebAnnotationCollectionGenerator:
    def __init__(self, generator_class, urn, objects):
        self.generator_class = generator_class
        self.objects = objects
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
            self.append_to_item_list(wa.obj)
        return self.item_list


def get_generator_for_kind(annotation_kind):
    return {
        "translation-alignment": TranslationAlignmentGenerator,
        "named-entities": NamedEntitiesGenerator,
        "audio-annotations": AudioAnnotationsGenerator,
    }[annotation_kind]
