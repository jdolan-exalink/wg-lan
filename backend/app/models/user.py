from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.device import Device
    from app.models.group import UserGroup
    from app.models.network import Network
    from app.models.peer import Peer
    from app.models.refresh_token import RefreshToken


class UserNetworkAccess(Base):
    """Direct assignment of a network to a user with allow/deny action."""
    __tablename__ = "user_network_access"
    __table_args__ = (
        UniqueConstraint("user_id", "network_id", name="uq_user_network_access"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    network_id: Mapped[int] = mapped_column(Integer, ForeignKey("networks.id", ondelete="CASCADE"), nullable=False)
    action: Mapped[str] = mapped_column(String, nullable=False, default="allow")  # 'allow' or 'deny'

    user: Mapped["User"] = relationship("User", back_populates="network_access")
    network: Mapped["Network"] = relationship("Network", back_populates="user_access")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    email: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    must_change_password: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_failed_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    failed_login_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    auth_source: Mapped[str] = mapped_column(String, nullable=False, default="local")  # 'local' or 'ad'

    # Relationships
    group_memberships: Mapped[list["UserGroup"]] = relationship(
        "UserGroup", back_populates="user", cascade="all, delete-orphan"
    )
    devices: Mapped[list["Device"]] = relationship(
        "Device", back_populates="user", cascade="all, delete-orphan"
    )
    peers: Mapped[list["Peer"]] = relationship(
        "Peer", back_populates="user", foreign_keys="Peer.user_id"
    )
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )
    network_access: Mapped[list["UserNetworkAccess"]] = relationship(
        "UserNetworkAccess", back_populates="user", cascade="all, delete-orphan"
    )
