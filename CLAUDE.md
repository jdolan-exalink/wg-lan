# WG-LAN

Open-source WireGuard control plane with guided onboarding, managed routing via zones/groups/policies, and basic observability.

## Tech Stack
- Backend: FastAPI (Python 3.12) + SQLAlchemy + SQLite
- Frontend: React + TypeScript + Vite + Tailwind + shadcn/ui
- Deploy: Docker Compose (single container)

## Project Structure
- `backend/` — FastAPI app with models, schemas, routers, services, utils
- `frontend/` — React SPA built with Vite
- `scripts/` — Docker entrypoint, init scripts

## Key Concepts
- **Zones**: logical destinations (e.g., "Planta" = 10.10.10.0/24)
- **Groups**: access profiles (e.g., "soporte" can access Planta + Ventas)
- **Policies**: group -> zone = allow/deny
- **Policy Compiler**: compiles groups/zones/policies into WireGuard AllowedIPs
- **Precedence**: deny_manual > allow_manual > deny_group > allow_group > no access

## Commands
- Backend dev: `cd backend && uvicorn app.main:app --reload --port 5000`
- Frontend dev: `cd frontend && npm run dev`
- Tests: `cd backend && pytest`
- Docker: `docker compose up --build`

## Architecture
- Hub-and-spoke WireGuard model (single server)
- AllowedIPs are compiled from policies, never manually set
- `wg syncconf` for live changes without dropping connections
- FastAPI serves the built SPA in production (no nginx needed)
- Auth: JWT in httpOnly cookies + CSRF double-submit
