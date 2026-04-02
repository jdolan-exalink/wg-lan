from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class Device(Base):
    """Registered client device for managed peers."""
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    device_name: Mapped[str] = mapped_column(String, nullable=False)
    hostname: Mapped[str | None] = mapped_column(String, nullable=True)
    os_type: Mapped[str | None] = mapped_column(String, nullable=True)  # linux, windows, macos, android, ios
    device_fingerprint: Mapped[str | None] = mapped_column(String, nullable=True, index=True)  # For future device binding
    status: Mapped[str] = mapped_column(String, nullable=False, default="active")  # active, inactive, revoked
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    config_revision: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship("User", back_populates="devices")
