from typing import List

from fastapi import (
    APIRouter,
    Depends,
    status
)

from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user

from app.models.user import User

from app.schemas.device_token_schema import (
    DeviceTokenCreate,
    DeviceTokenUpdate,
    DeviceTokenResponse
)

from app.services.device_token_service import (
    register_device_token,
    get_active_tokens,
    get_device_token,
    update_device_token,
    deactivate_device_token,
    delete_device_token
)


router = APIRouter(
    prefix="/device-tokens",
    tags=["Device Tokens"]
)


# =====================================================
# Register Device Token
# =====================================================

@router.post(
    "/",
    response_model=DeviceTokenResponse,
    status_code=status.HTTP_201_CREATED
)
def register_token(
    token: DeviceTokenCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    return register_device_token(
        db=db,
        token_data=token,
        current_user=current_user
    )


# =====================================================
# Get Active Tokens
# =====================================================

@router.get(
    "/",
    response_model=List[DeviceTokenResponse]
)
def fetch_tokens(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    return get_active_tokens(
        db=db,
        current_user=current_user
    )


# =====================================================
# Get Token By ID
# =====================================================

@router.get(
    "/{token_id}",
    response_model=DeviceTokenResponse
)
def fetch_token(
    token_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    return get_device_token(
        token_id=token_id,
        db=db,
        current_user=current_user
    )


# =====================================================
# Update Token
# =====================================================

@router.put(
    "/{token_id}",
    response_model=DeviceTokenResponse
)
def edit_token(
    token_id: int,
    token: DeviceTokenUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    return update_device_token(
        token_id=token_id,
        token_data=token,
        db=db,
        current_user=current_user
    )


# =====================================================
# Deactivate Token
# =====================================================

@router.put(
    "/{token_id}/deactivate",
    status_code=status.HTTP_200_OK
)
def deactivate_token(
    token_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    return deactivate_device_token(
        token_id=token_id,
        db=db,
        current_user=current_user
    )


# =====================================================
# Delete Token
# =====================================================

@router.delete(
    "/{token_id}",
    status_code=status.HTTP_200_OK
)
def remove_token(
    token_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    return delete_device_token(
        token_id=token_id,
        db=db,
        current_user=current_user
    )