from pydantic import BaseModel, field_validator

from app.utils.ip_utils import is_valid_cidr


class NetworkCreate(BaseModel):
    name: str
    subnet: str
    description: str | None = None
    network_type: str = "lan"  # 'lan' or 'vpn'
    is_default: bool = False

    @field_validator("subnet")
    @classmethod
    def validate_subnet(cls, v: str) -> str:
        if not is_valid_cidr(v):
            raise ValueError(f"Invalid CIDR notation: {v}")
        return v


class NetworkUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    network_type: str | None = None
    is_default: bool | None = None


class NetworkResponse(BaseModel):
    id: int
    name: str
    subnet: str
    description: str | None
    network_type: str
    is_default: bool
    peer_count: int = 0
    peers: list[dict] = []

    model_config = {"from_attributes": True}


class SubnetConflictCheck(BaseModel):
    subnet: str
    exclude_id: int | None = None


class SubnetConflictResponse(BaseModel):
    has_conflict: bool
    conflicting_network: str | None = None
