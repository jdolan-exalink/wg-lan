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
    try:
        return subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError:
        return subprocess.CompletedProcess(cmd, returncode=127, stdout="", stderr=f"{cmd[0]}: command not found")


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
    # Remove blanket ACCEPT rules on wg_interface left by previous versions
    while True:
        result = _run(["iptables", "-D", "FORWARD", "-i", settings.wg_interface, "-j", "ACCEPT"])
        if result.returncode != 0:
            break
    while True:
        result = _run(["iptables", "-D", "FORWARD", "-o", settings.wg_interface, "-j", "ACCEPT"])
        if result.returncode != 0:
            break
    while True:
        result = _run(["iptables", "-D", "FORWARD", "-i", settings.wg_interface, "-o", settings.wg_interface, "-j", "DROP"])
        if result.returncode != 0:
            break
    # Remove any orphan blanket ACCEPT rules without interface restriction
    while True:
        result = _run(["iptables", "-D", "FORWARD", "-j", "ACCEPT"])
        if result.returncode != 0:
            break

    # Remove old NETLOOM-FWD chain links (all instances)
    while True:
        result = _run(["iptables", "-D", "FORWARD", "-j", FORWARD_CHAIN])
        if result.returncode != 0:
            break
    while True:
        result = _run(["iptables", "-t", "nat", "-D", "POSTROUTING", "-j", POSTROUTING_CHAIN])
        if result.returncode != 0:
            break
    
    # Remove ALL SNAT rules to our server IP from POSTROUTING (including stale ones)
    # We parse the rules and delete by line number to handle any source subnet
    result = _run(["iptables", "-t", "nat", "-S", "POSTROUTING"])
    if result.returncode == 0:
        # Collect line numbers of SNAT rules to our server IP (in reverse order)
        # Note: -S output includes the policy line (-P POSTROUTING ACCEPT) which is NOT a real rule
        # Real rules are -A lines, and their position in the -S output (0-indexed, skipping -P) matches iptables line numbers
        stale_lines = []
        rule_num = 0
        for line in result.stdout.strip().splitlines():
            if line.startswith("-P "):
                continue  # Skip policy line
            rule_num += 1
            if "SNAT" in line and f"--to-source {server_ip}" in line:
                stale_lines.append(rule_num)
        
        # Delete in reverse order so line numbers don't shift
        for line_num in reversed(stale_lines):
            _run(["iptables", "-t", "nat", "-D", "POSTROUTING", str(line_num)])
            logger.info(f"Removed stale SNAT rule at line {line_num}")

    while True:
        result = _run([
            "iptables", "-t", "nat", "-D", "POSTROUTING",
            "-s", settings.subnet,
            "-o", outbound_iface,
            "-j", "MASQUERADE",
        ])
        if result.returncode != 0:
            break
    
    # Flush and delete old chains
    try:
        _run(["iptables", "-F", FORWARD_CHAIN])
        _run(["iptables", "-X", FORWARD_CHAIN])
    except Exception:
        pass
    try:
        _run(["iptables", "-t", "nat", "-F", POSTROUTING_CHAIN])
        _run(["iptables", "-t", "nat", "-X", POSTROUTING_CHAIN])
    except Exception:
        pass
    
    # === FORWARD rules ===
    # Re-create NETLOOM-FWD and INSERT at position 1 so it runs BEFORE
    # any existing ACCEPT rules (Docker, conntrack, etc.)
    _run(["iptables", "-N", FORWARD_CHAIN])
    _run(["iptables", "-I", "FORWARD", "1", "-j", FORWARD_CHAIN])

    from app.models.server_config import ServerConfig
    from app.models.group import PeerGroupMember
    from app.services.policy_compiler import compile_allowed_cidrs

    server_cfg_fw = db.query(ServerConfig).first()
    firewall_on = server_cfg_fw.firewall_enabled if server_cfg_fw else False

    if firewall_on:
        # Allow established/related so return packets always flow back
        _run(["iptables", "-A", FORWARD_CHAIN,
              "-m", "conntrack", "--ctstate", "ESTABLISHED,RELATED",
              "-j", "ACCEPT"])

        # Per-peer enforcement for peers that belong to groups
        enforced: list[str] = []
        all_peers = db.query(Peer).filter(
            Peer.is_enabled == True,
            Peer.peer_type != "server",
        ).all()
        for peer in all_peers:
            peer_ip = peer.assigned_ip.split("/")[0]
            has_groups = db.query(PeerGroupMember).filter(
                PeerGroupMember.peer_id == peer.id
            ).first() is not None
            if not has_groups:
                continue  # no groups → covered by blanket ACCEPT below

            # Collect all source IPs/CIDRs for this peer:
            # - the WireGuard tunnel IP itself
            # - any LAN subnets behind a branch_office router
            source_cidrs: list[str] = [peer_ip]
            if peer.peer_type == "branch_office" and peer.remote_subnets:
                try:
                    import json as _json
                    source_cidrs.extend(_json.loads(peer.remote_subnets))
                except (ValueError, TypeError):
                    pass

            allowed = compile_allowed_cidrs(db, peer.id)

            for src in source_cidrs:
                for cidr in allowed:
                    _run(["iptables", "-A", FORWARD_CHAIN,
                          "-i", settings.wg_interface,
                          "-s", src, "-d", cidr,
                          "-j", "ACCEPT"])
                # DROP everything else from this source
                _run(["iptables", "-A", FORWARD_CHAIN,
                      "-i", settings.wg_interface,
                      "-s", src,
                      "-j", "DROP"])
                # Flush conntrack so existing sessions are cut immediately
                _run(["conntrack", "-D", "-s", src])

            enforced.append(f"{peer.name}({len(source_cidrs)} srcs, {len(allowed)} cidrs)")

        logger.info(f"Firewall ON — per-peer enforcement: {enforced}")

        logger.info(f"Firewall ON — per-peer enforcement: {enforced}")
    else:
        logger.info("Firewall OFF — blanket ACCEPT on wg0")

    # Blanket ACCEPT: covers peers without groups (they are wg0-ingress only)
    # Return traffic for allowed sessions is already handled by ESTABLISHED/RELATED rule 1.
    # NOTE: intentionally NOT adding "-o wg0 ACCEPT" — that would let any machine on the
    # local LAN bypass policy enforcement by going eth0 → wg0.
    _run(["iptables", "-A", FORWARD_CHAIN,
          "-i", settings.wg_interface, "-j", "ACCEPT"])

    
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

    _run([
        "iptables", "-t", "nat", "-A", "POSTROUTING",
        "-s", settings.subnet,
        "-o", outbound_iface,
        "-j", "MASQUERADE",
    ])
    logger.info(f"MASQUERADE rule: {settings.subnet} -> {outbound_iface}")
    
    # Log MASQUERADE rule
    connection_log_service.log_connection(
        db=db,
        event_type="iptables_applied",
        message=f"MASQUERADE: {settings.subnet} -> {outbound_iface}",
        severity="info",
        details={
            "rule_type": "MASQUERADE",
            "source": settings.subnet,
            "destination": outbound_iface,
            "action": "MASQUERADE",
            "purpose": "Outbound NAT"
        }
    )
    
    # Log FORWARD rules
    connection_log_service.log_connection(
        db=db,
        event_type="iptables_applied",
        message=f"FORWARD: wg0 traffic allowed",
        severity="info",
        details={
            "rule_type": "FORWARD",
            "rules": [
                {"action": "ALLOW", "in": "wg0", "out": "*", "purpose": "Allow wg0 routed traffic"},
                {"action": "ALLOW", "in": "*", "out": "wg0", "purpose": "Allow return traffic"}
            ]
        }
    )
    
    logger.info(f"iptables rules applied: {len(branch_subnets)} SNAT rules, FORWARD rules set")


def get_fwd_rules() -> list[dict]:
    """
    Parse NETLOOM-FWD chain and return structured rule list.
    Each rule has: target (ACCEPT/DROP), src, dst, and match fields.
    Skips the ESTABLISHED/RELATED catch-all rule (internal housekeeping).
    """
    result = _run(["iptables", "-L", FORWARD_CHAIN, "-n", "--line-numbers"])
    if result.returncode != 0:
        return []

    rules = []
    for line in result.stdout.splitlines():
        parts = line.split()
        # Lines with rules start with a number
        if not parts or not parts[0].isdigit():
            continue
        target = parts[1] if len(parts) > 1 else "?"
        # Skip the ESTABLISHED/RELATED bookkeeping rule
        if "ctstate" in line and "ESTABLISHED" in line:
            continue
        # Format without -v: num target prot opt src dst [extra]
        # Columns: 0=num 1=target 2=prot 3=opt 4=src 5=dst 6+=extra
        src = parts[4] if len(parts) > 4 else "?"
        dst = parts[5] if len(parts) > 5 else "?"
        extra = " ".join(parts[6:]) if len(parts) > 6 else ""
        rules.append({
            "target": target,   # ACCEPT | DROP
            "src": src,
            "dst": dst,
            "extra": extra,
        })
    return rules


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
