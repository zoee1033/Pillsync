from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.schemas.profile_schema import ProfileUpdateRequest, ChangePasswordRequest
from app.utils.password import hash_password, verify_password


def update_profile_service(db: Session, current_user: User, data: ProfileUpdateRequest):
    """
    Update the authenticated user's profile and health data in PostgreSQL.
    """
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    update_dict = data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        if hasattr(user, key):
            setattr(user, key, value)

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
            "age": user.age,
            "gender": user.gender,
            "blood_group": user.blood_group,
            "weight": user.weight,
            "height": user.height,
            "medical_conditions": user.medical_conditions,
            "allergies": user.allergies,
            "emergency_contact": user.emergency_contact,
            "primary_doctor": user.primary_doctor,
            "hospital": user.hospital,
            "language": user.language,
            "timezone": user.timezone,
            "reminder_preferences": user.reminder_preferences,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }
    }


def change_password_service(db: Session, current_user: User, data: ChangePasswordRequest):
    """
    Verify current password, hash, and save the new password.
    """
    if data.new_password != data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match."
        )

    if not verify_password(data.current_password, current_user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password."
        )

    if verify_password(data.new_password, current_user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password cannot be the same as the current password."
        )

    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    new_hash = hash_password(data.new_password)
    user.password = new_hash
    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "message": "Password changed successfully.",
        "data": None
    }
