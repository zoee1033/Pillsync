from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# -----------------------------
# Base Schema
# -----------------------------
class TreatmentBase(BaseModel):
    disease_name: str = Field(
        ...,
        min_length=2,
        max_length=150,
        description="Disease or health issue"
    )

    doctor_name: Optional[str] = Field(
        default=None,
        max_length=100
    )

    diagnosis_date: Optional[date] = None

    start_date: date

    end_date: date

    status: str = Field(
        default="Active",
        description="Active | Completed | Cancelled"
    )

    notes: Optional[str] = None

    @field_validator("disease_name")
    @classmethod
    def validate_disease_name(cls, value):
        value = value.strip()

        if not value:
            raise ValueError("Disease name cannot be empty.")

        return value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value):
        allowed = [
            "Active",
            "Completed",
            "Cancelled"
        ]

        if value not in allowed:
            raise ValueError(
                "Status must be Active, Completed or Cancelled."
            )

        return value


# -----------------------------
# Create Treatment
# -----------------------------
class TreatmentCreate(TreatmentBase):

    @field_validator("end_date")
    @classmethod
    def validate_end_date(cls, end_date, info):
        start_date = info.data.get("start_date")

        if start_date and end_date < start_date:
            raise ValueError(
                "End date cannot be before start date."
            )

        return end_date


# -----------------------------
# Update Treatment
# -----------------------------
class TreatmentUpdate(BaseModel):

    disease_name: Optional[str] = None

    doctor_name: Optional[str] = None

    diagnosis_date: Optional[date] = None

    start_date: Optional[date] = None

    end_date: Optional[date] = None

    status: Optional[str] = None

    notes: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value):

        if value is None:
            return value

        allowed = [
            "Active",
            "Completed",
            "Cancelled"
        ]

        if value not in allowed:
            raise ValueError(
                "Status must be Active, Completed or Cancelled."
            )

        return value


# -----------------------------
# Response Schema
# -----------------------------
class TreatmentResponse(TreatmentBase):

    id: int

    user_id: int

    created_at: datetime

    updated_at: datetime

    class Config:
        from_attributes = True