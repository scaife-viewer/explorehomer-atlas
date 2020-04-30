from django.urls import path

from .views import (
    discovery,
    serve_wa,
    serve_web_annotation_collection,
    serve_web_annotation_page,
)


urlpatterns = [
    path(
        "<urn>/<slug:annotation_kind>/collection/",
        serve_web_annotation_collection,
        name="serve_web_annotation_collection",
    ),
    path(
        "<urn>/<slug:annotation_kind>/collection/<int:zero_page_number>/",
        serve_web_annotation_page,
        name="serve_web_annotation_page",
    ),
    path(
        "<urn>/<slug:annotation_kind>/<int:idx>/",
        serve_wa,
        name="serve_web_annotation",
    ),
    path("discovery/", discovery, name="web_annotation_discovery",),
]
