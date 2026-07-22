from datetime import datetime
from typing import Optional

from pydantic import (
    BaseModel,
    Field
)


# =====================================================
# Base Schema
# =====================================================

class DeviceTokenBase(BaseModel):

    fcm_token: str = Field(
        ...,
        min_length=20,
        description="Firebase Cloud Messaging Device Token"
    )

    device_name: Optional[str] = None

    browser: Optional[str] = None

    platform: Optional[str] = None

    is_active: bool = True


# =====================================================
# Register Device Token
# =====================================================

class DeviceTokenCreate(DeviceTokenBase):
    pass


# =====================================================
# Update Device Token
# =====================================================

class DeviceTokenUpdate(BaseModel):

    is_active: Optional[bool] = None

    device_name: Optional[str] = None

    browser: Optional[str] = None

    platform: Optional[str] = None


# =====================================================
# Response Schema
# =====================================================

class DeviceTokenResponse(DeviceTokenBase):

    id: int

    user_id: int

    last_used_at: datetime

    created_at: datetime

    updated_at: datetime

    class Config:
        from_attributes = True