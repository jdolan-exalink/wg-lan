# NetLoom - Managed Peers Architecture

## 1. Executive Summary

This document describes the architecture for adding **managed peers** to NetLoom while maintaining compatibility with traditional **roadwarrior** WireGuard peers. The system introduces a secure API for device provisioning, configuration versioning, delta sync, and a comprehensive user management system with an administrative web panel.

### Key Concepts
- **Managed Peers**: Clients that register via API, receive WireGuard configs, and sync incrementally
- **Roadwarrior Peers**: Traditional WireGuard peers managed manually via the existing UI
- **Users**: Human accounts for panel access (separate from WireGuard peers)
- **Devices**: Registered client machines for managed peers
- **Groups**: Access policy containers (existing concept, extended)

---

## 2. Technical Decisions

### 2.1 API Port Configuration
- **Decision**: Run API on configurable port (default 7771)
- **Justification**: Separates management API from the main web UI (7777), allows independent scaling and security policies
- **Implementation**: New `API_PORT`, `API_HOST` env vars in Settings

### 2.2 Password Hashing: Argon2id
- **Decision**: Use Argon2id via `passlib[argon2]`
- **Justification**: Argon2id is the winner of the Password Hashing Competition, resistant to GPU/ASIC attacks, memory-hard
- **Current State**: Already using Argon2 via passlib - confirmed compatible

### 2.3 JWT + Refresh Token Pattern
- **Decision**: Short-lived access tokens (JWT) + long-lived refresh tokens with rotation
- **Justification**: Limits exposure if access token is compromised; refresh token rotation detects token theft
- **Implementation**: 
  - Access token: 15-60 minutes (configurable)
  - Refresh token: 7-30 days (configurable), stored in DB with rotation
  - Both in httpOnly cookies with CSRF double-submit

### 2.4 Config Delivery: JSON + Delta Sync
- **Decision**: Bootstrap delivers full config as JSON; sync delivers delta
- **Justification**: 
  - JSON is easier to parse programmatically than .conf files
  - Delta sync reduces bandwidth and processing
  - Client can assemble .conf from JSON when needed
- **Structure**:
  ```json
  {
    "revision": 42,
    "server": { "public_key": "...", "endpoint": "..." },
    "peer": { "tunnel_address": "...", "allowed_ips": [...], "dns": "..." },
    "metadata": { "generated_at": "..." }
  }
  ```

### 2.5 Peer Type Separation
- **Decision**: `peer_type` field distinguishes `managed` vs `roadwarrior`
- **Justification**: Clear separation of concerns; managed peers use sync API, roadwarriors use static configs
- **Implementation**: Existing `peer_type` field extended with `managed` value

---

## 3. Security Decisions

### 3.1 Authentication Flow
```
Client → POST /api/v1/auth/login → Access Token + Refresh Token (httpOnly cookies)
Client → POST /api/v1/auth/refresh → New Access Token + New Refresh Token (rotation)
Client → POST /api/v1/auth/logout → Invalidate refresh token
```

### 3.2 Rate Limiting
- Login endpoint: 5 attempts per minute per IP
- Failed login tracking per user account
- Account lockout after N consecutive failures (configurable)

### 3.3 Session Invalidation
- User deactivated → All refresh tokens revoked
- Password changed → All refresh tokens revoked (configurable policy)
- Logout → Specific refresh token revoked

### 3.4 RBAC
- `is_admin`: Full panel access
- Regular users: Limited to their own profile (future expansion)
- API endpoints protected with `require_admin` dependency

---

## 4. Data Model

### 4.1 Users Table (Extended)
```
id                  INT PK
username            VARCHAR UNIQUE NOT NULL
email               VARCHAR NULL
password_hash       VARCHAR NOT NULL
is_active           BOOLEAN DEFAULT TRUE
is_admin            BOOLEAN DEFAULT FALSE
must_change_password BOOLEAN DEFAULT TRUE
onboarding_completed BOOLEAN DEFAULT FALSE
last_login_at       TIMESTAMP NULL
last_failed_login_at TIMESTAMP NULL
failed_login_count  INT DEFAULT 0
created_at          TIMESTAMP
updated_at          TIMESTAMP
```

### 4.2 Groups Table (Existing - Extended)
```
id                  INT PK
name                VARCHAR UNIQUE NOT NULL
description         VARCHAR NULL
is_active           BOOLEAN DEFAULT TRUE
created_at          TIMESTAMP
updated_at          TIMESTAMP
```

### 4.3 User_Groups (New - Many-to-Many)
```
id                  INT PK
user_id             INT FK → users.id
group_id            INT FK → peer_groups.id
assigned_at         TIMESTAMP
```

### 4.4 Refresh_Tokens (New)
```
id                  INT PK
user_id             INT FK → users.id
token_hash          VARCHAR NOT NULL (hash of actual token)
expires_at          TIMESTAMP NOT NULL
created_at          TIMESTAMP
revoked_at          TIMESTAMP NULL
user_agent          VARCHAR NULL
ip_address          VARCHAR NULL
```

### 4.5 Devices (New)
```
id                  INT PK
user_id             INT FK → users.id
device_name         VARCHAR NOT NULL
hostname            VARCHAR NULL
os_type             VARCHAR NULL (linux, windows, macos, android, ios)
device_fingerprint  VARCHAR NULL
status              VARCHAR DEFAULT 'active' (active, inactive, revoked)
last_seen_at        TIMESTAMP NULL
last_sync_at        TIMESTAMP NULL
config_revision     INT DEFAULT 0
created_at          TIMESTAMP
updated_at          TIMESTAMP
```

### 4.6 Peers Table (Extended)
```
id                  INT PK
name                VARCHAR NOT NULL
peer_type           VARCHAR NOT NULL (roadwarrior, managed)
user_id             INT FK → users.id NULL
device_id           INT FK → devices.id NULL
public_key          VARCHAR UNIQUE NOT NULL
preshared_key       VARCHAR NULL
tunnel_address      VARCHAR NOT NULL
allowed_ips         TEXT NULL
dns                 VARCHAR NULL
endpoint            VARCHAR NULL
persistent_keepalive INT DEFAULT 25
config_revision     INT DEFAULT 0
is_enabled          BOOLEAN DEFAULT TRUE
is_system           BOOLEAN DEFAULT FALSE
created_at          TIMESTAMP
updated_at          TIMESTAMP
```

### 4.7 Config_Revisions (New)
```
id                  INT PK
peer_id             INT FK → peers.id NULL (NULL = global config change)
device_id           INT FK → devices.id NULL
revision_number     INT NOT NULL
change_type         VARCHAR (network_added, network_removed, policy_changed, etc.)
changes             JSONB NULL
created_at          TIMESTAMP
```

### 4.8 Audit_Logs (Extended)
```
id                  INT PK
event_type          VARCHAR NOT NULL
actor_user_id       INT FK → users.id NULL
actor_device_id     INT FK → devices.id NULL
target_type         VARCHAR NULL
target_id           INT NULL
metadata            JSON NULL
ip_address          VARCHAR NULL
user_agent          VARCHAR NULL
created_at          TIMESTAMP
```

---

## 5. Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        NetLoom Server                           │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │   Web UI    │  │  Admin API  │  │    Client Sync API      │ │
│  │  (Port 7777)│  │  (Port 7771)│  │    (Port 7771)          │ │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────────┘ │
│         │                │                     │                │
│  ┌──────┴────────────────┴─────────────────────┴──────────────┐ │
│  │                    FastAPI Application                      │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────────┐ │ │
│  │  │   Auth   │ │  Users   │ │  Groups  │ │   Devices     │ │ │
│  │  │ Service  │ │ Service  │ │ Service  │ │   Service     │ │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └───────────────┘ │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────────┐ │ │
│  │  │  Peers   │ │  Config  │ │  Audit   │ │   Network     │ │ │
│  │  │ Service  │ │  Sync    │ │ Service  │ │   Service     │ │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └───────────────┘ │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    Database (SQLite)                        │ │
│  │  users │ groups │ user_groups │ refresh_tokens │ devices   │ │
│  │  peers │ config_revisions │ audit_logs │ networks │ policies│ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                  WireGuard (wg0)                            │ │
│  │  Roadwarrior Peers ←→ Static Configs                        │ │
│  │  Managed Peers ←→ Sync API ←→ Config Revisions              │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. API Structure

### 6.1 Authentication
```
POST   /api/v1/auth/login           - Authenticate user
POST   /api/v1/auth/refresh         - Refresh access token
POST   /api/v1/auth/logout          - Logout and revoke token
GET    /api/v1/auth/me              - Get current user info
POST   /api/v1/auth/change-password - Change password
```

### 6.2 Users
```
GET    /api/v1/users                - List users (admin)
POST   /api/v1/users                - Create user (admin)
GET    /api/v1/users/{id}           - Get user detail
PATCH  /api/v1/users/{id}           - Update user
POST   /api/v1/users/{id}/disable   - Deactivate user
POST   /api/v1/users/{id}/enable    - Reactivate user
POST   /api/v1/users/{id}/reset-password - Admin password reset
GET    /api/v1/users/{id}/groups    - Get user's groups
POST   /api/v1/users/{id}/groups    - Assign groups to user
DELETE /api/v1/users/{id}/groups/{group_id} - Remove group from user
```

### 6.3 Groups
```
GET    /api/v1/groups               - List groups
POST   /api/v1/groups               - Create group
GET    /api/v1/groups/{id}          - Get group detail
PATCH  /api/v1/groups/{id}          - Update group
DELETE /api/v1/groups/{id}          - Delete group
```

### 6.4 Devices
```
GET    /api/v1/devices              - List devices (admin)
GET    /api/v1/devices/{id}         - Get device detail
PATCH  /api/v1/devices/{id}         - Update device
```

### 6.5 Peers
```
GET    /api/v1/peers                - List peers
POST   /api/v1/peers                - Create peer
GET    /api/v1/peers/{id}           - Get peer detail
PATCH  /api/v1/peers/{id}           - Update peer
```

### 6.6 Client Sync API (Future Managed Client)
```
POST   /api/v1/client/login         - Device authentication
POST   /api/v1/client/register-device - Register new device
GET    /api/v1/client/config        - Get full WireGuard config
GET    /api/v1/client/config/version - Get current config revision
GET    /api/v1/client/config/delta  - Get config changes since revision
POST   /api/v1/client/status        - Report device/tunnel status
```

### 6.7 Audit
```
GET    /api/v1/audit/events         - List audit events
```

---

## 7. Frontend Navigation Structure

```
Sidebar Menu:
├── Dashboard
├── Peers
├── Networks
├── Users          ← NEW (above Groups)
├── Groups
├── Policies
├── Logs
└── System
```

### Users Page Features:
- List users with search
- Create/Edit user modal
- Activate/Deactivate toggle
- Reset password action
- View assigned groups
- Last login timestamp
- User detail view

---

## 8. Environment Variables

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=7771

# Security
SECRET_KEY=change-me-to-a-random-string
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# Database
DATABASE_URL=sqlite:///./data/netloom.db

# TLS (Optional)
TLS_ENABLED=false
TLS_CERT_PATH=
TLS_KEY_PATH=

# WireGuard
WG_SERVER_PUBLIC_KEY=
WG_SERVER_ENDPOINT=vpn.example.com
WG_DEFAULT_KEEPALIVE=25

# Sync
CONFIG_SYNC_INTERVAL=60
DEVICE_REGISTRATION_REQUIRED=true

# CORS
CORS_ORIGINS=["http://localhost:5173"]
```

---

## 9. Delta Sync Strategy

### 9.1 Revision Tracking
- Each config change increments a global `config_revision` counter
- Changes are recorded in `config_revisions` table
- Clients track their last known revision

### 9.2 Delta Response Format
```json
{
  "current_revision": 42,
  "client_revision": 38,
  "has_changes": true,
  "changes": [
    {
      "revision": 39,
      "type": "network_added",
      "data": { "network_id": 5, "cidr": "10.10.50.0/24" }
    },
    {
      "revision": 41,
      "type": "policy_changed",
      "data": { "policy_id": 12, "action": "deny" }
    }
  ]
}
```

### 9.3 No Changes Response
```json
{
  "current_revision": 42,
  "client_revision": 42,
  "has_changes": false,
  "changes": []
}
```

---

## 10. Future Phase Considerations

### 10.1 Device Binding
- `device_fingerprint` field prepared for hardware binding
- Can implement mTLS in future by adding cert validation

### 10.2 mTLS Preparation
- TLS config variables already defined
- Can add client certificate validation layer

### 10.3 Scaling
- SQLite suitable for single-server deployment
- Can migrate to PostgreSQL for multi-server setups
- Config sync can be event-driven with message queue

---

## 11. Implementation Order

1. ✅ Database models and migrations
2. ✅ Auth service enhancements (refresh tokens, session management)
3. ✅ User management API endpoints
4. ✅ Device and config sync endpoints
5. ✅ Frontend Users page
6. ✅ Sidebar navigation update
7. ✅ Audit logging enhancements
8. ✅ Environment configuration

---

## 12. Confirmation

**"Usuarios" page is positioned ABOVE "Groups" in the sidebar navigation.**

This is explicitly implemented in the Sidebar component's `navItems` array.
