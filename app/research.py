"""Evidence gathering with Tavily: insurer coverage policies, clinical guidelines,
and state/federal appeal rules. Every source gets a stable number so the
argument and letter can cite it as [n]."""
from __future__ import annotations

import asyncio

import httpx

from . import config

TAVILY_URL = "https://api.tavily.com/search"

# Authoritative domains we prefer for each kind of query.
DOMAINS = {
    "policy": [],  # insurer sites vary; leave open
    "clinical": ["ncbi.nlm.nih.gov", "pubmed.ncbi.nlm.nih.gov", "acr.org", "aafp.org",
                 "cancer.gov", "nccn.org", "uspreventiveservicestaskforce.org", "cms.gov"],
    "rules": ["healthcare.gov", "cms.gov", "dol.gov", "medicare.gov", "naic.org", "kff.org"],
}


async def _search(http: httpx.AsyncClient, query: str, kind: str, max_results: int = 4) -> list[dict]:
    body = {
        "query": query,
        "search_depth": "advanced",
        "max_results": max_results,
        "include_answer": False,
        "include_raw_content": False,
    }
    if DOMAINS.get(kind):
        body["include_domains"] = DOMAINS[kind]
    r = await http.post(TAVILY_URL, json=body,
                        headers={"Authorization": f"Bearer {config.TAVILY_API_KEY}"}, timeout=40)
    r.raise_for_status()
    out = []
    for res in r.json().get("results", []):
        out.append({
            "kind": kind,
            "query": query,
            "title": res.get("title", ""),
            "url": res.get("url", ""),
            "content": (res.get("content") or "")[:1200],
            "score": res.get("score", 0),
        })
    return out


async def gather(queries: list[dict]) -> list[dict]:
    """queries: [{"q": "...", "kind": "policy|clinical|rules"}]. Returns de-duplicated, numbered sources."""
    async with httpx.AsyncClient() as http:
        batches = await asyncio.gather(
            *[_search(http, q["q"], q.get("kind", "clinical")) for q in queries],
            return_exceptions=True,
        )
    seen, sources = set(), []
    for batch in batches:
        if isinstance(batch, Exception):
            continue
        for s in sorted(batch, key=lambda x: -x["score"]):
            if s["url"] in seen or not s["content"]:
                continue
            seen.add(s["url"])
            sources.append(s)
    sources = sources[:14]
    for i, s in enumerate(sources, 1):
        s["id"] = i
    return sources


def format_sources(sources: list[dict]) -> str:
    return "\n\n".join(f"[{s['id']}] ({s['kind']}) {s['title']}\n{s['url']}\n{s['content']}" for s in sources)
