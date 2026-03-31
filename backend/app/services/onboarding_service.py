"""
Onboarding Service
==================
Handles the initial server setup wizard that creates:
1. A "LAN Server" zone with the server's local network CIDR
2. An "All" group that grants access to all zones
3. A policy linking "All" group → "LAN Server" zone = allow
4. Marks the user's onboarding as completed

This sets up a default "allow all" configuration where new peers
can reach everything until explicitly restricted via groups.
"""

from sqlalchemy.orm import Session

from app.models.group import PeerGroup, Policy
from app.models.user import User
from app.models.zone import Zone, ZoneNetwork
from app.schemas.onboarding import OnboardingRequest


def complete_onboarding(db: Session, user: User, data: OnboardingRequest) -> dict:
    """
    Execute the onboarding wizard:
    1. Create "LAN Server" zone with the provided CIDR
    2. Create "All" group
    3. Create policy: All → LAN Server = allow
    4. Mark user.onboarding_completed = True
    """
    # Step 1: Create the LAN Server zone
    zone = Zone(
        name=data.server_lan_name,
        description=f"Server local network — {data.server_lan_cidr}",
    )
    db.add(zone)
    db.flush()  # Get zone.id

    zone_network = ZoneNetwork(
        zone_id=zone.id,
        cidr=data.server_lan_cidr,
        description="Server LAN",
    )
    db.add(zone_network)

    # Step 2: Create the "All" group
    group = PeerGroup(
        name="All",
        description="Default group — all peers start here with full access. Remove from All and add to specific groups to restrict access.",
    )
    db.add(group)
    db.flush()  # Get group.id

    # Step 3: Create policy: All → LAN Server = allow
    policy = Policy(
        group_id=group.id,
        zone_id=zone.id,
        action="allow",
    )
    db.add(policy)
    db.flush()  # Get policy.id

    # Step 4: Mark onboarding as completed
    user.onboarding_completed = True
    db.commit()

    return {
        "success": True,
        "message": "Onboarding completed. All peers will have full access by default.",
        "zone_id": zone.id,
        "group_id": group.id,
        "policy_id": policy.id,
    }
