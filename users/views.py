from rest_framework import generics
from rest_framework import status
from .models import (
    User,
    Patient,
    Doctor,
    Appointment,
    MedicalRecord,
    SecuritySettings,
    TrustedDevice,
    Notification,
    DeviceToken,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
import random
from django.utils import timezone
from django.utils.timezone import make_aware, is_naive
from datetime import datetime, timedelta
from rest_framework.exceptions import ValidationError
from django.utils.dateparse import parse_datetime
from rest_framework.views import APIView
from users.serializers import (
    RegisterSerializer,
    ProfileSerializer,
    SecuritySettingsSerializer,
    TrustedDeviceSerializer,
)
from patient.serializers import (
    MedicalRecordSerializer,
    AppointmentSerializer,
)


from users.utils import send_verification_email

from django.utils.translation import gettext_lazy as _

###


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer


###


class LoginView(APIView):

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": _("Invalid credentials")}, status=400)

        user = authenticate(username=user.username, password=password)

        if user is None:
            return Response({"error": _("Invalid credentials")}, status=400)

        # 🔥 التحقق من التفعيل
        if not user.is_verified:
            return Response({"error": _("Account not verified")}, status=403)

        refresh = RefreshToken.for_user(user)
        TrustedDevice.objects.create(
            user=user,
            device_name=request.data.get("device_name", "Unknown Device"),
            device_type=request.data.get("device_type", "mobile"),
            location=request.data.get("location", "Unknown"),
        )

        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            }
        )


###


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        try:
            refresh_token = request.data.get("refresh")
            device_id = request.data.get("device_id")

            if not refresh_token:
                raise ValidationError(_("Refresh token is required"))

            # 🟢 blacklist token
            token = RefreshToken(refresh_token)
            token.blacklist()

            # 🟢 تعطيل الجهاز الحالي
            if device_id:
                TrustedDevice.objects.filter(id=device_id, user=request.user).update(
                    is_active=False
                )

            return Response({"message": _("Logged out successfully")})

        except Exception:
            return Response({"error": _("Invalid token")}, status=400)


###


class AppointmentDetailView(generics.RetrieveAPIView):

    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        try:
            patient = Patient.objects.get(user=self.request.user)
        except Patient.DoesNotExist:
            return Appointment.objects.none()

        # المستخدم فقط يشوف مواعيده
        return Appointment.objects.filter(patient=patient)


###


class AIAnalysisView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        if request.user.role != "doctor":
            return Response({"error": _("Only doctors can use AI")}, status=403)

        appointment_id = request.data.get("appointment_id")

        if not appointment_id:
            return Response({"error": _("appointment_id is required")}, status=400)

        try:
            doctor = Doctor.objects.get(user=request.user)
            appointment = Appointment.objects.get(id=appointment_id, doctor=doctor)
        except:
            return Response({"error": _("Appointment not found")}, status=404)

        symptoms = appointment.patient_symptoms

        # 🔥 AI وهمي (محاكاة)
        symptoms_lower = symptoms.lower()

        if "fever" in symptoms_lower and "cough" in symptoms_lower:
            analysis = "Possible diagnosis: Flu or COVID-19"
        elif "headache" in symptoms_lower and "nausea" in symptoms_lower:
            analysis = "Possible diagnosis: Migraine"
        elif "stomach" in symptoms_lower:
            analysis = "Possible diagnosis: Gastritis"
        else:
            analysis = "Further medical examination required"

        return Response({"symptoms": symptoms, "analysis": analysis})


###

# نستخدمه في ال resend و forget password


class SendOTPView(APIView):

    def post(self, request):
        email = request.data.get("email")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": _("User not found")}, status=404)

        code = str(random.randint(100000, 999999))

        user.verification_code = code
        user.save()

        # إرسال ايميل
        send_verification_email(email, code)

        return Response(
            {"message": _("Acount created . Verification code sent to email .")}
        )


###


class VerifyOTPView(APIView):

    def post(self, request):
        email = request.data.get("email")
        code = request.data.get("code")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": _("User not found")}, status=404)

        if user.verification_code != code:
            return Response({"error": _("Invalid code")}, status=400)

        user.is_verified = True
        user.verification_code = None
        user.save()

        return Response({"message": _("Account verified successfully")})


###


class ForgotPasswordView(APIView):

    def post(self, request):
        email = request.data.get("email")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": _("User not found")}, status=404)

        code = str(random.randint(100000, 999999))

        user.verification_code = code
        user.save()

        send_verification_email(email, code)

        return Response({"message": _("Reset code sent")})


###


class VerifyResetCodeView(APIView):

    def post(self, request):
        email = request.data.get("email")
        code = request.data.get("code")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": _("User not found")}, status=404)

        if user.verification_code != code:
            return Response({"error": _("Invalid code")}, status=400)

        return Response({"message": _("Code verified")})


###


class ResetPasswordView(APIView):

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": _("User not found")}, status=404)

        user.set_password(password)
        user.verification_code = None
        user.save()

        return Response({"message": _("Password reset successful")})


###


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data)


###


class MedicalRecordsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            patient = Patient.objects.get(user=request.user)
        except Patient.DoesNotExist:
            return Response({"error": _("Patient not found")}, status=404)

        records = MedicalRecord.objects.filter(appointment__patient=patient).order_by(
            "-created_at"
        )[:5]

        serializer = MedicalRecordSerializer(records, many=True)
        return Response(serializer.data)


###


class AvailableSlotsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        date_str = request.GET.get("date")

        if not date_str:
            return Response({"error": _("Date is required")}, status=400)

        # تحويل التاريخ
        date = datetime.strptime(date_str, "%Y-%m-%d").date()

        #  كل الأوقات الممكنة
        start_time = datetime.combine(date, datetime.min.time()).replace(hour=9)
        end_time = datetime.combine(date, datetime.min.time()).replace(hour=17)

        slots = []
        current = start_time

        while current < end_time:
            slots.append(current)
            current += timedelta(minutes=30)

        # المواعيد المحجوزة
        booked = Appointment.objects.filter(
            appointment_date__date=date, status="pending"
        )

        booked_times = [b.appointment_date.time() for b in booked]

        # نحذف المحجوز
        available = [
            slot.strftime("%H:%M") for slot in slots if slot.time() not in booked_times
        ]

        return Response({"available_slots": available})


###


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")

        if not old_password or not new_password:
            return Response({"error": _("Both fields are required")}, status=400)

        user = request.user

        # تحقق من كلمة المرور القديمة
        if not user.check_password(old_password):
            return Response({"error": _("Old password is incorrect")}, status=400)

        # تغيير كلمة المرور
        user.set_password(new_password)
        user.save()

        return Response({"message": _("Password changed successfully")})


###


class SecuritySettingsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        settings, created = SecuritySettings.objects.get_or_create(user=request.user)

        serializer = SecuritySettingsSerializer(settings)

        return Response(serializer.data)

    def patch(self, request):

        settings, created = SecuritySettings.objects.get_or_create(user=request.user)

        serializer = SecuritySettingsSerializer(
            settings, data=request.data, partial=True
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)


###


class TrustedDevicesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        devices = TrustedDevice.objects.filter(user=request.user).order_by("-last_seen")

        serializer = TrustedDeviceSerializer(devices, many=True)

        return Response(serializer.data)


###

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import (
    OutstandingToken,
    BlacklistedToken,
)


class LogoutAllDevicesView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        # 🟢 blacklist كل tokens الخاصة بالمستخدم
        tokens = OutstandingToken.objects.filter(user=request.user)

        for token in tokens:

            try:
                BlacklistedToken.objects.get_or_create(token=token)
            except:
                pass

        # 🟢 تعطيل الأجهزة
        TrustedDevice.objects.filter(user=request.user).update(is_active=False)

        return Response({"message": _("Logged out from all devices")})


###


class NotificationUnreadCountView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        patient = getattr(
            request.user,
            "patient",
            None,
        )

        doctor = getattr(
            request.user,
            "doctor",
            None,
        )

        queryset = Notification.objects.none()

        if patient:

            queryset = Notification.objects.filter(
                patient=patient,
                is_read=False,
            )

        elif doctor:

            queryset = Notification.objects.filter(
                doctor=doctor,
                is_read=False,
            )

        return Response({"unread_count": queryset.count()})


####


class MarkNotificationReadView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, notification_id):

        notification = Notification.objects.filter(id=notification_id).first()

        if not notification:

            return Response(
                {"message": _("Notification not found.")},
                status=status.HTTP_404_NOT_FOUND,
            )

        # 🟢 security check
        if (
            hasattr(request.user, "doctor")
            and notification.doctor != request.user.doctor
        ):

            return Response(
                {"message": _("You are not allowed to access this notification.")},
                status=status.HTTP_403_FORBIDDEN,
            )

        if (
            hasattr(request.user, "patient")
            and notification.patient != request.user.patient
        ):

            return Response(
                {"message": _("You are not allowed to access this notification.")},
                status=status.HTTP_403_FORBIDDEN,
            )

        notification.is_read = True

        notification.save()

        return Response({"message": _("Notification marked as read.")})


####


class DismissNotificationView(APIView):

    permission_classes = [IsAuthenticated]

    def delete(self, request, notification_id):

        notification = Notification.objects.filter(id=notification_id).first()

        if not notification:

            return Response(
                {
                    "success": False,
                    "message": _("Notification not found."),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        doctor = getattr(
            request.user,
            "doctor",
            None,
        )

        patient = getattr(
            request.user,
            "patient",
            None,
        )

        # 🟢 doctor check
        if doctor and notification.doctor != doctor:

            return Response(
                {
                    "success": False,
                    "message": _("You are not allowed to access this notification."),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # 🟢 patient check
        if patient and notification.patient != patient:

            return Response(
                {
                    "success": False,
                    "message": _("You are not allowed to access this notification."),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        notification.delete()

        return Response(
            {
                "success": True,
                "message": _("Notification dismissed successfully."),
            },
            status=status.HTTP_200_OK,
        )


######


class MarkAllNotificationsReadView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        doctor = getattr(
            request.user,
            "doctor",
            None,
        )

        patient = getattr(
            request.user,
            "patient",
            None,
        )

        queryset = Notification.objects.none()

        # 🟢 doctor
        if doctor:

            queryset = Notification.objects.filter(
                doctor=doctor,
                is_read=False,
            )

        # 🟢 patient
        elif patient:

            queryset = Notification.objects.filter(
                patient=patient,
                is_read=False,
            )

        updated_count = queryset.update(is_read=True)

        return Response(
            {
                "success": True,
                "message": _("All notifications marked as read."),
                "updated_count": updated_count,
            },
            status=status.HTTP_200_OK,
        )


#######


class SaveDeviceTokenView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        token = request.data.get("token")

        if not token:
            raise ValidationError({"token": _("Token is required.")})

        DeviceToken.objects.update_or_create(
            token=token,
            defaults={
                "user": request.user,
            },
        )

        return Response(
            {
                "success": True,
                "message": _("Device token saved successfully."),
            }
        )
