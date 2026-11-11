"""Own two chains, replace their contents atomically, preserve other services."""
import ipaddress
import json
import logging
import shlex
import subprocess

from sqlalchemy.orm import Session

from app.config import settings
from app.models.network import Network
from app.models.peer import Peer
from app.models.server_config import ServerConfig
from app.services import connection_log_service
from app.services.policy_compiler import compile_allowed_cidrs

logger = logging.getLogger(__name__)
FORWARD_CHAIN = "NETLOOM-FWD"
POSTROUTING_CHAIN = "NETLOOM-POST"


def _run(cmd, input_data=None, check=True):
    result = subprocess.run(cmd, input=input_data, capture_output=True, text=True, timeout=30)
    if check and result.returncode:
        raise RuntimeError(f"{' '.join(cmd)}: {result.stderr.strip()}")
    return result


def _ipt(*args, table="filter", check=True):
    return _run(["iptables", "-w", "5", "-t", table, *args], check=check)


def _get_outbound_interface():
    routes = json.loads(_run(["ip", "-j", "-4", "route", "get", "1.1.1.1"]).stdout)
    return routes[0]["dev"]


def _get_server_ip(iface):
    rows = json.loads(_run(["ip", "-j", "-4", "addr", "show", "dev", iface]).stdout)
    return next((a["local"] for row in rows for a in row.get("addr_info", []) if a.get("family") == "inet"), None)


def _ensure_chain(chain, table):
    if _ipt("-S", chain, table=table, check=False).returncode:
        _ipt("-N", chain, table=table)


def _link(parent, chain, table):
    if _ipt("-C", parent, "-j", chain, table=table, check=False).returncode:
        _ipt("-I", parent, "1", "-j", chain, table=table)


def _sources(peer):
    sources = [peer.assigned_ip]
    if peer.peer_type == "branch_office" and peer.remote_subnets:
        sources += json.loads(peer.remote_subnets)
    return sources


def _permissions_from_rules(text):
    result = {}
    for line in text.splitlines():
        parts = shlex.split(line)
        if "-s" in parts and "-j" in parts:
            destinations = result.setdefault(parts[parts.index("-s")+1], set())
            if "-d" in parts and parts[parts.index("-j")+1] == "ACCEPT":
                destinations.add(parts[parts.index("-d")+1])
    return result


def revoked_ranges(before, after):
    remaining = [ipaddress.ip_network(n, strict=False) for n in before]
    for allowed in after:
        allow = ipaddress.ip_network(allowed, strict=False)
        updated = []
        for old in remaining:
            if not old.overlaps(allow):
                updated.append(old)
            elif allow.subnet_of(old):
                updated.extend(old.address_exclude(allow))
        remaining = updated
    return sorted({str(n) for n in remaining})


def build_rules(db, outbound_iface, server_ip):
    cfg = db.query(ServerConfig).first()
    firewall_on = bool(cfg and cfg.firewall_enabled)
    peers = db.query(Peer).filter(Peer.is_enabled == True, Peer.peer_type != "server").all()
    sources = sorted({s for p in peers for s in _sources(p)})
    permissions = {}
    forward = [f"-A {FORWARD_CHAIN} -i {settings.wg_interface} -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT"]
    # Return packets only; this does not grant initiation from local LANs.
    forward += [f"-A {FORWARD_CHAIN} -o {settings.wg_interface} -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT"]
    if firewall_on:
        for peer in peers:
            allowed = compile_allowed_cidrs(db, peer.id)
            for src in _sources(peer):
                src = str(ipaddress.ip_network(src, strict=False))
                permissions[src] = set(allowed)
                for dst in allowed:
                    forward.append(f"-A {FORWARD_CHAIN} -i {settings.wg_interface} -s {src} -d {dst} -j ACCEPT")
                forward.append(f"-A {FORWARD_CHAIN} -i {settings.wg_interface} -s {src} -j DROP")
        forward.append(f"-A {FORWARD_CHAIN} -i {settings.wg_interface} -j DROP")
    else:
        forward.append(f"-A {FORWARD_CHAIN} -i {settings.wg_interface} -j ACCEPT")
    nat = []
    networks = db.query(Network).order_by(Network.id).all()
    # Limit every NAT rule to known VPN sources, including branch LANs.
    for src in sources:
        for network in networks:
            if not network.nat_enabled:
                nat.append(f"-A {POSTROUTING_CHAIN} -s {src} -d {network.subnet} -j RETURN")
        for network in networks:
            if network.nat_enabled:
                nat.append(f"-A {POSTROUTING_CHAIN} -s {src} -d {network.subnet} -j MASQUERADE")
        nat.append(f"-A {POSTROUTING_CHAIN} -s {src} -o {outbound_iface} -j MASQUERADE")
    payload = "\n".join(["*filter", f":{FORWARD_CHAIN} - [0:0]", f"-F {FORWARD_CHAIN}", *forward, "COMMIT",
                          "*nat", f":{POSTROUTING_CHAIN} - [0:0]", f"-F {POSTROUTING_CHAIN}", *nat, "COMMIT", ""])
    return payload, permissions


def _remove_legacy_rules(db, outbound_iface, server_ip):
    # Exact shapes emitted by the previous NetLoom implementation, never all RETURNs.
    rules = [["-s", settings.subnet, "-o", outbound_iface, "-j", "MASQUERADE"]]
    for network in db.query(Network).all():
        if not network.nat_enabled:
            rules.append(["-d", network.subnet, "-j", "RETURN"])
        else:
            rules.append(["-s", settings.subnet, "-d", network.subnet, "-j", "MASQUERADE"])
    if server_ip:
        for peer in db.query(Peer).filter(Peer.peer_type == "branch_office").all():
            for src in json.loads(peer.remote_subnets or "[]"):
                rules.append(["-s", src, "-o", outbound_iface, "-j", "SNAT", "--to-source", server_ip])
    for rule in rules:
        while _ipt("-C", "POSTROUTING", *rule, table="nat", check=False).returncode == 0:
            _ipt("-D", "POSTROUTING", *rule, table="nat")


def apply_iptables_rules(db: Session):
    outbound = _get_outbound_interface()
    server_ip = _get_server_ip(outbound)
    _ensure_chain(FORWARD_CHAIN, "filter")
    _ensure_chain(POSTROUTING_CHAIN, "nat")
    before = _permissions_from_rules(_ipt("-S", FORWARD_CHAIN).stdout)
    payload, after = build_rules(db, outbound, server_ip)
    # Parse and validate first. --noflush preserves Docker, NetBird, and other chains.
    _run(["iptables-restore", "--wait", "5", "--noflush", "--test"], input_data=payload)
    _run(["iptables-restore", "--wait", "5", "--noflush"], input_data=payload)
    _link("FORWARD", FORWARD_CHAIN, "filter")
    _link("POSTROUTING", POSTROUTING_CHAIN, "nat")
    _remove_legacy_rules(db, outbound, server_ip)
    for src, destinations in after.items():
        # First enable: revoke the portion previously covered by blanket ACCEPT.
        previous = before.get(src, {"0.0.0.0/0"})
        for dst in revoked_ranges(previous, destinations):
            result = _run(["conntrack", "-D", "-s", src, "-d", dst], check=False)
            # conntrack returns 1 when no matching sessions exist.
            if result.returncode not in (0, 1) or (result.returncode == 1 and "0 flow entries" not in result.stderr + result.stdout):
                raise RuntimeError(f"No se pudieron revocar sesiones de {src} hacia {dst}: {result.stderr.strip()}")
    connection_log_service.log_connection(db, "iptables_applied", "Reglas de NetLoom aplicadas", details={"enforced_sources": len(after)})


def get_fwd_rules():
    result = _ipt("-S", FORWARD_CHAIN, check=False)
    if result.returncode:
        return []
    rules = []
    for line in result.stdout.splitlines():
        parts = shlex.split(line)
        if not parts or parts[0] != "-A" or "--ctstate" in parts:
            continue
        def value(flag, default="0.0.0.0/0"):
            return parts[parts.index(flag)+1] if flag in parts else default
        rules.append(dict(target=value("-j", "?"), src=value("-s"), dst=value("-d"), extra=line))
    return rules


def reset_iptables_rules():
    for table, parent, chain in [("filter", "FORWARD", FORWARD_CHAIN), ("nat", "POSTROUTING", POSTROUTING_CHAIN)]:
        while _ipt("-C", parent, "-j", chain, table=table, check=False).returncode == 0:
            _ipt("-D", parent, "-j", chain, table=table)
        _ipt("-F", chain, table=table)
        _ipt("-X", chain, table=table)
