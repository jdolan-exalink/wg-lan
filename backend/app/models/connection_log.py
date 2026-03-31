from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ConnectionLog(Base):
    """Logs WireGuard connection events for monitoring and troubleshooting."""
    __tablename__ = "connection_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    peer_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("peers.id"), nullable=True)
    peer_name: Mapped[str | None] = mapped_column(String, nullable=True)
    peer_ip: Mapped[str | None] = mapped_column(String, nullable=True)
    event_type: Mapped[str] = mapped_column(String, nullable=False)  # handshake, disconnect, timeout, firewall_block, config_applied, interface_up, interface_down, error
    severity: Mapped[str] = mapped_column(String, nullable=False, default="info")  # info, warning, error, critical
    message: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON with extra context
    source_ip: Mapped[str | None] = mapped_column(String, nullable=True)  # remote endpoint
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
