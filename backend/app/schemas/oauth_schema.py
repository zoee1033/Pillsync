from pydantic import BaseModel, EmailStr
from typing import Optional

class OAuthLoginRequest(BaseModel):
    id_token: Optional[str] = None
    email: EmailStr
    full_name: Optional[str] = "PillSync User"
    provider: Optional[str] = "google"
