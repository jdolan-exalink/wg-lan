"""
iptables Service
================
Manages iptables rules dynamically based on current WireGuard state.
Rules are recalculated whenever peers, zones, or networks change.

Rules managed:
- FORWARD: Allow wg0 traffic, block peer-to-peer
- POSTROUTING: MASQUERADE for outbound, SNAT for branch office return traffic
"""

import subprocess
import logging
import json
from sqlalchemy.orm import Session

from app.config import settings
from app.models.peer import Peer
from app.services import connection_log_service

logger = logging.getLogger(__name__)

# Chain names for NetLoom rules
FORWARD_CHAIN = "NETLOOM-FWD"
POSTROUTING_CHAIN = "NETLOOM-POST"


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True)


def _get_outbound_interface() -> str:
    """Detect the default outbound interface."""
    result = _run(["ip", "route", "get", "1.1.1.1"])
    if result.returncode == 0:
        for part in result.stdout.split():
            if part == "dev":
                idx = result.stdout.split().index("dev")
                parts = result.stdout.split()
                if idx + 1 < len(parts):
                    return parts[idx + 1]
    return "eth0"


def _get_server_ip(iface: str) -> str | None:
    """Get the primary IPv4 address of an interface."""
    result = _run(["ip", "-4", "addr", "show", iface])
    if result.returncode == 0:
        for line in result.stdout.splitlines():
            line = line.strip()
            if line.startswith("inet "):
                # Format: inet 192.168.70.165/23 brd ...
                return line.split()[1].split("/")[0]
    return None


def _ensure_chains():
    """Create custom chains if they don't exist."""
    # Create FORWARD chain
    _run(["iptables", "-N", FORWARD_CHAIN])
    # Create POSTROUTING chain
    _run(["iptables", "-t", "nat", "-N", POSTROUTING_CHAIN])
    
    # Link chains to main chains (idempotent - check first)
    result = _run(["iptables", "-C", "FORWARD", "-j", FORWARD_CHAIN])
    if result.returncode != 0:
        _run(["iptables", "-A", "FORWARD", "-j", FORWARD_CHAIN])
    
    result = _run(["iptables", "-t", "nat", "-C", "POSTROUTING", "-j", POSTROUTING_CHAIN])
    if result.returncode != 0:
        _run(["iptables", "-t", "nat", "-A", "POSTROUTING", "-j", POSTROUTING_CHAIN])


def _flush_chains():
    """Flush all rules from custom chains."""
    _run(["iptables", "-F", FORWARD_CHAIN])
    _run(["iptables", "-t", "nat", "-F", POSTROUTING_CHAIN])


def apply_iptables_rules(db: Session) -> None:
    """
    Apply dynamic iptables rules based on current WireGuard state.
    
    This function:
    1. Detects outbound interface and server IP
    2. Collects all branch office remote_subnets
    3. Applies FORWARD rules (allow wg0, block peer-to-peer)
    4. Applies POSTROUTING rules (SNAT for branch offices BEFORE MASQUERADE)
    
    Called automatically after apply_config() in wg_service.
    
    IMPORTANT: SNAT rules must come BEFORE MASQUERADE in the POSTROUTING chain.
    Otherwise MASQUERADE changes the source IP first and SNAT never matches.
    """
    logger.info("Applying dynamic iptables rules...")
    
    # Detect network configuration
    outbound_iface = _get_outbound_interface()
    server_ip = _get_server_ip(outbound_iface)
    
    if not server_ip:
        logger.warning(f"Could not detect server IP on {outbound_iface}, skipping iptables")
        return
    
    logger.info(f"Outbound interface: {outbound_iface}, Server IP: {server_ip}")
    
    # Collect all branch office remote_subnets
    branch_peers = db.query(Peer).filter(
        Peer.peer_type == "branch_office",
        Peer.is_enabled == True,
    ).all()
    
    branch_subnets: list[str] = []
    for peer in branch_peers:
        if peer.remote_subnets:
            import json
            try:
                subnets = json.loads(peer.remote_subnets)
                branch_subnets.extend(subnets)
            except (json.JSONDecodeError, TypeError):
                logger.warning(f"Invalid remote_subnets for peer {peer.name}: {peer.remote_subnets}")
    
    logger.info(f"Branch office subnets: {branch_subnets}")
    
    # === Clean up old rules ===
    # Remove old NetLoom chain links
    _run(["iptables", "-D", "FORWARD", "-j", FORWARD_CHAIN])
    _run(["iptables", "-t", "nat", "-D", "POSTROUTING", "-j", POSTROUTING_CHAIN])
    
    # Flush and delete old chains
    _run(["iptables", "-F", FORWARD_CHAIN])
    _run(["iptables", "-X", FORWARD_CHAIN])
    _run(["iptables", "-t", "nat", "-F", POSTROUTING_CHAIN])
    _run(["iptables", "-t", "nat", "-X", POSTROUTING_CHAIN])
    
    # === FORWARD rules ===
    # Allow traffic from wg0 to external networks
    _run(["iptables", "-A", "FORWARD", "-i", settings.wg_interface, "-j", "ACCEPT"])
    # Allow return traffic from external networks to wg0
    _run(["iptables", "-A", "FORWARD", "-o", settings.wg_interface, "-j", "ACCEPT"])
    # Block direct peer-to-peer traffic (isolation)
    _run(["iptables", "-A", "FORWARD", "-i", settings.wg_interface, "-o", settings.wg_interface, "-j", "DROP"])
    
    # === POSTROUTING rules ===
    # IMPORTANT: Insert SNAT rules at the TOP of POSTROUTING (before any MASQUERADE)
    # This ensures branch office traffic gets SNAT'd before MASQUERADE can change the source
    for subnet in branch_subnets:
        _run([
            "iptables", "-t", "nat", "-I", "POSTROUTING", "1",
            "-s", subnet,
            "-o", outbound_iface,
            "-j", "SNAT", "--to-source", server_ip
        ])
        logger.info(f"🟢 SNAT rule: {subnet} -> {server_ip} (return traffic routing)")
        
        # Log to database for UI display
        connection_log_service.log_connection(
            db=db,
            event_type="iptables_applied",
            message=f"SNAT: {subnet} -> {server_ip}",
            severity="info",
            details={
                "rule_type": "SNAT",
                "source": subnet,
                "destination": outbound_iface,
                "action": f"to:{server_ip}",
                "purpose": "Return traffic routing for branch office"
            }
        )
    
    # Log MASQUERADE rule
    connection_log_service.log_connection(
        db=db,
        event_type="iptables_applied",
        message=f"MASQUERADE on {outbound_iface}",
        severity="info",
        details={
            "rule_type": "MASQUERADE",
            "source": "0.0.0.0/0",
            "destination": outbound_iface,
            "action": "MASQUERADE",
            "purpose": "Outbound NAT"
        }
    )
    
    # Log FORWARD rules
    connection_log_service.log_connection(
        db=db,
        event_type="iptables_applied",
        message=f"FORWARD: wg0 traffic allowed, peer-to-peer blocked",
        severity="info",
        details={
            "rule_type": "FORWARD",
            "rules": [
                {"action": "ALLOW", "in": "wg0", "out": "*", "purpose": "Allow wg0 to external"},
                {"action": "ALLOW", "in": "*", "out": "wg0", "purpose": "Allow return traffic"},
                {"action": "BLOCK", "in": "wg0", "out": "wg0", "purpose": "Block peer-to-peer"}
            ]
        }
    )
    
    logger.info(f"iptables rules applied: {len(branch_subnets)} SNAT rules, FORWARD rules set")


def reset_iptables_rules() -> None:
    """Remove all NetLoom iptables rules."""
    logger.info("Resetting iptables rules...")
    
    # Remove chain links
    _run(["iptables", "-D", "FORWARD", "-j", FORWARD_CHAIN])
    _run(["iptables", "-t", "nat", "-D", "POSTROUTING", "-j", POSTROUTING_CHAIN])
    
    # Flush and delete chains
    _run(["iptables", "-F", FORWARD_CHAIN])
    _run(["iptables", "-X", FORWARD_CHAIN])
    _run(["iptables", "-t", "nat", "-F", POSTROUTING_CHAIN])
    _run(["iptables", "-t", "nat", "-X", POSTROUTING_CHAIN])
    
    logger.info("iptables rules reset")
