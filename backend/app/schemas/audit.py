from datetime import datetime

from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: int
    timestamp: datetime
    user_id: int | None
    action: str
    target_type: str | None
    target_id: int | None
    details: str | None
    ip_address: str | None

    model_config = {"from_attributes": True}
