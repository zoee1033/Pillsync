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

from app.schemas.medicine_schema import (
    MedicineCreate,
    MedicineUpdate,
    MedicineResponse
)

from app.services.medicine_service import (
    create_medicine,
    get_all_medicines,
    get_all_user_medicines,
    get_medicine_by_id,
    update_medicine,
    delete_medicine,
    get_refill_predictions,
    get_dosage_analysis
)


router = APIRouter(
    prefix="/medicines",
    tags=["Medicines"]
)


# =====================================================
# Refill Predictions
# =====================================================

@router.get("/refill-predictions")
def fetch_refill_predictions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_refill_predictions(db=db, current_user=current_user)


# =====================================================
# Dosage Analysis
# =====================================================

@router.get("/{medicine_id}/dosage-analysis")
def fetch_dosage_analysis(
    medicine_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_dosage_analysis(medicine_id=medicine_id, db=db, current_user=current_user)



# =====================================================
# Create Medicine
# =====================================================

@router.post(
    "/",
    response_model=MedicineResponse,
    status_code=status.HTTP_201_CREATED
)
def add_medicine(
    medicine: MedicineCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    return create_medicine(
        db=db,
        medicine=medicine,
        current_user=current_user
    )


# =====================================================
# Get All Medicines
# =====================================================

@router.get(
    "/",
    response_model=List[MedicineResponse]
)
def fetch_all_medicines(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    return get_all_user_medicines(
        db=db,
        current_user=current_user
    )


# =====================================================
# Get Medicines By Treatment
# =====================================================

@router.get(
    "/treatment/{treatment_id}",
    response_model=List[MedicineResponse]
)
def fetch_medicines(
    treatment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    return get_all_medicines(
        treatment_id=treatment_id,
        db=db,
        current_user=current_user
    )


# =====================================================
# Get Medicine By ID
# =====================================================

@router.get(
    "/{medicine_id}",
    response_model=MedicineResponse
)
def fetch_medicine(
    medicine_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    return get_medicine_by_id(
        medicine_id=medicine_id,
        db=db,
        current_user=current_user
    )


# =====================================================
# Update Medicine
# =====================================================

@router.put(
    "/{medicine_id}",
    response_model=MedicineResponse
)
def edit_medicine(
    medicine_id: int,
    medicine: MedicineUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    return update_medicine(
        medicine_id=medicine_id,
        medicine_data=medicine,
        db=db,
        current_user=current_user
    )


# =====================================================
# Delete Medicine
# =====================================================

@router.delete(
    "/{medicine_id}",
    status_code=status.HTTP_200_OK
)
def remove_medicine(
    medicine_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    return delete_medicine(
        medicine_id=medicine_id,
        db=db,
        current_user=current_user
    )