from pydantic import BaseModel
from typing import Optional


class ProfileUpdateRequest(BaseModel):
    full_name: str
    phone: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str
