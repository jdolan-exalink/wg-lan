from app.models.network import Network
from app.models.peer import Peer, PeerNetworkAccess
from app.services.policy_compiler import compile_allowed_cidrs


def test_direct_network_access_limits_peer_scope(db):
    allowed = Network(name="Branch LAN", subnet="192.168.67.0/24", network_type="lan")
    blocked = Network(name="Server LAN", subnet="192.168.1.0/24", network_type="lan")
    db.add_all([allowed, blocked])
    db.flush()

    peer = Peer(
        name="road1",
        peer_type="roadwarrior",
        device_type="laptop",
        private_key="priv",
        public_key="pub1",
        assigned_ip="100.169.0.2/32",
        tunnel_mode="split",
        persistent_keepalive=25,
        is_enabled=True,
        is_system=False,
    )
    db.add(peer)
    db.flush()

    db.add(PeerNetworkAccess(peer_id=peer.id, network_id=allowed.id))
    db.commit()

    assert compile_allowed_cidrs(db, peer.id) == ["192.168.67.0/24"]


def test_direct_network_access_is_included_in_allowed_cidrs(db):
    branch_lan = Network(name="Branch LAN", subnet="192.168.67.0/24", network_type="lan")
    db.add(branch_lan)
    db.flush()

    peer = Peer(
        name="road1",
        peer_type="roadwarrior",
        device_type="laptop",
        private_key="priv",
        public_key="pub1",
        assigned_ip="100.169.0.2/32",
        tunnel_mode="split",
        persistent_keepalive=25,
        is_enabled=True,
        is_system=False,
    )
    db.add(peer)
    db.flush()

    db.add(PeerNetworkAccess(peer_id=peer.id, network_id=branch_lan.id))
    db.commit()

    cidrs = compile_allowed_cidrs(db, peer.id)

    assert "192.168.67.0/24" in cidrs