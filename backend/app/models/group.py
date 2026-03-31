from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PeerGroup(Base):
    __tablename__ = "peer_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    policies: Mapped[list["Policy"]] = relationship(
        "Policy", back_populates="group", cascade="all, delete-orphan"
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


class Policy(Base):
    __tablename__ = "policies"
    __table_args__ = (UniqueConstraint("group_id", "zone_id", name="uq_group_zone"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(Integer, ForeignKey("peer_groups.id", ondelete="CASCADE"), nullable=False)
    zone_id: Mapped[int] = mapped_column(Integer, ForeignKey("zones.id", ondelete="CASCADE"), nullable=False)
    action: Mapped[str] = mapped_column(String, nullable=False)  # 'allow' or 'deny'

    group: Mapped["PeerGroup"] = relationship("PeerGroup", back_populates="policies")
    zone: Mapped["Zone"] = relationship("Zone")
