import json
from typing import Literal

from pydantic import BaseModel, field_validator

from app.utils.ip_utils import is_valid_cidr


class RoadWarriorCreate(BaseModel):
    name: str
    device_type: Literal["laptop", "ios", "android", "server"] = "laptop"
    tunnel_mode: Literal["full", "split"] = "split"
    network_id: int | None = None
    dns: str | None = None
    group_ids: list[int] = []
    persistent_keepalive: int = 25


class BranchOfficeCreate(BaseModel):
    name: str
    device_type: Literal["router", "server"] = "router"
    network_id: int | None = None
    remote_subnets: list[str]
    dns: str | None = None
    group_ids: list[int] = []
    persistent_keepalive: int = 25

    @field_validator("remote_subnets")
    @classmethod
    def validate_subnets(cls, v: list[str]) -> list[str]:
        for cidr in v:
            if not is_valid_cidr(cidr):
                raise ValueError(f"Invalid CIDR: {cidr}")
        return v


class PeerUpdate(BaseModel):
    name: str | None = None
    dns: str | None = None
    persistent_keepalive: int | None = None
    tunnel_mode: Literal["full", "split"] | None = None
    remote_subnets: list[str] | None = None

    @field_validator("remote_subnets")
    @classmethod
    def validate_subnets(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return v
        for cidr in v:
            if not is_valid_cidr(cidr):
                raise ValueError(f"Invalid CIDR: {cidr}")
        return v


class PeerOverrideCreate(BaseModel):
    network_id: int
    action: Literal["allow", "deny"]
    reason: str | None = None


class PeerResponse(BaseModel):
    id: int
    name: str
    peer_type: str
    device_type: str | None
    public_key: str
    assigned_ip: str
    network_id: int | None
    tunnel_mode: str
    remote_subnets: list[str]
    dns: str | None
    persistent_keepalive: int
    is_enabled: bool
    is_system: bool = False
    group_ids: list[int] = []
    created_at: str
    updated_at: str
    revoked_at: str | None
    is_online: bool = False
    sync_status: str = "green"  # green, yellow, red

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_peer(cls, peer, db=None, wg_status=None, sync_status="green") -> "PeerResponse":
        remote = json.loads(peer.remote_subnets) if peer.remote_subnets else []
        group_ids: list[int] = []
        if db is not None:
            from app.models.group import PeerGroupMember
            memberships = db.query(PeerGroupMember).filter(
                PeerGroupMember.peer_id == peer.id
            ).all()
            group_ids = [m.group_id for m in memberships]

        is_online = False
        if wg_status:
            is_online = wg_status.is_online

        return cls(
            id=peer.id,
            name=peer.name,
            peer_type=peer.peer_type,
            device_type=peer.device_type,
            public_key=peer.public_key,
            assigned_ip=peer.assigned_ip,
            network_id=peer.network_id,
            tunnel_mode=peer.tunnel_mode,
            remote_subnets=remote,
            dns=peer.dns,
            persistent_keepalive=peer.persistent_keepalive,
            is_enabled=peer.is_enabled,
            is_system=getattr(peer, 'is_system', False),
            group_ids=group_ids,
            created_at=peer.created_at.isoformat(),
            updated_at=peer.updated_at.isoformat(),
            revoked_at=peer.revoked_at.isoformat() if peer.revoked_at else None,
            is_online=is_online,
            sync_status=sync_status,
        )


class PeerPermissionSummary(BaseModel):
    group_policies: list[dict]
    overrides: list[dict]
    final_cidrs: list[str]
