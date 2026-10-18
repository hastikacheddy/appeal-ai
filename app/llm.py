"""Thin wrapper around the Nebius Token Factory (OpenAI-compatible) API.

Keeps a per-run ledger of which Nemotron model handled which step, with token
counts and latency, so the UI can show exactly how work was routed."""
from __future__ import annotations

import base64
import json
import re
import time
from dataclasses import dataclass, field

from openai import AsyncOpenAI

from . import config

_client: AsyncOpenAI | None = None


def client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=config.NEBIUS_API_KEY, base_url=config.NEBIUS_BASE_URL)
    return _client


@dataclass
class Ledger:
    entries: list[dict] = field(default_factory=list)

    def add(self, step: str, model: str, usage, seconds: float):
        self.entries.append({
            "step": step,
            "model": model,
            "prompt_tokens": getattr(usage, "prompt_tokens", 0) or 0,
            "completion_tokens": getattr(usage, "completion_tokens", 0) or 0,
            "seconds": round(seconds, 2),
        })


_THINK = re.compile(r"<think>.*?</think>", re.S)


def strip_reasoning(text: str) -> str:
    return _THINK.sub("", text or "").strip()


def parse_json(text: str):
    """Pull the first JSON object/array out of a model reply."""
    text = strip_reasoning(text)
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if fence:
        text = fence.group(1)
    start = min([i for i in (text.find("{"), text.find("[")) if i != -1], default=-1)
    if start == -1:
        raise ValueError("no JSON in model output")
    opener = text[start]
    closer = "}" if opener == "{" else "]"
    end = text.rfind(closer)
    return json.loads(text[start:end + 1])


async def chat(ledger: Ledger, step: str, model: str, system: str, user, *,
               temperature: float = 0.2, max_tokens: int = 2500, want_json: bool = False):
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    t0 = time.perf_counter()
    resp = await client().chat.completions.create(
        model=model, messages=messages, temperature=temperature, max_tokens=max_tokens,
    )
    ledger.add(step, model, resp.usage, time.perf_counter() - t0)
    text = resp.choices[0].message.content or ""
    if want_json:
        try:
            return parse_json(text)
        except (ValueError, json.JSONDecodeError):
            # One self-repair pass on the cheap model.
            t0 = time.perf_counter()
            fix = await client().chat.completions.create(
                model=config.MODEL_FAST, temperature=0, max_tokens=max_tokens,
                messages=[{"role": "system", "content": "Return ONLY valid JSON. No prose."},
                          {"role": "user", "content": f"Repair this into valid JSON:\n\n{text}"}],
            )
            ledger.add(step + " (json repair)", config.MODEL_FAST, fix.usage, time.perf_counter() - t0)
            return parse_json(fix.choices[0].message.content or "")
    return strip_reasoning(text)


def image_part(data: bytes, mime: str) -> dict:
    b64 = base64.b64encode(data).decode()
    return {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}}
