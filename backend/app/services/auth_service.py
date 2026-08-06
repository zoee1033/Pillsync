import secrets
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.models.otp import PasswordResetOTP
from app.schemas.auth_schema import RegisterRequest, LoginRequest
from app.utils.password import hash_password, verify_password
from app.utils.jwt_handler import create_access_token
from app.utils.email_sender import send_otp_email


def register_user(db: Session, user: RegisterRequest):
    """
    Register a new user.
    """

    # Check if email already exists
    existing_user = (
        db.query(User)
        .filter(User.email == user.email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered."
        )

    # Check password confirmation
    if user.password != user.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match."
        )

    # Create new user
    new_user = User(
        full_name=user.full_name,
        email=user.email,
        phone=user.phone,
        password=hash_password(user.password),
        role=user.role.lower(),
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Return user details (without password)
    return {
        "message": "Registration Successful",
        "user": {
            "id": new_user.id,
            "full_name": new_user.full_name,
            "email": new_user.email,
            "phone": new_user.phone,
            "role": new_user.role,
            "is_active": new_user.is_active,
        },
    }


def login_user(db: Session, user: LoginRequest):
    """
    Login an existing user.
    """

    existing_user = (
        db.query(User)
        .filter(User.email == user.email)
        .first()
    )

    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    if not verify_password(user.password, existing_user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    access_token = create_access_token(
        {
            "sub": existing_user.email,
            "role": existing_user.role,
            "id": existing_user.id,
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": existing_user.id,
            "full_name": existing_user.full_name,
            "email": existing_user.email,
            "role": existing_user.role,
        },
    }


# ==========================================
# Forgot Password & OTP Services
# ==========================================

def request_password_reset_otp(db: Session, email: str):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account found with this email address."
        )

    # Rate limiting check: check if an active OTP was requested in the last 60 seconds
    recent_otp = (
        db.query(PasswordResetOTP)
        .filter(
            PasswordResetOTP.email == email,
            PasswordResetOTP.is_used == False
        )
        .order_by(PasswordResetOTP.created_at.desc())
        .first()
    )

    now = datetime.now(timezone.utc)
    if recent_otp and recent_otp.created_at:
        created_time = recent_otp.created_at
        if created_time.tzinfo is None:
            created_time = created_time.replace(tzinfo=timezone.utc)
        if (now - created_time).total_seconds() < 60:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Please wait a minute before requesting another OTP."
            )

    # Generate 6-digit OTP
    otp_code = f"{secrets.randbelow(900000) + 100000}"
    expires_at = now + timedelta(minutes=10)

    otp_record = PasswordResetOTP(
        email=email,
        otp_code=otp_code,
        expires_at=expires_at,
        is_used=False
    )
    db.add(otp_record)
    db.commit()

    send_otp_email(email, otp_code)

    return {"message": "OTP sent to your registered email address."}


def verify_password_reset_otp(db: Session, email: str, otp: str):
    otp_record = (
        db.query(PasswordResetOTP)
        .filter(
            PasswordResetOTP.email == email,
            PasswordResetOTP.otp_code == otp,
            PasswordResetOTP.is_used == False
        )
        .order_by(PasswordResetOTP.created_at.desc())
        .first()
    )

    if not otp_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP code."
        )

    now = datetime.now(timezone.utc)
    exp = otp_record.expires_at
    if exp and exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)

    if now > exp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP has expired. Please request a new one."
        )

    return {"message": "OTP verified successfully."}


def reset_password_with_otp(db: Session, email: str, otp: str, new_password: str, confirm_password: str):
    if new_password != confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match."
        )

    verify_password_reset_otp(db, email, otp)

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    user.password = hash_password(new_password)

    # Invalidate OTP after successful reset
    otp_records = (
        db.query(PasswordResetOTP)
        .filter(
            PasswordResetOTP.email == email,
            PasswordResetOTP.otp_code == otp,
            PasswordResetOTP.is_used == False
        )
        .all()
    )
    for record in otp_records:
        record.is_used = True

    db.commit()

    return {"message": "Password reset successful. You can now log in with your new password."}


# ==========================================
# Google & Apple OAuth Services
# ==========================================

def oauth_login_user(db: Session, email: str, full_name: str | None = None, provider: str = "google"):
    existing_user = db.query(User).filter(User.email == email).first()

    if not existing_user:
        name = full_name if full_name and full_name.strip() else f"{provider.capitalize()} User"
        random_pwd = secrets.token_urlsafe(32)
        existing_user = User(
            full_name=name,
            email=email,
            password=hash_password(random_pwd),
            role="patient",
            is_active=True
        )
        db.add(existing_user)
        db.commit()
        db.refresh(existing_user)

    access_token = create_access_token(
        {
            "sub": existing_user.email,
            "role": existing_user.role,
            "id": existing_user.id,
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": existing_user.id,
            "full_name": existing_user.full_name,
            "email": existing_user.email,
            "role": existing_user.role,
        },
    }