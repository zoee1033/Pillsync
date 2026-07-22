from typing import List

from fastapi import (
    APIRouter,
    Depends,
    status,
    Query
)

from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user

from app.models.user import User

from app.schemas.reminder_schema import (
    ReminderCreate,
    ReminderUpdate,
    ReminderResponse
)

from app.services.reminder_service import (
    create_reminder,
    get_all_reminders,
    get_reminder_by_id,
    update_reminder,
    delete_reminder,
    snooze_reminder
)


router = APIRouter(
    prefix="/reminders",
    tags=["Reminders"]
)


# =====================================================
# Create Reminder
# =====================================================

@router.post(
    "/",
    response_model=ReminderResponse,
    status_code=status.HTTP_201_CREATED
)
def add_reminder(
    reminder: ReminderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    return create_reminder(
        db=db,
        reminder=reminder,
        current_user=current_user
    )


# =====================================================
# Get All Reminders
# =====================================================

@router.get(
    "/medicine/{medicine_id}",
    response_model=List[ReminderResponse]
)
def fetch_reminders(
    medicine_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    return get_all_reminders(
        medicine_id=medicine_id,
        db=db,
        current_user=current_user
    )


# =====================================================
# Get Reminder By ID
# =====================================================

@router.get(
    "/{reminder_id}",
    response_model=ReminderResponse
)
def fetch_reminder(
    reminder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    return get_reminder_by_id(
        reminder_id=reminder_id,
        db=db,
        current_user=current_user
    )


# =====================================================
# Update Reminder
# =====================================================

@router.put(
    "/{reminder_id}",
    response_model=ReminderResponse
)
def edit_reminder(
    reminder_id: int,
    reminder: ReminderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    return update_reminder(
        reminder_id=reminder_id,
        reminder_data=reminder,
        db=db,
        current_user=current_user
    )


# =====================================================
# Delete Reminder
# =====================================================

@router.delete(
    "/{reminder_id}",
    status_code=status.HTTP_200_OK
)
def remove_reminder(
    reminder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    return delete_reminder(
        reminder_id=reminder_id,
        db=db,
        current_user=current_user
    )


# =====================================================
# Snooze Reminder
# =====================================================

@router.put(
    "/{reminder_id}/snooze",
    response_model=ReminderResponse
)
def snooze(
    reminder_id: int,
    minutes: int = Query(
        10,
        ge=5,
        le=60
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    return snooze_reminder(
        reminder_id=reminder_id,
        minutes=minutes,
        db=db,
        current_user=current_user
    )