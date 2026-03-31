from pydantic import BaseModel


class OnboardingRequest(BaseModel):
    """Request body for completing onboarding."""
    server_lan_cidr: str  # e.g., "192.168.1.0/24"
    server_lan_name: str = "LAN Server"  # Zone name for server LAN


class OnboardingResponse(BaseModel):
    success: bool
    message: str
    zone_id: int
    group_id: int
    policy_id: int
