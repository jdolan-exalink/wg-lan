from typing import Literal

from pydantic import BaseModel


class PolicyUpsert(BaseModel):
    group_id: int
    zone_id: int
    action: Literal["allow", "deny"]


class PolicyResponse(BaseModel):
    id: int
    group_id: int
    zone_id: int
    action: str

    model_config = {"from_attributes": True}


class PolicyMatrixCell(BaseModel):
    action: str | None  # 'allow', 'deny', or None (no rule)
    policy_id: int | None


class PolicyMatrixRow(BaseModel):
    group_id: int
    group_name: str
    zones: dict[int, PolicyMatrixCell]  # zone_id -> cell


class PolicyMatrixResponse(BaseModel):
    groups: list[PolicyMatrixRow]
    zone_ids: list[int]
    zone_names: dict[int, str]  # zone_id -> name
