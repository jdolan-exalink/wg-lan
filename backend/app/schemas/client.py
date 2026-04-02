from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ── Client Login ──────────────────────────────────────────────

class ClientLoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)
    device_fingerprint: Optional[str] = None


class ClientLoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    device_id: Optional[int] = None
    requires_registration: bool = True


# ── Client Config ─────────────────────────────────────────────

class WireGuardServerConfig(BaseModel):
    public_key: str
    endpoint: str
    listen_port: int = 51820


class WireGuardPeerConfig(BaseModel):
    private_key: str
    address: str
    dns: Optional[str] = None
    persistent_keepalive: int = 25


class WireGuardInterfaceConfig(BaseModel):
    tunnel_address: str
    allowed_ips: list[str]
    dns: Optional[str] = None


class FullConfigResponse(BaseModel):
    revision: int
    server: WireGuardServerConfig
    interface: WireGuardInterfaceConfig
    peer: WireGuardPeerConfig
    metadata: dict = {}


# ── Delta Sync ────────────────────────────────────────────────

class ConfigChange(BaseModel):
    revision: int
    change_type: str
    data: dict = {}


class DeltaConfigResponse(BaseModel):
    current_revision: int
    client_revision: int
    has_changes: bool
    changes: list[ConfigChange] = []


# ── Config Version ────────────────────────────────────────────

class ConfigVersionResponse(BaseModel):
    current_revision: int
    last_updated_at: Optional[datetime] = None


# ── Client Status ─────────────────────────────────────────────

class ClientStatusRequest(BaseModel):
    device_id: int
    tunnel_status: str = Field(..., pattern="^(connected|disconnected|connecting)$")
    last_handshake: Optional[datetime] = None
    bytes_sent: Optional[int] = None
    bytes_received: Optional[int] = None
