from django.contrib import admin
from .models import (
    User,
    Patient,
    Doctor,
    Appointment,
    MedicalRecord,
    Prescription,
    Payment,
    AIAnalysis,
    DeviceToken,
    Invoice,
    Allergy,
    Medication,
    Scan,
    DoctorSettings,
    SecuritySettings,
    TrustedDevice,
    Notification,
    Clinic,
)
from django.contrib.auth.hashers import make_password


class UserAdmin(admin.ModelAdmin):
    list_display = ["username", "email", "role"]

    def save_model(self, request, obj, form, change):
        # تشفير كلمة المرور إذا لم تكن مشفرة
        if not obj.password.startswith("pbkdf2_"):
            obj.password = make_password(obj.password)
        super().save_model(request, obj, form, change)


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "phone",
        "gender",
        "medical_id",
        "blood_type",
        "height",
        "weight",
    )

    search_fields = ("user__username", "phone", "medical_id")

    list_filter = ("gender", "blood_type")

    ordering = ("id",)


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "specialization",
    )

    search_fields = ("user__username", "specialization")

    ordering = ("id",)


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "patient",
        "doctor",
        "appointment_date",
        "status",
    )

    search_fields = (
        "patientuserusername",
        "doctoruserusername",
    )

    list_filter = ("status", "appointment_date")

    ordering = ("-appointment_date",)


@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "appointment",
        "diagnosis",
        "created_at",
    )

    search_fields = ("diagnosis",)

    ordering = ("-created_at",)


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "medical_record",
        "medication_name",
        "dosage",
        "duration",
    )

    search_fields = ("medication_name",)

    ordering = ("id",)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "appointment",
        "amount",
        "payment_status",
        "created_at",
    )

    list_filter = ("payment_status",)

    ordering = ("-created_at",)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "patient",
        "amount",
        "status",
        "created_at",
    )

    list_filter = ("status",)

    ordering = ("-created_at",)


from .models import Vital


@admin.register(Vital)
class VitalAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "patient",
        "blood_pressure",
        "heart_rate",
        "glucose",
        "created_at",
    )

    ordering = ("-created_at",)


@admin.register(Allergy)
class AllergyAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "allergy_name", "severity")
    list_filter = ("severity",)


@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "patient",
        "drug_name",
        "dosage",
        "frequency",
    )

    list_filter = ("frequency",)


@admin.register(Scan)
class ScanAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "patient",
        "is_verified",
        "created_at",
    )

    list_filter = ("is_verified",)


@admin.register(DoctorSettings)
class DoctorSettingsAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "doctor",
        "clinic_start_time",
        "clinic_end_time",
        "biometric_enabled",
    )

    list_filter = (
        "clinic_start_time",
        "biometric_enabled",
    )

    search_fields = ("doctor__user__username",)

    ordering = ("id",)


@admin.register(SecuritySettings)
class SecuritySettingsAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "user",
        "two_factor_enabled",
        "language",
    )

    list_filter = ("two_factor_enabled",)

    search_fields = (
        "user__username",
        "user__email",
    )

    ordering = ("user",)


@admin.register(TrustedDevice)
class TrustedDeviceAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "user",
        "device_name",
        "device_type",
        "last_seen",
    )

    list_filter = ("last_seen",)

    search_fields = (
        "user__username",
        "device_name",
        "device_type",
    )

    ordering = ("-last_seen",)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "doctor",
        "patient",
        "notification_type",
        "is_urgent",
        "is_read",
        "created_at",
    )

    list_filter = (
        "notification_type",
        "is_urgent",
        "is_read",
    )

    search_fields = (
        "title",
        "message",
        "doctor__user__username",
        "patient__user__username",
    )

    ordering = ("-created_at",)


@admin.register(Clinic)
class ClinicAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "doctor",
        "name",
        "address",
        "phone_number",
        "opening_time",
        "closing_time",
    )

    search_fields = (
        "name",
        "address",
    )


admin.site.register(User, UserAdmin)
admin.site.register(AIAnalysis)
admin.site.register(DeviceToken)
