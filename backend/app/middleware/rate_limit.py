import time
from collections import defaultdict
from threading import Lock

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# In-memory rate limiter: after MAX_ATTEMPTS in WINDOW_SECONDS, block IP for BLOCK_DURATION_SECONDS
_attempts: dict[str, list[float]] = defaultdict(list)
_blocked: dict[str, float] = {}  # ip -> blocked_until timestamp
_lock = Lock()

MAX_ATTEMPTS = 10
WINDOW_SECONDS = 60
BLOCK_DURATION_SECONDS = 600  # 10 minutes

_RATE_LIMITED_PATHS = {"/api/auth/login", "/api/v1/client/login"}


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in _RATE_LIMITED_PATHS and request.method == "POST":
            client_ip = request.client.host if request.client else "unknown"
            now = time.time()

            with _lock:
                # Check active block
                blocked_until = _blocked.get(client_ip)
                if blocked_until:
                    if now < blocked_until:
                        return JSONResponse(
                            status_code=429,
                            content={"detail": "Too many login attempts. Try again in 10 minutes."},
                        )
                    else:
                        del _blocked[client_ip]
                        _attempts[client_ip] = []

                # Slide the window
                _attempts[client_ip] = [t for t in _attempts[client_ip] if now - t < WINDOW_SECONDS]

                if len(_attempts[client_ip]) >= MAX_ATTEMPTS:
                    _blocked[client_ip] = now + BLOCK_DURATION_SECONDS
                    return JSONResponse(
                        status_code=429,
                        content={"detail": "Too many login attempts. Try again in 10 minutes."},
                    )

                _attempts[client_ip].append(now)

        return await call_next(request)
