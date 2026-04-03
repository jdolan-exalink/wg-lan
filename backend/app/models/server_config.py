from datetime import datetime
from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ServerConfig(Base):
    __tablename__ = "server_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    interface_name: Mapped[str] = mapped_column(String, unique=True, nullable=False, default="wg0")
    private_key: Mapped[str] = mapped_column(String, nullable=False)
    public_key: Mapped[str] = mapped_column(String, nullable=False)
    listen_port: Mapped[int] = mapped_column(Integer, nullable=False, default=51820)
    address: Mapped[str] = mapped_column(String, nullable=False)  # e.g., 10.50.0.1/24
    dns: Mapped[str | None] = mapped_column(String, nullable=True)
    mtu: Mapped[int | None] = mapped_column(Integer, nullable=True, default=1420)
    post_up: Mapped[str | None] = mapped_column(String, nullable=True)
    post_down: Mapped[str | None] = mapped_column(String, nullable=True)
    endpoint: Mapped[str] = mapped_column(String, nullable=False)  # Public hostname/IP
    firewall_enabled: Mapped[bool] = mapped_column(nullable=False, default=False)  # When False, all traffic is allowed (permissive mode)
    client_retry_enabled: Mapped[bool] = mapped_column(nullable=False, default=False)  # When True, client will retry on connection failure
    last_config_changed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())  # Updated when routes/peers change
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    # Ports configuration
    admin_port: Mapped[int] = mapped_column(Integer, nullable=False, default=7777)
    api_http_port: Mapped[int] = mapped_column(Integer, nullable=False, default=7771)
    api_https_port: Mapped[int] = mapped_column(Integer, nullable=False, default=7772)
    api_http_enabled: Mapped[bool] = mapped_column(nullable=False, default=True)
    vpn_domain: Mapped[str | None] = mapped_column(String, nullable=True)
    # Active Directory Configuration
    ad_enabled: Mapped[bool] = mapped_column(nullable=False, default=False)
    ad_server: Mapped[str | None] = mapped_column(String, nullable=True)
    ad_server_backup: Mapped[str | None] = mapped_column(String, nullable=True)
    ad_base_dn: Mapped[str | None] = mapped_column(String, nullable=True)
    ad_bind_dn: Mapped[str | None] = mapped_column(String, nullable=True)  # Format: DOMAIN\username
    ad_bind_password: Mapped[str | None] = mapped_column(String, nullable=True)
    ad_user_filter: Mapped[str | None] = mapped_column(String, nullable=True)
    ad_group_filter: Mapped[str | None] = mapped_column(String, nullable=True)
    ad_use_ssl: Mapped[bool] = mapped_column(nullable=False, default=True)
    ad_require_membership: Mapped[bool] = mapped_column(nullable=False, default=True)
