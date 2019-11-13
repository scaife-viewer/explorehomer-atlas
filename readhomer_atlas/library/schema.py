from django.db.models import Q, Min, Max

import django_filters
from graphene import ObjectType, String, relay
from graphene.types import generic
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField

from .models import Book, Line, Version


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


class LineFilterSet(django_filters.FilterSet):
    reference = django_filters.CharFilter(method="reference_filter")

    class Meta:
        model = Line
        fields = ["position", "book__position", "version__urn"]

    def reference_filter(self, queryset, name, value):
        try:
            start, end = value.split("-")
        except ValueError:
            start = end = value
        # @@@ further validation required
        try:
            start_book, start_line = start.split(".")
        except ValueError:
            # @@@ handle "1"
            return queryset.none()
        try:
            end_book, end_line = end.split(".")
        except ValueError:
            # @@@ handle "1.1-2"
            return queryset.none()

        subquery = queryset.filter(
            Q(book__position=start_book, position=start_line)
            | Q(book__position=end_book, position=end_line)
        ).aggregate(min=Min("idx"), max=Max("idx"))
        queryset = queryset.filter(idx__gte=subquery["min"], idx__lte=subquery["max"])
        # @@@ select related required for performant `label`
        return queryset.select_related("book")


class LineNode(DjangoObjectType):
    label = String()

    class Meta:
        model = Line
        interfaces = (relay.Node,)
        filterset_class = LineFilterSet


class Query(ObjectType):
    version = relay.Node.Field(VersionNode)
    versions = LimitedConnectionField(VersionNode)

    book = relay.Node.Field(BookNode)
    books = LimitedConnectionField(BookNode)

    line = relay.Node.Field(LineNode)
    lines = LimitedConnectionField(LineNode)
