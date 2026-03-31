"""
Policy Compiler
===============
Compiles zones/groups/policies + peer_overrides into a concrete list of
allowed CIDRs for a given peer. This is the core business logic that
translates the declarative permission model into WireGuard AllowedIPs.

## Model: Allow-All by Default, Restrict via Groups

- **Peers without groups** → can reach ALL zones + ALL peer routes (allow-all)
- **Peers with groups** → can only reach what their group policies allow
- **Peer overrides** → always win (manual allow/deny per peer)

This means:
1. New peers start with full access (they're in the "All" group by default)
2. To restrict a peer: remove from "All", add to specific groups
3. Groups define what each peer can access via policies

Precedence (deny-first):
  1. deny_manual   (peer_overrides action='deny') — always wins
  2. allow_manual  (peer_overrides action='allow') — explicit peer-level allow
  3. deny_group    (policies action='deny' for any group the peer belongs to)
  4. allow_group   (policies action='allow' for any group the peer belongs to)
  5. allow_all     (default: if peer has NO groups, allow everything)

Additionally, compiles routes to other peers' remote_subnets (branch offices)
so that roadwarriors can reach LANs behind branch offices (NetMaker-style routing).
"""

import json
from sqlalchemy.orm import Session

from app.models.group import PeerGroupMember, Policy
from app.models.peer import Peer, PeerOverride
from app.models.zone import Zone, ZoneNetwork


def compile_allowed_cidrs(db: Session, peer_id: int) -> list[str]:
    """
    Return the list of CIDRs this peer is allowed to reach,
    based on group policies and peer-level overrides.
    
    If the peer has NO groups, returns ALL zone CIDRs (allow-all default).
    If the peer HAS groups, applies group policies with deny-first precedence.
    """
    # Step 1: Collect the peer's group IDs
    memberships = db.query(PeerGroupMember).filter(
        PeerGroupMember.peer_id == peer_id
    ).all()
    group_ids = [m.group_id for m in memberships]

    # Step 2: Collect peer-level overrides (always win)
    overrides = db.query(PeerOverride).filter(PeerOverride.peer_id == peer_id).all()
    override_allow_zones: set[int] = set()
    override_deny_zones: set[int] = set()

    for o in overrides:
        if o.action == "allow":
            override_allow_zones.add(o.zone_id)
        elif o.action == "deny":
            override_deny_zones.add(o.zone_id)

    # Step 3: If peer has NO groups and NO overrides → allow all zones
    if not group_ids and not override_allow_zones and not override_deny_zones:
        all_zones = db.query(ZoneNetwork).all()
        return sorted({zn.cidr for zn in all_zones})

    # Step 4: Collect group-level policies
    group_allow_zones: set[int] = set()
    group_deny_zones: set[int] = set()

    if group_ids:
        policies = db.query(Policy).filter(Policy.group_id.in_(group_ids)).all()
        for p in policies:
            if p.action == "allow":
                group_allow_zones.add(p.zone_id)
            elif p.action == "deny":
                group_deny_zones.add(p.zone_id)

    # Step 5: Apply precedence to determine final allowed zone IDs
    all_zone_ids = (
        group_allow_zones | group_deny_zones | override_allow_zones | override_deny_zones
    )

    allowed_zone_ids: set[int] = set()
    for zone_id in all_zone_ids:
        if zone_id in override_deny_zones:
            continue  # deny_manual wins
        if zone_id in override_allow_zones:
            allowed_zone_ids.add(zone_id)  # allow_manual
            continue
        if zone_id in group_deny_zones:
            continue  # deny_group
        if zone_id in group_allow_zones:
            allowed_zone_ids.add(zone_id)  # allow_group

    # Step 6: Resolve zone IDs to CIDRs
    if not allowed_zone_ids:
        return []

    zone_networks = (
        db.query(ZoneNetwork)
        .filter(ZoneNetwork.zone_id.in_(allowed_zone_ids))
        .all()
    )

    return sorted({zn.cidr for zn in zone_networks})


def compile_peer_routes(db: Session, peer_id: int) -> list[str]:
    """
    Return routes to other peers' networks that this peer should be able to reach.
    This enables NetMaker-style routing where roadwarriors can access LANs behind
    branch offices.
    
    For each enabled branch_office peer:
    - Include their remote_subnets (LANs behind the branch)
    - Include their VPN IP (for direct peer-to-peer via server)
    
    If the requesting peer has NO groups, include ALL branch routes.
    If the requesting peer HAS groups, only include routes for zones they can access.
    """
    # Get the requesting peer
    requesting_peer = db.query(Peer).filter(Peer.id == peer_id).first()
    if not requesting_peer:
        return []

    # Check if peer has any groups
    memberships = db.query(PeerGroupMember).filter(
        PeerGroupMember.peer_id == peer_id
    ).all()
    has_groups = len(memberships) > 0

    # Check for peer-level overrides
    overrides = db.query(PeerOverride).filter(PeerOverride.peer_id == peer_id).all()
    has_overrides = len(overrides) > 0

    # Get all enabled branch_office peers (excluding self)
    branch_peers = db.query(Peer).filter(
        Peer.peer_type == "branch_office",
        Peer.is_enabled == True,
        Peer.id != peer_id,
    ).all()

    # If peer has no groups and no overrides → allow all peer routes
    if not has_groups and not has_overrides:
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

    # If peer has groups → only include routes for zones they can access
    # For now, include all branch routes (zone-based filtering happens in compile_allowed_cidrs)
    # TODO: Add zone-based filtering for peer routes
    routes = set()
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
    Compile the complete AllowedIPs for a client config.
    Combines zone-based CIDRs + peer routes (branch office LANs).
    This is what goes into the client's [Peer] AllowedIPs directive.
    """
    zone_cidrs = compile_allowed_cidrs(db, peer_id)
    peer_routes_list = compile_peer_routes(db, peer_id)
    
    # Merge and deduplicate
    all_cidrs = set(zone_cidrs) | set(peer_routes_list)
    return sorted(all_cidrs)


def compile_override_summary(db: Session, peer_id: int) -> dict:
    """
    Return a summary of inherited vs manual permissions for display in the UI.
    Useful for the 'per-peer view' showing what's inherited and what's overridden.
    """
    memberships = db.query(PeerGroupMember).filter(
        PeerGroupMember.peer_id == peer_id
    ).all()
    group_ids = [m.group_id for m in memberships]

    group_policies: list[dict] = []
    if group_ids:
        policies = db.query(Policy).filter(Policy.group_id.in_(group_ids)).all()
        for p in policies:
            zone = db.query(Zone).filter(Zone.id == p.zone_id).first()
            group_policies.append({
                "zone_id": p.zone_id,
                "zone_name": zone.name if zone else str(p.zone_id),
                "action": p.action,
                "source": "group",
                "group_id": p.group_id,
            })

    overrides = db.query(PeerOverride).filter(PeerOverride.peer_id == peer_id).all()
    override_list: list[dict] = []
    for o in overrides:
        zone = db.query(Zone).filter(Zone.id == o.zone_id).first()
        override_list.append({
            "zone_id": o.zone_id,
            "zone_name": zone.name if zone else str(o.zone_id),
            "action": o.action,
            "source": "manual",
            "reason": o.reason,
        })

    final_cidrs = compile_allowed_cidrs(db, peer_id)

    return {
        "group_policies": group_policies,
        "overrides": override_list,
        "final_cidrs": final_cidrs,
    }
