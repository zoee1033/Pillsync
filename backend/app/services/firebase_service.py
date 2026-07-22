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

    message = messaging.Message(

        notification=messaging.Notification(

            title=title,

            body=body

        ),

        token=token,

        data=data or {}

    )

    response = messaging.send(
        message,
        app=firebase_app
    )

    return response