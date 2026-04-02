import shutil
from datetime import datetime
from pathlib import Path

import psutil
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import require_password_changed
from app.models.server_config import ServerConfig
from app.models.user import User
from app.schemas.system import BackupResponse, FirewallStatusResponse, FirewallStatusUpdate, HealthResponse, RegenerateKeyResponse, ServerConfigResponse, ServerConfigUpdate, SystemMetricsResponse, TLSConfigResponse, TLSConfigUpdate, TLSRegenerateCertResponse
from app.services import wg_service
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

    return HealthResponse(
        status="ok" if db_status == "ok" else "degraded",
        db=db_status,
        wg_interface=wg_status,
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
    """Return current host CPU and RAM usage."""
    ram = psutil.virtual_memory()
    cpu_percent = psutil.cpu_percent(interval=0.2)
    return SystemMetricsResponse(
        ram_percent=round(ram.percent, 1),
        ram_used_gb=round(ram.used / (1024 ** 3), 1),
        ram_total_gb=round(ram.total / (1024 ** 3), 1),
        cpu_percent=round(cpu_percent, 1),
        cpu_count=psutil.cpu_count(logical=True) or 1,
    )


@router.get("/backup/export")
def export_backup(_: User = Depends(require_password_changed)):
    """Download the current database as a backup file."""
    db_path = Path(settings.db_path)
    if not db_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Database file not found")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"netloom_{ts}.db"
    with open(db_path, "rb") as f:
        content = f.read()
    return Response(
        content=content,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


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
