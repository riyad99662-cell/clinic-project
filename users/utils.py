from users.firebase_service import send_push_notification
from users.models import Notification

import logging


def create_notification(
    *,
    title,
    message,
    notification_type,
    doctor=None,
    patient=None,
    is_urgent=False,
):

    # 1) إنشاء الإشعار في قاعدة البيانات
    notification = Notification.objects.create(
        doctor=doctor,
        patient=patient,
        title=title,
        message=message,
        notification_type=notification_type,
        is_urgent=is_urgent,
    )

    # 2) إرسال الإشعار للمريض
    if patient:
        try:
            send_push_notification(
                patient.user,
                title,
                message,
                data={
                    "type": notification_type,
                    "notification_id": str(notification.id),
                    "is_urgent": str(is_urgent),
                },
            )
        except Exception as e:
            print("Push error (patient):", e)

    # 3) إرسال الإشعار للطبيب
    if doctor:
        try:
            send_push_notification(
                doctor.user,
                title,
                message,
                data={
                    "type": notification_type,
                    "notification_id": str(notification.id),
                    "is_urgent": str(is_urgent),
                },
            )
        except Exception as e:
            print("Push error (doctor):", e)

    return notification


logger = logging.getLogger(__name__)

import resend


def send_verification_email(to_email, code):
    try:
        resend.Emails.send(
            {
                "from": "Clinic App <onboarding@resend.dev>",
                "to": to_email,
                "subject": "Your Verification Code",
                "html": f"<p>Your verification code is: <strong>{code}</strong></p>",
            }
        )
    except Exception as e:
        print("EMAIL ERROR:", e)
        raise
