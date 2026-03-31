"""
Policy Compiler
===============
Compiles zones/groups/policies + peer_overrides into a concrete list of
allowed CIDRs for a given peer. This is the core business logic that
translates the declarative permission model into WireGuard AllowedIPs.

Precedence (deny-first):
  1. deny_manual   (peer_overrides action='deny')
  2. allow_manual  (peer_overrides action='allow')
  3. deny_group    (policies action='deny' for any group the peer belongs to)
  4. allow_group   (policies action='allow' for any group the peer belongs to)
  5. no access     (default: deny if no matching rule)
"""

from sqlalchemy.orm import Session

from app.models.group import PeerGroupMember, Policy
from app.models.peer import PeerOverride
from app.models.zone import Zone, ZoneNetwork


def compile_allowed_cidrs(db: Session, peer_id: int) -> list[str]:
    """
    Return the list of CIDRs this peer is allowed to reach,
    based on group policies and peer-level overrides.
    """
    # Step 1: Collect the peer's group IDs
    memberships = db.query(PeerGroupMember).filter(
        PeerGroupMember.peer_id == peer_id
    ).all()
    group_ids = [m.group_id for m in memberships]

    # Step 2: Collect group-level policies: zone_id -> set of actions
    group_allow_zones: set[int] = set()
    group_deny_zones: set[int] = set()

    if group_ids:
        policies = db.query(Policy).filter(Policy.group_id.in_(group_ids)).all()
        for p in policies:
            if p.action == "allow":
                group_allow_zones.add(p.zone_id)
            elif p.action == "deny":
                group_deny_zones.add(p.zone_id)

    # Step 3: Collect peer-level overrides
    overrides = db.query(PeerOverride).filter(PeerOverride.peer_id == peer_id).all()
    override_allow_zones: set[int] = set()
    override_deny_zones: set[int] = set()

    for o in overrides:
        if o.action == "allow":
            override_allow_zones.add(o.zone_id)
        elif o.action == "deny":
            override_deny_zones.add(o.zone_id)

    # Step 4: Apply precedence to determine final allowed zone IDs
    # All zones that appear in any rule
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

    # Step 5: Resolve zone IDs to CIDRs
    if not allowed_zone_ids:
        return []

    zone_networks = (
        db.query(ZoneNetwork)
        .filter(ZoneNetwork.zone_id.in_(allowed_zone_ids))
        .all()
    )

    return sorted({zn.cidr for zn in zone_networks})


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
