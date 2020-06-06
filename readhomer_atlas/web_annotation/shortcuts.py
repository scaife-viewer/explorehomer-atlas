from django.conf import settings

from django.contrib.sites.models import Site


def build_absolute_url(url):
    # get_current should cache:
    # https://docs.djangoproject.com/en/2.2/ref/contrib/sites/#caching-the-current-site-object
    current_site = Site.objects.get_current()
    return "{scheme}://{host}{url}".format(
        scheme=settings.DEFAULT_HTTP_PROTOCOL, host=current_site.domain, url=url
    )
