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


# ==========================================================
# Process Notification Action (Single Source of Truth)
# ==========================================================

def process_notification_action(
    notification_id: int,
    action_type: str,
    db: Session,
    current_user: User
):
    action_type = action_type.lower().strip()
    print(f"[TRACE {datetime.utcnow().isoformat()}] [STAGE 8: BACKEND_API_REQUEST] process_notification_action: Notification ID={notification_id}, Action={action_type}", flush=True)

    if action_type == "delete":
        res = delete_notification(notification_id, db, current_user)
        print(f"[TRACE {datetime.utcnow().isoformat()}] [STAGE 9: DATABASE_UPDATE] Notification ID={notification_id} DELETED from PostgreSQL.", flush=True)
        return res

    notification = get_notification_by_id(notification_id, db, current_user)
    reminder = notification.reminder

    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found for this notification."
        )

    medicine = reminder.medicine
    treatment = medicine.treatment if medicine else None

    if action_type == "taken":
        from app.services.history_service import create_history
        from app.schemas.history_schema import HistoryCreate
        from app.models.enums import HistoryStatus

        create_history(
            db=db,
            history=HistoryCreate(
                treatment_id=treatment.id if treatment else 0,
                medicine_id=medicine.id if medicine else 0,
                reminder_id=reminder.id,
                scheduled_time=reminder.next_trigger_at or datetime.utcnow(),
                status=HistoryStatus.TAKEN.value,
                notes="Action taken via Notification"
            ),
            current_user=current_user
        )
        notification.is_read = True
        db.commit()
        db.refresh(notification)
        print(f"[TRACE {datetime.utcnow().isoformat()}] [STAGE 9: DATABASE_UPDATE] Notification ID={notification_id} updated: is_read=True, History row inserted, Medicine qty decremented to {medicine.quantity}.", flush=True)
        return notification

    elif action_type in ["skipped", "skip"]:
        from app.services.history_service import create_history
        from app.schemas.history_schema import HistoryCreate
        from app.models.enums import HistoryStatus

        create_history(
            db=db,
            history=HistoryCreate(
                treatment_id=treatment.id if treatment else 0,
                medicine_id=medicine.id if medicine else 0,
                reminder_id=reminder.id,
                scheduled_time=reminder.next_trigger_at or datetime.utcnow(),
                status=HistoryStatus.SKIPPED.value,
                skip_reason="Action skipped via Notification",
                notes="Skipped occurrence"
            ),
            current_user=current_user
        )
        notification.is_read = True
        db.commit()
        db.refresh(notification)
        print(f"[TRACE {datetime.utcnow().isoformat()}] [STAGE 9: DATABASE_UPDATE] Notification ID={notification_id} updated: is_read=True, History row inserted.", flush=True)
        return notification

    elif action_type in ["snooze", "snoozed"]:
        from app.services.reminder_service import snooze_reminder

        snooze_reminder(
            reminder_id=reminder.id,
            minutes=reminder.snooze_minutes or 10,
            db=db,
            current_user=current_user
        )
        notification.is_read = True
        db.commit()
        db.refresh(notification)
        print(f"[TRACE {datetime.utcnow().isoformat()}] [STAGE 9: DATABASE_UPDATE] Notification ID={notification_id} updated: is_read=True, Reminder snoozed.", flush=True)
        return notification

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid action_type '{action_type}'"
        )


def process_reminder_action(
    reminder_id: int,
    action_type: str,
    db: Session,
    current_user: User
):
    action_type = action_type.lower().strip()
    print(f"[TRACE {datetime.utcnow().isoformat()}] [STAGE 8: BACKEND_API_REQUEST] process_reminder_action: Reminder ID={reminder_id}, Action={action_type}", flush=True)

    reminder = (
        db.query(Reminder)
        .filter(Reminder.id == reminder_id)
        .first()
    )

    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found."
        )

    # Find unread notification if any
    notif = (
        db.query(Notification)
        .filter(
            Notification.reminder_id == reminder_id,
            Notification.user_id == current_user.id,
            Notification.is_read == False
        )
        .order_by(Notification.created_at.desc())
        .first()
    )

    if notif:
        return process_notification_action(notif.id, action_type, db, current_user)

    # Fallback when notification row is already deleted/missing
    medicine = reminder.medicine
    treatment = medicine.treatment if medicine else None

    if action_type == "taken":
        from app.services.history_service import create_history
        from app.schemas.history_schema import HistoryCreate
        from app.models.enums import HistoryStatus

        create_history(
            db=db,
            history=HistoryCreate(
                treatment_id=treatment.id if treatment else 0,
                medicine_id=medicine.id if medicine else 0,
                reminder_id=reminder.id,
                scheduled_time=reminder.next_trigger_at or datetime.utcnow(),
                status=HistoryStatus.TAKEN.value,
                notes="Action taken via Reminder"
            ),
            current_user=current_user
        )
        return {"message": "Dose marked taken successfully."}

    elif action_type in ["skipped", "skip"]:
        from app.services.history_service import create_history
        from app.schemas.history_schema import HistoryCreate
        from app.models.enums import HistoryStatus

        create_history(
            db=db,
            history=HistoryCreate(
                treatment_id=treatment.id if treatment else 0,
                medicine_id=medicine.id if medicine else 0,
                reminder_id=reminder.id,
                scheduled_time=reminder.next_trigger_at or datetime.utcnow(),
                status=HistoryStatus.SKIPPED.value,
                skip_reason="Action skipped via Reminder",
                notes="Skipped occurrence"
            ),
            current_user=current_user
        )
        return {"message": "Dose marked skipped successfully."}

    elif action_type in ["snooze", "snoozed"]:
        from app.services.reminder_service import snooze_reminder

        snooze_reminder(
            reminder_id=reminder.id,
            minutes=reminder.snooze_minutes or 10,
            db=db,
            current_user=current_user
        )
        return {"message": "Reminder snoozed successfully."}

    elif action_type == "delete":
        return {"message": "No notification to delete."}

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid action_type '{action_type}'"
        )