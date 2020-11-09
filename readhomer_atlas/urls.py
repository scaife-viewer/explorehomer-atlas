from django.urls import include, path

from django.contrib import admin

from .tocs.views import serve_toc, tocs_index


urlpatterns = [
    path("admin/", admin.site.urls),
    path("tocs/<filename>", serve_toc, name="serve_toc"),
    path("tocs/", tocs_index, name="tocs_index"),
    path("wa/", include("readhomer_atlas.web_annotation.urls")),
    path("", include("scaife_viewer.atlas.urls")),
]
