from users.firebase_service import send_push_notification
from users.models import Notification
from rest_framework.response import Response

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

    

    return Response(
        {
            "status": "success",
            "message": "Notification created and sent successfully",
            "notification": {
                "id": notification.id,
                "title": notification.title,
                "body": notification.message,
                "type": notification.notification_type,
                "is_urgent": notification.is_urgent,
            },
            "push_data_sent": {
                "type": notification_type,
                "notification_id": str(notification.id),
                "is_urgent": str(is_urgent),
            },
            "sent_to": {
                "patient": bool(patient),
                "doctor": bool(doctor),
            },
        }
    )


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
