import asyncio
from datetime import date

import pytest

from app import config, deadlines, llm, pipeline


def test_deadline_prefers_letter():
    d = deadlines.compute("2026-10-06", "2026-12-01", "medicaid", today=date(2026, 10, 18))
    assert d["due"] == "2026-12-01" and d["from_letter"]


def test_deadline_default_window():
    d = deadlines.compute("2026-10-06", None, "employer_or_aca", today=date(2026, 10, 18))
    assert d["due"] == "2027-04-04" and d["days_left"] == 168 and not d["from_letter"]


def test_parse_json_strips_reasoning_and_fences():
    txt = "<think>hmm {not json}</think>\nHere:\n```json\n{\"a\": [1, 2]}\n```"
    assert llm.parse_json(txt) == {"a": [1, 2]}


def test_ics_has_alarm():
    assert "BEGIN:VALARM" in deadlines.ics("x", "2026-11-01", "y")


def _collect(gen):
    async def go():
        return [ev async for ev in gen]
    return asyncio.run(go())


def test_demo_replay(monkeypatch):
    monkeypatch.setattr(config, "DEMO_MODE", "on")
    monkeypatch.setattr("asyncio.sleep", _nosleep)
    evs = _collect(pipeline.run([], ""))
    assert evs[-1]["type"] == "result" and evs[-1]["demo"]
    assert [e["id"] for e in evs if e["type"] == "step" and e["status"] == "done"] == \
        ["read", "triage", "research", "strategy", "draft", "verify"]


async def _nosleep(*a, **k):
    return None


def test_live_pipeline_routes_models(monkeypatch):
    """Live path with the network mocked: checks routing and citation filtering."""
    monkeypatch.setattr(config, "DEMO_MODE", "off")
    calls = []

    async def fake_chat(ledger, step, model, system, user, **kw):
        calls.append((step, model))
        ledger.add(step, model, None, 0.01)
        return {
            "read": {"insurer": "X", "plan_type": "medicaid", "denial_date": "2026-10-01", "appeal_deadline": None, "codes": []},
            "triage": {"category": "other", "category_label": "Other", "plain_english": "p", "appeal_path": [], "queries": [{"q": "a", "kind": "rules"}]},
            "strategy": {"strength": 3, "arguments": [{"title": "t", "point": "p", "cites": [1, 99]}]},
            "draft": "Letter [1]\n---DOCTOR---\nDoc",
            "verify": {"checked": 1, "supported": 1, "issues": []},
        }[step]

    async def fake_gather(q):
        return [{"id": 1, "kind": "rules", "title": "T", "url": "u", "content": "c", "score": 1}]

    monkeypatch.setattr(pipeline, "chat", fake_chat)
    monkeypatch.setattr(pipeline.research, "gather", fake_gather)
    evs = _collect(pipeline.run([(b"\x89PNG", "image/png")], ""))
    res = evs[-1]
    assert res["type"] == "result" and res["letter"] == "Letter [1]" and res["doctor_letter"] == "Doc"
    assert res["strategy"]["arguments"][0]["cites"] == [1]  # hallucinated [99] removed
    models = dict(calls)
    assert models["read"] == config.MODEL_VISION and models["triage"] == config.MODEL_FAST
    assert models["strategy"] == config.MODEL_ULTRA and models["draft"] == config.MODEL_SUPER
