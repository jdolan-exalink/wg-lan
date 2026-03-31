import json
from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.connection_log import ConnectionLog
from app.models.peer import Peer


def log_connection(
    db: Session,
    event_type: str,
    message: str,
    peer_id: int | None = None,
    peer_name: str | None = None,
    peer_ip: str | None = None,
    severity: str = "info",
    details: dict | None = None,
    source_ip: str | None = None,
    duration_ms: int | None = None,
) -> ConnectionLog:
    """Log a WireGuard connection event."""
    entry = ConnectionLog(
        peer_id=peer_id,
        peer_name=peer_name,
        peer_ip=peer_ip,
        event_type=event_type,
        severity=severity,
        message=message,
        details=json.dumps(details) if details else None,
        source_ip=source_ip,
        duration_ms=duration_ms,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def list_logs(
    db: Session,
    limit: int = 100,
    offset: int = 0,
    event_type: str | None = None,
    severity: str | None = None,
    peer_id: int | None = None,
) -> list[ConnectionLog]:
    """List connection logs with optional filters."""
    query = db.query(ConnectionLog).order_by(ConnectionLog.timestamp.desc())
    if event_type:
        query = query.filter(ConnectionLog.event_type == event_type)
    if severity:
        query = query.filter(ConnectionLog.severity == severity)
    if peer_id:
        query = query.filter(ConnectionLog.peer_id == peer_id)
    return query.offset(offset).limit(limit).all()


def get_stats(db: Session) -> dict:
    """Get connection statistics and health overview."""
    # Count by type
    type_counts = db.query(
        ConnectionLog.event_type,
        func.count(ConnectionLog.id)
    ).group_by(ConnectionLog.event_type).all()

    # Count by severity
    severity_counts = db.query(
        ConnectionLog.severity,
        func.count(ConnectionLog.id)
    ).group_by(ConnectionLog.severity).all()

    # Recent errors (last 24h)
    cutoff = datetime.now() - timedelta(hours=24)
    recent_errors = db.query(ConnectionLog).filter(
        ConnectionLog.severity.in_(["error", "critical"]),
        ConnectionLog.timestamp >= cutoff,
    ).order_by(ConnectionLog.timestamp.desc()).limit(20).all()

    # Peers with errors
    peer_errors = {}
    for log in recent_errors:
        if log.peer_id:
            if log.peer_id not in peer_errors:
                peer_errors[log.peer_id] = {
                    "peer_id": log.peer_id,
                    "peer_name": log.peer_name,
                    "error_count": 0,
                    "last_error": log.timestamp.isoformat(),
                    "last_message": log.message,
                }
            peer_errors[log.peer_id]["error_count"] += 1

    return {
        "total_events": db.query(ConnectionLog).count(),
        "events_by_type": {row[0]: row[1] for row in type_counts},
        "events_by_severity": {row[0]: row[1] for row in severity_counts},
        "peers_with_errors": list(peer_errors.values()),
    }


def sync_peer_status_logs(db: Session) -> None:
    """
    Check current peer statuses and log any disconnections or issues.
    Call this periodically to detect connection problems.
    """
    from app.services.wg_service import get_peer_statuses, ONLINE_THRESHOLD_SECONDS
    import time

    peers = db.query(Peer).filter(Peer.is_enabled == True).all()
    wg_statuses = get_peer_statuses()

    now = int(time.time())

    for peer in peers:
        status = wg_statuses.get(peer.public_key)
        if not status:
            # Peer not in wg output - might be disconnected
            continue

        if not status.is_online and status.last_handshake > 0:
            # Was connected but now offline
            time_since_hs = now - status.last_handshake
            log_connection(
                db=db,
                event_type="disconnect",
                message=f"Peer '{peer.name}' appears disconnected (last handshake {time_since_hs}s ago)",
                peer_id=peer.id,
                peer_name=peer.name,
                peer_ip=peer.assigned_ip,
                severity="warning",
                details={
                    "last_handshake": status.last_handshake,
                    "time_since_handshake": time_since_hs,
                    "threshold": ONLINE_THRESHOLD_SECONDS,
                    "endpoint": status.endpoint,
                },
                source_ip=status.endpoint,
            )
        elif status.is_online and status.last_handshake > 0:
            # Peer is online - log handshake
            log_connection(
                db=db,
                event_type="handshake",
                message=f"Peer '{peer.name}' connected (handshake {now - status.last_handshake}s ago)",
                peer_id=peer.id,
                peer_name=peer.name,
                peer_ip=peer.assigned_ip,
                severity="info",
                details={
                    "last_handshake": status.last_handshake,
                    "endpoint": status.endpoint,
                    "rx_bytes": status.rx_bytes,
                    "tx_bytes": status.tx_bytes,
                },
                source_ip=status.endpoint,
            )
