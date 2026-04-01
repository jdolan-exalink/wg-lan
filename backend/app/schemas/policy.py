from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class PolicyCreate(BaseModel):
    source_group_id: int
    dest_group_id: int
    direction: Literal["outbound", "inbound", "both"] = "both"
    action: Literal["allow", "deny"] = "allow"
    enabled: bool = True


class PolicyUpdate(BaseModel):
    direction: Literal["outbound", "inbound", "both"] | None = None
    action: Literal["allow", "deny"] | None = None
    enabled: bool | None = None


class PolicyResponse(BaseModel):
    id: int
    source_group_id: int
    source_group_name: str | None = None
    dest_group_id: int
    dest_group_name: str | None = None
    direction: str
    action: str
    enabled: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PolicyMatrixCell(BaseModel):
    action: str | None = None
    policy_id: int | None = None
    direction: str | None = None


class PolicyMatrixRow(BaseModel):
    source_group_id: int
    source_group_name: str
    dest_groups: dict[int, PolicyMatrixCell]  # dest_group_id -> cell


class PolicyMatrixResponse(BaseModel):
    source_groups: list[PolicyMatrixRow]
    dest_group_ids: list[int]
    dest_group_names: dict[int, str]
