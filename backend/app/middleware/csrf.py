import secrets

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "x-csrf-token"


class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Only check CSRF on mutating API endpoints that use cookie auth
        if request.method not in SAFE_METHODS and request.url.path.startswith("/api/"):
            # Skip CSRF check on login (no session cookie yet), health, and client API
            skip_paths = {"/api/auth/login", "/api/system/health"}
            skip_prefixes = ("/api/v1/client",)
            if request.url.path not in skip_paths and not request.url.path.startswith(skip_prefixes):
                cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
                header_token = request.headers.get(CSRF_HEADER_NAME)

                if not cookie_token or not header_token:
                    return JSONResponse(
                        status_code=403,
                        content={"detail": "CSRF token missing"},
                    )
                if not secrets.compare_digest(cookie_token, header_token):
                    return JSONResponse(
                        status_code=403,
                        content={"detail": "CSRF token mismatch"},
                    )

        return await call_next(request)
