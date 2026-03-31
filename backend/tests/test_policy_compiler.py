import pytest
from app.models.group import PeerGroup, PeerGroupMember, Policy
from app.models.peer import Peer, PeerOverride
from app.models.zone import Zone, ZoneNetwork
from app.models.network import Network
from app.services.policy_compiler import compile_allowed_cidrs


@pytest.fixture
def base_data(db):
    """Create zones, network, group, peer for tests."""
    network = Network(name="VPN", subnet="10.50.0.0/24", is_default=True)
    db.add(network)
    db.flush()

    planta = Zone(name="Planta")
    ventas = Zone(name="Ventas")
    laboratorio = Zone(name="Laboratorio")
    db.add_all([planta, ventas, laboratorio])
    db.flush()

    db.add(ZoneNetwork(zone_id=planta.id, cidr="10.10.10.0/24"))
    db.add(ZoneNetwork(zone_id=ventas.id, cidr="10.10.20.0/24"))
    db.add(ZoneNetwork(zone_id=laboratorio.id, cidr="10.10.30.0/24"))

    group = PeerGroup(name="rw_planta_ventas")
    db.add(group)
    db.flush()

    db.add(Policy(group_id=group.id, zone_id=planta.id, action="allow"))
    db.add(Policy(group_id=group.id, zone_id=ventas.id, action="allow"))

    peer = Peer(
        name="road1",
        peer_type="roadwarrior",
        private_key="priv",
        public_key="pub1",
        assigned_ip="10.50.0.2/32",
        network_id=network.id,
        tunnel_mode="split",
    )
    db.add(peer)
    db.flush()
    db.add(PeerGroupMember(peer_id=peer.id, group_id=group.id))
    db.commit()

    return {"peer": peer, "planta": planta, "ventas": ventas, "laboratorio": laboratorio, "group": group}


def test_compile_allows_group_zones(db, base_data):
    peer = base_data["peer"]
    cidrs = compile_allowed_cidrs(db, peer.id)
    assert "10.10.10.0/24" in cidrs  # Planta
    assert "10.10.20.0/24" in cidrs  # Ventas
    assert "10.10.30.0/24" not in cidrs  # Laboratorio not assigned


def test_no_groups_no_access(db, base_data):
    # Peer with no group memberships
    network = db.query(Network).first()
    peer2 = Peer(
        name="road2",
        peer_type="roadwarrior",
        private_key="priv2",
        public_key="pub2",
        assigned_ip="10.50.0.3/32",
        network_id=network.id,
        tunnel_mode="split",
    )
    db.add(peer2)
    db.commit()
    cidrs = compile_allowed_cidrs(db, peer2.id)
    assert cidrs == []


def test_manual_deny_overrides_group_allow(db, base_data):
    peer = base_data["peer"]
    planta = base_data["planta"]
    # Add manual deny for Planta
    db.add(PeerOverride(peer_id=peer.id, zone_id=planta.id, action="deny", reason="test"))
    db.commit()
    cidrs = compile_allowed_cidrs(db, peer.id)
    assert "10.10.10.0/24" not in cidrs  # Planta denied
    assert "10.10.20.0/24" in cidrs       # Ventas still allowed


def test_manual_allow_grants_extra_access(db, base_data):
    peer = base_data["peer"]
    laboratorio = base_data["laboratorio"]
    # Add manual allow for Laboratorio (not in group policy)
    db.add(PeerOverride(peer_id=peer.id, zone_id=laboratorio.id, action="allow", reason="special"))
    db.commit()
    cidrs = compile_allowed_cidrs(db, peer.id)
    assert "10.10.30.0/24" in cidrs  # Laboratorio now accessible


def test_manual_allow_wins_over_group_deny(db, base_data):
    peer = base_data["peer"]
    planta = base_data["planta"]
    group = base_data["group"]
    # Change group policy to deny Planta, then add manual allow
    policy = db.query(Policy).filter(Policy.group_id == group.id, Policy.zone_id == planta.id).first()
    policy.action = "deny"
    db.add(PeerOverride(peer_id=peer.id, zone_id=planta.id, action="allow", reason="exception"))
    db.commit()
    cidrs = compile_allowed_cidrs(db, peer.id)
    assert "10.10.10.0/24" in cidrs  # allow_manual wins over deny_group
