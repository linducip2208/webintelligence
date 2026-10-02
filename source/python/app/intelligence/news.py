def summarize_article(title, body):
    body = (body or "").strip()
    sents = [s.strip() for s in body.replace("!",".").replace("?",".").split(".") if s.strip()]
    return {"title": title, "summary": ". ".join(sents[:2]) + ("." if sents else ""), "method": "extractive"}
