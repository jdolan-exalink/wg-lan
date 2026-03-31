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
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
