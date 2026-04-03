from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.onboarding import OnboardingRequest, OnboardingResponse
from app.services.onboarding_service import complete_onboarding

router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])


@router.post("/complete", response_model=OnboardingResponse)
def complete_onboarding_endpoint(
    body: OnboardingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Complete the initial server setup wizard.
    Creates LAN Server zone, All group, and default allow policy.
    Must be called after changing the default password.
    """
    if current_user.onboarding_completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Onboarding has already been completed",
        )

    result = complete_onboarding(db, current_user, body)
    return OnboardingResponse(**result)


@router.get("/status")
def onboarding_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Check if onboarding has been completed."""
    return {
        "completed": current_user.onboarding_completed,
        "must_change_password": current_user.must_change_password,
    }


@router.post("/reset")
def reset_onboarding(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reset onboarding to allow re-running the setup wizard. Admin only."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can reset onboarding",
        )

    current_user.onboarding_completed = False
    db.commit()

    return {"message": "Onboarding reset successfully. User will be prompted to complete setup again."}
