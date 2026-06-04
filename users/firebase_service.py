from django.conf import settings
import firebase_admin

from firebase_admin import credentials
from firebase_admin import messaging

cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)


firebase_admin.initialize_app(cred)


def send_push_notification(
    user,
    title,
    body,
):

    tokens = user.device_tokens.all()

    for device in tokens:

        try:

            message = messaging.Message(
                token=device.token,
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
            )

            messaging.send(message)

        except Exception:
            continue
