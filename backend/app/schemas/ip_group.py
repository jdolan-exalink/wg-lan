from datetime import datetime

from pydantic import BaseModel


class IpGroupEntryCreate(BaseModel):
    ip_address: str
    label: str | None = None


class IpGroupEntryResponse(BaseModel):
    id: int
    ip_group_id: int
    ip_address: str
    label: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class IpGroupCreate(BaseModel):
    name: str
    network_id: int
    description: str | None = None
    entries: list[IpGroupEntryCreate] = []


class IpGroupUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class IpGroupResponse(BaseModel):
    id: int
    name: str
    network_id: int
    network_name: str | None = None
    subnet: str | None = None
    description: str | None = None
    entry_count: int = 0
    entries: list[IpGroupEntryResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
