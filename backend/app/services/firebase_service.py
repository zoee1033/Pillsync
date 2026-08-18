from firebase_admin import messaging, exceptions

from app.firebase.firebase_config import (
    firebase_app
)


import logging
logger = logging.getLogger("FIREBASE_SERVICE")


def send_push_notification(
    token: str,
    title: str,
    body: str,
    data: dict | None = None
):
    masked_token = f"{token[:6]}...{token[-6:]}" if len(token) > 12 else "***"
    from app.config import settings
    if settings.ENABLE_VERBOSE_FIREBASE_LOGS:
        logger.debug(f"Sending FCM push notification to token: {masked_token}")

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
        if settings.ENABLE_VERBOSE_FIREBASE_LOGS:
            logger.debug(f"Firebase Admin Success response: {response}")
        return response
    except messaging.UnregisteredError as e:
        error_code = getattr(e, 'code', 'Unregistered')
        logger.warning(f"Firebase UnregisteredError for token {masked_token}: code={error_code}, detail={e}")
        raise e
    except exceptions.FirebaseError as e:
        error_code = getattr(e, 'code', 'FirebaseError')
        logger.error(f"Firebase Error for token {masked_token}: code={error_code}, detail={e}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected Exception for token {masked_token}: {e}", exc_info=True)
        raise e