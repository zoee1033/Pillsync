from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.reminder import Reminder
from app.models.user import User

from app.schemas.notification_schema import (
    NotificationCreate,
    NotificationUpdate
)


# ==========================================================
# Create Notification
# ==========================================================

def create_notification(
    db: Session,
    notification: NotificationCreate,
    current_user: User
):

    reminder = (
        db.query(Reminder)
        .join(Reminder.medicine)
        .join(Reminder.medicine.property.mapper.class_.treatment)
        .filter(
            Reminder.id == notification.reminder_id
        )
        .first()
    )

    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found."
        )

    if reminder.medicine.treatment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied."
        )

    new_notification = Notification(
        user_id=current_user.id,
        reminder_id=notification.reminder_id,
        title=notification.title,
        message=notification.message,
        notification_type=notification.notification_type,
        is_read=False,
        is_sent=False
    )

    db.add(new_notification)
    db.commit()
    db.refresh(new_notification)

    return new_notification


# ==========================================================
# Get All Notifications
# ==========================================================

def get_notifications(
    db: Session,
    current_user: User
):

    return (
        db.query(Notification)
        .filter(
            Notification.user_id == current_user.id
        )
        .order_by(
            Notification.created_at.desc()
        )
        .all()
    )


# ==========================================================
# Get Notification By ID
# ==========================================================

def get_notification_by_id(
    notification_id: int,
    db: Session,
    current_user: User
):

    notification = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.user_id == current_user.id
        )
        .first()
    )

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found."
        )

    return notification


# ==========================================================
# Mark Notification As Read
# ==========================================================

def mark_as_read(
    notification_id: int,
    db: Session,
    current_user: User
):

    notification = get_notification_by_id(
        notification_id,
        db,
        current_user
    )

    notification.is_read = True

    db.commit()
    db.refresh(notification)

    return notification


# ==========================================================
# Mark Notification As Sent
# ==========================================================

def mark_as_sent(
    notification_id: int,
    db: Session
):

    notification = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id
        )
        .first()
    )

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found."
        )

    notification.is_sent = True
    notification.sent_at = datetime.utcnow()

    db.commit()
    db.refresh(notification)

    return notification


# ==========================================================
# Delete Notification
# ==========================================================

def delete_notification(
    notification_id: int,
    db: Session,
    current_user: User
):

    notification = get_notification_by_id(
        notification_id,
        db,
        current_user
    )

    db.delete(notification)
    db.commit()

    return {
        "message": "Notification deleted successfully."
    }


# ==========================================================
# Get Unread Notifications
# ==========================================================

def get_unread_notifications(
    db: Session,
    current_user: User
):

    return (
        db.query(Notification)
        .filter(
            Notification.user_id == current_user.id,
            Notification.is_read == False
        )
        .order_by(
            Notification.created_at.desc()
        )
        .all()
    )