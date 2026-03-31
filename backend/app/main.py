from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import Base, SessionLocal, engine
from app.middleware.csrf import CSRFMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.routers import auth, dashboard, groups, networks, peers, policies, system, zones
from app.services.auth_service import create_admin_user


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables (Alembic handles migrations, this is a safety net)
    Base.metadata.create_all(bind=engine)

    # Seed default admin user if not present
    db = SessionLocal()
    try:
        create_admin_user(db)
    finally:
        db.close()

    yield


app = FastAPI(
    title="WG-LAN",
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
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(CSRFMiddleware)

# API routers
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(peers.router)
app.include_router(networks.router)
app.include_router(zones.router)
app.include_router(groups.router)
app.include_router(policies.router)
app.include_router(system.router)

# Serve built React SPA (production)
_static_dir = Path(__file__).parent.parent / "static"
if _static_dir.exists():
    app.mount("/", StaticFiles(directory=str(_static_dir), html=True), name="spa")
