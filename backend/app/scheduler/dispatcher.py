from types import SimpleNamespace
from firebase_admin import messaging

from app.models.device_token import DeviceToken
from app.schemas.notification_schema import NotificationCreate
from app.services.firebase_service import send_push_notification
from app.services.notification_service import create_notification, mark_as_sent


def dispatch_reminder(db, reminder):
    """
    Send a push notification for a due reminder and persist a notification record.
    Iterates through active device tokens for the user and deactivates invalid/unregistered tokens.
    """

    medicine_id = getattr(reminder, "medicine_id", reminder.medicine.id)
    user_id = reminder.medicine.treatment.user_id

    active_tokens = (
        db.query(DeviceToken)
        .filter(
            DeviceToken.user_id == user_id,
            DeviceToken.is_active == True
        )
        .order_by(
            DeviceToken.last_used_at.desc(),
            DeviceToken.created_at.desc()
        )
        .all()
    )

    token_ids = [t.id for t in active_tokens]
    print(f"Active device token(s) for user {user_id}: {len(active_tokens)} found -> IDs {token_ids}")

    if not active_tokens:
        print(f"No active device token found for user {user_id}")
        return

    notification = None

    for device in active_tokens:
        masked_tok = f"{device.fcm_token[:6]}...{device.fcm_token[-6:]}" if len(device.fcm_token) > 12 else "***"
        print(f"Attempting push notification for user {user_id} using token ID {device.id} ({masked_tok})")

        try:
            if not notification:
                notification = create_notification(
                    db=db,
                    notification=NotificationCreate(
                        reminder_id=reminder.id,
                        title="💊 Pill Reminder",
                        message=f"It's time to take {reminder.medicine.medicine_name}",
                        notification_type="Reminder",
                    ),
                    current_user=SimpleNamespace(id=user_id),
                )

            response = send_push_notification(
                token=device.fcm_token,
                title="💊 Pill Reminder",
                body=f"It's time to take {reminder.medicine.medicine_name}",
                data={
                    "reminder_id": str(reminder.id),
                    "medicine_id": str(medicine_id),
                    "user_id": str(user_id),
                },
            )

            mark_as_sent(notification.id, db)
            print(f"Reminder sent successfully to user {user_id} using device token ID {device.id}")
            break

        except Exception as e:
            err_str = str(e).lower()
            is_unregistered = (
                isinstance(e, messaging.UnregisteredError)
                or "notregistered" in err_str
                or "invalid-registration-token" in err_str
                or "not a valid fcm registration token" in err_str
            )

            if is_unregistered:
                print(f"Token ID {device.id} is invalid/unregistered ({e}). Automatically deactivating token...")
                device.is_active = False
                try:
                    db.commit()
                except Exception as commit_err:
                    db.rollback()
                    print(f"Failed to deactivate token ID {device.id}: {commit_err}")
                print(f"Continuing to next available device token for user {user_id}...")
            else:
                print(f"Firebase error sending push to token ID {device.id}: {e}")