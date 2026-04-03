from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.models.device import Device
from app.models.peer import Peer
from app.models.network import Network
from app.models.config_revision import ConfigRevision
from app.schemas.client import (
    ClientLoginRequest,
    ClientLoginResponse,
    FullConfigResponse,
    WireGuardServerConfig,
    WireGuardPeerConfig,
    WireGuardInterfaceConfig,
    DeltaConfigResponse,
    ConfigChange,
    ConfigVersionResponse,
    ClientStatusRequest,
)
from app.schemas.device import DeviceRegisterRequest, DeviceRegisterResponse
from app.services.auth_service import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    revoke_refresh_token,
    verify_token,
)
from app.services.audit_service import log as audit_log
from app.services.connection_log_service import log_connection

router = APIRouter(prefix="/api/v1/client", tags=["client-sync"])

# Seconds since last_seen_at before a peer is considered disconnected
_ACTIVE_CONNECTION_TTL_SECONDS = 180

_bearer = HTTPBearer(auto_error=False)


def _detect_os(user_agent: str | None) -> tuple[str, str]:
    """
    Detect OS type and friendly name from User-Agent string.
    Returns (os_type, device_name_prefix).
    os_type: 'windows' | 'macos' | 'linux' | 'android' | 'ios' | 'unknown'
    """
    if not user_agent:
        return "unknown", "unknown"
    ua = user_agent.lower()
    if "windows" in ua:
        return "windows", "windows"
    if "darwin" in ua or "mac os" in ua or "macos" in ua:
        return "macos", "mac"
    if "android" in ua:
        return "android", "android"
    if "iphone" in ua or "ipad" in ua or "ios" in ua:
        return "ios", "ios"
    if "linux" in ua:
        return "linux", "linux"
    return "unknown", "unknown"


def _get_current_client_user(
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer),
    db: Session = Depends(get_db),
) -> User:
    """Authenticate client via Bearer token (not cookie)."""
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not credentials:
        raise exc
    user_id = verify_token(credentials.credentials)
    if user_id is None:
        raise exc
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise exc
    return user


def _get_or_create_peer(
    db: Session,
    user: User,
    request: Request | None = None,
) -> Peer:
    """
    Return the active Peer for the user.
    If it doesn't exist yet, auto-create it using only the username.
    The peer is identified by user_id - always the same peer for the same user.
    """
    from app.services.peer_service import create_roadwarrior
    from app.schemas.peer import RoadWarriorCreate

    # Find existing active peer for this user (no OS in name)
    peer = (
        db.query(Peer)
        .filter(
            Peer.user_id == user.id,
            Peer.is_enabled == True,
            Peer.peer_type == "roadwarrior",
        )
        .first()
    )

    if peer:
        # Update OS if we can detect it from User-Agent
        if request:
            os_type, _ = _detect_os(request.headers.get("user-agent"))
            if os_type != "unknown" and peer.os != os_type:
                peer.os = os_type
                db.commit()
        return peer

    # No peer yet — auto-create it (name = username only)
    # Detect OS from User-Agent if available
    os_type = "unknown"
    if request:
        os_type, _ = _detect_os(request.headers.get("user-agent"))
    
    device_type_map = {
        "windows": "laptop",
        "macos": "laptop",
        "linux": "laptop",
        "android": "android",
        "ios": "ios",
    }
    
    peer_data = RoadWarriorCreate(
        name=user.username,
        device_type=device_type_map.get(os_type, "user"),
        tunnel_mode="split",
        persistent_keepalive=25,
    )
    peer = create_roadwarrior(db, peer_data, created_by=user.id)

    # Link peer to user and set OS
    peer.user_id = user.id
    peer.os = os_type if os_type != "unknown" else None
    db.commit()
    db.refresh(peer)

    audit_log(
        db,
        "client.auto_provision",
        user_id=user.id,
        target_type="peer",
        target_id=peer.id,
        details={"peer_name": user.username},
    )

    return peer


@router.post("/login", response_model=ClientLoginResponse)
def client_login(
    body: ClientLoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """
    Authenticate client and return tokens.
    Auto-provisions a WireGuard Peer on first login (named by username only).
    Reuses existing peer if user already has one.
    """
    user = authenticate_user(db, body.username, body.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    # Block login if user already has an active connection (check by peer updated_at)
    existing_peer = (
        db.query(Peer)
        .filter(
            Peer.user_id == user.id,
            Peer.is_enabled == True,
            Peer.peer_type == "roadwarrior",
        )
        .first()
    )
    if existing_peer and existing_peer.updated_at:
        last_seen = existing_peer.updated_at
        if last_seen.tzinfo is None:
            last_seen = last_seen.replace(tzinfo=timezone.utc)
        age = (datetime.now(timezone.utc) - last_seen).total_seconds()
        if age < _ACTIVE_CONNECTION_TTL_SECONDS:
            log_connection(
                db,
                event_type="login_blocked",
                message=f"Login attempt rejected: user '{user.username}' already has an active connection",
                peer_id=existing_peer.id,
                peer_name=existing_peer.name,
                severity="warning",
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already has an active connection",
            )

    # Auto-provision peer if needed (uses username only, no OS)
    peer = _get_or_create_peer(db, user, request)

    access_token = create_access_token(user.id)
    refresh_token_str = create_refresh_token(
        db,
        user.id,
        user_agent=request.headers.get("user-agent"),
    )

    response.set_cookie(
        key="client_access_token",
        value=access_token,
        httponly=True,
        secure=settings.tls_enabled,
        samesite="lax",
        max_age=60 * settings.access_token_expire_minutes,
    )

    audit_log(
        db,
        "client.login",
        user_id=user.id,
        target_type="user",
        target_id=user.id,
    )

    return ClientLoginResponse(
        access_token=access_token,
        refresh_token=refresh_token_str,
        expires_in=60 * settings.access_token_expire_minutes,
        device_id=peer.id,
        requires_registration=False,
    )


@router.get("/config", response_model=FullConfigResponse)
def get_full_config(
    request: Request,
    user: User = Depends(_get_current_client_user),
    db: Session = Depends(get_db),
):
    """
    Get full WireGuard configuration for the authenticated client.
    peer_id is inferred from the token — no need to pass it manually.
    """
    from app.models.server_config import ServerConfig
    server_cfg = db.query(ServerConfig).first()
    if not server_cfg:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Server not configured")

    # Get or auto-provision the peer for this user
    peer = _get_or_create_peer(db, user, request)

    # Update last_seen
    peer.updated_at = datetime.now(timezone.utc)
    db.commit()

    # Get allowed IPs from policy compiler (includes VPN subnet + branch routes)
    from app.services.policy_compiler import compile_client_allowed_ips
    allowed_ips = compile_client_allowed_ips(db, peer.id)
    if not allowed_ips:
        # Fallback: all active networks
        networks = db.query(Network).filter(Network.is_active == True).all()
        allowed_ips = [n.cidr for n in networks] if networks else ["0.0.0.0/0"]

    latest_revision = (
        db.query(ConfigRevision)
        .order_by(ConfigRevision.revision_number.desc())
        .first()
    )
    revision = latest_revision.revision_number if latest_revision else 0

    return FullConfigResponse(
        revision=revision,
        server=WireGuardServerConfig(
            public_key=server_cfg.public_key,
            endpoint=server_cfg.endpoint,
            listen_port=server_cfg.listen_port,
        ),
        interface=WireGuardInterfaceConfig(
            tunnel_address=peer.assigned_ip,
            allowed_ips=allowed_ips,
            dns=peer.dns,
        ),
        peer=WireGuardPeerConfig(
            private_key=peer.private_key,
            address=peer.assigned_ip,
            dns=peer.dns,
            persistent_keepalive=peer.persistent_keepalive,
        ),
        metadata={
            "peer_id": peer.id,
            "peer_name": peer.name,
            "peer_type": peer.peer_type,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
    )


@router.get("/config/version", response_model=ConfigVersionResponse)
def get_config_version(
    user: User = Depends(_get_current_client_user),
    db: Session = Depends(get_db),
):
    """Get current configuration revision number."""
    latest_revision = (
        db.query(ConfigRevision)
        .order_by(ConfigRevision.revision_number.desc())
        .first()
    )
    
    if not latest_revision:
        return ConfigVersionResponse(current_revision=0)
    
    return ConfigVersionResponse(
        current_revision=latest_revision.revision_number,
        last_updated_at=latest_revision.created_at,
    )


@router.get("/config/delta", response_model=DeltaConfigResponse)
def get_config_delta(
    client_revision: int = 0,
    user: User = Depends(_get_current_client_user),
    db: Session = Depends(get_db),
):
    """Get configuration changes since client's last known revision."""
    latest_revision = (
        db.query(ConfigRevision)
        .order_by(ConfigRevision.revision_number.desc())
        .first()
    )
    
    current_revision = latest_revision.revision_number if latest_revision else 0
    
    # No changes
    if client_revision >= current_revision:
        return DeltaConfigResponse(
            current_revision=current_revision,
            client_revision=client_revision,
            has_changes=False,
            changes=[],
        )
    
    # Get changes since client revision
    changes = (
        db.query(ConfigRevision)
        .filter(ConfigRevision.revision_number > client_revision)
        .order_by(ConfigRevision.revision_number.asc())
        .all()
    )
    
    change_list = [
        ConfigChange(
            revision=c.revision_number,
            change_type=c.change_type,
            data={},  # TODO: Parse JSON from c.changes
        )
        for c in changes
    ]
    
    return DeltaConfigResponse(
        current_revision=current_revision,
        client_revision=client_revision,
        has_changes=True,
        changes=change_list,
    )


@router.post("/status", status_code=status.HTTP_200_OK)
def report_client_status(
    body: ClientStatusRequest,
    request: Request,
    user: User = Depends(_get_current_client_user),
    db: Session = Depends(get_db),
):
    """Report peer tunnel status (heartbeat)."""
    peer = db.query(Peer).filter(Peer.id == body.peer_id, Peer.user_id == user.id).first()
    if not peer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Peer not found")
    
    # Update updated_at as proxy for last_seen (we don't have a dedicated field)
    peer.updated_at = datetime.now(timezone.utc)
    db.commit()
    
    audit_log(
        db,
        "client.status_report",
        user_id=user.id,
        target_type="peer",
        target_id=peer.id,
        details={
            "tunnel_status": body.tunnel_status,
            "bytes_sent": body.bytes_sent,
            "bytes_received": body.bytes_received,
        },
        ip_address=request.client.host if request.client else None,
    )
    
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@router.get("/settings")
def get_client_settings(
    db: Session = Depends(get_db),
):
    """Get client-facing settings (no auth required for basic config)."""
    from app.models.server_config import ServerConfig
    cfg = db.query(ServerConfig).first()
    if not cfg:
        return {"client_retry_enabled": False}
    return {"client_retry_enabled": cfg.client_retry_enabled}
