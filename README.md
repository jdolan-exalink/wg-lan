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
- **HTTPS support** — self-signed TLS certificates with auto-generation, configurable via API and environment variables
- **Client sync API** — `/api/v1/client/*` endpoints for managed peer configuration and delta sync
- **Connection logging** — track peer connection events and status
- **Firewall management** — enable/disable iptables-based firewall with policy enforcement
- **User management** — multi-user support with role-based access control
- **Audit logging** — track all configuration changes and user actions
- **System metrics** — monitor CPU, RAM, and WireGuard interface status
- **Database backup/export** — create and download database backups

---

## Quick Start (Docker)

```bash
# 1. Copy and edit the environment file
cp .env.example .env
# Set NETLOOM_SECRET_KEY, NETLOOM_ADMIN_PASSWORD, NETLOOM_SERVER_ENDPOINT

# 2. Start
docker compose up -d

# 3. Open the dashboard
# HTTP:  http://<your-server-ip>:7777
# HTTPS: https://<your-server-ip>:7776
# Login: admin / admin123  (you will be forced to change the password)
```

**Required ports:**
| Port | Protocol | Purpose |
|------|----------|---------|
| 51820 | UDP | WireGuard VPN |
| 7777 | TCP | Web dashboard (HTTP) |
| 7776 | TCP | Web dashboard (HTTPS) |
| 7771 | TCP | Client sync API (HTTP) |
| 7772 | TCP | Client sync API (HTTPS) |

---

## Client API

Managed peers connect to a **dedicated API port**, separate from the admin dashboard:

| Protocol | Port | Base URL |
|----------|------|----------|
| HTTP | 7771 | `http://<server>:7771/api/v1/client/` |
| HTTPS | 7772 | `https://<server>:7772/api/v1/client/` |

**Key endpoints:**
- `POST /api/v1/client/login` — Authenticate and receive JWT tokens
- `GET /api/v1/client/config` — Get full WireGuard configuration
- `GET /api/v1/client/config/delta` — Get incremental config changes
- `POST /api/v1/client/status` — Report connection status

The client API has no web UI, no docs endpoints, and no admin routes — it's a clean API surface for managed peers only.

**Recommended:** Use HTTPS (port 7772) for production. The self-signed certificate is auto-generated. Clients should pin the certificate fingerprint or use `--insecure`/`verify=False` during development.

---

## Configuration

Key environment variables (see `.env` for the full list):

### Core Settings

| Variable | Default | Description |
|---|---|---|
| `NETLOOM_SECRET_KEY` | `change-me-...` | JWT signing secret — **change this** |
| `NETLOOM_ADMIN_PASSWORD` | `admin123` | Initial admin password (first run only) |
| `NETLOOM_SERVER_ENDPOINT` | `vpn.example.com` | Public hostname/IP peers connect to |
| `NETLOOM_SERVER_PORT` | `51820` | WireGuard listen port |
| `NETLOOM_SUBNET` | `100.169.0.0/16` | VPN subnet (server takes first host IP) |
| `NETLOOM_HTTP_PORT` | `7777` | Dashboard HTTP port |
| `NETLOOM_CLIENT_API_PORT` | `7771` | Client sync API port (HTTP) |
| `NETLOOM_CLIENT_API_TLS_PORT` | `7772` | Client sync API port (HTTPS) |

### TLS/HTTPS Settings

| Variable | Default | Description |
|---|---|---|
| `NETLOOM_TLS_ENABLED` | `false` | Enable HTTPS server |
| `NETLOOM_TLS_PORT` | `7776` | HTTPS listen port |
| `NETLOOM_TLS_AUTO_GENERATE` | `true` | Auto-generate self-signed certificate |
| `NETLOOM_TLS_CERT_DAYS` | `3650` | Certificate validity (days) |
| `NETLOOM_TLS_COUNTRY` | `US` | Certificate country (C) |
| `NETLOOM_TLS_STATE` | `California` | Certificate state (ST) |
| `NETLOOM_TLS_LOCALITY` | `San Francisco` | Certificate locality (L) |
| `NETLOOM_TLS_ORGANIZATION` | `NetLoom` | Certificate organization (O) |
| `NETLOOM_TLS_COMMON_NAME` | `netloom.local` | Certificate common name (CN) |

---

## TLS/HTTPS Configuration

### Enable HTTPS

Set in `.env`:
```bash
NETLOOM_TLS_ENABLED=true
```

The system will auto-generate a self-signed certificate on first start. Certificates are stored in `./certs/` and persisted via Docker volume.

### Via API (Settings)

All TLS parameters can be viewed and updated through the system API:

- `GET /api/system/tls` — View current TLS configuration
- `PUT /api/system/tls` — Update TLS settings
- `POST /api/system/tls/regenerate-cert` — Regenerate self-signed certificate

**Note:** TLS changes require a container restart to take effect.

### Using Your Own Certificates

Place your certificates in the `./certs/` directory and disable auto-generation:
```bash
NETLOOM_TLS_AUTO_GENERATE=false
NETLOOM_TLS_CERT_PATH=/app/certs/my-cert.crt
NETLOOM_TLS_KEY_PATH=/app/certs/my-key.key
```

---

## First-Run Flow

1. Container starts → server keypair generated automatically, server config saved to DB
2. WireGuard interface `wg0` brought up with the auto-generated config
3. TLS certificates generated (if enabled)
4. Admin user created (forced password change on first login)
5. Open dashboard → create zones, groups, policies, then add peers

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
│   │   ├── models/        # SQLAlchemy: user, peer, server_config, network, group, policy, audit, device
│   │   ├── routers/       # auth, peers, networks, groups, policies, system, dashboard, client, devices, onboarding
│   │   ├── services/      # auth, wg, peer, config, policy_compiler, dashboard, audit, iptables
│   │   ├── schemas/       # Pydantic request/response models
│   │   ├── middleware/    # CSRF protection, rate limiting
│   │   └── utils/         # ip_utils, wg_keygen, qr, tls_cert_generator
│   └── tests/
├── frontend/
│   └── src/
│       ├── pages/         # Dashboard, Peers, Networks, Groups, Policies, System, Onboarding
│       ├── components/    # Layout, wizards, forms, charts
│       ├── api/           # Axios client + per-domain modules
│       └── contexts/      # React contexts (auth, theme)
├── scripts/
│   ├── entrypoint.sh      # Docker startup with TLS support
│   └── init-db.py         # Manual DB init
├── config/                # WireGuard configuration files
├── data/                  # SQLite database + backups
├── certs/                 # TLS certificates (auto-mounted)
├── docker-compose.yml
└── Dockerfile
```

---

## Security Notes

- Peer private keys are stored in the server DB. This enables config regeneration and QR codes but means DB access = key access. Restrict access to the `./data/` volume.
- Dashboard is unauthenticated from a network perspective — restrict port 7777 to your LAN (firewall rule or `127.0.0.1:7777:7777` in docker-compose).
- Change `NETLOOM_SECRET_KEY` before deploying. A short random string is fine: `openssl rand -hex 32`.
- HTTPS with self-signed certificates is suitable for internal/LAN use. For public-facing deployments, use certificates from a trusted CA (Let's Encrypt, etc.).
- Auth uses JWT in httpOnly cookies with CSRF double-submit protection.

---

## License

MIT
