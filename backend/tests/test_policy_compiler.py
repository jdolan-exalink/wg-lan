import ipaddress
import pytest
from app.models.group import PeerGroup, PeerGroupMember, Policy, GroupNetworkAccess
from app.models.peer import Peer, PeerOverride
from app.models.network import Network
from app.models.ip_group import IpGroup, IpGroupEntry
from app.models.user import User, UserNetworkAccess
from app.models.user_group import UserGroup
from app.services.policy_compiler import compile_allowed_cidrs, compile_client_allowed_ips
from app.services.iptables_service import build_rules, revoked_ranges


@pytest.fixture
def policy_data(db):
    network = Network(name="Planta", subnet="192.168.207.0/24")
    other = Network(name="Otra", subnet="192.168.208.0/24")
    group = PeerGroup(name="Soporte")
    peer = Peer(name="Operador", peer_type="roadwarrior", private_key="private", public_key="public", assigned_ip="100.79.0.2/32")
    db.add_all([network, other, group, peer]); db.flush()
    db.add_all([PeerGroupMember(peer_id=peer.id, group_id=group.id), GroupNetworkAccess(group_id=group.id, network_id=network.id, action="allow")])
    db.commit()
    return peer, network, other, group


def test_group_allow_and_peer_deny(db, policy_data):
    peer, network, _, _ = policy_data
    assert compile_allowed_cidrs(db, peer.id, True) == [network.subnet]
    db.add(PeerOverride(peer_id=peer.id, network_id=network.id, action="deny")); db.commit()
    assert compile_allowed_cidrs(db, peer.id, True) == []


def test_deny_ip_inside_allowed_network(db, policy_data):
    peer, network, _, group = policy_data
    ips = IpGroup(name="Restringidos", network_id=network.id)
    db.add(ips); db.flush()
    db.add_all([IpGroupEntry(ip_group_id=ips.id, ip_address="192.168.207.25"), Policy(source_group_id=group.id, dest_ip_group_id=ips.id, action="deny", direction="outbound")]); db.commit()
    result = [ipaddress.ip_network(n) for n in compile_allowed_cidrs(db, peer.id, True)]
    assert not any(ipaddress.ip_address("192.168.207.25") in n for n in result)
    assert any(ipaddress.ip_address("192.168.207.26") in n for n in result)


def test_network_deny_wins_over_ip_allow(db, policy_data):
    peer, network, _, group = policy_data
    ips = IpGroup(name="Excepcion", network_id=network.id)
    db.add(ips); db.flush()
    db.add_all([PeerOverride(peer_id=peer.id, network_id=network.id, action="deny"), IpGroupEntry(ip_group_id=ips.id, ip_address="192.168.207.25"), Policy(source_group_id=group.id, dest_ip_group_id=ips.id, action="allow", direction="outbound")]); db.commit()
    assert compile_allowed_cidrs(db, peer.id, True) == []


def test_user_group_changes_affect_existing_peer(db, policy_data):
    peer, network, other, _ = policy_data
    user = User(username="test", password_hash="unused")
    group = PeerGroup(name="Tecnicos")
    db.add_all([user, group]); db.flush()
    peer.user_id = user.id
    db.add_all([UserGroup(user_id=user.id, group_id=group.id), GroupNetworkAccess(group_id=group.id, network_id=other.id, action="allow")]); db.commit()
    assert other.subnet in compile_allowed_cidrs(db, peer.id, True)
    db.query(UserGroup).filter_by(user_id=user.id).delete(); db.commit()
    assert other.subnet not in compile_allowed_cidrs(db, peer.id, True)


def test_routes_independent_of_permissions_and_exclude_own_lan(db, policy_data):
    peer, network, other, group = policy_data
    peer.peer_type = "branch_office"; peer.remote_subnets = '["192.168.207.0/24"]'
    network.peer_id = peer.id; db.commit()
    routes = compile_client_allowed_ips(db, peer.id)
    assert other.subnet in routes
    assert network.subnet not in routes
    db.add(PeerOverride(peer_id=peer.id, network_id=other.id, action="deny")); db.commit()
    assert compile_client_allowed_ips(db, peer.id) == routes


def test_peer_without_groups_still_has_user_denies_enforced(db, policy_data):
    from app.models.server_config import ServerConfig
    peer, network, _, _ = policy_data
    user = User(username="restricted", password_hash="unused")
    cfg = ServerConfig(private_key="private", public_key="public", address="100.79.0.1/16", endpoint="vpn", firewall_enabled=True)
    db.add_all([user, cfg]); db.flush()
    peer.user_id = user.id
    db.query(PeerGroupMember).filter_by(peer_id=peer.id).delete()
    db.add(UserNetworkAccess(user_id=user.id, network_id=network.id, action="deny")); db.commit()
    payload, permissions = build_rules(db, "eth0", "192.168.70.165")
    assert permissions[peer.assigned_ip] == set()
    assert '-i wg0 -j DROP' in payload
    assert '-i wg0 -s 100.79.0.2/32 -d 192.168.207.0/24 -j ACCEPT' not in payload


def test_revocation_only_cuts_removed_addresses():
    assert revoked_ranges(["192.168.207.0/24"], ["192.168.207.0/25"]) == ["192.168.207.128/25"]
    assert revoked_ranges(["192.168.207.0/24"], ["192.168.207.0/24", "192.168.208.0/24"]) == []


def test_removing_last_group_does_not_grant_everything(db, policy_data):
    peer, _, _, _ = policy_data
    db.query(PeerGroupMember).filter_by(peer_id=peer.id).delete(); db.commit()
    assert compile_allowed_cidrs(db, peer.id, force_policies=True) == []


def test_unowned_network_not_implicitly_granted_by_group_policy(db, policy_data):
    peer, _, other, group = policy_data
    destination = PeerGroup(name="Destino"); db.add(destination); db.flush()
    db.add(Policy(source_group_id=group.id, dest_group_id=destination.id, action="allow")); db.commit()
    assert other.subnet not in compile_allowed_cidrs(db, peer.id, force_policies=True)


def test_explicit_user_groups_remove_legacy_automatic_all_access(db, policy_data):
    from app.services.sync_service import clear_default_user_peer_groups
    peer, network, other, group = policy_data
    user = User(username="legacy", password_hash="unused")
    default = PeerGroup(name="All")
    db.add_all([user, default]); db.flush(); peer.user_id = user.id
    db.add_all([PeerGroupMember(peer_id=peer.id, group_id=default.id), GroupNetworkAccess(group_id=default.id, network_id=other.id, action="allow")]); db.commit()
    assert other.subnet in compile_allowed_cidrs(db, peer.id, True)
    clear_default_user_peer_groups(db, user.id); db.commit()
    assert other.subnet not in compile_allowed_cidrs(db, peer.id, True)
    assert network.subnet in compile_allowed_cidrs(db, peer.id, True)
