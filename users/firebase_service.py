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
                    title=title,
                    body=body,
                ),
                data=data or {},  # إضافة بيانات إضافية
            )

            # Send
            response = messaging.send(message)
            print(f"✅ Push sent to {device.token} | Response: {response}")

        except messaging.UnregisteredError:
            # Token expired → delete it
            print(f"🗑️ Removing invalid token: {device.token}")
            device.delete()

        except messaging.InvalidArgumentError:
            print(f"❌ Invalid token format: {device.token}")
            device.delete()

        except Exception as e:
            print(f"❌ Push error for token {device.token}: {e}")
            continue
