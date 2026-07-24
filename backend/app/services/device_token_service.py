from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.device_token import DeviceToken
from app.models.user import User

from app.schemas.device_token_schema import (
    DeviceTokenCreate,
    DeviceTokenUpdate
)


# ==========================================================
# Register Device Token
# ==========================================================

def register_device_token(
    db: Session,
    token_data: DeviceTokenCreate,
    current_user: User
):

    same_device_tokens = (
        db.query(DeviceToken)
        .filter(
            DeviceToken.user_id == current_user.id,
            DeviceToken.browser == token_data.browser,
            DeviceToken.fcm_token != token_data.fcm_token,
            DeviceToken.is_active == True
        )
        .all()
    )
    for old_tok in same_device_tokens:
        old_tok.is_active = False

    existing_token = (
        db.query(DeviceToken)
        .filter(
            DeviceToken.fcm_token == token_data.fcm_token
        )
        .first()
    )

    if existing_token:

        existing_token.user_id = current_user.id
        existing_token.device_name = token_data.device_name
        existing_token.browser = token_data.browser
        existing_token.platform = token_data.platform
        existing_token.is_active = True
        existing_token.last_used_at = datetime.utcnow()

        db.commit()
        db.refresh(existing_token)

        return existing_token

    new_token = DeviceToken(
        user_id=current_user.id,
        fcm_token=token_data.fcm_token,
        device_name=token_data.device_name,
        browser=token_data.browser,
        platform=token_data.platform,
        is_active=True,
        last_used_at=datetime.utcnow()
    )

    db.add(new_token)
    db.commit()
    db.refresh(new_token)

    return new_token


# ==========================================================
# Get All Active Tokens
# ==========================================================

def get_active_tokens(
    db: Session,
    current_user: User
):

    return (
        db.query(DeviceToken)
        .filter(
            DeviceToken.user_id == current_user.id,
            DeviceToken.is_active == True
        )
        .order_by(
            DeviceToken.created_at.desc()
        )
        .all()
    )


# ==========================================================
# Get Device Token By ID
# ==========================================================

def get_device_token(
    token_id: int,
    db: Session,
    current_user: User
):

    token = (
        db.query(DeviceToken)
        .filter(
            DeviceToken.id == token_id,
            DeviceToken.user_id == current_user.id
        )
        .first()
    )

    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device token not found."
        )

    return token


# ==========================================================
# Update Device Token
# ==========================================================

def update_device_token(
    token_id: int,
    token_data: DeviceTokenUpdate,
    db: Session,
    current_user: User
):

    token = get_device_token(
        token_id,
        db,
        current_user
    )

    update_data = token_data.model_dump(
        exclude_unset=True
    )

    for key, value in update_data.items():
        setattr(token, key, value)

    token.last_used_at = datetime.utcnow()

    db.commit()
    db.refresh(token)

    return token


# ==========================================================
# Deactivate Device Token
# ==========================================================

def deactivate_device_token(
    token_id: int,
    db: Session,
    current_user: User
):

    token = get_device_token(
        token_id,
        db,
        current_user
    )

    token.is_active = False
    token.last_used_at = datetime.utcnow()

    db.commit()
    db.refresh(token)

    return {
        "message": "Device token deactivated successfully."
    }


# ==========================================================
# Delete Device Token
# ==========================================================

def delete_device_token(
    token_id: int,
    db: Session,
    current_user: User
):

    token = get_device_token(
        token_id,
        db,
        current_user
    )

    db.delete(token)
    db.commit()

    return {
        "message": "Device token deleted successfully."
    }


# ==========================================================
# Get All Tokens Of Any User
# (Used by Firebase Scheduler)
# ==========================================================

def get_tokens_by_user_id(
    user_id: int,
    db: Session
):

    return (
        db.query(DeviceToken)
        .filter(
            DeviceToken.user_id == user_id,
            DeviceToken.is_active == True
        )
        .all()
    )