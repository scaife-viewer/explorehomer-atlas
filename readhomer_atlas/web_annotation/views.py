from django.conf import settings
from django.core.paginator import EmptyPage, Paginator
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.decorators.cache import cache_page

from ..library.models import Node
from .generators import (
    WebAnnotationCollectionGenerator,
    get_generator_for_kind,
)
from .shims import AlignmentsShim, NamedEntitiesShim
from .shortcuts import build_absolute_url
from .utils import as_zero_based, preferred_folio_urn


PAGE_SIZE = 10


def get_folio_obj(urn):
    return get_object_or_404(Node, **{"urn": preferred_folio_urn(urn)})


@cache_page(settings.DEFAULT_HTTP_CACHE_DURATION)
def serve_wa(request, annotation_kind, urn, idx, format):
    # @@@ query alignments from Postgres
    obj = None
    if annotation_kind == "translation-alignment":
        object_list = AlignmentsShim(urn).get_object_list()
    elif annotation_kind == "named-entities":
        object_list = NamedEntitiesShim(urn).get_object_list()

    for obj_ in object_list:
        if obj_["idx"] == idx:
            obj = obj_
            break
    if not obj:
        raise Http404

    generator_class = get_generator_for_kind(annotation_kind)
    wa = generator_class(urn, obj)
    try:
        if format == "text":
            return JsonResponse(data=wa.text_obj)
        elif format == "html":
            return JsonResponse(data=wa.html_obj)
        elif format == "compound":
            return JsonResponse(data=wa.compound_obj)
    except AttributeError:
        raise Http404
    else:
        raise Http404


@cache_page(settings.DEFAULT_HTTP_CACHE_DURATION)
def serve_web_annotation_collection(request, annotation_kind, urn, format):
    get_folio_obj(urn)

    if annotation_kind == "translation-alignment":
        # @@@ query alignments from Postgres
        object_list = AlignmentsShim(urn).get_object_list(fields=["idx"])
        label = f"Translation Alignments for {urn}"
    elif annotation_kind == "named-entities":
        object_list = NamedEntitiesShim(urn).get_object_list(fields=["idx"])
        label = f"Named Entities for {urn}"
    paginator = Paginator(object_list, per_page=PAGE_SIZE)

    urls = {
        "id": reverse_lazy(
            "serve_web_annotation_collection", args=[urn, annotation_kind, format]
        ),
        "first": reverse_lazy(
            "serve_web_annotation_page",
            args=[urn, annotation_kind, format, as_zero_based(paginator.page_range[0])],
        ),
        "last": reverse_lazy(
            "serve_web_annotation_page",
            args=[
                urn,
                annotation_kind,
                format,
                as_zero_based(paginator.page_range[-1]),
            ],
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
def serve_web_annotation_page(request, annotation_kind, urn, format, zero_page_number):
    get_folio_obj(urn)

    if annotation_kind == "translation-alignment":
        # @@@ query alignments from Postgres
        object_list = AlignmentsShim(urn).get_object_list()
    elif annotation_kind == "named-entities":
        object_list = NamedEntitiesShim(urn).get_object_list()

    page_number = zero_page_number + 1
    paginator = Paginator(object_list, per_page=PAGE_SIZE)
    try:
        page = paginator.page(page_number)
    except EmptyPage:
        raise Http404
    generator_class = get_generator_for_kind(annotation_kind)
    collection = WebAnnotationCollectionGenerator(
        generator_class, urn, page.object_list, format
    )
    urls = {
        "id": reverse_lazy(
            "serve_web_annotation_page",
            args=[urn, annotation_kind, format, as_zero_based(page_number)],
        ),
        "part_of": reverse_lazy(
            "serve_web_annotation_collection", args=[urn, annotation_kind, format]
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
            args=[
                urn,
                annotation_kind,
                format,
                as_zero_based(page.previous_page_number()),
            ],
        )
        data["prev"] = build_absolute_url(prev_url)
    if page.has_next():
        next_url = reverse_lazy(
            "serve_web_annotation_page",
            args=[urn, annotation_kind, format, as_zero_based(page.next_page_number())],
        )
        data["next"] = build_absolute_url(next_url)
    return JsonResponse(data)
