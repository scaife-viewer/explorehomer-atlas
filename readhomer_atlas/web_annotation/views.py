from django.conf import settings
from django.core.paginator import EmptyPage, Paginator
from django.http import Http404, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.decorators.cache import cache_page

from ..library.models import ImageAnnotation, Node
from .generators import (
    WebAnnotationCollectionGenerator,
    get_generator_for_kind,
)
from .shims import AlignmentsShim, AudioAnnotationsShim, NamedEntitiesShim
from .shortcuts import build_absolute_url
from .utils import (
    as_zero_based,
    folio_exemplar_urn_to_site_urn,
    preferred_folio_urn,
)


PAGE_SIZE = 10


def get_folio_obj(urn):
    return get_object_or_404(Node, **{"urn": preferred_folio_urn(urn)})


@cache_page(settings.DEFAULT_HTTP_CACHE_DURATION)
def serve_wa(request, annotation_kind, urn, idx):
    # @@@ query alignments from Postgres
    obj = None
    if annotation_kind == "translation-alignment":
        object_list = AlignmentsShim(urn).get_object_list()
    elif annotation_kind == "named-entities":
        object_list = NamedEntitiesShim(urn).get_object_list()
    elif annotation_kind == "audio-annotations":
        object_list = AudioAnnotationsShim(urn).get_object_list()

    for obj_ in object_list:
        if obj_["idx"] == idx:
            obj = obj_
            break
    if not obj:
        raise Http404

    generator_class = get_generator_for_kind(annotation_kind)
    wa = generator_class(urn, obj)
    return JsonResponse(data=wa.obj)


@cache_page(settings.DEFAULT_HTTP_CACHE_DURATION)
def serve_web_annotation_collection(request, annotation_kind, urn):
    get_folio_obj(urn)

    if annotation_kind == "translation-alignment":
        # @@@ query alignments from Postgres
        object_list = AlignmentsShim(urn).get_object_list(fields=["idx"])
        label = f"Translation Alignments for {urn}"
    elif annotation_kind == "named-entities":
        object_list = NamedEntitiesShim(urn).get_object_list(fields=["idx"])
        label = f"Named Entities for {urn}"
    elif annotation_kind == "audio-annotations":
        object_list = AudioAnnotationsShim(urn).get_object_list(fields=["idx"])
        label = f"Audio Annotations for {urn}"
    paginator = Paginator(object_list, per_page=PAGE_SIZE)

    urls = {
        "id": reverse_lazy(
            "serve_web_annotation_collection", args=[urn, annotation_kind]
        ),
        "first": reverse_lazy(
            "serve_web_annotation_page",
            args=[urn, annotation_kind, as_zero_based(paginator.page_range[0])],
        ),
        "last": reverse_lazy(
            "serve_web_annotation_page",
            args=[urn, annotation_kind, as_zero_based(paginator.page_range[-1])],
        ),
    }
    data = {
        "@context": "http://www.w3.org/ns/anno.jsonld",
        "id": build_absolute_url(urls["id"]),
        "type": "AnnotationCollection",
        "label": label,
        "total": paginator.count,
        "first": build_absolute_url(urls["first"]),
        "last": build_absolute_url(urls["last"]),
    }
    return JsonResponse(data)


@cache_page(settings.DEFAULT_HTTP_CACHE_DURATION)
def serve_web_annotation_page(request, annotation_kind, urn, zero_page_number):
    get_folio_obj(urn)

    if annotation_kind == "translation-alignment":
        # @@@ query alignments from Postgres
        object_list = AlignmentsShim(urn).get_object_list()
    elif annotation_kind == "named-entities":
        object_list = NamedEntitiesShim(urn).get_object_list()
    elif annotation_kind == "audio-annotations":
        object_list = AudioAnnotationsShim(urn).get_object_list()

    page_number = zero_page_number + 1
    paginator = Paginator(object_list, per_page=PAGE_SIZE)
    try:
        page = paginator.page(page_number)
    except EmptyPage:
        raise Http404
    generator_class = get_generator_for_kind(annotation_kind)
    collection = WebAnnotationCollectionGenerator(
        generator_class, urn, page.object_list
    )
    urls = {
        "id": reverse_lazy(
            "serve_web_annotation_page",
            args=[urn, annotation_kind, as_zero_based(page_number)],
        ),
        "part_of": reverse_lazy(
            "serve_web_annotation_collection", args=[urn, annotation_kind]
        ),
    }
    data = {
        "@context": "http://www.w3.org/ns/anno.jsonld",
        "id": build_absolute_url(urls["id"]),
        "type": "AnnotationPage",
        "partOf": build_absolute_url(urls["part_of"]),
        "startIndex": as_zero_based(page.start_index()),
        "items": collection.items,
    }
    if page.has_previous():
        prev_url = reverse_lazy(
            "serve_web_annotation_page",
            args=[urn, annotation_kind, as_zero_based(page.previous_page_number())],
        )
        data["prev"] = build_absolute_url(prev_url)
    if page.has_next():
        next_url = reverse_lazy(
            "serve_web_annotation_page",
            args=[urn, annotation_kind, as_zero_based(page.next_page_number())],
        )
        data["next"] = build_absolute_url(next_url)
    return JsonResponse(data)


@cache_page(settings.DEFAULT_HTTP_CACHE_DURATION)
def discovery(request):
    canvas_id = request.GET.get("canvas_id")
    if not canvas_id:
        return HttpResponseBadRequest("canvas_id is required")

    image_annotation = get_object_or_404(ImageAnnotation, canvas_identifier=canvas_id)
    folio_exemplar_urn = image_annotation.text_parts.first().urn
    cite_urn = folio_exemplar_urn_to_site_urn(folio_exemplar_urn)
    collections = []
    # @@@ move metadata to shim classes
    # or otherwise encapsulate the queries required
    possible_collections = [
        {"annotation_kind": "translation-alignment", "shim_class": AlignmentsShim},
        {"annotation_kind": "named-entities", "shim_class": NamedEntitiesShim},
        {"annotation_kind": "audio-annotations", "shim_class": AudioAnnotationsShim},
    ]
    for possibility in possible_collections:
        shim_obj = possibility["shim_class"](cite_urn)
        if shim_obj.get_object_list(fields=["idx"]):
            collection_url = reverse_lazy(
                "serve_web_annotation_collection",
                kwargs={
                    "urn": cite_urn,
                    "annotation_kind": possibility["annotation_kind"],
                },
            )
            collections.append(build_absolute_url(collection_url))
    return JsonResponse({"collections": collections})
