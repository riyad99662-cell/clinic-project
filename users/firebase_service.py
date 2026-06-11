from firebase_admin import exceptions
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


def send_push_notification(user, title, body, data=None):
    """
    إرسال إشعار للمستخدم مع معالجة الأخطاء وحذف التوكنات المنتهية.
    """

    if firebase_app is None:
        print("❌ Firebase not initialized")
        return

    tokens = user.device_tokens.all()

    if not tokens:
        print(f"⚠️ No device tokens for user {user.id}")
        return

    for device in tokens:
        try:
            # Build message
            message = messaging.Message(
                token=device.token,
                notification=messaging.Notification(
                    title=str(title),
                    body=str(body),
                ),
                data=data or {},
                android=messaging.AndroidConfig(
                    priority="high",
                    notification=messaging.AndroidNotification(
                        priority="max",
                        channel_id="clinic_channel",
                    ),
                ),
            )

            # Send
            response = messaging.send(message)
            print(f"✅ Push sent to {device.token} | Response: {response}")

        except exceptions.NotFoundError:
            print(f"🗑️ Token not found (expired or deleted): {device.token}")
            device.delete()

        except exceptions.InvalidArgumentError:
            print(f"❌ Invalid token format: {device.token}")
            device.delete()

        except exceptions.UnauthenticatedError as e:
            print(f"❌ Firebase credentials error: {e}")

        except exceptions.FirebaseError as e:
            print(f"❌ Firebase error for {device.token}: {e}")

        except Exception as e:
            print(f"❌ Unknown error for {device.token}: {e}")
