from django.db.models import Max, Min, Q

import django_filters
from graphene import Connection, ObjectType, String, relay
from graphene.types import generic
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django.utils import camelize
from keyset_pagination.paginator import KeysetPaginator

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
        **resolver_kwargs,
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
            **resolver_kwargs,
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

    def _resolve_ref(self, value):
        book_position = None
        line_position = None
        try:
            book_position, line_position = value.split(".")
        except ValueError:
            book_position = value
        return book_position, line_position

    def reference_filter(self, queryset, name, value):
        """
        1
        1-2
        1.1-1.2
        1.1-7
        """
        predicate = Q()
        try:
            start, end = value.split("-")
        except ValueError:
            start = end = value

        start_book, start_line = self._resolve_ref(start)
        if start_book and start_line:
            condition = Q(book__position=start_book, position=start_line)
            predicate.add(condition, Q.OR)
        elif start_book:
            condition = Q(book__position=start_book, position=1)
            predicate.add(condition, Q.OR)
        else:
            return queryset.none()

        end_book, end_line = self._resolve_ref(end)
        if end_book and end_line:
            condition = Q(book__position=end_book, position=end_line)
            predicate.add(condition, Q.OR)
        elif end_book:
            condition = Q(book__position=end_book)
            predicate.add(condition, Q.OR)
        else:
            return queryset.none()
        subquery = queryset.filter(predicate).aggregate(min=Min("idx"), max=Max("idx"))
        queryset = queryset.filter(idx__gte=subquery["min"], idx__lte=subquery["max"])
        return queryset


class LineNode(DjangoObjectType):
    label = String()

    class Meta:
        model = Line
        interfaces = (relay.Node,)
        filterset_class = LineFilterSet


# @@@ we might return portions of this reference filter to LineFilterSet
class PassageLineFilterSet(django_filters.FilterSet):
    reference = django_filters.CharFilter(method="reference_filter")

    class Meta:
        model = Line
        fields = []

    def _resolve_ref(self, value):
        book_position = None
        line_position = None
        try:
            book_position, line_position = value.split(".")
        except ValueError:
            book_position = value
        # @@@ implement URN healing
        return book_position, line_position

    def reference_filter(self, queryset, name, value):
        """
        1
        1-2
        1.1-1.2
        @@@ review with jhrr as part of a larger URN validation library
        @@@ on the python side
        1.1-7
        """
        # @@@ self.request may not be the best place, but is accessible on the Connection as
        # info.context
        self.request.passage = dict(urn=value)

        # @@@ eventually, we'll need to ensure we're querying by the urn with a trailing `:`
        version_urn, ref = value.rsplit(":", maxsplit=1)
        try:
            self.request.passage["version"] = Version.objects.get(urn=version_urn)
        except Version.DoesNotExist:
            raise Exception(f"{version_urn} was not found.")
        else:
            queryset = queryset.filter(version__urn=version_urn)

        predicate = Q()
        try:
            start, end = ref.split("-")
        except ValueError:
            start = end = ref

        start_book, start_line = self._resolve_ref(start)
        if start_book and start_line:
            condition = Q(book__position=start_book, position=start_line)
            predicate.add(condition, Q.OR)
        elif start_book:
            condition = Q(book__position=start_book, position=1)
            predicate.add(condition, Q.OR)
        else:
            return queryset.none()

        end_book, end_line = self._resolve_ref(end)
        if end_book and end_line:
            condition = Q(book__position=end_book, position=end_line)
            predicate.add(condition, Q.OR)
        elif end_book:
            condition = Q(book__position=end_book)
            predicate.add(condition, Q.OR)
        else:
            return queryset.none()
        subquery = queryset.filter(predicate).aggregate(min=Min("idx"), max=Max("idx"))
        queryset = queryset.filter(idx__gte=subquery["min"], idx__lte=subquery["max"])

        self.request.passage["lines_qs"] = queryset
        return queryset


class PassageLineConnection(Connection):
    metadata = generic.GenericScalar()

    class Meta:
        abstract = True

    @staticmethod
    def generate_passage_urn(version, object_list):
        first = object_list[0]
        last = object_list[-1]
        if first == last:
            return first.urn
        passage_ref = "-".join([first.ref, last.ref])
        return f"{version.urn}:{passage_ref}"

    @staticmethod
    def valid_previous_next_objs(previous_objects, next_objects):
        """
        Prevent paginator from wrapping around to the beginning of the queryset
        """
        if (
            next_objects
            and previous_objects
            and next_objects[0].idx < previous_objects[0].idx
        ):
            return previous_objects, []
        return previous_objects, next_objects

    def get_previous_next_objs(self, queryset, per_page, obj):
        paginator = KeysetPaginator(queryset.order_by("idx"), per_page)
        page = paginator.get_page(f"[false, {obj.idx - 1}]")
        previous_objects = paginator.get_page(page.previous_page_number()).object_list
        next_objects = paginator.get_page(page.next_page_number()).object_list
        return self.valid_previous_next_objs(previous_objects, next_objects)

    def get_sibling_metadata(self, version, all_queryset, filtered_queryset):
        previous_objects, next_objects = self.get_previous_next_objs(
            all_queryset, filtered_queryset.count(), filtered_queryset.first()
        )
        data = {}
        if previous_objects:
            data["previous"] = self.generate_passage_urn(version, previous_objects)

        if next_objects:
            data["next"] = self.generate_passage_urn(version, next_objects)
        return {"siblings": data}

    def resolve_metadata(self, info, *args, **kwargs):
        passage_dict = info.context.passage
        if not passage_dict:
            return

        urn = passage_dict["urn"]
        version = passage_dict["version"]
        lines_queryset = passage_dict["lines_qs"]

        ref = urn.rsplit(":", maxsplit=1)[1]
        try:
            book_level_ref = int(ref.rsplit("-")[0])
        except ValueError:
            book_level_ref = None

        data = {}
        if book_level_ref:
            books_queryset = version.books.filter(
                pk__in=lines_queryset.values_list("book")
            )
            data.update(
                self.get_sibling_metadata(version, version.books.all(), books_queryset)
            )
        else:
            data.update(
                self.get_sibling_metadata(version, version.lines.all(), lines_queryset)
            )
        return camelize(data)


class PassageLineNode(DjangoObjectType):
    label = String()

    class Meta:
        model = Line
        interfaces = (relay.Node,)
        filterset_class = PassageLineFilterSet
        connection_class = PassageLineConnection


class Query(ObjectType):
    version = relay.Node.Field(VersionNode)
    versions = LimitedConnectionField(VersionNode)

    book = relay.Node.Field(BookNode)
    books = LimitedConnectionField(BookNode)

    line = relay.Node.Field(LineNode)
    lines = LimitedConnectionField(LineNode)

    # no passage line available because we will only support querying by reference
    passage_lines = LimitedConnectionField(PassageLineNode)
