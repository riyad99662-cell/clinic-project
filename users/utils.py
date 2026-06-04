from users.firebase_service import send_push_notification
from users.models import Notification


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
