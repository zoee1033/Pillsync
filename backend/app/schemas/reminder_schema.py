from datetime import datetime, time
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# =====================================================
# Base Schema
# =====================================================

class ReminderBase(BaseModel):

    reminder_time: time

    repeat_type: str = Field(
        default="Daily",
        description="Daily | Weekly | Monthly | Custom"
    )

    notification_enabled: bool = True

    snooze_minutes: int = Field(
        default=10,
        ge=5,
        le=60
    )

    status: str = Field(
        default="Active",
        description="Active | Paused | Completed"
    )

    @field_validator("repeat_type")
    @classmethod
    def validate_repeat_type(cls, value):

        allowed = [
            "Daily",
            "Weekly",
            "Monthly",
            "Custom"
        ]

        if value not in allowed:
            raise ValueError(
                f"Repeat type must be one of {allowed}"
            )

        return value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value):

        allowed = [
            "Active",
            "Paused",
            "Completed"
        ]

        if value not in allowed:
            raise ValueError(
                f"Status must be one of {allowed}"
            )

        return value


# =====================================================
# Create Reminder
# =====================================================

class ReminderCreate(ReminderBase):

    medicine_id: int


# =====================================================
# Update Reminder
# =====================================================

class ReminderUpdate(BaseModel):

    reminder_time: Optional[time] = None

    repeat_type: Optional[str] = None

    notification_enabled: Optional[bool] = None

    snooze_minutes: Optional[int] = None

    status: Optional[str] = None

    @field_validator("repeat_type")
    @classmethod
    def validate_repeat_type(cls, value):

        if value is None:
            return value

        allowed = [
            "Daily",
            "Weekly",
            "Monthly",
            "Custom"
        ]

        if value not in allowed:
            raise ValueError(
                f"Repeat type must be one of {allowed}"
            )

        return value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value):

        if value is None:
            return value

        allowed = [
            "Active",
            "Paused",
            "Completed"
        ]

        if value not in allowed:
            raise ValueError(
                f"Status must be one of {allowed}"
            )

        return value


# =====================================================
# Response Schema
# =====================================================

class ReminderResponse(ReminderBase):

    id: int

    medicine_id: int

    next_trigger_at: Optional[datetime]

    last_triggered_at: Optional[datetime]

    created_at: datetime

    updated_at: datetime

    class Config:
        from_attributes = True