import json

from sqlalchemy.orm import Session

from app.models.audit import AuditLog


def log(
    db: Session,
    action: str,
    user_id: int | None = None,
    target_type: str | None = None,
    target_id: int | None = None,
    details: dict | None = None,
    ip_address: str | None = None,
    actor_device_id: int | None = None,
) -> None:
    entry = AuditLog(
        action=action,
        user_id=user_id,
        target_type=target_type,
        target_id=target_id,
        details=json.dumps(details) if details else None,
        ip_address=ip_address,
        actor_device_id=actor_device_id,
    )
    db.add(entry)
    db.commit()


def list_logs(
    db: Session,
    limit: int = 100,
    offset: int = 0,
    target_type: str | None = None,
) -> list[AuditLog]:
    query = db.query(AuditLog).order_by(AuditLog.timestamp.desc())
    if target_type:
        query = query.filter(AuditLog.target_type == target_type)
    return query.offset(offset).limit(limit).all()
