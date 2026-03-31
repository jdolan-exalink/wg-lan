import ipaddress


def is_valid_cidr(value: str) -> bool:
    try:
        ipaddress.ip_network(value, strict=False)
        return True
    except ValueError:
        return False


def subnets_overlap(cidr_a: str, cidr_b: str) -> bool:
    try:
        net_a = ipaddress.ip_network(cidr_a, strict=False)
        net_b = ipaddress.ip_network(cidr_b, strict=False)
        return net_a.overlaps(net_b)
    except ValueError:
        return False


def get_next_available_ip(subnet_cidr: str, used_ips: list[str]) -> str:
    """
    Return the next available host IP in the subnet as a /32 CIDR.
    Skips the first host (reserved for the server gateway).
    Raises ValueError if the subnet is exhausted.
    """
    network = ipaddress.ip_network(subnet_cidr, strict=False)
    hosts = list(network.hosts())

    if not hosts:
        raise ValueError(f"Subnet {subnet_cidr} has no usable hosts")

    # First host is the server gateway — skip it
    available = hosts[1:]

    used_set = set()
    for ip in used_ips:
        # Normalise: strip /32 suffix if present
        used_set.add(ip.split("/")[0])

    for host in available:
        if str(host) not in used_set:
            return f"{host}/32"

    raise ValueError(f"Subnet {subnet_cidr} is exhausted (no IPs available)")


def get_server_ip(subnet_cidr: str) -> str:
    """Return the first host IP (server gateway) for a subnet."""
    network = ipaddress.ip_network(subnet_cidr, strict=False)
    hosts = list(network.hosts())
    if not hosts:
        raise ValueError(f"Subnet {subnet_cidr} has no usable hosts")
    return f"{hosts[0]}/{network.prefixlen}"


def get_usable_host_count(subnet_cidr: str) -> int:
    """Total usable hosts minus 1 (server gateway)."""
    network = ipaddress.ip_network(subnet_cidr, strict=False)
    return max(0, network.num_addresses - 3)  # network + broadcast + server


def format_allowed_ips(cidrs: list[str]) -> str:
    """Join a list of CIDRs into a comma-separated AllowedIPs string."""
    return ", ".join(cidrs)
