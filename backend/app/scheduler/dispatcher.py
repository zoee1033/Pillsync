from app.models.device_token import DeviceToken
from app.services.firebase_service import send_push_notification


def dispatch_reminder(db, reminder):
    """
    Send a push notification for a due reminder.
    """

    # Get the user through the relationship chain
    user_id = reminder.medicine.treatment.user_id

    device = (
        db.query(DeviceToken)
        .filter(
            DeviceToken.user_id == user_id,
            DeviceToken.is_active == True
        )
        .first()
    )

    if not device:
        print(f"No active device token found for user {user_id}")
        return

    try:
        send_push_notification(
            token=device.fcm_token,
            title="💊 Pill Reminder",
            body=f"It's time to take {reminder.medicine.medicine_name}",
            data={
                "reminder_id": str(reminder.id),
                "medicine_id": str(reminder.medicine_id),
                "user_id": str(user_id)
            }
        )

        print(
            f"Reminder sent successfully to user {user_id}"
        )

    except Exception as e:
        print(f"Firebase Error: {e}")