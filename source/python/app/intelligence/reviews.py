from collections import Counter
from ..analytics.ml import sentiment
def analyze(reviews):
    sents = [sentiment(r.get("text","")) for r in reviews]
    return {"count": len(reviews),
            "avg_rating": round(sum(r.get("rating",0) for r in reviews)/len(reviews),2) if reviews else None,
            "sentiment": dict(Counter(sents))}
