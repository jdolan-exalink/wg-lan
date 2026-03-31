"""
Config Service
==============
Generates WireGuard .conf file contents for clients and the server.
All config strings are pure text — no subprocess calls here.
"""

from app.models.peer import Peer
from app.models.server_config import ServerConfig
from app.utils.ip_utils import format_allowed_ips


def generate_client_config(
    peer: Peer,
    server_config: ServerConfig,
    allowed_cidrs: list[str],
) -> str:
    """
    Build the [Interface] + [Peer] .conf content for a client device.
    allowed_cidrs is the compiled list from policy_compiler.
    If tunnel_mode is 'full', AllowedIPs is overridden to 0.0.0.0/0, ::/0.
    """
    if peer.tunnel_mode == "full":
        client_allowed_ips = "0.0.0.0/0, ::/0"
    else:
        if allowed_cidrs:
            client_allowed_ips = format_allowed_ips(allowed_cidrs)
        else:
            # Use 0.0.0.0/32 as placeholder - routes no traffic but keeps config valid
            client_allowed_ips = "0.0.0.0/32"

    lines = [
        "[Interface]",
        f"PrivateKey = {peer.private_key}",
        f"Address = {peer.assigned_ip}",
    ]
    if peer.dns:
        lines.append(f"DNS = {peer.dns}")
    elif server_config.dns:
        lines.append(f"DNS = {server_config.dns}")

    lines += [
        "",
        "[Peer]",
        f"PublicKey = {server_config.public_key}",
    ]
    if peer.preshared_key:
        lines.append(f"PresharedKey = {peer.preshared_key}")

    lines += [
        f"Endpoint = {server_config.endpoint}:{server_config.listen_port}",
        f"AllowedIPs = {client_allowed_ips}",
    ]
    if peer.persistent_keepalive and peer.persistent_keepalive > 0:
        lines.append(f"PersistentKeepalive = {peer.persistent_keepalive}")

    return "\n".join(lines) + "\n"


def generate_server_peer_block(peer: Peer, server_allowed_ips: list[str]) -> str:
    """
    Build a single [Peer] block for the server-side wg0.conf.
    server_allowed_ips: for RoadWarrior = [assigned_ip/32]
                        for BranchOffice = [assigned_ip/32] + remote_subnets
    """
    lines = [
        "[Peer]",
        f"# {peer.name}",
        f"PublicKey = {peer.public_key}",
    ]
    if peer.preshared_key:
        lines.append(f"PresharedKey = {peer.preshared_key}")

    lines.append(f"AllowedIPs = {format_allowed_ips(server_allowed_ips)}")
    return "\n".join(lines)


def generate_full_server_config(
    server_config: ServerConfig,
    enabled_peers: list[tuple[Peer, list[str]]],  # (peer, server_allowed_ips)
) -> str:
    """
    Build the complete wg0.conf for the server side.
    enabled_peers is a list of (peer, server_allowed_ips) for all active peers.
    """
    lines = [
        "[Interface]",
        f"PrivateKey = {server_config.private_key}",
        f"Address = {server_config.address}",
        f"ListenPort = {server_config.listen_port}",
    ]
    if server_config.mtu:
        lines.append(f"MTU = {server_config.mtu}")
    if server_config.post_up:
        lines.append(f"PostUp = {server_config.post_up}")
    if server_config.post_down:
        lines.append(f"PostDown = {server_config.post_down}")

    for peer, server_allowed_ips in enabled_peers:
        lines += ["", generate_server_peer_block(peer, server_allowed_ips)]

    return "\n".join(lines) + "\n"


def build_server_allowed_ips(peer: Peer) -> list[str]:
    """Return the AllowedIPs list for the server side of a peer."""
    import json
    ips = [peer.assigned_ip]
    if peer.peer_type == "branch_office" and peer.remote_subnets:
        remote = json.loads(peer.remote_subnets)
        ips.extend(remote)
    return ips
