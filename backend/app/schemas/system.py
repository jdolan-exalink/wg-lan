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


class SystemMetricsResponse(BaseModel):
    ram_percent: float
    ram_used_gb: float
    ram_total_gb: float
    cpu_percent: float
    cpu_count: int


class TLSConfigResponse(BaseModel):
    tls_enabled: bool
    tls_cert_path: str
    tls_key_path: str
    tls_host: str
    tls_port: int
    http_port: int
    tls_auto_generate: bool
    tls_cert_days: int
    tls_country: str
    tls_state: str
    tls_locality: str
    tls_organization: str
    tls_common_name: str
    cert_exists: bool
    key_exists: bool

    model_config = {"from_attributes": False}


class TLSConfigUpdate(BaseModel):
    tls_enabled: bool | None = None
    tls_cert_path: str | None = None
    tls_key_path: str | None = None
    tls_host: str | None = None
    tls_port: int | None = None
    http_port: int | None = None
    tls_auto_generate: bool | None = None
    tls_cert_days: int | None = None
    tls_country: str | None = None
    tls_state: str | None = None
    tls_locality: str | None = None
    tls_organization: str | None = None
    tls_common_name: str | None = None


class TLSRegenerateCertResponse(BaseModel):
    message: str
    cert_path: str
    key_path: str
