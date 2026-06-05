from django.conf import settings
import firebase_admin
from firebase_admin import credentials, messaging
import os
import json

# Initialize Firebase once
if not firebase_admin._apps:
    cred = credentials.Certificate(json.loads(os.getenv("FIREBASE_CREDENTIALS")))
    firebase_app = firebase_admin.initialize_app(cred)
else:
    firebase_app = firebase_admin.get_app()


def send_push_notification(user, title, body):
    if firebase_app is None:
        print("Firebase not initialized")
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
            print("Push sent to:", device.token)

        except Exception as e:
            print("Push error:", e)
            continue
print("Firebase initialized:", firebase_app is not None)
