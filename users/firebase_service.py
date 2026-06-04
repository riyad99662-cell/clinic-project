from django.conf import settings
import firebase_admin
from firebase_admin import credentials, messaging
import os

firebase_app = None

if hasattr(settings, "FIREBASE_CREDENTIALS_PATH") and os.path.exists(
    settings.FIREBASE_CREDENTIALS_PATH
):

    cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)

    firebase_app = firebase_admin.initialize_app(cred)

def send_push_notification(
    user,
    title,
    body,
):
    if firebase_app is None :
        return 
    
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
