from datetime import datetime, timezone
import json
import pytest
from fastapi import HTTPException
from starlette.requests import Request
from app.models.peer import Peer, PeerOverride
from app.models.user import User
from app.models.server_config import ServerConfig
from app.models.network import Network
from app.models.config_revision import ConfigRevision
from app.schemas.client import ClientStatusRequest
from app.schemas.peer import PeerOverrideCreate
from app.routers.client import get_config_delta, get_config_version, report_client_status, get_full_config
from app.services import sync_service, peer_service, iptables_service
from app.services.wg_service import ApplyError


@pytest.fixture
def synced(db):
    cfg = ServerConfig(private_key="server-private", public_key="server-public", address="100.79.0.1/16", endpoint="vpn.test")
    users = [User(username=f"user{i}", password_hash="unused") for i in range(2)]
    db.add_all([cfg, *users]); db.flush()
    peers = [Peer(name=f"peer{i}", peer_type="roadwarrior", private_key=f"private{i}", public_key=f"public{i}", assigned_ip=f"100.79.0.{i+2}/32", user_id=user.id) for i, user in enumerate(users)]
    db.add_all(peers); db.commit()
    sync_service.refresh_revisions(db)
    return users, peers


def test_revisions_idempotent_and_new_network_marks_existing_hosts(db, synced):
    _, peers = synced
    previous = [p.config_revision for p in peers]
    assert sync_service.refresh_revisions(db) == []
    db.add(Network(name="Nueva", subnet="192.168.208.0/24")); db.commit()
    assert sync_service.refresh_revisions(db) == [p.id for p in peers]
    assert all(p.config_revision > before for p, before in zip(peers, previous))
    for change in db.query(ConfigRevision).all():
        assert "private" not in change.changes


def test_delta_is_scoped_to_authenticated_peer_and_contains_routes(db, synced):
    users, peers = synced
    result = get_config_delta(client_revision=0, user=users[0], db=db)
    assert result.current_revision == peers[0].config_revision
    assert len(result.changes) == 1
    assert "allowed_ips" in result.changes[0].data
    assert get_config_version(user=users[0], db=db).current_revision == peers[0].config_revision
    assert get_config_delta(client_revision=result.current_revision, user=users[0], db=db).has_changes is False


def test_heartbeat_is_not_download_or_application_ack(db, synced):
    users, peers = synced
    peer = peers[0]
    request = Request({"type":"http", "headers":[], "client":("127.0.0.1",1234)})
    report_client_status(ClientStatusRequest(peer_id=peer.id, tunnel_status="connected"), request, users[0], db)
    assert peer.last_seen_at is not None
    assert peer.last_config_downloaded_at is None
    assert sync_service.sync_state(peer)[0] == "red"
    get_full_config(request, users[0], db)
    assert sync_service.sync_state(peer)[0] == "yellow"
    report_client_status(ClientStatusRequest(peer_id=peer.id, tunnel_status="connected", applied_revision=peer.config_revision), request, users[0], db)
    assert sync_service.sync_state(peer)[0] == "green"
    db.add(Network(name="Nueva", subnet="192.168.208.0/24")); db.commit(); sync_service.refresh_revisions(db)
    assert sync_service.sync_state(peer)[0] == "yellow"


def test_ack_cannot_claim_another_peers_revision(db, synced):
    users, peers = synced
    request = Request({"type":"http", "headers":[], "client":("127.0.0.1",1234)})
    with pytest.raises(HTTPException):
        report_client_status(ClientStatusRequest(peer_id=peers[1].id, tunnel_status="connected", applied_revision=peers[0].config_revision), request, users[1], db)


def test_override_reapplies_and_reports_failure_without_false_success(db, synced, monkeypatch):
    _, peers = synced
    network = Network(name="LAN", subnet="192.168.208.0/24")
    db.add(network); db.commit()
    calls = []
    monkeypatch.setattr(iptables_service, "apply_iptables_rules", lambda db: calls.append(True))
    peer_service.upsert_override(db, peers[0], PeerOverrideCreate(network_id=network.id, action="allow"))
    peer_service.delete_override(db, peers[0].id, network.id)
    assert len(calls) == 2
    def fail(db):
        raise RuntimeError("simulated firewall failure")
    monkeypatch.setattr(iptables_service, "apply_iptables_rules", fail)
    with pytest.raises(ApplyError, match="aplicación pendiente"):
        peer_service.upsert_override(db, peers[0], PeerOverrideCreate(network_id=network.id, action="deny"))
    assert db.query(PeerOverride).one().action == "deny"


def test_manual_ack_rejects_old_revision(db, synced):
    from app.routers.peers import acknowledge_manual_config
    from app.schemas.peer import ConfigAppliedRequest
    users, peers = synced
    peer = peers[0]
    acknowledge_manual_config(peer.id, ConfigAppliedRequest(revision=peer.config_revision), db, users[0])
    old = peer.config_revision
    db.add(Network(name="Nueva", subnet="192.168.208.0/24")); db.commit(); sync_service.refresh_revisions(db)
    with pytest.raises(HTTPException):
        acknowledge_manual_config(peer.id, ConfigAppliedRequest(revision=old), db, users[0])
    assert sync_service.sync_state(peer)[0] != "green"
