"""Runtime configuration. Every model id can be overridden from the environment,
so you can match whatever the Token Factory /v1/models endpoint lists for your account."""
import os

NEBIUS_API_KEY = os.getenv("NEBIUS_API_KEY", "")
NEBIUS_BASE_URL = os.getenv("NEBIUS_BASE_URL", "https://api.tokenfactory.nebius.com/v1/")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

# Model routing: right-size every call.
#   VISION  - reads scanned / photographed denial letters
#   FAST    - triage, classification, query generation (cheap + low latency)
#   SUPER   - drafting and citation checking (everyday workhorse)
#   ULTRA   - the hard part: building the legal/clinical argument
MODEL_VISION = os.getenv("MODEL_VISION", "nvidia/Nemotron-3.5-Super-VL")
MODEL_FAST = os.getenv("MODEL_FAST", "nvidia/Nemotron-3_5-Lightning")
MODEL_SUPER = os.getenv("MODEL_SUPER", "nvidia/nemotron-3-super-120b-a12b")
MODEL_ULTRA = os.getenv("MODEL_ULTRA", "nvidia/Nemotron-3-Ultra-550b-a55b")

# Demo mode replays a recorded run so the UI works without keys (clearly labelled in the UI).
DEMO_MODE = os.getenv("DEMO_MODE", "auto")  # auto | on | off


def demo_active() -> bool:
    if DEMO_MODE == "on":
        return True
    if DEMO_MODE == "off":
        return False
    return not (NEBIUS_API_KEY and TAVILY_API_KEY)
