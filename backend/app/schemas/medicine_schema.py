from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# =====================================================
# Base Schema
# =====================================================

class MedicineBase(BaseModel):

    medicine_name: str = Field(
        ...,
        min_length=2,
        max_length=150
    )

    medicine_type: str = Field(
        ...,
        description="Tablet, Capsule, Syrup, Injection, Drops, Ointment"
    )

    dosage: str = Field(
        ...,
        description="Example: 500 mg, 5 ml, 2 tablets"
    )

    quantity: int = Field(
        ...,
        ge=0
    )

    instructions: Optional[str] = None

    is_active: bool = True

    @field_validator("medicine_name")
    @classmethod
    def validate_name(cls, value):

        value = value.strip()

        if not value:
            raise ValueError(
                "Medicine name cannot be empty."
            )

        return value

    @field_validator("medicine_type")
    @classmethod
    def validate_type(cls, value):

        allowed = [
            "Tablet",
            "Capsule",
            "Syrup",
            "Injection",
            "Drops",
            "Ointment",
            "Inhaler",
            "Other"
        ]

        if value not in allowed:
            raise ValueError(
                f"Medicine type must be one of {allowed}"
            )

        return value


# =====================================================
# Create Medicine
# =====================================================

class MedicineCreate(MedicineBase):

    treatment_id: int

    quantity: int = Field(
        ...,
        gt=0
    )


# =====================================================
# Update Medicine
# =====================================================

class MedicineUpdate(BaseModel):

    medicine_name: Optional[str] = None

    medicine_type: Optional[str] = None

    dosage: Optional[str] = None

    quantity: Optional[int] = None

    instructions: Optional[str] = None

    is_active: Optional[bool] = None

    @field_validator("medicine_type")
    @classmethod
    def validate_type(cls, value):

        if value is None:
            return value

        allowed = [
            "Tablet",
            "Capsule",
            "Syrup",
            "Injection",
            "Drops",
            "Ointment",
            "Inhaler",
            "Other"
        ]

        if value not in allowed:
            raise ValueError(
                f"Medicine type must be one of {allowed}"
            )

        return value


# =====================================================
# Response Schema
# =====================================================

class MedicineResponse(MedicineBase):

    id: int

    treatment_id: int

    created_at: datetime

    updated_at: datetime

    class Config:
        from_attributes = True