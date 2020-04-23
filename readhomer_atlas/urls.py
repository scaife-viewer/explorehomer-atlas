from django.urls import include, path
from django.views.decorators.csrf import csrf_exempt

from django.contrib import admin

from graphene_django.views import GraphQLView

from .ducat_wrapper.views import DucatApp, serve_cex
from .tocs.views import serve_toc, tocs_index


urlpatterns = [
    path("admin/", admin.site.urls),
    path("graphql/", csrf_exempt(GraphQLView.as_view(graphiql=True))),
    path("tocs/<filename>", serve_toc, name="serve_toc"),
    path("tocs/", tocs_index, name="tocs_index"),
    path("wa/", include("readhomer_atlas.web_annotation.urls")),
    path("ducat/<filename>", serve_cex, name="serve_cex"),
    path("ducat/", DucatApp.as_view(), name="ducat"),
]
