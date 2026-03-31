from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "NETLOOM_"}

    # Security
    secret_key: str = "change-me-to-a-random-string"
    admin_password: str = "admin123"
    access_token_expire_hours: int = 24

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

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.db_path}"

    @property
    def wg_config_file(self) -> str:
        return f"{self.wg_config_path}/{self.wg_interface}.conf"


settings = Settings()
