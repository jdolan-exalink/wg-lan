import subprocess
import pytest
from app.services import iptables_service as fw
from app.models.network import Network
from app.models.peer import Peer
from app.models.server_config import ServerConfig


def test_nat_limited_to_known_sources_and_no_foreign_chain_changes(db):
    db.add(ServerConfig(private_key="private", public_key="public", address="100.79.0.1/16", endpoint="vpn"))
    db.add(Peer(name="branch", peer_type="branch_office", private_key="private", public_key="public", assigned_ip="100.79.0.2/32", remote_subnets='["192.168.207.0/24"]'))
    db.add(Network(name="LAN", subnet="192.168.70.0/23", nat_enabled=False)); db.commit()
    payload, _ = fw.build_rules(db, "eth0", "192.168.70.165")
    assert "DOCKER" not in payload and "NETBIRD" not in payload
    assert "-F FORWARD" not in payload and "-F POSTROUTING" not in payload
    assert "-s 192.168.207.0/24 -d 192.168.70.0/23 -j RETURN" in payload
    assert all(" -s " in line for line in payload.splitlines() if line.startswith("-A NETLOOM-POST"))


def test_invalid_restore_is_not_applied_and_no_sessions_flushed(db, monkeypatch):
    calls = []
    monkeypatch.setattr(fw, "_get_outbound_interface", lambda: "eth0")
    monkeypatch.setattr(fw, "_get_server_ip", lambda iface: "192.168.70.165")
    def run(args, input_data=None, check=True):
        calls.append(args)
        if "--test" in args:
            raise RuntimeError("invalid generated rules")
        return subprocess.CompletedProcess(args, 0, "", "")
    monkeypatch.setattr(fw, "_run", run)
    with pytest.raises(RuntimeError, match="invalid generated"):
        fw.apply_iptables_rules(db)
    assert not any(args[0] == "conntrack" for args in calls)
    assert all("--test" in args for args in calls if args[0] == "iptables-restore")


def test_empty_permissions_preserved_when_reading_previous_rules():
    rules = '-A NETLOOM-FWD -i wg0 -s 100.79.0.2/32 -j DROP\n'
    assert fw._permissions_from_rules(rules) == {"100.79.0.2/32":set()}
    assert fw.revoked_ranges(fw._permissions_from_rules(rules)["100.79.0.2/32"], []) == []
