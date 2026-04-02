from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.middleware.csrf import CSRFMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.routers import audit, auth, connection_logs, dashboard, groups, networks, onboarding, peers, policies, system, users, version
from app.routers.devices import router as devices_router
from app.routers.client import router as client_router
from app.services.auth_service import create_admin_user, create_server_config


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables (Alembic handles migrations, this is a safety net)
    Base.metadata.create_all(bind=engine)

    # Seed defaults if not present
    db = SessionLocal()
    try:
        create_admin_user(db)
        create_server_config(db)
    finally:
        db.close()

    yield


app = FastAPI(
    title="NetLoom",
    description="Open-source WireGuard control plane",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Middleware (order matters: outermost first)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(CSRFMiddleware)

# API routers
app.include_router(auth.router)
app.include_router(onboarding.router)
app.include_router(dashboard.router)
app.include_router(peers.router)
app.include_router(networks.router)
app.include_router(groups.router)
app.include_router(policies.router)
app.include_router(system.router)
app.include_router(audit.router)
app.include_router(users.router)
app.include_router(devices_router)
app.include_router(client_router)
app.include_router(connection_logs.router)
app.include_router(version.router)

# Serve built React SPA (production)
_static_dir = Path(__file__).parent.parent / "static"
if _static_dir.exists():
    # Serve static assets (JS, CSS, etc.)
    app.mount("/assets", StaticFiles(directory=str(_static_dir / "assets")), name="assets")

    # SPA fallback: serve index.html for all non-API routes
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve the React SPA for all non-API routes."""
        return FileResponse(str(_static_dir / "index.html"))
