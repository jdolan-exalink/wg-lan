from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Peer(Base):
    __tablename__ = "peers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    peer_type: Mapped[str] = mapped_column(String, nullable=False)  # 'roadwarrior' or 'branch_office'
    device_type: Mapped[str | None] = mapped_column(String, nullable=True)  # laptop, ios, android, router, server
    private_key: Mapped[str] = mapped_column(String, nullable=False)
    public_key: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    preshared_key: Mapped[str | None] = mapped_column(String, nullable=True)
    assigned_ip: Mapped[str] = mapped_column(String, unique=True, nullable=False)  # e.g., 10.50.0.2/32
    network_id: Mapped[int] = mapped_column(Integer, ForeignKey("networks.id"), nullable=False)
    tunnel_mode: Mapped[str] = mapped_column(String, nullable=False, default="split")  # 'full' or 'split'
    remote_subnets: Mapped[str | None] = mapped_column(String, nullable=True)  # JSON array, branch_office only
    dns: Mapped[str | None] = mapped_column(String, nullable=True)
    persistent_keepalive: Mapped[int] = mapped_column(Integer, nullable=False, default=25)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)

    network: Mapped["Network"] = relationship("Network")
    group_memberships: Mapped[list["PeerGroupMember"]] = relationship(
        "PeerGroupMember", cascade="all, delete-orphan"
    )


class PeerOverride(Base):
    __tablename__ = "peer_overrides"
    __table_args__ = (
        UniqueConstraint("peer_id", "zone_id", name="uq_peer_zone_override"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    peer_id: Mapped[int] = mapped_column(Integer, ForeignKey("peers.id", ondelete="CASCADE"), nullable=False)
    zone_id: Mapped[int] = mapped_column(Integer, ForeignKey("zones.id", ondelete="CASCADE"), nullable=False)
    action: Mapped[str] = mapped_column(String, nullable=False)  # 'allow' or 'deny'
    reason: Mapped[str | None] = mapped_column(String, nullable=True)

    peer: Mapped["Peer"] = relationship("Peer")
    zone: Mapped["Zone"] = relationship("Zone")
