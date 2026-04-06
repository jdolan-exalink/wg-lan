from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.models.user import User
from app.models.user_group import UserGroup
from app.models.group import PeerGroup
from app.schemas.user import (
    UserCreateRequest,
    UserUpdateRequest,
    UserChangePasswordRequest,
    UserResetPasswordRequest,
    UserResponse,
    UserDetailResponse,
    GroupSummary,
    UserGroupAssignRequest,
    UserNetworkAssignment,
    UserNetworkAssignmentCreate,
    MessageResponse,
)
from app.services.auth_service import hash_password, revoke_all_user_tokens, verify_password
from app.services.audit_service import log as audit_log
from app.services import iptables_service
from app.models.user import UserNetworkAccess
from app.models.network import Network

router = APIRouter(prefix="/api/v1/users", tags=["users-v1"])


@router.get("", response_model=list[UserResponse])
def list_users(
    search: Optional[str] = Query(None, description="Search by username or email"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_admin: Optional[bool] = Query(None, description="Filter by admin status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """List users with optional filtering and search."""
    query = db.query(User)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (User.username.ilike(search_pattern)) |
            (User.email.ilike(search_pattern) if User.email is not None else False)
        )
    
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    if is_admin is not None:
        query = query.filter(User.is_admin == is_admin)
    
    users = query.order_by(User.id).offset(skip).limit(limit).all()
    return users


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    body: UserCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Create a new user."""
    if body.password != body.password_confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match",
        )
    
    existing = db.query(User).filter(User.username == body.username).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")
    
    if body.email:
        existing_email = db.query(User).filter(User.email == body.email).first()
        if existing_email:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")
    
    user = User(
        username=body.username,
        email=body.email,
        password_hash=hash_password(body.password),
        is_active=body.is_active,
        is_admin=body.is_admin,
        must_change_password=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    audit_log(
        db,
        "user.create",
        user_id=current_user.id,
        target_type="user",
        target_id=user.id,
        details={"username": user.username},
        ip_address=request.client.host if request.client else None,
    )
    return user


@router.get("/{user_id}", response_model=UserDetailResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Get user details including assigned groups."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Get user's groups
    user_groups = (
        db.query(PeerGroup)
        .join(UserGroup, UserGroup.group_id == PeerGroup.id)
        .filter(UserGroup.user_id == user_id)
        .all()
    )
    
    response = UserDetailResponse.model_validate(user)
    response.groups = [
        GroupSummary(id=g.id, name=g.name, description=g.description)
        for g in user_groups
    ]
    return response


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    body: UserUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Update user details."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Prevent self-deactivation
    if user_id == current_user.id and body.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account",
        )
    
    # Prevent removing last admin
    if body.is_admin is False and user.is_admin:
        admin_count = db.query(User).filter(User.is_admin == True, User.id != user_id).count()
        if admin_count == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove admin status from the last admin",
            )
    
    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    audit_log(
        db,
        "user.update",
        user_id=current_user.id,
        target_type="user",
        target_id=user_id,
        details={"fields_updated": list(update_data.keys())},
        ip_address=request.client.host if request.client else None,
    )
    return user


@router.post("/{user_id}/disable", response_model=UserResponse)
def disable_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Deactivate a user and invalidate all their sessions."""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account",
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    if user.username == "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate the default admin account",
        )
    
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is already inactive")
    
    user.is_active = False
    db.commit()
    
    # Invalidate all sessions
    revoke_all_user_tokens(db, user_id)
    
    audit_log(
        db,
        "user.disable",
        user_id=current_user.id,
        target_type="user",
        target_id=user_id,
        details={"username": user.username},
        ip_address=request.client.host if request.client else None,
    )
    return user


@router.post("/{user_id}/enable", response_model=UserResponse)
def enable_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Reactivate a user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    if user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is already active")
    
    user.is_active = True
    db.commit()
    db.refresh(user)
    
    audit_log(
        db,
        "user.enable",
        user_id=current_user.id,
        target_type="user",
        target_id=user_id,
        details={"username": user.username},
        ip_address=request.client.host if request.client else None,
    )
    return user


@router.post("/{user_id}/reset-password", response_model=UserResponse)
def reset_password(
    user_id: int,
    body: UserResetPasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Admin reset of user password."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    user.password_hash = hash_password(body.new_password)
    user.must_change_password = True
    db.commit()
    db.refresh(user)
    
    # Invalidate all sessions on password reset
    revoke_all_user_tokens(db, user_id)
    
    audit_log(
        db,
        "user.reset_password",
        user_id=current_user.id,
        target_type="user",
        target_id=user_id,
        details={"username": user.username},
        ip_address=request.client.host if request.client else None,
    )
    return user


@router.post("/{user_id}/change-password", response_model=MessageResponse)
def change_user_password(
    user_id: int,
    body: UserChangePasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Change password (user can change their own, admin can change any)."""
    # Users can only change their own password unless they're admin
    if user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Verify current password (only for self-change)
    if user_id == current_user.id:
        if not verify_password(body.current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            )
    
    if body.new_password != body.new_password_confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New passwords do not match",
        )
    
    if body.current_password == body.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password",
        )
    
    user.password_hash = hash_password(body.new_password)
    user.must_change_password = False
    db.commit()
    
    # Invalidate all sessions on password change
    revoke_all_user_tokens(db, user_id)
    
    audit_log(
        db,
        "auth.password_change",
        user_id=current_user.id,
        target_type="user",
        target_id=user_id,
        ip_address=request.client.host if request.client else None,
    )
    return MessageResponse(message="Password changed successfully")


# ── User-Group Assignment ─────────────────────────────────────

@router.get("/{user_id}/groups", response_model=list[GroupSummary])
def get_user_groups(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Get groups assigned to a user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    groups = (
        db.query(PeerGroup)
        .join(UserGroup, UserGroup.group_id == PeerGroup.id)
        .filter(UserGroup.user_id == user_id)
        .all()
    )
    
    return [
        GroupSummary(id=g.id, name=g.name, description=g.description)
        for g in groups
    ]


@router.post("/{user_id}/groups", response_model=list[GroupSummary])
def assign_user_groups(
    user_id: int,
    body: UserGroupAssignRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Assign groups to a user (replaces existing assignments)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Validate all groups exist
    groups = db.query(PeerGroup).filter(PeerGroup.id.in_(body.group_ids)).all()
    if len(groups) != len(body.group_ids):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more groups not found")
    
    # Remove existing assignments
    db.query(UserGroup).filter(UserGroup.user_id == user_id).delete()
    
    # Add new assignments
    for group_id in body.group_ids:
        user_group = UserGroup(user_id=user_id, group_id=group_id)
        db.add(user_group)
    
    db.commit()
    
    audit_log(
        db,
        "user.groups_updated",
        user_id=current_user.id,
        target_type="user",
        target_id=user_id,
        details={"group_ids": body.group_ids},
        ip_address=request.client.host if request.client else None,
    )
    
    return [
        GroupSummary(id=g.id, name=g.name, description=g.description)
        for g in groups
    ]


@router.delete("/{user_id}/groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_user_group(
    user_id: int,
    group_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Remove a group assignment from a user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    group = db.query(PeerGroup).filter(PeerGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    
    db.query(UserGroup).filter(
        UserGroup.user_id == user_id,
        UserGroup.group_id == group_id,
    ).delete()
    db.commit()
    
    audit_log(
        db,
        "user.group_removed",
        user_id=current_user.id,
        target_type="user",
        target_id=user_id,
        details={"group_id": group_id, "group_name": group.name},
        ip_address=request.client.host if request.client else None,
    )


# ── User-Network Assignment ─────────────────────────────────────

def _apply_user_network_changes(db: Session) -> None:
    """Re-apply iptables rules after user network assignment changes."""
    try:
        iptables_service.apply_iptables_rules(db)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"iptables re-apply after user network change: {e}")


@router.get("/{user_id}/networks", response_model=list[UserNetworkAssignment])
def get_user_networks(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """List all networks assigned to a user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    assignments = db.query(UserNetworkAccess).filter(
        UserNetworkAccess.user_id == user_id
    ).all()
    
    result = []
    for a in assignments:
        network = db.query(Network).filter(Network.id == a.network_id).first()
        if network:
            result.append(UserNetworkAssignment(
                id=a.id,
                network_id=a.network_id,
                network_name=network.name,
                subnet=network.subnet,
                network_type=network.network_type,
                action=a.action,
            ))
    return result


@router.post("/{user_id}/networks", response_model=UserNetworkAssignment, status_code=status.HTTP_201_CREATED)
def assign_network_to_user(
    user_id: int,
    body: UserNetworkAssignmentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Assign a network to a user with allow/deny action."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    network = db.query(Network).filter(Network.id == body.network_id).first()
    if not network:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Network not found")
    
    # Check if assignment already exists
    existing = db.query(UserNetworkAccess).filter(
        UserNetworkAccess.user_id == user_id,
        UserNetworkAccess.network_id == body.network_id,
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Network already assigned to this user")
    
    assignment = UserNetworkAccess(
        user_id=user_id,
        network_id=body.network_id,
        action=body.action,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    
    _apply_user_network_changes(db)
    
    audit_log(
        db,
        "user.network_assigned",
        user_id=current_user.id,
        target_type="user",
        target_id=user_id,
        details={"network_id": body.network_id, "network_name": network.name, "action": body.action},
        ip_address=request.client.host if request.client else None,
    )
    
    return UserNetworkAssignment(
        id=assignment.id,
        network_id=assignment.network_id,
        network_name=network.name,
        subnet=network.subnet,
        network_type=network.network_type,
        action=assignment.action,
    )


@router.delete("/{user_id}/networks/{network_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_network_from_user(
    user_id: int,
    network_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Remove a network assignment from a user."""
    assignment = db.query(UserNetworkAccess).filter(
        UserNetworkAccess.user_id == user_id,
        UserNetworkAccess.network_id == network_id,
    ).first()
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Network assignment not found")
    
    db.delete(assignment)
    db.commit()
    _apply_user_network_changes(db)
    
    audit_log(
        db,
        "user.network_removed",
        user_id=current_user.id,
        target_type="user",
        target_id=user_id,
        details={"network_id": network_id},
        ip_address=request.client.host if request.client else None,
    )
