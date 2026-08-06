from firebase_admin import messaging, exceptions

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
    print(f"Sending FCM push notification to token: {masked_token}", flush=True)

    payload_data = data.copy() if data else {}
    payload_data["title"] = title
    payload_data["body"] = body

    # Use data-only payload to prevent duplicate notifications between Firebase default handler and Service Worker
    message = messaging.Message(
        token=token,
        data=payload_data
    )

    try:
        response = messaging.send(
            message,
            app=firebase_app
        )
        print(f"Firebase Admin Success response: {response}", flush=True)
        return response
    except messaging.UnregisteredError as e:
        error_code = getattr(e, 'code', 'Unregistered')
        print(f"Firebase UnregisteredError for token {masked_token}: code={error_code}, detail={e}", flush=True)
        raise e
    except exceptions.FirebaseError as e:
        error_code = getattr(e, 'code', 'FirebaseError')
        print(f"Firebase Error for token {masked_token}: code={error_code}, detail={e}", flush=True)
        raise e
    except Exception as e:
        print(f"Unexpected Exception for token {masked_token}: {e}", flush=True)
        raise e