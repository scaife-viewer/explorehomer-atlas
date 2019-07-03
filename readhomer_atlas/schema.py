import graphene

import readhomer_atlas.library.schema


class Query(readhomer_atlas.library.schema.Query, graphene.ObjectType):
    # This class will inherit from multiple Queries
    # as we begin to add more apps to our project
    pass


schema = graphene.Schema(query=Query)
