from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.utils.jwt_handler import verify_access_token

# Define OAuth2 scheme indicating where FastAPI should look for the token
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="auth/token"
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get the currently authenticated user from the JWT token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = verify_access_token(token)
    if payload is None:
        raise credentials_exception

    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception

    return user


def require_role(allowed_roles: list):
    """
    Dependency factory to restrict route access to specific roles.
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_role = (current_user.role or "patient").lower()
        allowed_normalized = [r.lower() for r in allowed_roles]
        if user_role not in allowed_normalized:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden. Required role: {', '.join(allowed_roles)}"
            )
        return current_user
    return role_checker


require_patient = require_role(["patient"])
require_caregiver = require_role(["caregiver", "admin"])
require_admin = require_role(["admin"])


def verify_caregiver_patient_access(db: Session, caregiver_user: User, patient_id: int):
    """
    Verifies that a caregiver is linked to the requested patient_id, or user is admin.
    Raises HTTP 403 if unauthorized.
    """
    from app.models.caregiver_patient import CaregiverPatient

    user_role = (caregiver_user.role or "patient").lower()
    if user_role == "admin":
        return True

    if user_role == "patient":
        if caregiver_user.id != patient_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to other patient's data."
            )
        return True

    # Check CaregiverPatient relationship
    link = db.query(CaregiverPatient).filter(
        CaregiverPatient.caregiver_id == caregiver_user.id,
        CaregiverPatient.patient_id == patient_id,
        CaregiverPatient.status == "active"
    ).first()

    if not link:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Caregiver is not linked to this patient."
        )

    return True

