from django.urls import path

from .views import (
    serve_wa,
    serve_web_annotation_collection,
    serve_web_annotation_page,
)


urlpatterns = [
    path(
        "<urn>/translation-alignment/collection/<format>/",
        serve_web_annotation_collection,
        name="serve_web_annotation_collection",
    ),
    path(
        "<urn>/translation-alignment/collection/<format>/<int:zero_page_number>/",
        serve_web_annotation_page,
        name="serve_web_annotation_page",
    ),
    path(
        "<urn>/translation-alignment/<int:idx>/<format>/",
        serve_wa,
        name="serve_web_annotation",
    ),
]
