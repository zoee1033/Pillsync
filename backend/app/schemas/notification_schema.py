from datetime import datetime
from typing import Optional

from pydantic import (
    BaseModel,
    Field,
    field_validator
)


# =====================================================
# Base Schema
# =====================================================

class NotificationBase(BaseModel):

    title: str = Field(
        ...,
        min_length=2,
        max_length=200
    )

    message: str = Field(
        ...,
        min_length=2
    )

    notification_type: str = Field(
        default="Reminder",
        description="Reminder | System | Alert"
    )

    is_read: bool = False

    is_sent: bool = False

    @field_validator("notification_type")
    @classmethod
    def validate_notification_type(cls, value):

        allowed = [
            "Reminder",
            "System",
            "Alert",
            "Refill"
        ]

        if value not in allowed:
            raise ValueError(
                f"Notification type must be one of {allowed}"
            )

        return value


# =====================================================
# Create Notification
# =====================================================

class NotificationCreate(NotificationBase):

    reminder_id: Optional[int] = None


# =====================================================
# Update Notification
# =====================================================

class NotificationUpdate(BaseModel):

    is_read: Optional[bool] = None

    is_sent: Optional[bool] = None


# =====================================================
# Response Schema
# =====================================================

class NotificationResponse(NotificationBase):

    id: int

    user_id: int

    reminder_id: Optional[int] = None

    sent_at: Optional[datetime]

    created_at: datetime

    updated_at: datetime

    class Config:
        from_attributes = True