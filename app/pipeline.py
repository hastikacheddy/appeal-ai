"""The Appeal agent pipeline.

  1. READ      Nemotron VL (vision)  - scanned letter -> structured facts
  2. TRIAGE    Nemotron Lightning    - classify denial, plan research queries
  3. RESEARCH  Tavily                - insurer policy, clinical guidelines, appeal rules
  4. STRATEGY  Nemotron 3 Ultra      - build the argument from evidence only
  5. DRAFT     Nemotron 3 Super      - appeal letter + doctor's letter of medical necessity
  6. VERIFY    Nemotron 3 Super      - check every [n] citation against its source

Yields progress events so the UI can show each step live.
"""
from __future__ import annotations

import json
from typing import AsyncIterator

import pymupdf

from . import config, deadlines, demo_data, prompts, research
from .llm import Ledger, chat, image_part

MAX_PAGES = 4


def _pdf_to_inputs(data: bytes) -> tuple[str, list[tuple[bytes, str]]]:
    doc = pymupdf.open(stream=data, filetype="pdf")
    text = "\n".join(p.get_text() for p in doc.pages(0, min(MAX_PAGES, doc.page_count)))
    images = []
    if len(text.strip()) < 200:  # scanned PDF -> render pages for the vision model
        for page in doc.pages(0, min(MAX_PAGES, doc.page_count)):
            images.append((page.get_pixmap(dpi=150).tobytes("png"), "image/png"))
    return text, images


def _event(kind: str, **kw) -> dict:
    return {"type": kind, **kw}


async def run(files: list[tuple[bytes, str]], pasted_text: str = "", notes: str = "") -> AsyncIterator[dict]:
    if config.demo_active():
        async for ev in demo_data.replay():
            yield ev
        return

    ledger = Ledger()

    # ---- 1. READ -------------------------------------------------------------
    text, images = pasted_text, []
    for data, mime in files:
        if mime == "application/pdf":
            t, imgs = _pdf_to_inputs(data)
            text += "\n" + t
            images += imgs
        elif mime.startswith("image/"):
            images.append((data, mime))
        else:
            text += "\n" + data.decode(errors="ignore")

    if images:
        model = config.MODEL_VISION
        content = [{"type": "text", "text": "Extract the denial facts from these letter pages."}]
        content += [image_part(d, m) for d, m in images[:MAX_PAGES]]
        if text.strip():
            content.append({"type": "text", "text": "Additional text:\n" + text[:6000]})
    else:
        model = config.MODEL_FAST
        content = "Denial letter text:\n\n" + text[:12000]

    yield _event("step", id="read", status="running", model=model,
                 detail=f"Reading {len(images)} page image(s)" if images else "Reading letter text")
    facts = await chat(ledger, "read", model, prompts.EXTRACT, content, want_json=True, max_tokens=1200)
    if notes:
        facts["patient_notes"] = notes
    yield _event("step", id="read", status="done", model=model, data=facts)

    # ---- 2. TRIAGE -----------------------------------------------------------
    yield _event("step", id="triage", status="running", model=config.MODEL_FAST, detail="Classifying the denial")
    triage = await chat(ledger, "triage", config.MODEL_FAST, prompts.TRIAGE,
                        json.dumps(facts), want_json=True, max_tokens=1200)
    deadline = deadlines.compute(facts.get("denial_date"), facts.get("appeal_deadline"), facts.get("plan_type"))
    yield _event("step", id="triage", status="done", model=config.MODEL_FAST,
                 data={**triage, "deadline": deadline})

    # ---- 3. RESEARCH ---------------------------------------------------------
    queries = triage.get("queries", [])[:6]
    yield _event("step", id="research", status="running", model="Tavily",
                 detail=f"Running {len(queries)} searches", data={"queries": queries})
    sources = await research.gather(queries)
    yield _event("step", id="research", status="done", model="Tavily", data={"sources": sources})

    # ---- 4. STRATEGY (Ultra) -------------------------------------------------
    yield _event("step", id="strategy", status="running", model=config.MODEL_ULTRA,
                 detail="Building the argument from evidence")
    case = f"DENIAL FACTS:\n{json.dumps(facts, indent=1)}\n\nCLASSIFICATION:\n{json.dumps(triage)}\n\nSOURCES:\n{research.format_sources(sources)}"
    strategy = await chat(ledger, "strategy", config.MODEL_ULTRA, prompts.STRATEGY, case,
                          want_json=True, max_tokens=6000, temperature=0.3)
    valid = {s["id"] for s in sources}
    for a in strategy.get("arguments", []):
        a["cites"] = [c for c in a.get("cites", []) if c in valid]
    yield _event("step", id="strategy", status="done", model=config.MODEL_ULTRA, data=strategy)

    # ---- 5. DRAFT (Super) ----------------------------------------------------
    yield _event("step", id="draft", status="running", model=config.MODEL_SUPER, detail="Writing your appeal letter")
    draft_in = f"{case}\n\nSTRATEGY:\n{json.dumps(strategy)}\n\nAPPEAL DEADLINE: {deadline['due']}"
    out = await chat(ledger, "draft", config.MODEL_SUPER, prompts.DRAFT, draft_in, max_tokens=3000, temperature=0.4)
    letter, _, doctor = out.partition("---DOCTOR---")
    yield _event("step", id="draft", status="done", model=config.MODEL_SUPER)

    # ---- 6. VERIFY (Super) ---------------------------------------------------
    yield _event("step", id="verify", status="running", model=config.MODEL_SUPER, detail="Checking every citation")
    try:
        check = await chat(ledger, "verify", config.MODEL_SUPER, prompts.VERIFY,
                           f"LETTER:\n{letter}\n\nSOURCES:\n{research.format_sources(sources)}",
                           want_json=True, max_tokens=1500, temperature=0)
    except Exception as e:  # verification is advisory; never block the letter
        check = {"checked": 0, "supported": 0, "issues": [], "error": str(e)}
    yield _event("step", id="verify", status="done", model=config.MODEL_SUPER, data=check)

    yield _event("result", facts=facts, triage=triage, deadline=deadline, sources=sources,
                 strategy=strategy, letter=letter.strip(), doctor_letter=doctor.strip(),
                 verification=check, ledger=ledger.entries, demo=False)


async def run_to_completion(*args, **kw) -> dict:
    result = {}
    async for ev in run(*args, **kw):
        if ev["type"] == "result":
            result = ev
    return result
