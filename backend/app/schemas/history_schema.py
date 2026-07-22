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

class HistoryBase(BaseModel):

    scheduled_time: datetime

    status: str = Field(
        ...,
        description="Taken | Skipped | Missed | Snoozed"
    )

    skip_reason: Optional[str] = None

    notes: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value):

        allowed = [
            "Taken",
            "Skipped",
            "Missed",
            "Snoozed"
        ]

        if value not in allowed:
            raise ValueError(
                f"Status must be one of {allowed}"
            )

        return value


# =====================================================
# Create History
# =====================================================

class HistoryCreate(HistoryBase):

    treatment_id: int

    medicine_id: int

    reminder_id: int


# =====================================================
# Update History
# =====================================================

class HistoryUpdate(BaseModel):

    status: Optional[str] = None

    skip_reason: Optional[str] = None

    notes: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value):

        if value is None:
            return value

        allowed = [
            "Taken",
            "Skipped",
            "Missed",
            "Snoozed"
        ]

        if value not in allowed:
            raise ValueError(
                f"Status must be one of {allowed}"
            )

        return value


# =====================================================
# Response Schema
# =====================================================

class HistoryResponse(HistoryBase):

    id: int

    user_id: int

    treatment_id: int

    medicine_id: int

    reminder_id: int

    action_time: datetime

    created_at: datetime

    class Config:
        from_attributes = True