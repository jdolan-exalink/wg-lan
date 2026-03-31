from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class ConnectionLogResponse(BaseModel):
    id: int
    timestamp: datetime
    peer_id: int | None
    peer_name: str | None
    peer_ip: str | None
    event_type: str
    severity: str
    message: str
    details: str | None
    source_ip: str | None
    duration_ms: int | None

    model_config = {"from_attributes": True}


class ConnectionLogFilters(BaseModel):
    event_type: str | None = None
    severity: str | None = None
    peer_id: int | None = None
    limit: int = 100
    offset: int = 0


class ConnectionStats(BaseModel):
    total_events: int
    events_by_type: dict[str, int]
    events_by_severity: dict[str, int]
    online_peers: int
    offline_peers: int
    peers_with_errors: list[dict]
