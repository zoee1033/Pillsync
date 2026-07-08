from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.middleware.auth import get_current_user
from app.schemas.profile_schema import ProfileUpdateRequest, ChangePasswordRequest
from app.services.profile_service import update_profile_service, change_password_service

router = APIRouter(
    prefix="/profile",
    tags=["Profile Management"]
)


@router.get("/me")
def get_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get the authenticated user's profile details.
    """
    return {
        "message": "Profile fetched successfully.",
        "data": {
            "id": current_user.id,
            "full_name": current_user.full_name,
            "email": current_user.email,
            "phone": current_user.phone,
            "role": current_user.role,
            "is_active": current_user.is_active,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        }
    }


@router.put("/update")
def update_profile(
    data: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update the authenticated user's full name and phone number.
    """
    return update_profile_service(db, current_user, data)


@router.put("/change-password")
def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change the authenticated user's password.
    """
    return change_password_service(db, current_user, data)
