"""
Onboarding Service
==================
Handles the initial server setup wizard that creates:
1. A default Network with the server's local network CIDR
2. An "All" group (peers without groups get allow-all by default)
3. Marks the user's onboarding as completed

In the new group-to-group policy model, peers that belong to no groups
automatically get access to all networks (allow-all default).
"""

from sqlalchemy.orm import Session

from app.models.group import PeerGroup
from app.models.network import Network
from app.models.user import User
from app.schemas.onboarding import OnboardingRequest


def complete_onboarding(db: Session, user: User, data: OnboardingRequest) -> dict:
    """
    Execute the onboarding wizard:
    1. Create default Network with the provided CIDR
    2. Create "All" group
    3. Mark user.onboarding_completed = True
    """
    # Step 1: Create the server LAN Network
    network = Network(
        name=data.server_lan_name,
        subnet=data.server_lan_cidr,
        description=f"Server local network — {data.server_lan_cidr}",
        network_type="lan",
        is_default=True,
    )
    db.add(network)
    db.flush()  # Get network.id

    # Step 2: Create the "All" group
    group = PeerGroup(
        name="All",
        description="Default group — all peers start here with full access. Remove from All and add to specific groups to restrict access.",
    )
    db.add(group)
    db.flush()  # Get group.id

    # Step 3: Mark onboarding as completed
    user.onboarding_completed = True
    db.commit()

    return {
        "success": True,
        "message": "Onboarding completed. All peers will have full access by default.",
        "network_id": network.id,
        "group_id": group.id,
    }
