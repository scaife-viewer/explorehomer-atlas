from django.db.models import Max, Min, Q

import django_filters
from graphene import Connection, ObjectType, String, relay
from graphene.types import generic
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django.utils import camelize

from .models import Book, Line, Version
from .utils import get_chunker


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

    def resolve_metadata(obj, *args, **kwargs):
        return camelize(obj.metadata)


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
        end_book, end_line = self._resolve_ref(end)

        if start_book and start_line:
            condition = Q(book__position=start_book, position=start_line)
            predicate.add(condition, Q.OR)
        elif start_book:
            condition = Q(book__position=start_book, position=1)
            predicate.add(condition, Q.OR)
        else:
            raise ValueError(f"Invalid reference: {value}")

        if start_book and start_line and end_book and end_line:
            condition = Q(book__position=end_book, position=end_line)
            predicate.add(condition, Q.OR)
        elif start_book and not start_line and end_book and not end_line:
            condition = Q(book__position=end_book)
            predicate.add(condition, Q.OR)
        else:
            raise ValueError(f"Invalid reference: {value}")

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

        dirty_version_urn, ref = value.rsplit(":", maxsplit=1)
        # restore the trailing :
        version_urn = f"{dirty_version_urn}:"
        try:
            self.request.passage["version"] = Version.objects.get(urn=version_urn)
        except Version.DoesNotExist:
            raise Exception(f"{version_urn} was not found.")
        else:
            queryset = queryset.filter(version__urn=version_urn)

        predicate = Q()
        if not ref:
            # @@@ get all the lines in the work; do we want to support this
            # or should we just return the first line?
            start = queryset.first().ref
            end = queryset.last().ref
        else:
            try:
                start, end = ref.split("-")
            except ValueError:
                start = end = ref

        start_book, start_line = self._resolve_ref(start)
        end_book, end_line = self._resolve_ref(end)

        if start_book and start_line:
            condition = Q(book__position=start_book, position=start_line)
            predicate.add(condition, Q.OR)
        elif start_book:
            condition = Q(book__position=start_book, position=1)
            predicate.add(condition, Q.OR)
        else:
            raise ValueError(f"Invalid reference: {value}")

        if start_book and start_line and end_book and end_line:
            condition = Q(book__position=end_book, position=end_line)
            predicate.add(condition, Q.OR)
        elif start_book and not start_line and end_book and not end_line:
            condition = Q(book__position=end_book)
            predicate.add(condition, Q.OR)
        else:
            raise ValueError(f"Invalid reference: {value}")

        subquery = queryset.filter(predicate).aggregate(min=Min("idx"), max=Max("idx"))
        queryset = queryset.filter(idx__gte=subquery["min"], idx__lte=subquery["max"])

        self.request.passage["lines_qs"] = queryset
        self.request.passage["start_idx"] = subquery["min"]
        self.request.passage["chunk_length"] = subquery["max"] - subquery["min"] + 1

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
            return first.get("urn")
        line_refs = [line.get("ref") for line in [first, last]]
        passage_ref = "-".join(line_refs)
        return f"{version.urn}{passage_ref}"

    def get_ancestor_metadata(self, obj):
        data = []
        if obj:
            data.append(
                {
                    # @@@ proper name for this is ref or position?
                    "ref": obj.ref,
                    "urn": obj.book.urn,
                }
            )
        return data

    def get_sibling_metadata(self, version, all_queryset, start_idx, count):
        data = {}

        chunker = get_chunker(
            all_queryset, start_idx, count, queryset_values=["idx", "urn", "ref"]
        )
        previous_objects, next_objects = chunker.get_prev_next_boundaries()

        if previous_objects:
            data["previous"] = self.generate_passage_urn(version, previous_objects)

        if next_objects:
            data["next"] = self.generate_passage_urn(version, next_objects)
        return data

    def get_children_metadata(self, lines_queryset):
        data = []
        for line in lines_queryset.values("position", "urn"):
            data.append(
                {
                    # @@@ proper name is lsb or position
                    "lsb": str(line.get("position")),
                    "urn": line.get("urn"),
                }
            )
        return data

    def resolve_metadata(self, info, *args, **kwargs):
        # @@@ resolve metadata.siblings|ancestors|children individually
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
            # @@@ is it worth another query to detect
            # if we should do this as a list or using
            # SQL queries?
            # Might be something we can pre-calculate
            # within version metadata
            books_queryset = list(
                version.books.filter(
                    pk__in=lines_queryset.values_list("book")
                ).values_list("idx", flat=True)
            )
            start_idx = books_queryset[0]
            chunk_length = len(books_queryset)
            data["siblings"] = self.get_sibling_metadata(
                version, version.books.all(), start_idx, chunk_length
            )
            data["children"] = self.get_children_metadata(lines_queryset)
        else:
            start_idx = passage_dict["start_idx"]
            chunk_length = passage_dict["chunk_length"]
            data["siblings"] = self.get_sibling_metadata(
                version, version.lines.all(), start_idx, chunk_length
            )
            data["ancestors"] = self.get_ancestor_metadata(lines_queryset.first())
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
