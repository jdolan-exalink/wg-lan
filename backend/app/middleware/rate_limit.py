import time
from collections import defaultdict
from threading import Lock

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# Simple in-memory rate limiter: max attempts per window per IP
_store: dict[str, list[float]] = defaultdict(list)
_lock = Lock()

LOGIN_MAX_ATTEMPTS = 10
LOGIN_WINDOW_SECONDS = 60


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/api/auth/login" and request.method == "POST":
            client_ip = request.client.host if request.client else "unknown"
            now = time.time()

            with _lock:
                attempts = _store[client_ip]
                # Remove attempts outside the window
                _store[client_ip] = [t for t in attempts if now - t < LOGIN_WINDOW_SECONDS]

                if len(_store[client_ip]) >= LOGIN_MAX_ATTEMPTS:
                    return JSONResponse(
                        status_code=429,
                        content={"detail": "Too many login attempts. Try again later."},
                    )

                _store[client_ip].append(now)

        return await call_next(request)
