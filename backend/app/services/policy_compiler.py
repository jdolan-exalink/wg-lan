"""
Policy Compiler v2
==================
Compiles groups/policies into a concrete list of allowed CIDRs for a given peer.

## New Model: Group-to-Group Policies

- **Peers without groups** → can reach ALL networks (allow-all default)
- **Peers with groups** → can only reach what their group policies allow
- **Policies** define access between groups with direction control:
  - `outbound`: source group can reach dest group's networks
  - `inbound`: dest group can reach source group's networks
  - `both`: bidirectional access

Precedence (deny-first):
  1. deny_manual   (peer_overrides action='deny') — always wins
  2. allow_manual  (peer_overrides action='allow') — explicit peer-level allow
  3. deny_group    (policies action='deny' for any group the peer belongs to)
  4. allow_group   (policies action='allow' for any group the peer belongs to)
  5. allow_all     (default: if peer has NO groups, allow everything)
"""

import json
import logging
import ipaddress
from sqlalchemy.orm import Session

from app.models.group import PeerGroupMember, Policy
from app.models.peer import Peer, PeerNetworkAccess, PeerOverride
from app.models.network import Network
from app.models.server_config import ServerConfig

logger = logging.getLogger(__name__)


def compile_allowed_cidrs(db: Session, peer_id: int) -> list[str]:
    """
    Return the list of CIDRs this peer is allowed to reach,
    based on group-to-group policies and peer-level overrides.

    When firewall is DISABLED (default), returns ALL networks for everyone.
    When firewall is ENABLED, applies group policies (deny-first precedence).
    Only policies with enabled=True are evaluated.
    """
    # Step 0: Check global firewall switch — when OFF, allow everything
    config = db.query(ServerConfig).first()
    if config is not None and not config.firewall_enabled:
        all_networks = db.query(Network).all()
        cidrs = sorted({n.subnet for n in all_networks})
        logger.info(f"Peer {peer_id}: firewall disabled — ALLOW-ALL, CIDRs: {cidrs}")
        return cidrs

    # Step 1: Collect the peer's group IDs
    memberships = db.query(PeerGroupMember).filter(
        PeerGroupMember.peer_id == peer_id
    ).all()
    group_ids = [m.group_id for m in memberships]

    # Step 2: Collect peer-level overrides (always win)
    overrides = db.query(PeerOverride).filter(PeerOverride.peer_id == peer_id).all()
    direct_allow_networks = {
        row[0]
        for row in db.query(PeerNetworkAccess.network_id).filter(
            PeerNetworkAccess.peer_id == peer_id
        ).all()
    }
    override_allow_networks: set[int] = set()
    override_deny_networks: set[int] = set()

    for o in overrides:
        if o.action == "allow":
            override_allow_networks.add(o.network_id)
        elif o.action == "deny":
            override_deny_networks.add(o.network_id)

    # Step 3: If peer has NO groups and NO overrides → allow all networks
    if (
        not group_ids
        and not direct_allow_networks
        and not override_allow_networks
        and not override_deny_networks
    ):
        all_networks = db.query(Network).all()
        cidrs = sorted({n.subnet for n in all_networks})
        logger.info(f"Peer {peer_id}: ALLOW-ALL mode, CIDRs: {cidrs}")
        return cidrs

    # Step 4: Collect group-level policies
    allowed_network_ids: set[int] = set(direct_allow_networks)
    blocked_network_ids: set[int] = set()

    if group_ids:
        # Outbound policies: peer's group can reach dest group's networks
        outbound_policies = db.query(Policy).filter(
            Policy.source_group_id.in_(group_ids),
            Policy.direction.in_(["outbound", "both"]),
            Policy.enabled == True,
        ).all()

        # Inbound policies: dest group can reach peer's group's networks
        inbound_policies = db.query(Policy).filter(
            Policy.dest_group_id.in_(group_ids),
            Policy.direction.in_(["inbound", "both"]),
            Policy.enabled == True,
        ).all()
        
        for p in outbound_policies:
            dest_member_networks = _get_group_networks(db, p.dest_group_id)
            if p.action == "allow":
                allowed_network_ids.update(dest_member_networks)
            elif p.action == "deny":
                blocked_network_ids.update(dest_member_networks)
        
        for p in inbound_policies:
            source_member_networks = _get_group_networks(db, p.source_group_id)
            if p.action == "allow":
                allowed_network_ids.update(source_member_networks)
            elif p.action == "deny":
                blocked_network_ids.update(source_member_networks)

    # Step 5: Apply precedence
    manual_allow_networks = direct_allow_networks | override_allow_networks
    all_network_ids = allowed_network_ids | blocked_network_ids | manual_allow_networks | override_deny_networks
    
    final_network_ids: set[int] = set()
    for network_id in all_network_ids:
        if network_id in override_deny_networks:
            continue
        if network_id in manual_allow_networks:
            final_network_ids.add(network_id)
            continue
        if network_id in blocked_network_ids:
            continue
        if network_id in allowed_network_ids:
            final_network_ids.add(network_id)

    # Step 6: Resolve network IDs to CIDRs
    if not final_network_ids:
        peer = db.query(Peer).filter(Peer.id == peer_id).first()
        peer_name = peer.name if peer else f"peer-{peer_id}"
        logger.warning(f"Peer {peer_name} ({peer_id}): BLOCKED - no networks allowed (groups: {group_ids})")
        return []

    networks = db.query(Network).filter(Network.id.in_(final_network_ids)).all()
    cidrs = sorted({n.subnet for n in networks})
    
    peer = db.query(Peer).filter(Peer.id == peer_id).first()
    peer_name = peer.name if peer else f"peer-{peer_id}"
    
    logger.info(f"Peer {peer_name} ({peer_id}): ALLOWED networks: {[(n.name, n.subnet) for n in networks]}")
    if blocked_network_ids:
        blocked_nets = db.query(Network).filter(Network.id.in_(blocked_network_ids)).all()
        logger.warning(f"Peer {peer_name} ({peer_id}): BLOCKED networks: {[(n.name, n.subnet) for n in blocked_nets]}")
    logger.info(f"Peer {peer_name} ({peer_id}): Final CIDRs: {cidrs}")
    
    return cidrs


def _get_group_networks(db: Session, group_id: int) -> set[int]:
    """Get all network IDs associated with a group's members, plus networks with no owner."""
    member_peer_ids = db.query(PeerGroupMember.peer_id).filter(
        PeerGroupMember.group_id == group_id
    ).all()
    member_peer_ids = [row[0] for row in member_peer_ids]
    
    network_ids: set[int] = set()
    
    if member_peer_ids:
        owned = db.query(Network.id).filter(
            Network.peer_id.in_(member_peer_ids)
        ).all()
        network_ids.update(row[0] for row in owned)
    
    orphaned = db.query(Network.id).filter(
        Network.peer_id.is_(None)
    ).all()
    network_ids.update(row[0] for row in orphaned)
    
    return network_ids


def compile_peer_routes(db: Session, peer_id: int) -> list[str]:
    """
    Return routes to all other branch-office peers' networks.
    Policy enforcement is done server-side via iptables, so the client
    config always receives the full set of routes.
    """
    branch_peers = db.query(Peer).filter(
        Peer.peer_type == "branch_office",
        Peer.is_enabled == True,
        Peer.id != peer_id,
    ).all()

    routes: set[str] = set()
    for branch in branch_peers:
        vpn_ip = branch.assigned_ip.split("/")[0]
        routes.add(f"{vpn_ip}/32")
        if branch.remote_subnets:
            try:
                subnets = json.loads(branch.remote_subnets)
                for subnet in subnets:
                    routes.add(subnet)
            except (json.JSONDecodeError, TypeError):
                pass

    return sorted(routes)


def compile_client_allowed_ips(db: Session, peer_id: int) -> list[str]:
    """
    Compile AllowedIPs for a client config.
    Always returns ALL networks + ALL branch routes + VPN subnet.
    Policy enforcement is done server-side via iptables, so the client
    config never needs to be re-downloaded when policies change.
    """
    from app.config import settings
    from app.models.network import Network

    vpn_subnet = settings.subnet

    # All known networks (LAN + VPN)
    all_networks = db.query(Network).all()
    network_cidrs = {n.subnet for n in all_networks}

    # All branch-office routes (VPN IPs + remote subnets)
    peer_routes_list = compile_peer_routes(db, peer_id)

    all_cidrs = {vpn_subnet} | network_cidrs | set(peer_routes_list)
    cleaned_cidrs = _remove_redundant_cidrs(all_cidrs)

    return sorted(cleaned_cidrs)


def _remove_redundant_cidrs(cidrs: set[str]) -> set[str]:
    """Remove CIDRs that are already contained within larger CIDRs."""
    networks = []
    for cidr in cidrs:
        try:
            networks.append(ipaddress.ip_network(cidr, strict=False))
        except ValueError:
            pass
    
    networks.sort(key=lambda n: n.prefixlen)
    
    result = set()
    for net in networks:
        is_redundant = False
        for existing in result:
            if net.subnet_of(existing):
                is_redundant = True
                break
        
        if not is_redundant:
            result.add(net)
    
    return {str(net) for net in result}


def _cidr_overlaps_with_allowed(cidr: str, allowed_cidrs: set[str]) -> bool:
    """Check if a CIDR overlaps with any of the allowed CIDRs."""
    if not allowed_cidrs:
        return False
    
    try:
        target = ipaddress.ip_network(cidr, strict=False)
        for allowed in allowed_cidrs:
            allowed_net = ipaddress.ip_network(allowed, strict=False)
            if target.overlaps(allowed_net):
                return True
    except ValueError:
        return cidr in allowed_cidrs
    
    return False


def compile_override_summary(db: Session, peer_id: int) -> dict:
    """
    Return a summary of a peer's permissions:
    - group_policies: list of policy-derived access entries
    - overrides: list of peer-level override entries
    - final_cidrs: the final allowed CIDRs after compilation
    """
    from app.models.group import PeerGroupMember
    from app.models.network import Network
    
    # Get peer's groups
    memberships = db.query(PeerGroupMember).filter(
        PeerGroupMember.peer_id == peer_id
    ).all()
    group_ids = [m.group_id for m in memberships]
    
    # Get group policies
    group_policies = []
    if group_ids:
        from app.models.group import Policy
        policies = db.query(Policy).filter(
            (Policy.source_group_id.in_(group_ids)) |
            (Policy.dest_group_id.in_(group_ids))
        ).all()
        for p in policies:
            source_group = db.query(PeerGroupMember).filter(
                PeerGroupMember.group_id == p.source_group_id
            ).first()
            dest_group = db.query(PeerGroupMember).filter(
                PeerGroupMember.group_id == p.dest_group_id
            ).first()
            group_policies.append({
                "source_group_id": p.source_group_id,
                "dest_group_id": p.dest_group_id,
                "action": p.action,
                "direction": p.direction,
            })
    
    # Get peer overrides
    overrides = db.query(PeerOverride).filter(PeerOverride.peer_id == peer_id).all()
    override_list = []
    for o in overrides:
        network = db.query(Network).filter(Network.id == o.network_id).first()
        override_list.append({
            "network_id": o.network_id,
            "network_name": network.name if network else f"network-{o.network_id}",
            "subnet": network.subnet if network else "unknown",
            "action": o.action,
        })
    
    # Get final CIDRs
    final_cidrs = compile_allowed_cidrs(db, peer_id)
    
    return {
        "group_policies": group_policies,
        "overrides": override_list,
        "final_cidrs": final_cidrs,
    }
