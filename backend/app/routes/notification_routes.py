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

from app.schemas.notification_schema import (
    NotificationCreate,
    NotificationUpdate,
    NotificationResponse
)

from app.services.notification_service import (
    create_notification,
    get_notifications,
    get_notification_by_id,
    mark_as_read,
    mark_as_sent,
    delete_notification,
    get_unread_notifications,
    process_notification_action,
    process_reminder_action
)

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"]
)


# =====================================================
# Create Notification
# =====================================================

@router.post(
    "/",
    response_model=NotificationResponse,
    status_code=status.HTTP_201_CREATED
)
def add_notification(
    notification: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    return create_notification(
        db=db,
        notification=notification,
        current_user=current_user
    )


# =====================================================
# Get All Notifications
# =====================================================

@router.get(
    "/",
    response_model=List[NotificationResponse]
)
def fetch_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    return get_notifications(
        db=db,
        current_user=current_user
    )


# =====================================================
# Get Notification By ID
# =====================================================

@router.get(
    "/{notification_id}",
    response_model=NotificationResponse
)
def fetch_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    return get_notification_by_id(
        notification_id=notification_id,
        db=db,
        current_user=current_user
    )


# =====================================================
# Get Unread Notifications
# =====================================================

@router.get(
    "/unread",
    response_model=List[NotificationResponse]
)
def unread_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    return get_unread_notifications(
        db=db,
        current_user=current_user
    )


# =====================================================
# Perform Notification Action (Single Source of Truth)
# =====================================================

@router.put(
    "/{notification_id}/action"
)
def execute_notification_action_endpoint(
    notification_id: int,
    action_type: str = Query(
        ...,
        description="taken | skipped | snooze | delete"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    return process_notification_action(
        notification_id=notification_id,
        action_type=action_type,
        db=db,
        current_user=current_user
    )


@router.put(
    "/reminder/{reminder_id}/action"
)
def execute_reminder_action_endpoint(
    reminder_id: int,
    action_type: str = Query(
        ...,
        description="taken | skipped | snooze | delete"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    return process_reminder_action(
        reminder_id=reminder_id,
        action_type=action_type,
        db=db,
        current_user=current_user
    )


# =====================================================
# Mark As Read
# =====================================================

@router.put(
    "/{notification_id}/read",
    response_model=NotificationResponse
)
def read_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    return mark_as_read(
        notification_id=notification_id,
        db=db,
        current_user=current_user
    )


# =====================================================
# Mark As Sent
# =====================================================

@router.put(
    "/{notification_id}/sent",
    response_model=NotificationResponse
)
def sent_notification(
    notification_id: int,
    db: Session = Depends(get_db)
):

    return mark_as_sent(
        notification_id=notification_id,
        db=db
    )


# =====================================================
# Delete Notification
# =====================================================

@router.delete(
    "/{notification_id}",
    status_code=status.HTTP_200_OK
)
def remove_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    return delete_notification(
        notification_id=notification_id,
        db=db,
        current_user=current_user
    )