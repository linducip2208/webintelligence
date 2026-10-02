"""Research planner + reproducibility bundle — stdlib only."""
import re
STOP = {"what","which","how","many","much","does","are","the","this","that","with","from","into","show","find"}
def keywords(question: str, top=8):
    words = [x for x in re.findall(r"[a-z]{4,}", (question or "").lower()) if x not in STOP]
    freq, order = {}, []
    for x in words:
        if x not in freq: order.append(x)
        freq[x] = freq.get(x, 0) + 1
    return sorted(order, key=lambda x: -freq[x])[:top]
INTENTS = [("price", ["price","pricing","cost"]), ("competitor", ["competitor","rival","market"]),
           ("change", ["chang","monitor","website"]), ("company", ["company","startup","firm"])]
def plan(question: str):
    q = (question or "").lower()
    intents = [n for n, ws in INTENTS if any(x in q for x in ws)] or ["general"]
    kws = keywords(question)
    steps = [{"id": i+1, "name": n, "status": "pending"} for i, n in enumerate(
        ["source_discovery", "collection", "extraction", "normalization",
         "entity_resolution", "correlation", "verification", "report"])]
    return {"question": question, "intents": intents, "keywords": kws, "steps": steps,
            "prompt_version": "v1"}
def bundle(run: dict):
    return {"question": run.get("question"), "plan": run.get("plan"),
            "sources": run.get("sources"), "job_ids": run.get("job_ids"),
            "evidence_ids": run.get("evidence_ids"), "ai": {
                "provider": run.get("ai_provider"), "model": run.get("ai_model"),
                "prompt_version": run.get("prompt_version")},
            "analysis": run.get("analysis"), "config": run.get("config"),
            "created_at": run.get("created_at"), "finished_at": run.get("finished_at")}
