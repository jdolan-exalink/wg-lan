import os
import time
import statistics

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response

from app.dependencies import require_password_changed
from app.models.user import User

router = APIRouter(prefix="/api/speedtest", tags=["speedtest"])


@router.get("/download")
def speedtest_download(
    size: int = 1048576,
    _: User = Depends(require_password_changed),
):
    """Generate a payload of given size for client-side download speed testing."""
    data = os.urandom(min(size, 100 * 1024 * 1024))
    return Response(content=data, media_type="application/octet-stream")


@router.post("/upload")
def speedtest_upload(
    request: Request,
    _: User = Depends(require_password_changed),
):
    """Accept uploaded data for client-side upload speed testing."""
    return {"received": True}


@router.get("/ping")
def speedtest_ping(
    _: User = Depends(require_password_changed),
):
    """Minimal endpoint for latency measurement. Returns tiny payload."""
    return {"t": int(time.time() * 1000)}
