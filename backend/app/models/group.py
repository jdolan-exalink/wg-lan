from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.network import Network
    from app.models.peer import Peer
    from app.models.user_group import UserGroup


class ADGroupMapping(Base):
    """AD Group to NetLoom Group mapping."""
    __tablename__ = "ad_group_mappings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ad_group_dn: Mapped[str] = mapped_column(String, nullable=False)
    ad_group_name: Mapped[str] = mapped_column(String, nullable=False)
    netloom_group_id: Mapped[int] = mapped_column(Integer, ForeignKey("peer_groups.id", ondelete="CASCADE"), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    netloom_group: Mapped["PeerGroup"] = relationship("PeerGroup", back_populates="ad_mappings")


class GroupNetworkAccess(Base):
    """Direct assignment of a network to a group with allow/deny action."""
    __tablename__ = "group_network_access"
    __table_args__ = (
        UniqueConstraint("group_id", "network_id", name="uq_group_network_access"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(Integer, ForeignKey("peer_groups.id", ondelete="CASCADE"), nullable=False)
    network_id: Mapped[int] = mapped_column(Integer, ForeignKey("networks.id", ondelete="CASCADE"), nullable=False)
    action: Mapped[str] = mapped_column(String, nullable=False, default="allow")  # 'allow' or 'deny'

    group: Mapped["PeerGroup"] = relationship("PeerGroup", back_populates="network_access")
    network: Mapped["Network"] = relationship("Network", back_populates="group_access")


class PeerGroup(Base):
    __tablename__ = "peer_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
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
    user_groups: Mapped[list["UserGroup"]] = relationship(
        "UserGroup", back_populates="group", cascade="all, delete-orphan"
    )
    network_access: Mapped[list["GroupNetworkAccess"]] = relationship(
        "GroupNetworkAccess", back_populates="group", cascade="all, delete-orphan"
    )
    ad_mappings: Mapped[list["ADGroupMapping"]] = relationship(
        "ADGroupMapping", back_populates="netloom_group", cascade="all, delete-orphan"
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
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # display & evaluation order
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    source_group: Mapped["PeerGroup"] = relationship("PeerGroup", back_populates="source_policies", foreign_keys=[source_group_id])
    dest_group: Mapped["PeerGroup"] = relationship("PeerGroup", back_populates="dest_policies", foreign_keys=[dest_group_id])

    @property
    def source_group_name(self) -> str | None:
        return self.source_group.name if self.source_group else None

    @property
    def dest_group_name(self) -> str | None:
        return self.dest_group.name if self.dest_group else None
