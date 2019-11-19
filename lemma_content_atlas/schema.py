import graphene

import lemma_content_atlas.library.schema


class Query(lemma_content_atlas.library.schema.Query, graphene.ObjectType):
    # This class will inherit from multiple Queries
    # as we begin to add more apps to our project
    pass


schema = graphene.Schema(query=Query)
