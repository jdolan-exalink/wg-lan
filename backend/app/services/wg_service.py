"""
WireGuard Service
=================
All subprocess calls to the wg/wg-quick binaries are centralised here.
Uses 'wg syncconf' to apply config changes without dropping existing connections.
"""

import json
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import settings
from app.models.peer import Peer
from app.services.config_service import build_server_allowed_ips, generate_full_server_config
from app.services import connection_log_service


ONLINE_THRESHOLD_SECONDS = 180


@dataclass
class PeerStatus:
    public_key: str
    endpoint: str | None
    last_handshake: int  # epoch seconds, 0 = never
    rx_bytes: int
    tx_bytes: int
    is_online: bool


def _run(cmd: list[str], input_data: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        input=input_data,
        capture_output=True,
        text=True,
    )


def apply_config(db: Session) -> None:
    """
    Regenerate wg0.conf from DB state and apply via wg syncconf.
    Does not drop existing connections.

    Note: wg syncconf only accepts native wg directives (PrivateKey, ListenPort,
    PublicKey, AllowedIPs, PresharedKey, PersistentKeepalive). wg-quick directives
    like Address, DNS, MTU, PostUp, PostDown must be stripped.

    If the interface doesn't exist yet, uses wg-quick up to create it first.
    """
    from app.models.server_config import ServerConfig

    server_cfg = db.query(ServerConfig).first()
    if not server_cfg:
        return

    peers = db.query(Peer).filter(Peer.is_enabled == True).all()
    peer_pairs = [(p, build_server_allowed_ips(p)) for p in peers]

    config_str = generate_full_server_config(server_cfg, peer_pairs)
    config_path = Path(settings.wg_config_file)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(config_str)

    # Build stripped config for wg syncconf — only native wg directives allowed
    # wg-quick directives: Address, DNS, MTU, PostUp, PostDown
    wg_quick_directives = {"address", "dns", "mtu", "postup", "postdown"}
    stripped_lines = []
    in_interface = True
    for line in config_str.splitlines():
        stripped = line.strip()
        if stripped.lower() == "[peer]":
            in_interface = False
            stripped_lines.append(line)
            continue
        if in_interface:
            key = stripped.split("=")[0].strip().lower() if "=" in stripped else ""
            if key in wg_quick_directives:
                continue
        stripped_lines.append(line)
    stripped_config = "\n".join(stripped_lines)

    # If interface doesn't exist, create it with wg-quick up first
    if not is_interface_up():
        start_time = time.time()
        result = _run(["wg-quick", "up", settings.wg_interface])
        duration_ms = int((time.time() - start_time) * 1000)
        if result.returncode != 0:
            connection_log_service.log_connection(
                db=db,
                event_type="interface_up",
                message=f"Failed to bring up WireGuard interface: {result.stderr.strip()}",
                severity="critical",
                details={"stderr": result.stderr.strip(), "returncode": result.returncode},
                duration_ms=duration_ms,
            )
            raise RuntimeError(f"wg-quick up failed: {result.stderr.strip()}")
        connection_log_service.log_connection(
            db=db,
            event_type="interface_up",
            message="WireGuard interface brought up successfully",
            severity="info",
            duration_ms=duration_ms,
        )

    start_time = time.time()
    result = _run(
        ["wg", "syncconf", settings.wg_interface, "/dev/stdin"],
        input_data=stripped_config,
    )
    duration_ms = int((time.time() - start_time) * 1000)
    if result.returncode != 0:
        connection_log_service.log_connection(
            db=db,
            event_type="config_applied",
            message=f"Failed to apply WireGuard config: {result.stderr.strip()}",
            severity="error",
            details={"stderr": result.stderr.strip(), "returncode": result.returncode},
            duration_ms=duration_ms,
        )
        raise RuntimeError(f"wg syncconf failed: {result.stderr.strip()}")
    
    connection_log_service.log_connection(
        db=db,
        event_type="config_applied",
        message=f"WireGuard config applied successfully ({len(peers)} peers)",
        severity="info",
        details={"peer_count": len(peers)},
        duration_ms=duration_ms,
    )


def ensure_interface_up(db: Session) -> None:
    """Ensure WireGuard interface is up. Creates it if needed, applies config."""
    if is_interface_up():
        return
    apply_config(db)


def get_peer_statuses(interface: str = "") -> dict[str, PeerStatus]:
    """
    Run 'wg show all dump' and parse peer status.
    Returns a dict keyed by public_key.
    """
    iface = interface or settings.wg_interface
    result = _run(["wg", "show", iface, "dump"])
    if result.returncode != 0:
        return {}

    statuses: dict[str, PeerStatus] = {}
    lines = result.stdout.strip().splitlines()

    # First line is the interface line — skip it
    for line in lines[1:]:
        parts = line.split("\t")
        if len(parts) < 8:
            continue
        public_key = parts[0]
        endpoint = parts[2] if parts[2] != "(none)" else None
        last_handshake = int(parts[4]) if parts[4].isdigit() else 0
        rx_bytes = int(parts[5]) if parts[5].isdigit() else 0
        tx_bytes = int(parts[6]) if parts[6].isdigit() else 0

        now = int(datetime.now(timezone.utc).timestamp())
        is_online = (
            last_handshake > 0
            and (now - last_handshake) < ONLINE_THRESHOLD_SECONDS
        )

        statuses[public_key] = PeerStatus(
            public_key=public_key,
            endpoint=endpoint,
            last_handshake=last_handshake,
            rx_bytes=rx_bytes,
            tx_bytes=tx_bytes,
            is_online=is_online,
        )

    return statuses


def bring_up() -> None:
    start_time = time.time()
    result = _run(["wg-quick", "up", settings.wg_interface])
    duration_ms = int((time.time() - start_time) * 1000)
    if result.returncode != 0:
        raise RuntimeError(f"wg-quick up failed: {result.stderr.strip()}")


def bring_down() -> None:
    start_time = time.time()
    result = _run(["wg-quick", "down", settings.wg_interface])
    duration_ms = int((time.time() - start_time) * 1000)
    if result.returncode != 0:
        raise RuntimeError(f"wg-quick down failed: {result.stderr.strip()}")


def is_interface_up() -> bool:
    result = _run(["wg", "show", settings.wg_interface])
    return result.returncode == 0
