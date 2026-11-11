"""Inspect Linux routes and reconcile only routes owned by NetLoom (proto 242)."""
import ipaddress
import json
import subprocess
from threading import RLock

from sqlalchemy.orm import Session

from app.config import settings
from app.models.network import Network
from app.models.peer import Peer

ROUTE_PROTOCOL = "242"
route_lock = RLock()


def _run(args: list[str]) -> str:
    result = subprocess.run(args, capture_output=True, text=True, timeout=15)
    if result.returncode:
        raise RuntimeError(f"{' '.join(args)}: {result.stderr.strip()}")
    return result.stdout


def system_routes() -> list[dict]:
    return json.loads(_run(["ip", "-j", "-4", "route", "show", "table", "all"]))


def _main(route: dict) -> bool:
    return str(route.get("table", "main")) in {"main", "254"}


def _managed(route: dict) -> bool:
    return str(route.get("protocol")) == ROUTE_PROTOCOL


def _subnet(value: str):
    return ipaddress.ip_network(value, strict=False)


def desired_routes(db: Session) -> list[dict]:
    peers = {p.id: p for p in db.query(Peer).all()}
    desired = []
    for network in db.query(Network).order_by(Network.id).all():
        peer = peers.get(network.peer_id)
        item = dict(network_id=network.id, name=network.name, destination=network.subnet,
                    peer_id=network.peer_id, peer_name=peer.name if peer else None,
                    gateway=network.gateway_ip, interface=None, enabled=True)
        if peer and peer.peer_type == "branch_office":
            item.update(interface=settings.wg_interface, enabled=peer.is_enabled)
        desired.append(item)
    return desired


def route_inventory(db: Session) -> dict:
    actual = [dict(r, dst=str(_subnet(r["dst"]))) if r.get("dst", "default") != "default" else r
              for r in system_routes()]
    main = [r for r in actual if _main(r)]
    expected = desired_routes(db)
    for item in expected:
        target = _subnet(item["destination"])
        exact = [r for r in main if r.get("dst") == str(target)]
        if not item["enabled"]:
            item.update(status="disabled", message="Gateway deshabilitado")
        elif item["interface"] or item["gateway"]:
            matches = [r for r in exact if r.get("type", "unicast") == "unicast"
                       and (not item["interface"] or r.get("dev") == item["interface"])
                       and r.get("gateway") == item["gateway"]]
            item.update(status="active" if matches else "conflict" if exact else "missing",
                        message="Ruta instalada" if matches else "Ruta diferente en Linux" if exact else "Falta instalar la ruta")
        else:
            connected = [r for r in main if r.get("protocol") == "kernel"
                         and r.get("scope") == "link" and r.get("dst") != "default"
                         and target.subnet_of(_subnet(r["dst"]))]
            item.update(status="connected" if connected else "unconfigured",
                        interface=connected[0].get("dev") if connected else None,
                        message="Red conectada al servidor" if connected else "Asigná un gateway de sucursal o una IP de siguiente salto")
            if connected and connected[0].get("dev", "").startswith(("docker", "br-")):
                item.update(status="conflict", message="El destino coincide con una red de Docker; definí el gateway real o resolvé el solapamiento")
    warnings = []
    for item in expected:
        target = _subnet(item["destination"])
        for route in main:
            if route.get("dst", "default") == "default" or route.get("protocol") != "kernel":
                continue
            connected = _subnet(route["dst"])
            if target.overlaps(connected) and (item["gateway"] or item["peer_id"] and item["interface"] == settings.wg_interface
                                               or route.get("dev", "").startswith(("docker", "br-"))):
                warnings.append(f"{item['name']} ({target}) se solapa con {connected} en {route.get('dev')}")
    return {"expected": expected, "routes": [dict(destination=r.get("dst", "default"),
            gateway=r.get("gateway"), interface=r.get("dev"), table=str(r.get("table", "main")),
            protocol=str(r.get("protocol", "")), scope=r.get("scope"),
            route_type=r.get("type", "unicast"), metric=r.get("metric"), managed=_managed(r)) for r in actual],
            "warnings": sorted(set(warnings))}


def reconcile_routes(db: Session) -> dict:
    """Do not replace foreign routes, connected routes, or the default gateway."""
    with route_lock:
        inventory = route_inventory(db)
        active = {i["destination"]: i for i in inventory["expected"]
                  if i["enabled"] and (i["gateway"] or i["interface"] == settings.wg_interface)}
        changed = []
        # Remove only explicitly tagged routes. Existing wg-quick routes are preserved.
        for route in inventory["routes"]:
            if not route["managed"] or route["table"] not in {"main", "254"}:
                continue
            item = active.get(route["destination"])
            if item and item["gateway"] == route["gateway"] and (not item["interface"] or item["interface"] == route["interface"]):
                continue
            args = ["ip", "-4", "route", "del", route["destination"], "proto", ROUTE_PROTOCOL]
            if route["gateway"]:
                args += ["via", route["gateway"]]
            if route["interface"]:
                args += ["dev", route["interface"]]
            _run(args)
            changed.append(f"removed {route['destination']}")
        for item in active.values():
            if item["status"] == "active":
                # Adopt only the precise link routes wg-quick generated for these LANs.
                legacy = [r for r in inventory["routes"] if r["destination"] == item["destination"]
                          and r["interface"] == settings.wg_interface and r["gateway"] is None
                          and r["table"] in {"main", "254"} and r["scope"] == "link"
                          and r["protocol"] in {"boot", "static", ""} and not r["managed"]]
                if legacy and item["interface"] == settings.wg_interface:
                    _run(["ip", "-4", "route", "replace", item["destination"], "dev", settings.wg_interface,
                          "proto", ROUTE_PROTOCOL])
                    changed.append(f"adopted {item['destination']}")
                continue
            if item["status"] == "conflict":
                foreign = [r for r in inventory["routes"] if r["destination"] == item["destination"]
                           and r["table"] in {"main", "254"} and not r["managed"]]
                if foreign:
                    raise RuntimeError(f"Ruta ajena en conflicto para {item['destination']}; revisala antes de aplicar")
            args = ["ip", "-4", "route", "add", item["destination"]]
            if item["gateway"]:
                # Require a directly reachable next hop; never guess an interface.
                lookup = json.loads(_run(["ip", "-j", "-4", "route", "get", item["gateway"]]))[0]
                if lookup.get("gateway") or lookup.get("dev") == settings.wg_interface or lookup.get("type") == "local":
                    raise RuntimeError(f"El siguiente salto {item['gateway']} no es un router directamente conectado")
                args += ["via", item["gateway"], "dev", lookup["dev"]]
            else:
                args += ["dev", item["interface"]]
            _run(args + ["proto", ROUTE_PROTOCOL])
            changed.append(f"added {item['destination']}")
        return {"changes": changed, **route_inventory(db)}
