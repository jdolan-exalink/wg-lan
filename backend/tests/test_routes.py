import json
import pytest
from app.models.network import Network
from app.models.peer import Peer
from app.services import route_service, network_service
from app.schemas.network import NetworkCreate, NetworkUpdate


@pytest.fixture
def routing(db, monkeypatch):
    peer = Peer(name="Sucursal", peer_type="branch_office", private_key="priv", public_key="pub", assigned_ip="100.79.0.45/32", remote_subnets='[]', is_enabled=True)
    db.add(peer); db.commit()
    actual = [dict(dst="192.168.70.0/23", dev="eth0", protocol="kernel", scope="link"), dict(dst="default", gateway="192.168.70.1", dev="eth0", protocol="static")]
    calls = []
    monkeypatch.setattr(route_service, "system_routes", lambda: [dict(r) for r in actual])
    def run(args):
        calls.append(args)
        if "get" in args:
            return json.dumps([dict(dst=args[-1], dev="eth0")])
        action, dst = args[3:5]
        if action in {"del", "replace"}:
            actual[:] = [r for r in actual if r["dst"] != dst]
        if action in {"add", "replace"}:
            actual.append(dict(dst=dst, dev=args[args.index("dev")+1], protocol="242", scope="link", **({"gateway":args[args.index("via")+1]} if "via" in args else {})))
        return ""
    monkeypatch.setattr(route_service, "_run", run)
    return peer, actual, calls


def test_new_network_creates_route_and_allowed_ips(db, routing):
    peer, actual, calls = routing
    network_service.create_network(db, NetworkCreate(name="Carniceria 7", subnet="192.168.207.0/24", peer_id=peer.id))
    assert json.loads(peer.remote_subnets) == ["192.168.207.0/24"]
    result = route_service.reconcile_routes(db)
    assert result["expected"][0]["status"] == "active"
    assert any(r["dst"] == "192.168.207.0/24" and r["dev"] == "wg0" for r in actual)
    route_service.reconcile_routes(db)
    assert len(calls) == 1


def test_disabling_branch_removes_only_owned_route(db, routing):
    peer, actual, _ = routing
    network_service.create_network(db, NetworkCreate(name="Sucursal", subnet="192.168.207.0/24", peer_id=peer.id))
    route_service.reconcile_routes(db)
    peer.is_enabled = False; db.commit()
    route_service.reconcile_routes(db)
    assert [r["dst"] for r in actual] == ["192.168.70.0/23", "default"]


def test_conflicting_foreign_route_is_not_replaced(db, routing):
    peer, actual, calls = routing
    network_service.create_network(db, NetworkCreate(name="Sucursal", subnet="192.168.207.0/24", peer_id=peer.id))
    actual.append(dict(dst="192.168.207.0/24", dev="wt0", protocol="static"))
    with pytest.raises(RuntimeError, match="ajena"):
        route_service.reconcile_routes(db)
    assert not calls


def test_connected_network_and_unconfigured_network(db, routing):
    network_service.create_network(db, NetworkCreate(name="LAN", subnet="192.168.70.0/23"))
    network_service.create_network(db, NetworkCreate(name="Pendiente", subnet="192.168.208.0/24"))
    result = route_service.reconcile_routes(db)
    assert [r["status"] for r in result["expected"]] == ["connected", "unconfigured"]
    assert not routing[2]


def test_gateway_change_and_clear_updates_both_models(db, routing):
    peer, _, _ = routing
    network = network_service.create_network(db, NetworkCreate(name="Sucursal", subnet="192.168.207.0/24", peer_id=peer.id))
    network_service.update_network(db, network, NetworkUpdate(peer_id=None, gateway_ip="192.168.70.2"))
    assert json.loads(peer.remote_subnets) == []
    route_service.reconcile_routes(db)
    assert any(r.get("gateway") == "192.168.70.2" for r in routing[1])
    network_service.update_network(db, network, NetworkUpdate(gateway_ip=None))
    route_service.reconcile_routes(db)
    assert all(r["dst"] != network.subnet for r in routing[1])


def test_adopt_legacy_wg_route_for_later_removal(db, routing):
    peer, actual, _ = routing
    network_service.create_network(db, NetworkCreate(name="Sucursal", subnet="192.168.207.0/24", peer_id=peer.id))
    actual.append(dict(dst="192.168.207.0/24", dev="wg0", protocol="boot", scope="link"))
    route_service.reconcile_routes(db)
    assert actual[-1]["protocol"] == "242"
    peer.is_enabled = False; db.commit(); route_service.reconcile_routes(db)
    assert all(r["dst"] != "192.168.207.0/24" for r in actual)


def test_network_api_applies_route_without_restarting_wireguard(db, routing, monkeypatch, tmp_path):
    from app.models.server_config import ServerConfig
    from app.routers.networks import create_network
    from app.services import wg_service, iptables_service
    from app.config import settings
    import subprocess
    db.add(ServerConfig(private_key="private", public_key="public", address="100.79.0.1/16", endpoint="vpn")); db.commit()
    monkeypatch.setattr(settings, "wg_config_path", str(tmp_path))
    monkeypatch.setattr(wg_service, "is_interface_up", lambda: True)
    commands = []
    def run(args, input_data=None):
        commands.append(args)
        return subprocess.CompletedProcess(args, 0, "", "")
    monkeypatch.setattr(wg_service, "_run", run)
    monkeypatch.setattr(iptables_service, "apply_iptables_rules", lambda db: None)
    create_network(NetworkCreate(name="Nueva LAN", subnet="192.168.208.0/24", peer_id=routing[0].id), db, None)
    assert any(r["dst"] == "192.168.208.0/24" for r in routing[1])
    assert commands == [["wg", "syncconf", "wg0", "/dev/stdin"]]
    assert (tmp_path / "wg0.conf").stat().st_mode & 0o777 == 0o600


def test_deleting_network_removes_permissions_and_owned_subnet(db, routing):
    from app.models.group import PeerGroup, GroupNetworkAccess
    from app.models.user import User, UserNetworkAccess
    from app.models.peer import PeerNetworkAccess, PeerOverride
    peer, _, _ = routing
    network = network_service.create_network(db, NetworkCreate(name="Sucursal", subnet="192.168.207.0/24", peer_id=peer.id))
    group = PeerGroup(name="All"); user = User(username="test", password_hash="unused")
    db.add_all([group,user]); db.flush()
    db.add_all([GroupNetworkAccess(group_id=group.id, network_id=network.id, action="allow"), UserNetworkAccess(user_id=user.id, network_id=network.id, action="allow"), PeerNetworkAccess(peer_id=peer.id, network_id=network.id), PeerOverride(peer_id=peer.id, network_id=network.id, action="deny")]); db.commit()
    route_service.reconcile_routes(db)
    network_service.delete_network(db, network)
    route_service.reconcile_routes(db)
    assert json.loads(peer.remote_subnets) == []
    for model in [Network, GroupNetworkAccess, UserNetworkAccess, PeerNetworkAccess, PeerOverride]:
        assert db.query(model).count() == 0


def test_reserved_network_can_be_associated_when_branch_created(db, monkeypatch):
    from app.services import peer_service
    from app.schemas.peer import BranchOfficeCreate
    from app.models.user import User
    from app.models.server_config import ServerConfig
    from app.services import wg_service
    db.add(ServerConfig(private_key="priv", public_key="pub", address="100.79.0.1/16", endpoint="vpn"))
    user = User(username="admin", password_hash="unused"); db.add(user); db.commit()
    reserved = network_service.create_network(db, NetworkCreate(name="Carniceria 8", subnet="192.168.208.0/24", nat_enabled=False))
    monkeypatch.setattr(wg_service, "apply_config", lambda db: None)
    monkeypatch.setattr(peer_service, "safe_generate_keypair", lambda: ("private", "new-public"))
    peer = peer_service.create_branch_office(db, BranchOfficeCreate(name="Carniceria 8", remote_subnets=["192.168.208.0/24"]), created_by=user.id)
    db.refresh(reserved)
    assert reserved.peer_id == peer.id
    assert reserved.nat_enabled is False
    assert json.loads(peer.remote_subnets) == [reserved.subnet]
