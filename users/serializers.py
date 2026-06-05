from urllib import request
from rest_framework import serializers
from .models import (
    User,
    Patient,
    Doctor,
    SecuritySettings,
    TrustedDevice,
    Notification,
    DeviceToken,
)
import random
from users.utils import safe_send_mail
from django.conf import settings

from django.utils.translation import gettext_lazy as _

class RegisterSerializer(serializers.ModelSerializer):

    full_name = serializers.CharField(write_only=True)
    phone = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["full_name", "email", "phone", "password"]

    def create(self, validated_data):
        full_name = validated_data.pop("full_name")
        phone = validated_data.pop("phone")
        email = request.data.get("email")
        username = full_name.replace(" ", "").lower()

        user = User.objects.create(
            username=username, email=validated_data["email"], role="patient"
        )

        user.set_password(validated_data["password"])

        # 🔥 إنشاء OTP
        code = str(random.randint(100000, 999999))
        user.verification_code = code
        user.save()

        # 🔥 إرسال الإيميل
        import logging
        logger = logging.getLogger(__name__)

        try:
            safe_send_mail(
                _("Your Verification Code"),
                _("Your code is: %(code)s") % {"code": code},
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False,
            )
        except Exception as e:
            logger.error(f"EMAIL ERROR: {e}")
            raise e

        # إنشاء Patient
        Patient.objects.create(user=user, phone=phone)

        return user


###


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ["phone", "address", "birth_date", "gender"]


###


class DoctorSerializer(serializers.ModelSerializer):

    class Meta:
        model = Doctor
        fields = ["specialization", "clinic_name", "clinic_address"]


###


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "role"]


###


class SecuritySettingsSerializer(serializers.ModelSerializer):

    class Meta:
        model = SecuritySettings
        fields = [
            "language",
            "data_sharing",
            "profile_visibility",
            "two_factor_enabled",
            "biometric_enabled",
        ]


####


class TrustedDeviceSerializer(serializers.ModelSerializer):

    class Meta:
        model = TrustedDevice
        fields = "__all__"


###


class NotificationSerializer(serializers.ModelSerializer):

    patient_name = serializers.SerializerMethodField()

    doctor_name = serializers.SerializerMethodField()

    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M")

    class Meta:

        model = Notification

        fields = [
            "id",
            "notification_type",
            "title",
            "message",
            "is_read",
            "is_urgent",
            "created_at",
            "patient_name",
            "doctor_name",
        ]

    def get_patient_name(self, obj):

        if obj.patient:

            return obj.patient.user.username

        return None

    def get_doctor_name(self, obj):

        if obj.doctor:

            return obj.doctor.user.username

        return None


####


class DeviceTokenSerializer(serializers.ModelSerializer):

    class Meta:
        model = DeviceToken
        fields = ["token"]
