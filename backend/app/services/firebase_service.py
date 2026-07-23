from firebase_admin import messaging

from app.firebase.firebase_config import (
    firebase_app
)


def send_push_notification(
    token: str,
    title: str,
    body: str,
    data: dict | None = None
):
    masked_token = f"{token[:6]}...{token[-6:]}" if len(token) > 12 else "***"
    print(f"Sending FCM push notification to token: {masked_token}")

    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body
        ),
        token=token,
        data=data or {}
    )

    try:
        response = messaging.send(
            message,
            app=firebase_app
        )
        print(f"Firebase Admin Success response: {response}")
        return response
    except messaging.UnregisteredError as e:
        error_code = getattr(e, 'code', 'Unregistered')
        print(f"Firebase UnregisteredError for token {masked_token}: code={error_code}, detail={e}")
        raise e
    except messaging.FirebaseError as e:
        error_code = getattr(e, 'code', 'FirebaseError')
        print(f"Firebase Error for token {masked_token}: code={error_code}, detail={e}")
        raise e
    except Exception as e:
        print(f"Unexpected Exception for token {masked_token}: {e}")
        raise e