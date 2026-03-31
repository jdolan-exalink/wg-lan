from pydantic import BaseModel, field_validator

from app.utils.ip_utils import is_valid_cidr


class ZoneNetworkCreate(BaseModel):
    cidr: str
    description: str | None = None

    @field_validator("cidr")
    @classmethod
    def validate_cidr(cls, v: str) -> str:
        if not is_valid_cidr(v):
            raise ValueError(f"Invalid CIDR notation: {v}")
        return v


class ZoneNetworkResponse(BaseModel):
    id: int
    cidr: str
    description: str | None

    model_config = {"from_attributes": True}


class ZoneCreate(BaseModel):
    name: str
    description: str | None = None
    networks: list[ZoneNetworkCreate] = []


class ZoneUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class ZoneResponse(BaseModel):
    id: int
    name: str
    description: str | None
    networks: list[ZoneNetworkResponse] = []

    model_config = {"from_attributes": True}
