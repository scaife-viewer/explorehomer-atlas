import os

from django.conf import settings
from django.http import FileResponse, Http404
from django.urls import reverse
from django.views.generic import TemplateView


CEX_DATA_PATH = os.path.join(
    settings.PROJECT_ROOT, "data", "annotations", "text-alignments", "raw"
)


class DucatApp(TemplateView):
    template_name = "ducat_wrapper/ducat.html"

    def get_context_data(self, **kwargs):
        return {
            "default_library_url": reverse(
                "serve_cex", args=["tlg0012.tlg001.word_alignment.cex"]
            )
        }


def serve_cex(request, filename):
    path = os.path.join(CEX_DATA_PATH, filename)
    if not os.path.exists(path):
        raise Http404
    return FileResponse(open(path, "rb"))
