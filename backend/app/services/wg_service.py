"""
WireGuard Service
=================
All subprocess calls to the wg/wg-quick binaries are centralised here.
Uses 'wg syncconf' to apply config changes without dropping existing connections.
"""

import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import settings
from app.models.peer import Peer
from app.services.config_service import build_server_allowed_ips, generate_full_server_config


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

    # Build stripped config (no PostUp/PostDown — syncconf doesn't support them)
    stripped_lines = []
    for line in config_str.splitlines():
        stripped = line.strip()
        if not stripped.lower().startswith("postup") and not stripped.lower().startswith("postdown"):
            stripped_lines.append(line)
    stripped_config = "\n".join(stripped_lines)

    result = _run(
        ["wg", "syncconf", settings.wg_interface, "/dev/stdin"],
        input_data=stripped_config,
    )
    if result.returncode != 0:
        raise RuntimeError(f"wg syncconf failed: {result.stderr.strip()}")


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
    result = _run(["wg-quick", "up", settings.wg_interface])
    if result.returncode != 0:
        raise RuntimeError(f"wg-quick up failed: {result.stderr.strip()}")


def bring_down() -> None:
    result = _run(["wg-quick", "down", settings.wg_interface])
    if result.returncode != 0:
        raise RuntimeError(f"wg-quick down failed: {result.stderr.strip()}")


def is_interface_up() -> bool:
    result = _run(["wg", "show", settings.wg_interface])
    return result.returncode == 0
