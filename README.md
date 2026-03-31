# NetLoom

Open-source WireGuard control plane with a web dashboard. Manage peers, define access zones, assign group-based policies, and compile `AllowedIPs` automatically — no manual CIDR editing.

**Stack:** FastAPI · React · SQLite · Docker Compose

---

## Features

- **Guided peer onboarding** — RoadWarrior (mobile/laptop) and Branch Office (site-to-site) wizards
- **Zone/Group access model** — define logical destinations, assign peers to groups, set policies per group
- **Policy compiler** — compiles `AllowedIPs` from zones/groups/policies with deny-first precedence
- **Live config sync** — `wg syncconf` keeps WireGuard running while applying changes
- **QR codes** — scan from mobile to import peer config
- **Auto-init** — server keypair and VPN subnet provisioned automatically on first run

---

## Quick Start (Docker)

```bash
# 1. Copy and edit the environment file
cp .env.example .env
# Set NETLOOM_SECRET_KEY, NETLOOM_ADMIN_PASSWORD, NETLOOM_SERVER_ENDPOINT

# 2. Start
docker compose up -d

# 3. Open the dashboard
# http://<your-server-ip>:7777
# Login: admin / admin123  (you will be forced to change the password)
```

**Required ports:**
| Port | Protocol | Purpose |
|------|----------|---------|
| 51820 | UDP | WireGuard VPN |
| 7777 | TCP | Web dashboard |

---

## Configuration

Key environment variables (see `.env.example` for the full list):

| Variable | Default | Description |
|---|---|---|
| `NETLOOM_SECRET_KEY` | `change-me-...` | JWT signing secret — **change this** |
| `NETLOOM_ADMIN_PASSWORD` | `admin123` | Initial admin password (first run only) |
| `NETLOOM_SERVER_ENDPOINT` | `vpn.example.com` | Public hostname/IP peers connect to |
| `NETLOOM_SERVER_PORT` | `51820` | WireGuard listen port |
| `NETLOOM_SUBNET` | `100.169.0.0/16` | VPN subnet (server takes first host IP) |
| `NETLOOM_PORT` | `7777` | Dashboard listen port |

---

## First-Run Flow

1. Container starts → server keypair generated automatically, server config saved to DB
2. WireGuard interface `wg0` brought up with the auto-generated config
3. Admin user created (forced password change on first login)
4. Open dashboard → create zones, groups, policies, then add peers

---

## Access Model

```
Zones    — logical destinations (e.g. "Office LAN" = 192.168.1.0/24)
Groups   — access profiles (e.g. "employees", "contractors")
Policies — group → zone = allow | deny
```

**Precedence:** `deny_manual > allow_manual > deny_group > allow_group > no access`

Peer `AllowedIPs` are compiled dynamically at config generation time — never stored statically.

---

## Manual / Development Setup

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m alembic upgrade head
python ../scripts/init-db.py       # create admin user + server config
uvicorn app.main:app --reload --port 7777
```

### Frontend

```bash
cd frontend
npm install
npm run dev      # proxies /api to localhost:7777
```

### Tests

```bash
cd backend
pytest
```

---

## Project Structure

```
NetLoom/
├── backend/
│   ├── app/
│   │   ├── models/        # SQLAlchemy: user, peer, server_config, zone, group, policy, audit
│   │   ├── routers/       # auth, peers, networks, zones, groups, policies, system, dashboard
│   │   ├── services/      # auth, wg, peer, config, policy_compiler, dashboard, audit
│   │   └── utils/         # ip_utils, wg_keygen, qr
│   └── tests/
├── frontend/
│   └── src/
│       ├── pages/         # Dashboard, Peers, Networks, Zones, Groups, Policies, System
│       ├── components/    # Layout, wizards, forms
│       └── api/           # Axios client + per-domain modules
├── scripts/
│   ├── entrypoint.sh      # Docker startup
│   └── init-db.py         # Manual DB init
├── docker-compose.yml
└── Dockerfile
```

---

## Security Notes

- Peer private keys are stored in the server DB. This enables config regeneration and QR codes but means DB access = key access. Restrict access to the `./data/` volume.
- Dashboard is unauthenticated from a network perspective — restrict port 7777 to your LAN (firewall rule or `127.0.0.1:7777:7777` in docker-compose).
- Change `WG_LAN_SECRET_KEY` before deploying. A short random string is fine: `openssl rand -hex 32`.

---

## License

MIT
