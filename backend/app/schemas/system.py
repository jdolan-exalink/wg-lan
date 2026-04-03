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
    client_retry_enabled: bool = False
    admin_port: int = 7777
    api_http_port: int = 7771
    api_https_port: int = 7772
    api_http_enabled: bool = True
    vpn_domain: str | None = None

    model_config = {"from_attributes": True}


class ServerConfigUpdate(BaseModel):
    address: str | None = None
    listen_port: int | None = None
    dns: str | None = None
    mtu: int | None = None
    post_up: str | None = None
    post_down: str | None = None
    endpoint: str | None = None
    client_retry_enabled: bool | None = None
    admin_port: int | None = None
    api_http_port: int | None = None
    api_https_port: int | None = None
    api_http_enabled: bool | None = None
    vpn_domain: str | None = None


class RegenerateKeyResponse(BaseModel):
    public_key: str
    message: str


class HealthResponse(BaseModel):
    status: str
    db: str
    wg_interface: str
    tunnel_count: int
    uptime_seconds: int
    is_initialized: bool = True

    model_config = {"from_attributes": True}


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
    disk_percent: float
    disk_used_gb: float
    disk_total_gb: float


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


class ADConfigResponse(BaseModel):
    ad_enabled: bool
    ad_server: str | None
    ad_server_backup: str | None
    ad_base_dn: str | None
    ad_bind_dn: str | None
    ad_user_filter: str | None
    ad_group_filter: str | None
    ad_use_ssl: bool
    ad_require_membership: bool

    model_config = {"from_attributes": True}


class ADConfigUpdate(BaseModel):
    ad_enabled: bool | None = None
    ad_server: str | None = None
    ad_server_backup: str | None = None
    ad_base_dn: str | None = None
    ad_bind_dn: str | None = None
    ad_bind_password: str | None = None
    ad_user_filter: str | None = None
    ad_group_filter: str | None = None
    ad_use_ssl: bool | None = None
    ad_require_membership: bool | None = None


class ADGroupMappingResponse(BaseModel):
    id: int
    ad_group_dn: str
    ad_group_name: str
    netloom_group_id: int
    netloom_group_name: str | None = None
    enabled: bool
    priority: int

    model_config = {"from_attributes": True}


class ADGroupMappingCreate(BaseModel):
    ad_group_dn: str
    ad_group_name: str
    netloom_group_id: int
    enabled: bool = True
    priority: int = 0


class ADGroupMappingUpdate(BaseModel):
    netloom_group_id: int | None = None
    enabled: bool | None = None
    priority: int | None = None


class ADGroupMappingBulkCreate(BaseModel):
    mappings: list[ADGroupMappingCreate]


class ADGroupsFromADResponse(BaseModel):
    groups: list[dict]
