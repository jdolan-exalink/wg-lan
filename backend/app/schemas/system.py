from pydantic import BaseModel


class ServerConfigResponse(BaseModel):
    id: int
    interface_name: str
    public_key: str
    listen_port: int
    address: str
    dns: str | None
    mtu: int | None
    post_up: str | None
    post_down: str | None
    endpoint: str

    model_config = {"from_attributes": True}


class ServerConfigUpdate(BaseModel):
    address: str | None = None
    listen_port: int | None = None
    dns: str | None = None
    mtu: int | None = None
    post_up: str | None = None
    post_down: str | None = None
    endpoint: str | None = None


class RegenerateKeyResponse(BaseModel):
    public_key: str
    message: str


class HealthResponse(BaseModel):
    status: str
    db: str
    wg_interface: str


class BackupResponse(BaseModel):
    message: str
    path: str


class FirewallStatusResponse(BaseModel):
    firewall_enabled: bool


class FirewallStatusUpdate(BaseModel):
    firewall_enabled: bool
