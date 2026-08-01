from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db

from app.schemas.auth_schema import (
    RegisterRequest,
    LoginRequest
)
from app.schemas.otp_schema import (
    ForgotPasswordRequest,
    VerifyOTPRequest,
    ResetPasswordRequest
)
from app.schemas.oauth_schema import (
    OAuthLoginRequest
)

from app.services.auth_service import (
    register_user,
    login_user,
    request_password_reset_otp,
    verify_password_reset_otp,
    reset_password_with_otp,
    oauth_login_user
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


# ==========================================
# Register User
# ==========================================

@router.post("/register")
def register(
    user: RegisterRequest,
    db: Session = Depends(get_db)
):
    return register_user(db, user)


# ==========================================
# Login (Frontend - JSON)
# ==========================================

@router.post("/login")
def login(
    user: LoginRequest,
    db: Session = Depends(get_db)
):
    return login_user(db, user)


# ==========================================
# OAuth2 Login (Swagger)
# ==========================================

@router.post("/token")
def login_for_swagger(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    login_request = LoginRequest(
        email=form_data.username,
        password=form_data.password
    )

    return login_user(db, login_request)


# ==========================================
# Forgot Password & OTP Routes
# ==========================================

@router.post("/forgot-password/request")
def forgot_password_request(
    payload: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    return request_password_reset_otp(db, payload.email)


@router.post("/forgot-password/verify-otp")
def forgot_password_verify(
    payload: VerifyOTPRequest,
    db: Session = Depends(get_db)
):
    return verify_password_reset_otp(db, payload.email, payload.otp)


@router.post("/forgot-password/reset")
def forgot_password_reset(
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    return reset_password_with_otp(
        db,
        payload.email,
        payload.otp,
        payload.new_password,
        payload.confirm_password
    )


# ==========================================
# Google & Apple OAuth Routes
# ==========================================

@router.post("/google")
def google_login(
    payload: OAuthLoginRequest,
    db: Session = Depends(get_db)
):
    return oauth_login_user(
        db,
        email=payload.email,
        full_name=payload.full_name,
        provider="google"
    )


@router.post("/apple")
def apple_login(
    payload: OAuthLoginRequest,
    db: Session = Depends(get_db)
):
    return oauth_login_user(
        db,
        email=payload.email,
        full_name=payload.full_name,
        provider="apple"
    )