from django.db.models import Q

import django_filters
from graphene import Connection, Field, ObjectType, String, relay
from graphene.types import generic
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django.utils import camelize

# from .models import Node as TextPart
from .models import (
    AudioAnnotation,
    ImageAnnotation,
    MetricalAnnotation,
    NamedEntity,
    Node,
    TextAlignment,
    TextAlignmentChunk,
    TextAnnotation,
    Token,
)
from .passage import Passage, PassageSiblingMetadata
from .utils import (
    extract_version_urn_and_ref,
    filter_via_ref_predicate,
    get_textparts_from_passage_reference,
)


# @@@ alias Node because relay.Node is quite different
TextPart = Node


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


class PassageSiblingMetadataNode(ObjectType):
    # @@@ dry for resolving scalars
    all_siblings = generic.GenericScalar(name="all")
    selected = generic.GenericScalar()
    previous = generic.GenericScalar()
    next_siblings = generic.GenericScalar(name="next")

    def resolve_all_siblings(obj, info, **kwargs):
        return obj.all

    def resolve_selected(obj, info, **kwargs):
        return obj.selected

    def resolve_previous(obj, info, **kwargs):
        return obj.previous

    def resolve_next_siblings(obj, info, **kwargs):
        return obj.next


class PassageTextPartConnection(Connection):
    metadata = generic.GenericScalar()
    sibling_metadata = Field(PassageSiblingMetadataNode)

    class Meta:
        abstract = True

    @staticmethod
    def generate_passage_urn(version, object_list):
        first = object_list[0]
        last = object_list[-1]

        if first == last:
            return first.get("urn")
        line_refs = [tp.get("ref") for tp in [first, last]]
        passage_ref = "-".join(line_refs)
        return f"{version.urn}{passage_ref}"

    def get_ancestor_metadata(self, version, obj):
        # @@@ we need to stop it at the version boundary for backwards
        # compatability with SV
        data = []
        if obj and obj.get_parent() != version:
            ancestor_refparts = obj.ref.split(".")[:-1]
            for pos, part in enumerate(ancestor_refparts):
                ancestor_ref = ".".join(ancestor_refparts[: pos + 1])
                data.append(
                    {
                        # @@@ proper name for this is ref or position?
                        "ref": ancestor_ref,
                        "urn": f"{version.urn}{ancestor_ref}",
                    }
                )
        return data

    def get_adjacent_passages(self, version, previous_objects, next_objects):
        data = {}
        if previous_objects:
            data["previous"] = self.generate_passage_urn(version, previous_objects)

        if next_objects:
            data["next"] = self.generate_passage_urn(version, next_objects)
        return data

    def get_children_metadata(self, start_obj):
        data = []
        for tp in start_obj.get_children().values("ref", "urn"):
            lcp = tp["ref"].split(".").pop()
            data.append({"lcp": lcp, "urn": tp.get("urn")})
        return data

    def resolve_metadata(self, info, *args, **kwargs):
        data = {}
        # @@@ resolve metadata attrs individually
        passage = info.context.passage
        data.update(
            self.get_adjacent_passages(
                passage.version, passage.previous_objects, passage.next_objects
            )
        )
        data["human_reference"] = passage.human_readable_reference

        data["ancestors"] = self.get_ancestor_metadata(passage.version, passage.start)
        data["children"] = self.get_children_metadata(passage.start)
        return camelize(data)

    def resolve_sibling_metadata(self, info, *args, **kwargs):
        passage = info.context.passage
        return PassageSiblingMetadata(passage)


# @@@ consider refactoring with TextPartsReferenceFilterMixin
class TextPartFilterSet(django_filters.FilterSet):
    reference = django_filters.CharFilter(method="reference_filter")

    def reference_filter(self, queryset, name, value):
        version_urn, ref = extract_version_urn_and_ref(value)
        start, end = ref.split("-")
        refs = [start]
        if end:
            refs.append(end)
        predicate = Q(ref__in=refs)
        queryset = queryset.filter(
            # @@@ this reference filter doesn't work because of
            # depth assumptions
            urn__startswith=version_urn,
            depth=len(start.split(".")) + 1,
        )
        return filter_via_ref_predicate(queryset, predicate)

    class Meta:
        model = TextPart
        fields = {
            "urn": ["exact", "startswith"],
            "ref": ["exact", "startswith"],
            "depth": ["exact", "lt", "gt"],
            "rank": ["exact", "lt", "gt"],
            "kind": ["exact"],
            "idx": ["exact"],
        }


def initialize_passage(request, reference):
    # @@@ mimic how DataLoaders are using request == info.context
    request.passage = Passage(reference)


class TextPartsReferenceFilterMixin:
    def get_lowest_textparts_queryset(self, value):
        initialize_passage(self.request, value)
        version = self.request.passage.version
        return get_textparts_from_passage_reference(value, version=version)


class PassageTextPartFilterSet(TextPartsReferenceFilterMixin, django_filters.FilterSet):
    reference = django_filters.CharFilter(method="reference_filter")

    class Meta:
        model = TextPart
        fields = []

    def reference_filter(self, queryset, name, value):
        return self.get_lowest_textparts_queryset(value)


class AbstractTextPartNode(DjangoObjectType):
    label = String()
    name = String()
    metadata = generic.GenericScalar()

    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(cls, **meta_options):
        meta_options.update(
            {
                "model": TextPart,
                "interfaces": (relay.Node,),
                "filterset_class": TextPartFilterSet,
            }
        )
        super().__init_subclass_with_meta__(**meta_options)

    def resolve_metadata(obj, *args, **kwargs):
        return camelize(obj.metadata)


class VersionNode(AbstractTextPartNode):
    text_alignment_chunks = LimitedConnectionField(lambda: TextAlignmentChunkNode)

    @classmethod
    def get_queryset(cls, queryset, info):
        return queryset.filter(kind="version").order_by("urn")

    def resolve_metadata(obj, *args, **kwargs):
        metadata = obj.metadata
        work = obj.get_parent()
        text_group = work.get_parent()
        # @@@ backport lang map
        lang_map = {
            "eng": "English",
            "grc": "Greek",
        }
        metadata.update(
            {
                "work_label": work.label,
                "text_group_label": text_group.label,
                "lang": metadata["lang"],
                "human_lang": lang_map[metadata["lang"]],
            }
        )
        return camelize(metadata)


class TextPartNode(AbstractTextPartNode):
    pass


class PassageTextPartNode(DjangoObjectType):
    label = String()

    class Meta:
        model = TextPart
        interfaces = (relay.Node,)
        connection_class = PassageTextPartConnection
        filterset_class = PassageTextPartFilterSet


class TreeNode(ObjectType):
    tree = generic.GenericScalar()

    def resolve_tree(obj, info, **kwargs):
        return obj


class TextAlignmentNode(DjangoObjectType):
    metadata = generic.GenericScalar()

    class Meta:
        model = TextAlignment
        interfaces = (relay.Node,)
        filter_fields = ["name", "slug"]


class TextAlignmentChunkFilterSet(
    TextPartsReferenceFilterMixin, django_filters.FilterSet
):
    reference = django_filters.CharFilter(method="reference_filter")
    contains = django_filters.CharFilter(method="contains_reference_filter")

    class Meta:
        model = TextAlignmentChunk
        fields = [
            "start",
            "end",
            "version__urn",
            "idx",
        ]

    def reference_filter(self, queryset, name, value):
        textparts_queryset = self.get_lowest_textparts_queryset(value)
        return queryset.filter(
            Q(start__in=textparts_queryset) | Q(end__in=textparts_queryset)
        )

    def contains_reference_filter(self, queryset, name, value):
        textparts_queryset = self.get_lowest_textparts_queryset(value)
        start = textparts_queryset.first()
        end = textparts_queryset.last()
        version = self.request.passage.version
        return (
            queryset.filter(version=version)
            .filter(end__idx__gte=start.idx)
            .filter(start__idx__lte=end.idx)
        )


class TextAlignmentChunkNode(DjangoObjectType):
    items = generic.GenericScalar()

    class Meta:
        model = TextAlignmentChunk
        interfaces = (relay.Node,)
        filterset_class = TextAlignmentChunkFilterSet


class TextAnnotationFilterSet(TextPartsReferenceFilterMixin, django_filters.FilterSet):
    reference = django_filters.CharFilter(method="reference_filter")

    class Meta:
        model = TextAnnotation
        fields = ["urn"]

    def reference_filter(self, queryset, name, value):
        textparts_queryset = self.get_lowest_textparts_queryset(value)
        return queryset.filter(text_parts__in=textparts_queryset).distinct()


class TextAnnotationNode(DjangoObjectType):
    data = generic.GenericScalar()

    class Meta:
        model = TextAnnotation
        interfaces = (relay.Node,)
        filterset_class = TextAnnotationFilterSet


class MetricalAnnotationNode(DjangoObjectType):
    data = generic.GenericScalar()
    metrical_pattern = String()

    class Meta:
        model = MetricalAnnotation
        interfaces = (relay.Node,)
        filter_fields = ["urn"]


class ImageAnnotationFilterSet(TextPartsReferenceFilterMixin, django_filters.FilterSet):
    reference = django_filters.CharFilter(method="reference_filter")

    class Meta:
        model = ImageAnnotation
        fields = ["urn"]

    def reference_filter(self, queryset, name, value):
        # Reference filters work at the lowest text parts, but we've chosen to
        # apply the ImageAnnotation :: TextPart link at the folio level.

        # Since individual lines are at the roi level, we query there.
        textparts_queryset = self.get_lowest_textparts_queryset(value)
        return queryset.filter(roi__text_parts__in=textparts_queryset).distinct()


class ImageAnnotationNode(DjangoObjectType):
    text_parts = LimitedConnectionField(lambda: TextPartNode)
    data = generic.GenericScalar()

    class Meta:
        model = ImageAnnotation
        interfaces = (relay.Node,)
        filterset_class = ImageAnnotationFilterSet


class AudioAnnotationNode(DjangoObjectType):
    data = generic.GenericScalar()

    class Meta:
        model = AudioAnnotation
        interfaces = (relay.Node,)
        filter_fields = ["urn"]


class TokenFilterSet(django_filters.FilterSet):
    class Meta:
        model = Token
        fields = {"text_part__urn": ["exact", "startswith"]}


class TokenNode(DjangoObjectType):
    class Meta:
        model = Token
        interfaces = (relay.Node,)
        filterset_class = TokenFilterSet


class NamedEntityFilterSet(TextPartsReferenceFilterMixin, django_filters.FilterSet):
    reference = django_filters.CharFilter(method="reference_filter")

    class Meta:
        model = NamedEntity
        fields = ["urn", "kind"]

    def reference_filter(self, queryset, name, value):
        textparts_queryset = self.get_lowest_textparts_queryset(value)
        return queryset.filter(tokens__text_part__in=textparts_queryset).distinct()


class NamedEntityNode(DjangoObjectType):
    data = generic.GenericScalar()

    class Meta:
        model = NamedEntity
        interfaces = (relay.Node,)
        filterset_class = NamedEntityFilterSet


class Query(ObjectType):
    version = relay.Node.Field(VersionNode)
    versions = LimitedConnectionField(VersionNode)

    text_part = relay.Node.Field(TextPartNode)
    text_parts = LimitedConnectionField(TextPartNode)

    # No passage_text_part endpoint available here like the others because we
    # will only support querying by reference.
    passage_text_parts = LimitedConnectionField(PassageTextPartNode)

    text_alignment_chunk = relay.Node.Field(TextAlignmentChunkNode)
    text_alignment_chunks = LimitedConnectionField(TextAlignmentChunkNode)

    text_annotation = relay.Node.Field(TextAnnotationNode)
    text_annotations = LimitedConnectionField(TextAnnotationNode)

    metrical_annotation = relay.Node.Field(MetricalAnnotationNode)
    metrical_annotations = LimitedConnectionField(MetricalAnnotationNode)

    image_annotation = relay.Node.Field(ImageAnnotationNode)
    image_annotations = LimitedConnectionField(ImageAnnotationNode)

    audio_annotation = relay.Node.Field(AudioAnnotationNode)
    audio_annotations = LimitedConnectionField(AudioAnnotationNode)

    tree = Field(TreeNode, urn=String(required=True), up_to=String(required=False))

    token = relay.Node.Field(TokenNode)
    tokens = LimitedConnectionField(TokenNode)

    named_entity = relay.Node.Field(NamedEntityNode)
    named_entities = LimitedConnectionField(NamedEntityNode)

    def resolve_tree(obj, info, urn, **kwargs):
        return TextPart.dump_tree(
            root=TextPart.objects.get(urn=urn), up_to=kwargs.get("up_to")
        )
