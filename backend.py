"""PixelErase AI background removal API.
Runs rembg's open-source segmentation locally and returns an in-memory PNG.
"""
from __future__ import annotations
import io
import os
from typing import Annotated
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from PIL import Image, UnidentifiedImageError
from rembg import new_session, remove

MAX_FILE_SIZE = 15 * 1024 * 1024
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_ORIGINS = [x.strip() for x in os.getenv(
    "ALLOWED_ORIGINS", "http://localhost:5500,http://127.0.0.1:5500,http://localhost:8000,http://127.0.0.1:8000,null"
).split(",") if x.strip()]
MODEL = os.getenv("REMBG_MODEL", "u2net")

app = FastAPI(title="PixelErase AI API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
_session = None

def get_session():
    global _session
    if _session is None:
        _session = new_session(MODEL)
    return _session

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "model": MODEL}

@app.post("/api/remove-background", response_class=Response)
async def remove_background(file: Annotated[UploadFile, File(description="JPG, PNG, or WEBP image")]) -> Response:
    content_type = (file.content_type or "").lower()
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(415, "Unsupported format. Use JPG, PNG, or WEBP.")
    data = await file.read(MAX_FILE_SIZE + 1)
    await file.close()
    if not data:
        raise HTTPException(400, "The uploaded file is empty.")
    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(413, "Image exceeds the 15 MB limit.")
    try:
        with Image.open(io.BytesIO(data)) as probe:
            probe.verify()
        output = remove(data, session=get_session(), force_return_bytes=True)
        with Image.open(io.BytesIO(output)) as result:
            if result.format != "PNG" or "A" not in result.mode:
                raise ValueError("Model output has no alpha channel")
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise HTTPException(400, "Invalid or corrupted image.") from exc
    except Exception as exc:
        raise HTTPException(500, "The removal model could not process this image.") from exc
    stem = os.path.splitext(file.filename or "image")[0]
    safe_stem = "".join(ch for ch in stem if ch.isalnum() or ch in "-_ ")[:80] or "image"
    return Response(
        content=output,
        media_type="image/png",
        headers={"Content-Disposition": f'inline; filename="{safe_stem}-transparent.png"', "Cache-Control": "no-store"},
    )
