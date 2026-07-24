from datetime import datetime, date
from typing import Optional

from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator
)

from app.models.enums import HistoryStatus


# =====================================================
# Base Schema
# =====================================================

class HistoryBase(BaseModel):

    scheduled_time: datetime

    status: str = Field(
        ...,
        description="Completed | Medicine Completed | Expired | Cancelled | Taken | Skipped | Missed | Snoozed"
    )

    skip_reason: Optional[str] = None

    notes: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value):

        allowed = [s.value for s in HistoryStatus]

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

    medicine_id: Optional[int] = None

    reminder_id: Optional[int] = None

    @model_validator(mode="after")
    def validate_user_action_fields(self):
        user_actions = [
            HistoryStatus.TAKEN.value,
            HistoryStatus.SKIPPED.value,
            HistoryStatus.MISSED.value,
            HistoryStatus.SNOOZED.value,
        ]
        if self.status in user_actions:
            if not self.medicine_id or not self.reminder_id:
                raise ValueError(
                    f"Status '{self.status}' requires medicine_id and reminder_id."
                )
        return self


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

        allowed = [s.value for s in HistoryStatus]

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

    medicine_id: Optional[int] = None

    reminder_id: Optional[int] = None

    medicine_name: Optional[str] = None

    treatment_name: Optional[str] = None

    dosage: Optional[str] = None

    reminder_time: Optional[str] = None

    start_date: Optional[date] = None

    end_date: Optional[date] = None

    completion_date: Optional[date] = None

    duration: Optional[str] = None

    action_time: datetime

    created_at: datetime

    class Config:
        from_attributes = True