from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.peer import Peer
    from app.models.device import Device


class ConfigRevision(Base):
    """Tracks configuration changes for delta sync."""
    __tablename__ = "config_revisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    peer_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("peers.id", ondelete="SET NULL"), nullable=True)
    device_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("devices.id", ondelete="SET NULL"), nullable=True)
    revision_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    change_type: Mapped[str] = mapped_column(String, nullable=False)  # network_added, network_removed, policy_changed, peer_updated, etc.
    changes: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON serialized change details
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    peer: Mapped["Peer | None"] = relationship("Peer")
    device: Mapped["Device | None"] = relationship("Device")
