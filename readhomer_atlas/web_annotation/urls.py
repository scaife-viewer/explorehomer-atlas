from django.urls import path

from .views import (
    serve_wa,
    serve_web_annotation_collection,
    serve_web_annotation_page,
)


urlpatterns = [
    # @@@ make format optional
    path(
        "<urn>/<slug:annotation_kind>/collection/<format>/",
        serve_web_annotation_collection,
        name="serve_web_annotation_collection",
    ),
    path(
        "<urn>/<slug:annotation_kind>/collection/<format>/<int:zero_page_number>/",
        serve_web_annotation_page,
        name="serve_web_annotation_page",
    ),
    path(
        "<urn>/<slug:annotation_kind>/<int:idx>/<format>/",
        serve_wa,
        name="serve_web_annotation",
    ),
]
