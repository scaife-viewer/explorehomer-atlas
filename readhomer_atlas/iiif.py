from posixpath import join as urljoin
from urllib.parse import quote_plus, unquote


class IIIFResolver:
    BASE_URL = "https://image.library.jhu.edu/iiif/"
    # @@@ figure out what this actually is in IIIF spec terms
    CANVAS_BASE_URL = "https://rosetest.library.jhu.edu/rosademo/iiif3/"
    COLLETION_SUBDIR = "homer/VA"
    iruri_kwargs = {
        "region": "full",
        "size": "full",
        "rotation": "0",
        "quality": "default",
        "format": "jpg",
    }

    def __init__(self, urn):
        """
        IIIFResolver("urn:cite2:hmt:vaimg.2017a:VA012VN_0514")
        """
        self.urn = urn

    @property
    def munged_image_path(self):
        image_part = self.urn.rsplit(":", maxsplit=1).pop()
        return image_part.replace("_", "-")

    @property
    def iiif_image_id(self):
        path = urljoin(self.COLLETION_SUBDIR, self.munged_image_path)
        return quote_plus(path)

    @property
    def identifier(self):
        return urljoin(self.BASE_URL, self.iiif_image_id)

    @property
    def info_url(self):
        info_path = "image.json"
        return urljoin(self.identifier, info_path)

    def build_image_request_url(self, **kwargs):
        iruri_kwargs = {}
        iruri_kwargs.update(self.iruri_kwargs)
        iruri_kwargs.update(**kwargs)
        return urljoin(
            self.identifier,
            "{region}/{size}/{rotation}/{quality}.{format}".format(**iruri_kwargs),
        )

    @property
    def image_url(self):
        return self.build_image_request_url()

    @property
    def canvas_url(self):
        path = unquote(self.iiif_image_id)
        return urljoin(self.CANVAS_BASE_URL, path, "canvas")

    def get_region_by_pct(self, dimensions):
        percentages = ",".join(
            [
                f'{dimensions["x"]:.2f}',
                f'{dimensions["y"]:.2f}',
                f'{dimensions["w"]:.2f}',
                f'{dimensions["h"]:.2f}',
            ]
        )
        return f"pct:{percentages}"
