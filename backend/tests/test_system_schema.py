import pytest
from pydantic import ValidationError

from app.schemas.system import ServerConfigUpdate


def test_server_config_update_rejects_blank_address():
    with pytest.raises(ValidationError):
        ServerConfigUpdate(address="   ")


def test_server_config_update_rejects_invalid_address():
    with pytest.raises(ValidationError):
        ServerConfigUpdate(address="not-a-cidr")


def test_server_config_update_normalizes_optional_blank_strings():
    body = ServerConfigUpdate(
        dns="   ",
        post_up="  ",
        post_down="  ",
        vpn_domain="  ",
    )

    assert body.dns is None
    assert body.post_up is None
    assert body.post_down is None
    assert body.vpn_domain is None


def test_server_config_update_trims_address_and_endpoint():
    body = ServerConfigUpdate(
        address=" 100.79.0.1/16 ",
        endpoint=" vpn.sodecar.ar ",
    )

    assert body.address == "100.79.0.1/16"
    assert body.endpoint == "vpn.sodecar.ar"
