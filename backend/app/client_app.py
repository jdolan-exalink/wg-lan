"""
Client API - Dedicated FastAPI application for managed peer sync.
This app runs on a separate port (7771) and only exposes client-facing endpoints.
No web dashboard, no admin routes — just the client sync API.
"""
from fastapi import FastAPI

from app.routers.client import router as client_router

app = FastAPI(
    title="NetLoom Client API",
    description="Dedicated API for managed WireGuard peer synchronization",
    version="0.1.0",
    docs_url=None,  # No docs on client API
    redoc_url=None,
    openapi_url=None,
)

# Only include client-facing routes
app.include_router(client_router)
