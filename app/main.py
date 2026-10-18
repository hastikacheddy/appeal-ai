"""Appeal - web server. Run: uvicorn app.main:app --reload"""
from __future__ import annotations

import json
import mimetypes
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles

from . import config, deadlines, pipeline

ROOT = Path(__file__).resolve().parent.parent
MAX_BYTES = 12 * 1024 * 1024

app = FastAPI(title="Appeal", description="Fight a health-insurance denial with Nemotron on Nebius.")


@app.get("/api/health")
def health():
    return {
        "ok": True,
        "demo": config.demo_active(),
        "models": {"vision": config.MODEL_VISION, "fast": config.MODEL_FAST,
                   "super": config.MODEL_SUPER, "ultra": config.MODEL_ULTRA},
    }


@app.post("/api/appeal")
async def appeal(files: list[UploadFile] = File(default=[]), text: str = Form(""), notes: str = Form("")):
    inputs = []
    for f in files[:4]:
        data = await f.read()
        if len(data) > MAX_BYTES:
            return JSONResponse({"error": f"{f.filename} is larger than 12 MB"}, status_code=413)
        mime = f.content_type or mimetypes.guess_type(f.filename or "")[0] or "application/octet-stream"
        inputs.append((data, mime))
    if not inputs and not text.strip() and not config.demo_active():
        return JSONResponse({"error": "Upload your denial letter or paste its text."}, status_code=400)

    async def stream():
        try:
            async for ev in pipeline.run(inputs, text, notes):
                yield f"data: {json.dumps(ev)}\n\n"
        except Exception as e:  # surface failures to the UI instead of a dead stream
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)[:400]})}\n\n"

    # Nothing is written to disk: uploads live only in memory for the length of this request.
    return StreamingResponse(stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.get("/api/ics")
def ics(due: str, send_by: str, insurer: str = "your insurer"):
    body = deadlines.ics(f"Send insurance appeal to {insurer}", send_by,
                         f"Final appeal deadline: {due}. Send by today to leave time for delivery.")
    return Response(body, media_type="text/calendar",
                    headers={"Content-Disposition": 'attachment; filename="appeal-deadline.ics"'})


@app.get("/sample-letter.png")
def sample():
    return FileResponse(ROOT / "samples" / "sample_denial.png")


app.mount("/", StaticFiles(directory=ROOT / "static", html=True), name="static")
