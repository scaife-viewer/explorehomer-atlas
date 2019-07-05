from graphene import ObjectType, String, relay
from graphene.types import generic
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField

from .models import AlignmentChunk, Book, Line, Version, VersionAlignment


class LimitedConnectionField(DjangoFilterConnectionField):
    """
    Ensures that queries without `first` or `last` return up to
    `max_limit` results.
    """

    @classmethod
    def connection_resolver(
        cls,
        resolver,
        connection,
        default_manager,
        max_limit,
        enforce_first_or_last,
        filterset_class,
        filtering_args,
        root,
        info,
        **resolver_kwargs
    ):
        first = resolver_kwargs.get("first")
        last = resolver_kwargs.get("last")
        if not first and not last:
            resolver_kwargs["first"] = max_limit

        return super(LimitedConnectionField, cls).connection_resolver(
            resolver,
            connection,
            default_manager,
            max_limit,
            enforce_first_or_last,
            filterset_class,
            filtering_args,
            root,
            info,
            **resolver_kwargs
        )


class VersionNode(DjangoObjectType):
    metadata = generic.GenericScalar()
    books = LimitedConnectionField(lambda: BookNode)
    lines = LimitedConnectionField(lambda: LineNode)

    class Meta:
        model = Version
        interfaces = (relay.Node,)
        filter_fields = ["name", "urn"]


class BookNode(DjangoObjectType):
    label = String()
    lines = LimitedConnectionField(lambda: LineNode)

    class Meta:
        model = Book
        interfaces = (relay.Node,)
        filter_fields = ["position", "version__urn"]


class LineNode(DjangoObjectType):
    label = String()
    alignment_chunks = LimitedConnectionField(lambda: AlignmentChunkNode)

    class Meta:
        model = Line
        interfaces = (relay.Node,)
        filter_fields = ["position", "book__position", "version__urn"]


class VersionAlignmentNode(DjangoObjectType):
    metadata = generic.GenericScalar()

    class Meta:
        model = VersionAlignment
        interfaces = (relay.Node,)
        filter_fields = ["name", "slug"]


class AlignmentChunkNode(DjangoObjectType):
    items = generic.GenericScalar()

    class Meta:
        model = AlignmentChunk
        interfaces = (relay.Node,)
        filter_fields = [
            "start",
            "end",
            "start__book__position",
            "start__position",
            "end__book__position",
            "end__position",
            "version__urn",
        ]


class Query(ObjectType):
    version = relay.Node.Field(VersionNode)
    versions = LimitedConnectionField(VersionNode)

    book = relay.Node.Field(BookNode)
    books = LimitedConnectionField(BookNode)

    line = relay.Node.Field(LineNode)
    lines = LimitedConnectionField(LineNode)

    alignment_chunk = relay.Node.Field(AlignmentChunkNode)
    alignment_chunks = LimitedConnectionField(AlignmentChunkNode)
