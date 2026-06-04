from rest_framework import serializers
from django.core.mail import send_mail
from django.conf import settings
from users.models import (
    Appointment,
    MedicalRecord,
    Invoice,
    MedicalCondition,
    Scan,
    Clinic,
    Patient,
)
from doctor.serializers import PrescriptionSerializer
from rest_framework.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class AppointmentSerializer(serializers.ModelSerializer):

    doctor_name = serializers.CharField(source="doctor.user.username", read_only=True)
    patient_name = serializers.CharField(source="patient.user.username", read_only=True)
    clinic_name = serializers.CharField(source="doctor.clinic_name", read_only=True)
    clinic_address = serializers.CharField(
        source="doctor.clinic_address", read_only=True
    )
    session_duration = serializers.IntegerField(default=30)

    def get_doctor_name(self, obj):
        return f"Dr. {obj.doctor.user.username}"

    class Meta:
        model = Appointment
        fields = [
            "id",
            "doctor_name",
            "patient_name",
            "appointment_date",
            "status",
            "clinic_name",
            "clinic_address",
            "session_duration",
            # "patient_symptoms",
        ]


###


class MedicalRecordSerializer(serializers.ModelSerializer):

    doctor_name = serializers.CharField(
        source="appointment.doctor.user.username", read_only=True
    )
    appointment_date = serializers.DateTimeField(
        source="appointment.appointment_date", read_only=True
    )

    prescriptions = PrescriptionSerializer(many=True, read_only=True)

    class Meta:
        model = MedicalRecord
        fields = [
            "id",
            "doctor_name",
            "appointment_date",
            "diagnosis",
            "notes",
            "heart_rate",
            "temperature",
            "prescriptions",
            "created_at",
        ]


###


class InvoiceSerializer(serializers.ModelSerializer):

    doctor_name = serializers.CharField(
        source="appointment.doctor.user.username", read_only=True
    )
    appointment_date = serializers.DateTimeField(
        source="appointment.appointment_date", read_only=True
    )

    class Meta:
        model = Invoice
        fields = [
            "id",
            "reference",
            "amount",
            "status",
            "payment_method",
            "doctor_name",
            "appointment_date",
            "created_at",
        ]


###


class NextAppointmentSerializer(serializers.ModelSerializer):

    doctor_name = serializers.CharField(
        source="doctor.user.username",
        read_only=True,
    )

    clinic_address = serializers.CharField(
        source="doctor.clinic_address",
        read_only=True,
    )
    specialization = serializers.CharField(source="doctor.specialization")

    class Meta:
        model = Appointment

        fields = [
            "id",
            "appointment_date",
            "status",
            "doctor_name",
            "clinic_address",
            "specialization",
        ]


###


class PatientProfileSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Patient
        fields = [
            "name",
            "medical_id",
            "blood_type",
            "height",
            "weight",
            "profile_image",
        ]


###

from rest_framework import serializers
from users.models import MedicalRecord


class MedicalRecordListSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source="appointment.doctor.user.username")
    appointment_date = serializers.DateTimeField(source="appointment.appointment_date")

    class Meta:
        model = MedicalRecord
        fields = [
            "id",
            "doctor_name",
            "appointment_date",
            "diagnosis",
            "created_at",
        ]


###

from users.models import Vital


class VitalSerializer(serializers.ModelSerializer):

    class Meta:
        model = Vital
        fields = "__all__"
        read_only_fields = ["patient", "created_at"]

    # 🔥 blood pressure format
    def validate_blood_pressure(self, value):
        try:
            systolic, diastolic = value.split("/")
            systolic = int(systolic)
            diastolic = int(diastolic)
        except:
            raise serializers.ValidationError(_("Format must be like 120/80"))

        if not (80 <= systolic <= 200):
            raise serializers.ValidationError(_("Invalid systolic value"))

        if not (50 <= diastolic <= 130):
            raise serializers.ValidationError(_("Invalid diastolic value"))

        return value

    # 🔥 heart rate
    def validate_heart_rate(self, value):
        if not (40 <= value <= 200):
            raise serializers.ValidationError(_("Heart rate out of range"))
        return value

    # 🔥 glucose
    def validate_glucose(self, value):
        if not (50 <= value <= 500):
            raise serializers.ValidationError(_("Glucose value unrealistic"))
        return value


###


from rest_framework import serializers
from users.models import MedicalCondition
from datetime import date


class MedicalConditionSerializer(serializers.ModelSerializer):

    class Meta:
        model = MedicalCondition
        fields = [
            "id",
            "condition_name",
            "condition_status",
            "diagnosed_at",
            "notes",
        ]
        read_only_fields = ["patient"]

    # 🔥 1 — condition_name
    def validate_condition_name(self, value):
        if len(value) < 3:
            raise serializers.ValidationError(_("Condition name too short"))
        return value

    # 🔥 2 — condition_status
    def validate_condition_status(self, value):
        allowed = ["high_risk", "managed", "stable"]
        if value not in allowed:
            raise serializers.ValidationError(_("Invalid status"))
        return value

    # 🔥 3 — diagnosed_at
    def validate_diagnosed_at(self, value):
        if value > date.today():
            raise serializers.ValidationError(_("Date cannot be in the future"))
        return value

    # 🔥 4 — global validation
    def validate(self, data):
        if data.get("condition_status") == "high_risk" and not data.get("notes"):
            raise serializers.ValidationError(
                {"notes": _("Notes required for high risk conditions")}
            )
        return data


###

from users.models import Allergy


class AllergySerializer(serializers.ModelSerializer):
    class Meta:
        model = Allergy
        fields = "__all__"
        read_only_fields = ["patient"]

    def validate_allergy_name(self, value):
        if len(value) < 2:
            raise serializers.ValidationError(_("Too short"))
        return value


###

from users.models import Medication


class MedicationSerializer(serializers.ModelSerializer):
    frequency_display = serializers.CharField(
        source="get_frequency_display", read_only=True
    )

    class Meta:
        model = Medication
        fields = [
            "id",
            "drug_name",
            "dosage",
            "frequency",
            "frequency_display",
            "notes",
        ]
        read_only_fields = ["patient"]

    # 🔥 validation
    def validate_drug_name(self, value):
        if len(value) < 2:
            raise serializers.ValidationError(_("Drug name too short"))
        return value

    def validate_dosage(self, value):
        if not any(char.isdigit() for char in value):
            raise serializers.ValidationError(_("Dosage must contain a number"))
        return value


###


class ScanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scan
        fields = "__all__"
        read_only_fields = ["patient", "is_verified", "extracted_data"]


###

from rest_framework import serializers
from users.models import Payment


class PatientPaymentSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(
        source="appointment.doctor.user.username", read_only=True
    )

    appointment_date = serializers.DateTimeField(
        source="appointment.date", read_only=True
    )

    invoice_id = serializers.IntegerField(source="invoice.id", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "amount",
            "payment_status",
            "payment_method",
            "doctor_name",
            "appointment_date",
            "invoice_id",
            "created_at",
        ]


###


class BillingTransactionSerializer(serializers.ModelSerializer):

    patient_name = serializers.CharField(source="appointment.patient.user.username")

    class Meta:
        model = Payment

        fields = [
            "id",
            "patient_name",
            "amount",
            "payment_method",
            "payment_status",
            "transaction_reference",
            "created_at",
        ]


####


class UpdateHealthSerializer(serializers.Serializer):

    # 🟢 Patient info
    blood_type = serializers.CharField(required=False)
    height = serializers.FloatField(required=False)
    weight = serializers.FloatField(required=False)

    # 🟢 Vital info
    blood_pressure = serializers.CharField(required=False)
    heart_rate = serializers.IntegerField(required=False)
    glucose = serializers.FloatField(required=False)


######


class ClinicSerializer(serializers.ModelSerializer):

    doctor_name = serializers.CharField(source="doctor.user.username", read_only=True)

    class Meta:
        model = Clinic

        fields = [
            "id",
            "name",
            "doctor_name",
            "address",
            "latitude",
            "longitude",
            "phone_number",
            "opening_time",
            "closing_time",
        ]


#####
