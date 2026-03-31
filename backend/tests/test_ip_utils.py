import pytest
from app.utils.ip_utils import (
    format_allowed_ips,
    get_next_available_ip,
    get_server_ip,
    get_usable_host_count,
    is_valid_cidr,
    subnets_overlap,
)


def test_is_valid_cidr():
    assert is_valid_cidr("10.50.0.0/24") is True
    assert is_valid_cidr("192.168.1.0/24") is True
    assert is_valid_cidr("10.0.0.1/32") is True
    assert is_valid_cidr("not-a-cidr") is False
    assert is_valid_cidr("10.50.0.300/24") is False


def test_subnets_overlap():
    assert subnets_overlap("10.50.0.0/24", "10.50.0.0/24") is True
    assert subnets_overlap("10.50.0.0/24", "10.50.0.128/25") is True
    assert subnets_overlap("10.50.0.0/24", "10.50.1.0/24") is False
    assert subnets_overlap("192.168.0.0/16", "192.168.1.0/24") is True


def test_get_next_available_ip():
    # First available is .2 (server takes .1)
    ip = get_next_available_ip("10.50.0.0/24", [])
    assert ip == "10.50.0.2/32"

    # Skip used IPs
    ip = get_next_available_ip("10.50.0.0/24", ["10.50.0.2", "10.50.0.3"])
    assert ip == "10.50.0.4/32"


def test_get_next_available_ip_exhausted():
    # /30 has 4 addresses, 2 usable hosts (one reserved for server = 1 left)
    with pytest.raises(ValueError, match="exhausted"):
        get_next_available_ip("10.50.0.0/30", ["10.50.0.2"])


def test_get_server_ip():
    assert get_server_ip("10.50.0.0/24") == "10.50.0.1/24"
    assert get_server_ip("192.168.10.0/24") == "192.168.10.1/24"


def test_format_allowed_ips():
    cidrs = ["10.10.10.0/24", "10.10.20.0/24"]
    assert format_allowed_ips(cidrs) == "10.10.10.0/24, 10.10.20.0/24"


def test_get_usable_host_count():
    assert get_usable_host_count("10.50.0.0/24") == 253  # 256 - 3
    assert get_usable_host_count("10.50.0.0/30") == 1    # 4 - 3
