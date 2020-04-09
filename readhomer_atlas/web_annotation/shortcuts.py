from django.conf import settings

from django.contrib.sites.models import Site


CURRENT_SITE = Site.objects.get_current()


def build_absolute_url(url):
    return "{scheme}://{host}{url}".format(
        scheme=settings.DEFAULT_HTTP_PROTOCOL, host=CURRENT_SITE.domain, url=url
    )
