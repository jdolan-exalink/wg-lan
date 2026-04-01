from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.peer import Peer


class PeerGroup(Base):
    __tablename__ = "peer_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    source_policies: Mapped[list["Policy"]] = relationship(
        "Policy", back_populates="source_group", cascade="all, delete-orphan",
        foreign_keys="Policy.source_group_id"
    )
    dest_policies: Mapped[list["Policy"]] = relationship(
        "Policy", back_populates="dest_group", cascade="all, delete-orphan",
        foreign_keys="Policy.dest_group_id"
    )
    members: Mapped[list["PeerGroupMember"]] = relationship(
        "PeerGroupMember", back_populates="group", cascade="all, delete-orphan"
    )


class PeerGroupMember(Base):
    __tablename__ = "peer_group_members"
    __table_args__ = (UniqueConstraint("peer_id", "group_id", name="uq_peer_group"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    peer_id: Mapped[int] = mapped_column(Integer, ForeignKey("peers.id", ondelete="CASCADE"), nullable=False)
    group_id: Mapped[int] = mapped_column(Integer, ForeignKey("peer_groups.id", ondelete="CASCADE"), nullable=False)

    group: Mapped["PeerGroup"] = relationship("PeerGroup", back_populates="members")
    peer: Mapped["Peer"] = relationship("Peer", back_populates="group_memberships")


class Policy(Base):
    __tablename__ = "policies"
    __table_args__ = (
        UniqueConstraint("source_group_id", "dest_group_id", "direction", name="uq_policy_source_dest_direction"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_group_id: Mapped[int] = mapped_column(Integer, ForeignKey("peer_groups.id", ondelete="CASCADE"), nullable=False)
    dest_group_id: Mapped[int] = mapped_column(Integer, ForeignKey("peer_groups.id", ondelete="CASCADE"), nullable=False)
    direction: Mapped[str] = mapped_column(String, nullable=False, default="both")  # 'outbound', 'inbound', 'both'
    action: Mapped[str] = mapped_column(String, nullable=False, default="allow")  # 'allow' or 'deny'
    enabled: Mapped[bool] = mapped_column(nullable=False, default=True)  # When False, rule is inactive
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    source_group: Mapped["PeerGroup"] = relationship("PeerGroup", back_populates="source_policies", foreign_keys=[source_group_id])
    dest_group: Mapped["PeerGroup"] = relationship("PeerGroup", back_populates="dest_policies", foreign_keys=[dest_group_id])
