from users.firebase_service import send_push_notification
from users.models import Notification

import logging
from django.core.mail import EmailMultiAlternatives, get_connection
from django.conf import settings


def create_notification(
    *,
    title,
    message,
    notification_type,
    doctor=None,
    patient=None,
    is_urgent=False,
):

    notification = Notification.objects.create(
        doctor=doctor,
        patient=patient,
        title=title,
        message=message,
        notification_type=notification_type,
        is_urgent=is_urgent,
    )
    if patient:
        send_push_notification(
            patient.user,
            title,
            message,
        )

    if doctor:
        send_push_notification(
            doctor.user,
            title,
            message,
        )

    return notification

logger = logging.getLogger(__name__)

def send_mail(
    subject,
    message,
    from_email,
    recipient_list,
    *,
    fail_silently=False,
    auth_user=None,
    auth_password=None,
    connection=None,
    html_message=None,
):
    try:
        connection = connection or get_connection(
            username=auth_user,
            password=auth_password,
            fail_silently=False,  # نخليه False لنمسك الأخطاء
        )

        mail = EmailMultiAlternatives(
            subject,
            message,
            from_email or settings.DEFAULT_FROM_EMAIL,
            recipient_list,
            connection=connection,
        )

        if html_message:
            mail.attach_alternative(html_message, "text/html")

        return mail.send()

    except Exception as e:
        # مهم جدًا: لا نكسر التطبيق
        logger.error(f"Email sending failed: {e}")

        # ما نوقف التسجيل أو الـ API
        if fail_silently:
            return 0

        # إذا بدك صارم (اختياري)
        # raise

        return 0
