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
- **IP Group Policies**: source group → specific IPs (not entire networks)

Precedence (deny-first):
  1. deny_override     (peer_overrides action='deny') — always wins
  2. deny_user         (user_network_access action='deny') — user-level deny
  3. deny_group        (group_network_access action='deny') — group-level deny
  4. deny_policy       (policies action='deny') — policy-level deny (group or ip-group)
  5. allow_user        (user_network_access action='allow') — user-level allow
  6. allow_group       (group_network_access action='allow') — group-level allow
  7. allow_manual      (peer_overrides action='allow', peer_network_access) — peer-level allow
  8. allow_policy      (policies action='allow') — policy-level allow (group or ip-group)
  9. allow_all         (default: if peer has NO groups/assignments/overrides, allow everything)
"""

import json
import logging
import ipaddress
from sqlalchemy.orm import Session

from app.models.group import PeerGroupMember, Policy, GroupNetworkAccess
from app.models.peer import Peer, PeerNetworkAccess, PeerOverride
from app.models.network import Network
from app.models.server_config import ServerConfig
from app.models.user import UserNetworkAccess
from app.models.ip_group import IpGroup, IpGroupEntry

logger = logging.getLogger(__name__)


def compile_allowed_cidrs(db: Session, peer_id: int, force_policies: bool = False) -> list[str]:
    """
    Return the list of CIDRs this peer is allowed to reach,
    based on group-to-group policies and peer-level overrides.

    When firewall is DISABLED (default), returns ALL networks for everyone.
    When firewall is ENABLED, applies group policies (deny-first precedence).
    Only policies with enabled=True are evaluated.
    
    force_policies: when True, ignores firewall_enabled and always applies policies
    """
    # Step 0: Check global firewall switch — when OFF, allow everything
    # But allow force_policies to override this
    config = db.query(ServerConfig).first()
    if config is not None and not config.firewall_enabled and not force_policies:
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

    # Step 2b: Collect user-level network assignments (if peer belongs to a user)
    peer = db.query(Peer).filter(Peer.id == peer_id).first()
    user_allow_networks: set[int] = set()
    user_deny_networks: set[int] = set()
    if peer and peer.user_id:
        user_assignments = db.query(UserNetworkAccess).filter(
            UserNetworkAccess.user_id == peer.user_id
        ).all()
        for ua in user_assignments:
            if ua.action == "allow":
                user_allow_networks.add(ua.network_id)
            elif ua.action == "deny":
                user_deny_networks.add(ua.network_id)

    # Step 2c: Collect group-level network assignments
    group_allow_networks: set[int] = set()
    group_deny_networks: set[int] = set()
    if group_ids:
        group_assignments = db.query(GroupNetworkAccess).filter(
            GroupNetworkAccess.group_id.in_(group_ids)
        ).all()
        for ga in group_assignments:
            if ga.action == "allow":
                group_allow_networks.add(ga.network_id)
            elif ga.action == "deny":
                group_deny_networks.add(ga.network_id)

    # Step 3: If peer has NO groups, NO user assignments, NO group assignments, and NO overrides → allow all networks
    if (
        not group_ids
        and not direct_allow_networks
        and not override_allow_networks
        and not override_deny_networks
        and not user_allow_networks
        and not user_deny_networks
        and not group_allow_networks
        and not group_deny_networks
    ):
        all_networks = db.query(Network).all()
        cidrs = sorted({n.subnet for n in all_networks})
        logger.info(f"Peer {peer_id}: ALLOW-ALL mode, CIDRs: {cidrs}")
        return cidrs

    # Step 4: Collect group-level policies
    allowed_network_ids: set[int] = set(direct_allow_networks)
    blocked_network_ids: set[int] = set()
    allowed_ips: set[str] = set()
    blocked_ips: set[str] = set()

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
            if p.dest_ip_group_id:
                # IP group policy: resolve to individual IPs
                ips = _get_ip_group_cidrs(db, p.dest_ip_group_id)
                if p.action == "allow":
                    allowed_ips.update(ips)
                elif p.action == "deny":
                    blocked_ips.update(ips)
            elif p.dest_group_id:
                dest_member_networks = _get_group_networks(db, p.dest_group_id)
                if p.action == "allow":
                    allowed_network_ids.update(dest_member_networks)
                elif p.action == "deny":
                    blocked_network_ids.update(dest_member_networks)
        
        for p in inbound_policies:
            if p.dest_ip_group_id:
                ips = _get_ip_group_cidrs(db, p.dest_ip_group_id)
                if p.action == "allow":
                    allowed_ips.update(ips)
                elif p.action == "deny":
                    blocked_ips.update(ips)
            elif p.dest_group_id:
                source_member_networks = _get_group_networks(db, p.source_group_id)
                if p.action == "allow":
                    allowed_network_ids.update(source_member_networks)
                elif p.action == "deny":
                    blocked_network_ids.update(source_member_networks)

    # Step 5: Apply precedence (deny-first)
    # Precedence: deny_user > deny_group > deny_policy > allow_user > allow_group > allow_policy > allow_manual
    manual_allow_networks = direct_allow_networks | override_allow_networks
    
    # Start with all network IDs that appear anywhere
    all_network_ids = (
        allowed_network_ids 
        | blocked_network_ids 
        | manual_allow_networks 
        | override_deny_networks
        | user_allow_networks
        | user_deny_networks
        | group_allow_networks
        | group_deny_networks
    )
    
    final_network_ids: set[int] = set()
    for network_id in all_network_ids:
        # Highest priority: explicit denies
        if network_id in override_deny_networks:
            continue  # peer-level deny always wins
        if network_id in user_deny_networks:
            continue  # user-level deny wins
        if network_id in group_deny_networks:
            continue  # group-level deny wins
        if network_id in blocked_network_ids:
            continue  # policy-level deny
        
        # Explicit allows (in precedence order)
        if network_id in user_allow_networks:
            final_network_ids.add(network_id)  # user-level allow
            continue
        if network_id in group_allow_networks:
            final_network_ids.add(network_id)  # group-level allow
            continue
        if network_id in manual_allow_networks:
            final_network_ids.add(network_id)  # peer-level manual allow
            continue
        if network_id in allowed_network_ids:
            final_network_ids.add(network_id)  # policy-level allow

    # Resolve network IDs to CIDRs
    final_cidrs: set[str] = set()
    if final_network_ids:
        networks = db.query(Network).filter(Network.id.in_(final_network_ids)).all()
        final_cidrs.update(n.subnet for n in networks)

    # Apply IP-level denies: remove any /32 that is blocked
    # Apply IP-level allows: add /32 CIDRs that are not blocked
    for ip in allowed_ips:
        if ip not in blocked_ips:
            final_cidrs.add(ip)

    if not final_network_ids and not allowed_ips:
        peer = db.query(Peer).filter(Peer.id == peer_id).first()
        peer_name = peer.name if peer else f"peer-{peer_id}"
        logger.warning(f"Peer {peer_name} ({peer_id}): BLOCKED - no networks allowed (groups: {group_ids})")
        return []

    cidrs = sorted(final_cidrs)
    
    peer = db.query(Peer).filter(Peer.id == peer_id).first()
    peer_name = peer.name if peer else f"peer-{peer_id}"
    
    logger.info(f"Peer {peer_name} ({peer_id}): ALLOWED networks: {cidrs}")
    if blocked_network_ids:
        blocked_nets = db.query(Network).filter(Network.id.in_(blocked_network_ids)).all()
        logger.warning(f"Peer {peer_name} ({peer_id}): BLOCKED networks: {[(n.name, n.subnet) for n in blocked_nets]}")
    if blocked_ips:
        logger.warning(f"Peer {peer_name} ({peer_id}): BLOCKED IPs: {blocked_ips}")
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


def _get_ip_group_cidrs(db: Session, ip_group_id: int) -> set[str]:
    """Get all individual IP addresses from an IP group as /32 CIDRs."""
    entries = db.query(IpGroupEntry).filter(
        IpGroupEntry.ip_group_id == ip_group_id
    ).all()
    return {f"{e.ip_address}/32" for e in entries}


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
    If tunnel_mode is 'full', returns all networks (0.0.0.0/0, ::/0).
    If tunnel_mode is 'split', returns only VPN subnet and allowed networks via policies.
    Always respects tunnel_mode regardless of firewall state.
    """
    from app.models.peer import Peer
    
    peer = db.query(Peer).filter(Peer.id == peer_id).first()
    if not peer:
        return []
    
    # Full tunnel: allow everything
    if peer.tunnel_mode == "full":
        return ["0.0.0.0/0", "::/0"]
    
    # Split tunnel: always use policy-based allowed networks
    # Do NOT use the firewall-disabled shortcut - always respect policies
    allowed_cidrs = compile_allowed_cidrs(db, peer_id, force_policies=True)
    
    # Always include VPN subnet
    from app.config import settings
    vpn_subnet = settings.subnet
    if vpn_subnet not in allowed_cidrs:
        allowed_cidrs.append(vpn_subnet)
    
    return sorted(allowed_cidrs)


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
