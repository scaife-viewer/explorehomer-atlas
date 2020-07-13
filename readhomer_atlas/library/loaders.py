from collections import defaultdict
from promise import Promise
from promise.dataloader import DataLoader as BaseLoader

from .models import Node, NamedEntity, Token


# @@@ h/t to Saleor
class DataLoader(BaseLoader):
    context_key = None
    context = None

    def __new__(cls, context):
        key = cls.context_key
        if key is None:
            raise TypeError("Data loader %r does not define a context key" % (cls,))
        if not hasattr(context, "dataloaders"):
            context.dataloaders = {}
        if key not in context.dataloaders:
            context.dataloaders[key] = super().__new__(cls, context)
        loader = context.dataloaders[key]
        assert isinstance(loader, cls)
        return loader

    def __init__(self, context):
        if self.context != context:
            self.context = context
            self.user = context.user
            super().__init__()

    def batch_load_fn(self, keys):
        results = self.batch_load(keys)
        if not isinstance(results, Promise):
            return Promise.resolve(results)
        return results


class NamedEntityLoader(DataLoader):
    context_key = "entity_loader"

    def batch_load(self, keys):
        tokens = Token.objects.filter(pk__in=keys).prefetch_related("named_entities")
        token_entities_map = defaultdict(list)
        for token in tokens:
            entities = []
            for entitiy in token.named_entities.all():
                entities.append(entitiy)
            token_entities_map[token.id] = entities
        return [token_entities_map.get(token_id, []) for token_id in keys]


class TokenLoader(DataLoader):
    context_key = "token_loader"

    def batch_load(self, keys):
        lines = Node.objects.filter(pk__in=keys).prefetch_related("tokens")
        line_token_map = defaultdict(list)
        for line in lines:
            tokens = []
            for token in line.tokens.all():
                tokens.append(token)
            line_token_map[line.id] = tokens
        return [line_token_map.get(line_id, []) for line_id in keys]
