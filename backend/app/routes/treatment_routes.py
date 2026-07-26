from typing import List

from fastapi import (
    APIRouter,
    Depends,
    status
)

from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user

from app.models.user import User

from app.schemas.treatment_schema import (
    TreatmentCreate,
    TreatmentUpdate,
    TreatmentResponse
)

from app.services.treatment_service import (
    create_treatment,
    get_all_treatments,
    get_treatment_by_id,
    update_treatment,
    delete_treatment
)


router = APIRouter(
    prefix="/treatments",
    tags=["Treatments"]
)


# ==========================================
# Create Treatment
# ==========================================

@router.post(
    "/",
    response_model=TreatmentResponse,
    status_code=status.HTTP_201_CREATED
)
def add_treatment(
    treatment: TreatmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    return create_treatment(
        db=db,
        treatment=treatment,
        current_user=current_user
    )


# ==========================================
# Get All Treatments
# ==========================================

@router.get(
    "/",
    response_model=List[TreatmentResponse]
)
def fetch_treatments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    return get_all_treatments(
        db=db,
        current_user=current_user
    )


# ==========================================
# Get One Treatment
# ==========================================

@router.get(
    "/{treatment_id}",
    response_model=TreatmentResponse
)
def fetch_treatment(
    treatment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    return get_treatment_by_id(
        treatment_id=treatment_id,
        db=db,
        current_user=current_user
    )


# ==========================================
# Update Treatment
# ==========================================

@router.put(
    "/{treatment_id}",
    response_model=TreatmentResponse
)
def edit_treatment(
    treatment_id: int,
    treatment: TreatmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    return update_treatment(
        treatment_id=treatment_id,
        treatment_data=treatment,
        db=db,
        current_user=current_user
    )


# ==========================================
# Delete Treatment
# ==========================================

@router.delete(
    "/{treatment_id}",
    status_code=status.HTTP_200_OK
)
def remove_treatment(
    treatment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    return delete_treatment(
        treatment_id=treatment_id,
        db=db,
        current_user=current_user
    )