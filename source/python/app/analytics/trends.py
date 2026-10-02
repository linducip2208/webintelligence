from collections import Counter
import re
def emerging_topics(titles, top=10):
    words = []
    for t in titles:
        words += [x for x in re.findall(r"[a-z]{4,}", (t or "").lower())]
    stop = {"with","from","this","that","have","will","price","review","best"}
    return Counter(w for w in words if w not in stop).most_common(top)
