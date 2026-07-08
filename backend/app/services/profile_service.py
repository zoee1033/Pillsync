from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.schemas.profile_schema import ProfileUpdateRequest, ChangePasswordRequest
from app.utils.password import hash_password, verify_password


def update_profile_service(db: Session, current_user: User, data: ProfileUpdateRequest):
    """
    Update the authenticated user's name and phone number in the database.
    """
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    user.full_name = data.full_name
    user.phone = data.phone

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "message": "Profile updated successfully.",
        "data": {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "phone": user.phone,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }
    }


def change_password_service(db: Session, current_user: User, data: ChangePasswordRequest):
    """
    Verify the current password, then hash and save the new password.
    """
    # 1. Verify passwords match
    if data.new_password != data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match."
        )

    # 2. Check that current password is correct
    if not verify_password(data.current_password, current_user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password."
        )

    # 3. Prevent reusing the same password
    if verify_password(data.new_password, current_user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password cannot be the same as the current password."
        )

    # 4. Attach current_user to the active SQLAlchemy session by reloading it
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    new_hash = hash_password(data.new_password)

    # 5. Explicitly persist the update
    user.password = new_hash
    db.add(user)
    db.commit()
    db.refresh(user)

    # 6. Immediately verify the update by querying from database again
    db.expire(user)  # force expire to reload from db on next access
    verified_user = db.query(User).filter(User.id == current_user.id).first()

    if verified_user.password != new_hash:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password update failed to persist in the database."
        )

    return {
        "message": "Password changed successfully.",
        "data": None
    }

