from pydantic import BaseModel
from typing import Optional


class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    weight: Optional[str] = None
    height: Optional[str] = None
    medical_conditions: Optional[str] = None
    allergies: Optional[str] = None
    emergency_contact: Optional[str] = None
    primary_doctor: Optional[str] = None
    hospital: Optional[str] = None
    language: Optional[str] = None
    timezone: Optional[str] = None
    reminder_preferences: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str
