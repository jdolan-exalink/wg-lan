from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class IpGroup(Base):
    """A named group of specific IPs within a network (e.g. 'Servidores', 'Impresoras')."""
    __tablename__ = "ip_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    network_id: Mapped[int] = mapped_column(Integer, ForeignKey("networks.id", ondelete="CASCADE"), nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    network = relationship("Network", back_populates="ip_groups")
    entries: Mapped[list["IpGroupEntry"]] = relationship(
        "IpGroupEntry", back_populates="ip_group", cascade="all, delete-orphan",
        order_by="IpGroupEntry.ip_address",
    )
    dest_policies: Mapped[list["Policy"]] = relationship(
        "Policy", back_populates="dest_ip_group", cascade="all, delete-orphan",
    )


class IpGroupEntry(Base):
    """A single IP address with an optional label inside an IpGroup."""
    __tablename__ = "ip_group_entries"
    __table_args__ = (
        UniqueConstraint("ip_group_id", "ip_address", name="uq_ip_group_entry"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ip_group_id: Mapped[int] = mapped_column(Integer, ForeignKey("ip_groups.id", ondelete="CASCADE"), nullable=False)
    ip_address: Mapped[str] = mapped_column(String, nullable=False)
    label: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    ip_group: Mapped["IpGroup"] = relationship("IpGroup", back_populates="entries")
