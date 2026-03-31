from pydantic import BaseModel


class VersionResponse(BaseModel):
    version: str
    version_name: str
    build_date: str
