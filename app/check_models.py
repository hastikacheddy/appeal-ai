"""List Nemotron models on your Token Factory account and confirm the configured ids exist.
Usage: NEBIUS_API_KEY=... python -m app.check_models"""
from openai import OpenAI

from . import config

ids = sorted(m.id for m in OpenAI(api_key=config.NEBIUS_API_KEY, base_url=config.NEBIUS_BASE_URL).models.list())
print("NVIDIA models available:")
for i in ids:
    if "nvidia" in i.lower() or "nemotron" in i.lower():
        print("  ", i)
print("\nConfigured:")
for name in ("MODEL_VISION", "MODEL_FAST", "MODEL_SUPER", "MODEL_ULTRA"):
    mid = getattr(config, name)
    print(f"  {name:13} {mid:45} {'OK' if mid in ids else 'NOT FOUND - set it in .env'}")
