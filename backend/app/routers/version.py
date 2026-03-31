from fastapi import APIRouter

from app.schemas.version import VersionResponse
from app.version import VERSION, VERSION_NAME, BUILD_DATE

router = APIRouter(prefix="/api/version", tags=["version"])


@router.get("", response_model=VersionResponse)
def get_version():
    return VersionResponse(
        version=VERSION,
        version_name=VERSION_NAME,
        build_date=BUILD_DATE,
    )
