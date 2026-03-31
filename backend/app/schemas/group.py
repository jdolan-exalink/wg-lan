from pydantic import BaseModel


class PeerGroupCreate(BaseModel):
    name: str
    description: str | None = None


class PeerGroupUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class PeerGroupResponse(BaseModel):
    id: int
    name: str
    description: str | None
    member_count: int = 0

    model_config = {"from_attributes": True}


class AddMembersRequest(BaseModel):
    peer_ids: list[int]
