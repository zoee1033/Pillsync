from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.database import Base

class PasswordResetOTP(Base):
    __tablename__ = "password_reset_otps"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(120), nullable=False, index=True)
    otp_code = Column(String(6), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
