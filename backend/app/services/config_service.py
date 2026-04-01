"""
Config Service
==============
Generates WireGuard .conf file contents for clients and the server.
All config strings are pure text — no subprocess calls here.
"""

import json

from app.config import settings
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
            # No zones assigned yet — use VPN subnet as placeholder
            # This keeps the config valid while allowing the peer to connect
            # Once onboarding is done and zones are created, re-download the config
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


def generate_mikrotik_config(
    peer: Peer,
    server_config: ServerConfig,
    allowed_cidrs: list[str],
) -> str:
    """
    Build a MikroTik RouterOS WireGuard import file.
    
    MikroTik uses its own import format (NOT standard .conf):
    - No [Interface]/[Peer] section headers
    - Uses key: value format (no spaces around colon)
    - Multiple allowed-addresses on one line, comma-separated
    
    This format is used with: /interface wireguard/wg-import file=
    """
    # Build allowed-address list (comma-separated, no spaces)
    if peer.tunnel_mode == "full":
        allowed_addresses = "0.0.0.0/0,::/0"
    else:
        if allowed_cidrs:
            allowed_addresses = ",".join(allowed_cidrs)
        else:
            allowed_addresses = "0.0.0.0/32"

    # MikroTik import format (NOT standard WireGuard .conf)
    lines = [
        f"interface: wg0",
        f"public-key: {server_config.public_key}",
        f"private-key: {peer.private_key}",
        f"allowed-address: {allowed_addresses}",
        f"client-address: {peer.assigned_ip}",
        f"client-endpoint: {server_config.endpoint}:{server_config.listen_port}",
    ]
    
    if peer.dns:
        lines.append(f"client-dns: {peer.dns}")
    elif server_config.dns:
        lines.append(f"client-dns: {server_config.dns}")
    
    if peer.persistent_keepalive and peer.persistent_keepalive > 0:
        lines.append(f"client-keepalive: {peer.persistent_keepalive}")
    
    if peer.preshared_key:
        lines.append(f"preshared-key: {peer.preshared_key}")

    # Join with LF (Unix line endings) and add final newline
    return "\n".join(lines) + "\n"


def generate_mikrotik_manual_commands(
    peer: Peer,
    server_config: ServerConfig,
    allowed_cidrs: list[str],
) -> str:
    """
    Generate MikroTik RouterOS CLI commands for manual configuration.
    This is often more reliable than importing a file.
    
    Returns RouterOS CLI commands that can be pasted directly into the terminal.
    Includes:
    - WireGuard interface creation
    - IP address assignment
    - Peer configuration
    - Static routes to VPN subnet and all allowed networks
    """
    import ipaddress
    
    # Build allowed-address list (comma-separated, no spaces)
    if peer.tunnel_mode == "full":
        allowed_addresses = "0.0.0.0/0,::/0"
    else:
        if allowed_cidrs:
            allowed_addresses = ",".join(allowed_cidrs)
        else:
            allowed_addresses = "0.0.0.0/32"
    
    # Parse endpoint
    endpoint = server_config.endpoint
    port = server_config.listen_port
    
    # Generate interface name from peer name (safe characters only)
    iface_name = f"wg-{peer.name.lower().replace(' ', '-').replace('_', '-')}"
    
    commands = [
        f"# === WireGuard Interface ===",
        f"/interface wireguard add name={iface_name} private-key=\"{peer.private_key}\"",
        f"/ip address add address={peer.assigned_ip} interface={iface_name}",
        f"",
        f"# === WireGuard Peer ===",
        f"/interface wireguard peers add interface={iface_name} public-key=\"{server_config.public_key}\" endpoint-address={endpoint} endpoint-port={port} allowed-address={allowed_addresses} persistent-keepalive={peer.persistent_keepalive or 25}",
    ]
    
    if peer.dns or server_config.dns:
        dns = peer.dns or server_config.dns
        commands.append(f"/ip dns set servers={dns}")
    
    # Add static routes to VPN subnet and all allowed networks
    commands.append(f"")
    commands.append(f"# === Static Routes ===")
    
    # Parse VPN subnet
    vpn_network = ipaddress.ip_network(server_config.address, strict=False)
    vpn_subnet_str = str(vpn_network)
    
    # Route to VPN subnet (so MikroTik can reach other VPN peers)
    commands.append(f"/ip route add dst-address={vpn_subnet_str} gateway={iface_name}")
    
    # Routes to all allowed networks (zones, other branch offices, etc.)
    for cidr in allowed_cidrs:
        try:
            cidr_network = ipaddress.ip_network(cidr, strict=False)
            # Skip if this CIDR is the VPN subnet itself or contained within it
            if cidr_network == vpn_network or cidr_network.subnet_of(vpn_network):
                continue
            commands.append(f"/ip route add dst-address={cidr} gateway={iface_name}")
        except ValueError:
            # Skip invalid CIDRs
            continue
    
    return "\n".join(commands) + "\n"


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
