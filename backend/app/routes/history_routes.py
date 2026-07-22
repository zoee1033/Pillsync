from typing import List

from fastapi import (
    APIRouter,
    Depends,
    Query,
    status
)

from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user

from app.models.user import User

from app.schemas.history_schema import (
    HistoryCreate,
    HistoryUpdate,
    HistoryResponse
)

from app.services.history_service import (
    create_history,
    get_history,
    get_history_by_id,
    update_history,
    delete_history,
    mark_taken,
    mark_skipped,
    mark_missed
)

router = APIRouter(
    prefix="/history",
    tags=["History"]
)


# =====================================================
# Create History
# =====================================================

@router.post(
    "/",
    response_model=HistoryResponse,
    status_code=status.HTTP_201_CREATED
)
def add_history(
    history: HistoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    return create_history(
        db=db,
        history=history,
        current_user=current_user
    )


# =====================================================
# Get All History
# =====================================================

@router.get(
    "/",
    response_model=List[HistoryResponse]
)
def fetch_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    return get_history(
        db=db,
        current_user=current_user
    )


# =====================================================
# Get History By ID
# =====================================================

@router.get(
    "/{history_id}",
    response_model=HistoryResponse
)
def fetch_history_by_id(
    history_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    return get_history_by_id(
        history_id=history_id,
        db=db,
        current_user=current_user
    )


# =====================================================
# Update History
# =====================================================

@router.put(
    "/{history_id}",
    response_model=HistoryResponse
)
def edit_history(
    history_id: int,
    history: HistoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    return update_history(
        history_id=history_id,
        history_data=history,
        db=db,
        current_user=current_user
    )


# =====================================================
# Delete History
# =====================================================

@router.delete(
    "/{history_id}",
    status_code=status.HTTP_200_OK
)
def remove_history(
    history_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    return delete_history(
        history_id=history_id,
        db=db,
        current_user=current_user
    )


# =====================================================
# Mark Taken
# =====================================================

@router.put(
    "/{history_id}/taken",
    response_model=HistoryResponse
)
def taken(
    history_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    return mark_taken(
        history_id=history_id,
        db=db,
        current_user=current_user
    )


# =====================================================
# Mark Skipped
# =====================================================

@router.put(
    "/{history_id}/skipped",
    response_model=HistoryResponse
)
def skipped(
    history_id: int,
    reason: str = Query(
        ...,
        description="Reason for skipping medicine"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    return mark_skipped(
        history_id=history_id,
        reason=reason,
        db=db,
        current_user=current_user
    )


# =====================================================
# Mark Missed
# =====================================================

@router.put(
    "/{history_id}/missed",
    response_model=HistoryResponse
)
def missed(
    history_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    return mark_missed(
        history_id=history_id,
        db=db,
        current_user=current_user
    )