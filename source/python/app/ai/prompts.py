"""Prompt registry: versioned templates, no hardcoded strings in logic."""
import re

PROMPTS = {
    ("research_plan", "v1"): ("You plan web research. Question: {question}\n"
                              "Return steps: discover, collect, extract, resolve, "
                              "correlate, verify, report."),
    ("summarize_evidence", "v1"): ("Summarize ONLY the evidence below in 3 bullets. "
                                   "Cite source ids. Do not invent facts.\n{evidence}"),
    ("claim_check", "v1"): ("Decide VERIFIED/UNVERIFIED/CONFLICTED for: {claim}\n"
                            "Evidence:\n{evidence}"),
}


def render(name: str, version: str = "v1", **kw):
    tpl = PROMPTS.get((name, version))
    if not tpl:
        raise KeyError(f"unknown prompt {name}@{version}")
    out = tpl
    for k, v in kw.items():
        out = out.replace("{" + k + "}", str(v))
    leftovers = set(re.findall(r"\{(\w+)\}", out))
    if leftovers:
        raise KeyError(f"missing prompt vars: {sorted(leftovers)}")
    return out


def catalog():
    return [{"name": n, "version": v} for n, v in sorted(PROMPTS)]
