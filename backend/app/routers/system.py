import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from io import BytesIO

import psutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import require_password_changed
from app.models.server_config import ServerConfig
from app.models.user import User
from app.models.group import PeerGroup, ADGroupMapping
from app.schemas.system import (
    ADConfigResponse,
    ADConfigUpdate,
    ADGroupMappingResponse,
    ADGroupMappingCreate,
    ADGroupMappingUpdate,
    ADGroupMappingBulkCreate,
    ADGroupsFromADResponse,
    BackupResponse,
    FirewallStatusResponse,
    FirewallStatusUpdate,
    HealthResponse,
    RegenerateKeyResponse,
    ServerConfigResponse,
    ServerConfigUpdate,
    SystemMetricsResponse,
    TLSConfigResponse,
    TLSConfigUpdate,
    TLSRegenerateCertResponse,
)
from app.services import wg_service
from app.services import ad_service, ad_mapping_service
from app.utils.wg_keygen import safe_generate_keypair

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)):
    try:
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "error"

    wg_status = "up" if wg_service.is_interface_up() else "down"

    # Count active tunnels (enabled peers)
    from app.models.peer import Peer
    tunnel_count = db.query(Peer).filter(Peer.is_enabled == True).count()

    # Get server uptime
    import os
    uptime_seconds = 0
    try:
        with open("/proc/uptime", "r") as f:
            uptime_seconds = int(float(f.read().split()[0]))
    except Exception:
        pass

    # Check if server is initialized
    from app.models.server_config import ServerConfig
    server_config = db.query(ServerConfig).first()
    is_initialized = server_config is not None

    return HealthResponse(
        status="ok" if db_status == "ok" else "degraded",
        db=db_status,
        wg_interface=wg_status,
        tunnel_count=tunnel_count,
        uptime_seconds=uptime_seconds,
        is_initialized=is_initialized,
    )


@router.get("/server-config", response_model=ServerConfigResponse)
def get_server_config(
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    cfg = db.query(ServerConfig).first()
    if not cfg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not initialised")
    return cfg


@router.put("/server-config", response_model=ServerConfigResponse)
def update_server_config(
    body: ServerConfigUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    cfg = db.query(ServerConfig).first()
    if not cfg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not initialised")

    update_data = body.model_dump(exclude_none=True)
    for key, value in update_data.items():
        setattr(cfg, key, value)

    db.commit()
    db.refresh(cfg)

    # Try to apply config to WireGuard (may fail if WG not available)
    try:
        wg_service.apply_config(db)
    except Exception:
        pass

    return cfg


@router.post("/server-config/regenerate-key", response_model=RegenerateKeyResponse)
def regenerate_keypair(
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    """Regenerate server keypair. This will disconnect all clients."""
    cfg = db.query(ServerConfig).first()
    if not cfg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not initialised")

    private_key, public_key = safe_generate_keypair()
    cfg.private_key = private_key
    cfg.public_key = public_key
    db.commit()
    db.refresh(cfg)

    # Try to apply config to WireGuard
    try:
        wg_service.apply_config(db)
    except Exception:
        pass

    return RegenerateKeyResponse(
        public_key=public_key,
        message="Server keypair regenerated. All clients must update their config files.",
    )


@router.post("/apply-config")
def apply_config(
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    """Apply config to WireGuard. Auto-restarts WG if needed."""
    try:
        wg_service.apply_config(db)
        # Ensure WG is running after applying config
        if not wg_service.is_interface_up():
            try:
                wg_service.bring_up()
            except Exception:
                pass  # May fail on systems without WG kernel module
        return {"message": "Config applied successfully"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/backup", response_model=BackupResponse)
def backup(
    _: User = Depends(require_password_changed),
):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = Path("./data/backups")
    backup_dir.mkdir(parents=True, exist_ok=True)

    db_path = Path(settings.db_path)
    if db_path.exists():
        dest = backup_dir / f"netloom_{ts}.db"
        shutil.copy2(db_path, dest)
        return BackupResponse(message="Backup created", path=str(dest))

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Database file not found")


@router.post("/wg/up")
def wg_up(
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    """Bring WireGuard interface up. Creates it if needed."""
    if wg_service.is_interface_up():
        return {"message": "WireGuard interface is already up"}
    try:
        wg_service.ensure_interface_up(db)
        return {"message": "WireGuard interface brought up"}
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"WireGuard not available: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bring up WireGuard: {str(e)}",
        )


@router.post("/wg/down")
def wg_down(
    _: User = Depends(require_password_changed),
):
    """Bring WireGuard interface down."""
    if not wg_service.is_interface_up():
        return {"message": "WireGuard interface is already down"}
    try:
        wg_service.bring_down()
        return {"message": "WireGuard interface brought down"}
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"WireGuard not available: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bring down WireGuard: {str(e)}",
        )


@router.post("/wg/restart")
def wg_restart(
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    """Restart WireGuard: apply config, bring down, bring up."""
    try:
        wg_service.apply_config(db)
        try:
            wg_service.bring_down()
        except Exception:
            pass  # May already be down
        wg_service.bring_up()
        return {"message": "WireGuard restarted successfully"}
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"WireGuard not available: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restart WireGuard: {str(e)}",
        )


@router.get("/firewall", response_model=FirewallStatusResponse)
def get_firewall_status(
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    """Get the firewall enabled/disabled state. When disabled, all traffic is allowed."""
    cfg = db.query(ServerConfig).first()
    if not cfg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not initialised")
    return FirewallStatusResponse(firewall_enabled=cfg.firewall_enabled)


@router.patch("/firewall", response_model=FirewallStatusResponse)
def set_firewall_status(
    body: FirewallStatusUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    """Enable or disable the firewall. When disabled, all peers can reach all networks."""
    cfg = db.query(ServerConfig).first()
    if not cfg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not initialised")
    cfg.firewall_enabled = body.firewall_enabled
    db.commit()
    db.refresh(cfg)
    try:
        from app.services import iptables_service
        iptables_service.apply_iptables_rules(db)
    except Exception:
        pass
    return FirewallStatusResponse(firewall_enabled=cfg.firewall_enabled)


@router.get("/metrics", response_model=SystemMetricsResponse)
def get_metrics(_: User = Depends(require_password_changed)):
    """Return current host CPU, RAM and disk usage."""
    ram = psutil.virtual_memory()
    cpu_percent = psutil.cpu_percent(interval=0.2)
    disk = psutil.disk_usage("/")
    return SystemMetricsResponse(
        ram_percent=round(ram.percent, 1),
        ram_used_gb=round(ram.used / (1024 ** 3), 1),
        ram_total_gb=round(ram.total / (1024 ** 3), 1),
        cpu_percent=round(cpu_percent, 1),
        cpu_count=psutil.cpu_count(logical=True) or 1,
        disk_percent=round(disk.percent, 1),
        disk_used_gb=round(disk.used / (1024 ** 3), 1),
        disk_total_gb=round(disk.total / (1024 ** 3), 1),
    )


@router.get("/backup/export")
def export_backup(_: User = Depends(require_password_changed)):
    """Download database and .env as a zip backup file."""
    db_path = Path(settings.db_path)
    if not db_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Database file not found")
    
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"netloom_{ts}.zip"
    
    # Create ZIP in memory
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # Add database file
        with open(db_path, "rb") as f:
            zf.writestr("netloom.db", f.read())
        
        # Add .env file if it exists
        env_path = Path("./.env")
        if env_path.exists():
            with open(env_path, "r") as f:
                zf.writestr(".env", f.read())
        elif env_path.exists():
            with open(env_path, "r") as f:
                zf.writestr(".env", f.read())
    
    buffer.seek(0)
    return Response(
        content=buffer.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/backup/import")
def import_backup(
    file: UploadFile,
    _: User = Depends(require_password_changed),
):
    """Restore backup from uploaded zip file."""
    import tempfile
    import os
    
    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only .zip files are supported")
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
        content = file.file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        with zipfile.ZipFile(tmp_path, "r") as zf:
            # Extract database
            if "netloom.db" in zf.namelist():
                db_path = Path(settings.db_path)
                db_path.parent.mkdir(parents=True, exist_ok=True)
                with zf.open("netloom.db") as db_file:
                    with open(db_path, "wb") as out:
                        out.write(db_file.read())
            
            # Extract .env if present
            if ".env" in zf.namelist():
                with zf.open(".env") as env_file:
                    env_content = env_file.read().decode("utf-8")
                # Write to common locations
                for env_path in [Path("./.env"), Path("../.env")]:
                    try:
                        with open(env_path, "w") as f:
                            f.write(env_content)
                    except Exception:
                        pass
        
        return {"message": "Backup restored successfully"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Restore failed: {str(e)}")
    finally:
        os.unlink(tmp_path)


# ============================================================================
# TLS/HTTPS Configuration Endpoints
# ============================================================================

@router.get("/tls", response_model=TLSConfigResponse)
def get_tls_config(
    _: User = Depends(require_password_changed),
):
    """Get current TLS/HTTPS configuration."""
    from pathlib import Path as PathLib
    
    cert_path = PathLib(settings.tls_cert_path)
    key_path = PathLib(settings.tls_key_path)
    
    return TLSConfigResponse(
        tls_enabled=settings.tls_enabled,
        tls_cert_path=settings.tls_cert_path,
        tls_key_path=settings.tls_key_path,
        tls_host=settings.tls_host,
        tls_port=settings.tls_port,
        http_port=settings.http_port,
        tls_auto_generate=settings.tls_auto_generate,
        tls_cert_days=settings.tls_cert_days,
        tls_country=settings.tls_country,
        tls_state=settings.tls_state,
        tls_locality=settings.tls_locality,
        tls_organization=settings.tls_organization,
        tls_common_name=settings.tls_common_name,
        cert_exists=cert_path.exists(),
        key_exists=key_path.exists(),
    )


@router.put("/tls", response_model=TLSConfigResponse)
def update_tls_config(
    body: TLSConfigUpdate,
    _: User = Depends(require_password_changed),
):
    """
    Update TLS/HTTPS configuration.
    
    Note: Changes require a container restart to take effect.
    """
    from pathlib import Path as PathLib
    
    # Update settings in memory (will persist via env vars or config file)
    update_data = body.model_dump(exclude_none=True)
    for key, value in update_data.items():
        if hasattr(settings, key):
            setattr(settings, key, value)
    
    cert_path = PathLib(settings.tls_cert_path)
    key_path = PathLib(settings.tls_key_path)
    
    return TLSConfigResponse(
        tls_enabled=settings.tls_enabled,
        tls_cert_path=settings.tls_cert_path,
        tls_key_path=settings.tls_key_path,
        tls_host=settings.tls_host,
        tls_port=settings.tls_port,
        http_port=settings.http_port,
        tls_auto_generate=settings.tls_auto_generate,
        tls_cert_days=settings.tls_cert_days,
        tls_country=settings.tls_country,
        tls_state=settings.tls_state,
        tls_locality=settings.tls_locality,
        tls_organization=settings.tls_organization,
        tls_common_name=settings.tls_common_name,
        cert_exists=cert_path.exists(),
        key_exists=key_path.exists(),
    )


@router.post("/tls/regenerate-cert", response_model=TLSRegenerateCertResponse)
def regenerate_tls_cert(
    _: User = Depends(require_password_changed),
):
    """
    Regenerate self-signed TLS certificate.
    
    This will create a new self-signed certificate with the current settings.
    Requires container restart to take effect.
    """
    from app.utils.tls_cert_generator import generate_self_signed_cert
    
    try:
        cert_path, key_path = generate_self_signed_cert(
            cert_path=settings.tls_cert_path,
            key_path=settings.tls_key_path,
            country=settings.tls_country,
            state=settings.tls_state,
            locality=settings.tls_locality,
            organization=settings.tls_organization,
            common_name=settings.tls_common_name,
            days_valid=settings.tls_cert_days,
        )
        
        return TLSRegenerateCertResponse(
            message="TLS certificate regenerated successfully. Restart container to apply.",
            cert_path=cert_path,
            key_path=key_path,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to regenerate certificate: {str(e)}",
        )


# ============================================================================
# Active Directory Configuration Endpoints
# ============================================================================


@router.get("/ad", response_model=ADConfigResponse)
def get_ad_config(
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    """Get current Active Directory configuration."""
    cfg = db.query(ServerConfig).first()
    if not cfg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not initialised")

    return ADConfigResponse(
        ad_enabled=cfg.ad_enabled,
        ad_server=cfg.ad_server,
        ad_server_backup=cfg.ad_server_backup,
        ad_base_dn=cfg.ad_base_dn,
        ad_bind_dn=cfg.ad_bind_dn,
        ad_user_filter=cfg.ad_user_filter,
        ad_group_filter=cfg.ad_group_filter,
        ad_use_ssl=cfg.ad_use_ssl,
        ad_require_membership=cfg.ad_require_membership,
    )


@router.put("/ad", response_model=ADConfigResponse)
def update_ad_config(
    body: ADConfigUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    """Update Active Directory configuration."""
    cfg = db.query(ServerConfig).first()
    if not cfg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not initialised")

    update_data = body.model_dump(exclude_unset=True)

    password_value = update_data.pop("ad_bind_password", None)
    if password_value:
        from cryptography.fernet import Fernet
        import base64
        key_bytes = settings.secret_key.encode()[:32]
        key_bytes = key_bytes.ljust(32, b'0')
        key = base64.urlsafe_b64encode(key_bytes).decode()
        f = Fernet(key)
        cfg.ad_bind_password = f.encrypt(password_value.encode()).decode()

    for key, value in update_data.items():
        if hasattr(cfg, key):
            if value == "":
                value = None
            setattr(cfg, key, value)

    db.commit()
    db.refresh(cfg)

    return ADConfigResponse(
        ad_enabled=cfg.ad_enabled,
        ad_server=cfg.ad_server,
        ad_server_backup=cfg.ad_server_backup,
        ad_base_dn=cfg.ad_base_dn,
        ad_bind_dn=cfg.ad_bind_dn,
        ad_user_filter=cfg.ad_user_filter,
        ad_group_filter=cfg.ad_group_filter,
        ad_use_ssl=cfg.ad_use_ssl,
        ad_require_membership=cfg.ad_require_membership,
    )


@router.post("/ad/test-connection")
def test_ad_connection(
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    """Test connection to Active Directory server."""
    result = ad_service.test_ad_connection(db)
    return result


@router.get("/ad/groups", response_model=ADGroupsFromADResponse)
def get_ad_groups_from_server(
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    """Get list of groups from Active Directory server."""
    groups = ad_service.get_ad_groups(db)
    return ADGroupsFromADResponse(groups=groups)


@router.get("/ad/group-mappings", response_model=list[ADGroupMappingResponse])
def get_ad_group_mappings(
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    """Get all AD to NetLoom group mappings."""
    mappings = ad_mapping_service.get_ad_group_mappings(db)
    result = []
    for m in mappings:
        group_name = None
        group = db.query(PeerGroup).filter(PeerGroup.id == m.netloom_group_id).first()
        if group:
            group_name = group.name
        result.append(ADGroupMappingResponse(
            id=m.id,
            ad_group_dn=m.ad_group_dn,
            ad_group_name=m.ad_group_name,
            netloom_group_id=m.netloom_group_id,
            netloom_group_name=group_name,
            enabled=m.enabled,
            priority=m.priority,
        ))
    return result


@router.post("/ad/group-mappings", response_model=ADGroupMappingResponse)
def create_ad_group_mapping(
    body: ADGroupMappingCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    """Create a new AD to NetLoom group mapping."""
    group = db.query(PeerGroup).filter(PeerGroup.id == body.netloom_group_id).first()
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NetLoom group not found")

    mapping = ad_mapping_service.create_ad_group_mapping(
        db,
        ad_group_dn=body.ad_group_dn,
        ad_group_name=body.ad_group_name,
        netloom_group_id=body.netloom_group_id,
        enabled=body.enabled,
        priority=body.priority,
    )

    return ADGroupMappingResponse(
        id=mapping.id,
        ad_group_dn=mapping.ad_group_dn,
        ad_group_name=mapping.ad_group_name,
        netloom_group_id=mapping.netloom_group_id,
        netloom_group_name=group.name,
        enabled=mapping.enabled,
        priority=mapping.priority,
    )


@router.post("/ad/group-mappings/bulk", response_model=list[ADGroupMappingResponse])
def bulk_create_ad_group_mappings(
    body: ADGroupMappingBulkCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    """Create multiple AD to NetLoom group mappings at once."""
    mappings_data = [m.model_dump() for m in body.mappings]
    mappings = ad_mapping_service.bulk_create_ad_group_mappings(db, mappings_data)

    result = []
    for m in mappings:
        group_name = None
        group = db.query(PeerGroup).filter(PeerGroup.id == m.netloom_group_id).first()
        if group:
            group_name = group.name
        result.append(ADGroupMappingResponse(
            id=m.id,
            ad_group_dn=m.ad_group_dn,
            ad_group_name=m.ad_group_name,
            netloom_group_id=m.netloom_group_id,
            netloom_group_name=group_name,
            enabled=m.enabled,
            priority=m.priority,
        ))
    return result


@router.patch("/ad/group-mappings/{mapping_id}", response_model=ADGroupMappingResponse)
def update_ad_group_mapping(
    mapping_id: int,
    body: ADGroupMappingUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    """Update an existing AD to NetLoom group mapping."""
    if body.netloom_group_id:
        group = db.query(PeerGroup).filter(PeerGroup.id == body.netloom_group_id).first()
        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NetLoom group not found")

    mapping = ad_mapping_service.update_ad_group_mapping(
        db,
        mapping_id,
        netloom_group_id=body.netloom_group_id,
        enabled=body.enabled,
        priority=body.priority,
    )

    if not mapping:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mapping not found")

    group_name = None
    if mapping.netloom_group_id:
        group = db.query(PeerGroup).filter(PeerGroup.id == mapping.netloom_group_id).first()
        if group:
            group_name = group.name

    return ADGroupMappingResponse(
        id=mapping.id,
        ad_group_dn=mapping.ad_group_dn,
        ad_group_name=mapping.ad_group_name,
        netloom_group_id=mapping.netloom_group_id,
        netloom_group_name=group_name,
        enabled=mapping.enabled,
        priority=mapping.priority,
    )


@router.delete("/ad/group-mappings/{mapping_id}")
def delete_ad_group_mapping(
    mapping_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_password_changed),
):
    """Delete an AD to NetLoom group mapping."""
    success = ad_mapping_service.delete_ad_group_mapping(db, mapping_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mapping not found")
    return {"message": "Mapping deleted successfully"}
