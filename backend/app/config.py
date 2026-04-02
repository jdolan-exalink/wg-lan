from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "NETLOOM_"}

    # Security
    secret_key: str = "change-me-to-a-random-string"
    admin_password: str = "admin123"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    # Server
    host: str = "0.0.0.0"
    port: int = 7777
    debug: bool = False

    # Database
    db_path: str = "./data/netloom.db"

    # WireGuard
    server_endpoint: str = "vpn.example.com"
    server_port: int = 51820
    subnet: str = "100.169.0.0/16"
    wg_config_path: str = "/etc/wireguard"
    wg_interface: str = "wg0"
    wg_default_keepalive: int = 25

    # Sync
    config_sync_interval: int = 60
    device_registration_required: bool = True

    # TLS/HTTPS
    tls_enabled: bool = False
    tls_cert_path: str = "/app/certs/server.crt"
    tls_key_path: str = "/app/certs/server.key"
    tls_host: str = "0.0.0.0"
    tls_port: int = 7776
    http_port: int = 7777
    client_api_port: int = 7771  # Dedicated port for client API (HTTP)
    client_api_tls_port: int = 7772  # Dedicated port for client API (HTTPS)
    tls_auto_generate: bool = True  # Auto-generate self-signed cert if not exists
    tls_cert_days: int = 3650  # Certificate validity in days (10 years)
    tls_country: str = "US"
    tls_state: str = "California"
    tls_locality: str = "San Francisco"
    tls_organization: str = "NetLoom"
    tls_common_name: str = "netloom.local"

    # CORS
    cors_origins: list[str] = ["http://localhost:5173"]

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.db_path}"

    @property
    def wg_config_file(self) -> str:
        return f"{self.wg_config_path}/{self.wg_interface}.conf"


settings = Settings()
