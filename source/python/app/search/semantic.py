"""Persistent semantic search: deterministic hashed embeddings + JSON index.
No external deps. Index survives restarts via DATA_DIR/vectors.json.
Embeddings are labeled as lexical-hash vectors (honest, not neural)."""
import hashlib
import json
import math
import os

DIM = 128


def embed(text: str, dim: int = DIM):
    v = [0.0] * dim
    for tok in __import__("re").findall(r"[a-z0-9]{3,}", (text or "").lower()):
        h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
        v[h % dim] += 1.0
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [round(x / n, 6) for x in v]


def _cos(a, b):
    return sum(x * y for x, y in zip(a, b))


class Index:
    def __init__(self, path=""):
        self.path = path
        self.docs = {}  # doc_id -> {"vec": [...], "text": "...", "ref": {}}
        if path and os.path.exists(path):
            try:
                self.docs = json.load(open(path, encoding="utf-8"))
            except Exception:
                self.docs = {}

    def add(self, doc_id, text, ref=None):
        self.docs[str(doc_id)] = {"vec": embed(text), "text": (text or "")[:500],
                                  "ref": ref or {}}
        self.save()

    def remove(self, doc_id):
        self.docs.pop(str(doc_id), None)
        self.save()

    def search(self, query, k=5):
        q = embed(query)
        ranked = sorted(self.docs.items(), key=lambda kv: -_cos(q, kv[1]["vec"]))
        return [{"id": did, "score": round(_cos(q, d["vec"]), 4),
                 "text": d["text"], "ref": d["ref"]} for did, d in ranked[:k]]

    def save(self):
        if not self.path:
            return
        tmp = self.path + ".tmp"
        try:
            os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
            json.dump(self.docs, open(tmp, "w", encoding="utf-8"))
            os.replace(tmp, self.path)
        except Exception:
            pass


def default_path():
    return os.path.join(os.getenv("DATA_DIR", "data"), "vectors.json")


_IDX = {"i": None}


def get_index():
    if _IDX["i"] is None:
        _IDX["i"] = Index(default_path())
    return _IDX["i"]
