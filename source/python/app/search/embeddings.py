import math
class EmbeddingProvider:
    def embed(self, texts): raise NotImplementedError
class NoopEmbedding(EmbeddingProvider):
    def embed(self, texts):
        return [[float(len(t) % 97), float(sum(map(ord, t[:32])) % 97)] for t in texts]
class VectorStore:
    def __init__(self): self.items = []
    def add(self, vec, ref): self.items.append((vec, ref))
    def query(self, vec, k=5):
        def cos(a, b):
            n = math.sqrt(sum(x*x for x in a)) * math.sqrt(sum(x*x for x in b))
            return sum(x*y for x, y in zip(a, b))/n if n else 0
        return sorted(self.items, key=lambda it: -cos(vec, it[0]))[:k]
