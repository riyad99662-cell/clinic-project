from rest_framework import serializers
from ai.serializers import AIAnalysisSerializer

from users.models import (
    Prescription,
    Vital,
    Scan,
    MedicalRecord,
    Appointment,
    Payment,
    MedicalCondition,
    Patient,
    DoctorSettings,
    Doctor,
)
from datetime import date
from django.utils.translation import gettext_lazy as _

###


class PrescriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prescription
        fields = ["medication_name", "dosage", "duration"]


###


class DoctorPatientSerializer(serializers.ModelSerializer):

    name = serializers.CharField(source="user.username")

    age = serializers.SerializerMethodField()

    latest_condition = serializers.SerializerMethodField()

    status_badge = serializers.SerializerMethodField()

    last_appointment = serializers.DateTimeField(read_only=True)

    total_visits = serializers.IntegerField(read_only=True)

    class Meta:
        model = Patient

        fields = [
            "id",
            "name",
            "phone",
            "age",
            "total_visits",
            "last_appointment",
            "latest_condition",
            "status_badge",
        ]

    # 🟢 العمر
    def get_age(self, obj):

        if not obj.birth_date:
            return None

        today = date.today()

        return (
            today.year
            - obj.birth_date.year
            - ((today.month, today.day) < (obj.birth_date.month, obj.birth_date.day))
        )

    # 🟢 آخر حالة مرضية
    def get_latest_condition(self, obj):

        condition = (
            MedicalCondition.objects.filter(patient=obj)
            .order_by("-diagnosed_at")
            .first()
        )

        if condition:
            return condition.condition_name

        return None

    # 🟢 badge
    def get_status_badge(self, obj):

        condition = (
            MedicalCondition.objects.filter(patient=obj)
            .order_by("-diagnosed_at")
            .first()
        )

        if not condition:
            return "normal"

        severity = condition.severity

        if severity == "high":
            return "critical"

        elif severity == "medium":
            return "chronic"

        return "normal"


###


class PatientBasicSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="user.username")

    class Meta:
        model = Patient
        fields = ["id", "name", "phone", "gender", "birth_date"]


###


class MedicalRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalRecord
        fields = "__all__"


###


class VitalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vital
        fields = "__all__"


###


class PrescriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prescription
        fields = "__all__"


###


class ScanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scan
        fields = "__all__"


###


class DoctorScheduleSerializer(serializers.ModelSerializer):

    patient_name = serializers.CharField(source="patient.user.username")

    class Meta:
        model = Appointment
        fields = [
            "id",
            "appointment_date",
            "patient_name",
            "status",
            "consultation_type",
        ]


###


class DoctorPaymentSerializer(serializers.ModelSerializer):

    patient_name = serializers.CharField(source="appointment.patient.user.username")

    class Meta:
        model = Payment
        fields = [
            "id",
            "amount",
            "payment_method",
            "payment_status",
            "created_at",
            "patient_name",
        ]


###


class EditMedicalRecordSerializer(serializers.Serializer):

    # 🟢 patient info
    patient_id = serializers.IntegerField(source="id")

    patient_name = serializers.CharField(source="user.username")

    medical_id = serializers.CharField()

    age = serializers.SerializerMethodField()

    # 🟢 vitals
    blood_pressure = serializers.SerializerMethodField()

    heart_rate = serializers.SerializerMethodField()

    glucose = serializers.SerializerMethodField()

    weight = serializers.FloatField()

    # 🟢 diagnosis
    diagnosis = serializers.SerializerMethodField()

    notes = serializers.SerializerMethodField()

    # 🟢 prescriptions
    prescriptions = serializers.SerializerMethodField()

    # -------------------------
    # age
    # -------------------------

    def get_age(self, obj):

        if not obj.birth_date:
            return None

        today = date.today()

        return (
            today.year
            - obj.birth_date.year
            - ((today.month, today.day) < (obj.birth_date.month, obj.birth_date.day))
        )

    # -------------------------
    # latest vital
    # -------------------------

    def get_latest_vital(self, obj):

        return Vital.objects.filter(patient=obj).order_by("-created_at").first()

    def get_blood_pressure(self, obj):

        vital = self.get_latest_vital(obj)

        return vital.blood_pressure if vital else None

    def get_heart_rate(self, obj):

        vital = self.get_latest_vital(obj)

        return vital.heart_rate if vital else None

    def get_glucose(self, obj):

        vital = self.get_latest_vital(obj)

        return vital.glucose if vital else None

    # -------------------------
    # medical record
    # -------------------------

    def get_latest_record(self, obj):

        return (
            MedicalRecord.objects.filter(appointment__patient=obj)
            .order_by("-created_at")
            .first()
        )

    def get_diagnosis(self, obj):

        record = self.get_latest_record(obj)

        return record.diagnosis if record else None

    def get_notes(self, obj):

        record = self.get_latest_record(obj)

        return record.notes if record else None

    # -------------------------
    # prescriptions
    # -------------------------

    def get_prescriptions(self, obj):

        record = self.get_latest_record(obj)

        if not record:
            return []

        prescriptions = Prescription.objects.filter(medical_record=record)

        return PrescriptionSerializer(prescriptions, many=True).data


###


class UpdateMedicalRecordSerializer(serializers.Serializer):

    # 🟢 vitals
    blood_pressure = serializers.CharField(required=False)

    heart_rate = serializers.IntegerField(required=False)

    glucose = serializers.FloatField(required=False)

    weight = serializers.FloatField(required=False)

    # 🟢 medical record
    diagnosis = serializers.CharField(required=False)

    notes = serializers.CharField(required=False)


###


class PrescriptionCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Prescription

        fields = [
            "id",
            "medication_name",
            "dosage",
            "duration",
            "frequency",
        ]

    def validate_medication_name(self, value):

        if len(value) < 2:
            raise serializers.ValidationError(_("Medication name too short"))

        return value


###


class PrescriptionUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Prescription

        fields = [
            "medication_name",
            "dosage",
            "duration",
            "frequency",
        ]

    def validate_medication_name(self, value):

        if len(value) < 2:

            raise serializers.ValidationError(_("Medication name too short"))

        return value


###


class DailyScheduleSerializer(serializers.ModelSerializer):

    patient_name = serializers.CharField(source="patient.user.username")

    class Meta:
        model = Appointment
        fields = [
            "id",
            "appointment_date",
            "session_duration",
            "consultation_type",
            "status",
            "patient_name",
            "priority",
        ]


###


class AppointmentPatientSerializer(serializers.ModelSerializer):

    name = serializers.CharField(source="user.username")

    age = serializers.SerializerMethodField()

    class Meta:

        model = Patient

        fields = [
            "id",
            "name",
            "gender",
            "blood_type",
            "height",
            "weight",
            "age",
        ]

    def get_age(self, obj):

        if not obj.birth_date:
            return None

        today = date.today()

        return (
            today.year
            - obj.birth_date.year
            - ((today.month, today.day) < (obj.birth_date.month, obj.birth_date.day))
        )


#####
class AppointmentRequestSerializer(serializers.ModelSerializer):

    patient_name = serializers.CharField(source="patient.user.username")
    ai_analysis = serializers.SerializerMethodField()
    patient_info = AppointmentPatientSerializer(
        source="patient",
        read_only=True,
    )

    class Meta:
        model = Appointment
        fields = [
            "id",
            "patient_name",
            "appointment_date",
            "patient_symptoms",
            "ai_analysis",
            "status",
            "consultation_type",
            "priority",
            "patient_info",
        ]

    def get_ai_analysis(self, obj):

        analysis = obj.ai_analyses.first()

        if not analysis:
            return None

        return AIAnalysisSerializer(analysis).data


###


class AppointmentReviewSerializer(serializers.ModelSerializer):

    patient_name = serializers.CharField(source="patient.user.username")

    patient_phone = serializers.CharField(source="patient.phone")

    patient_info = AppointmentPatientSerializer(
        source="patient",
        read_only=True,
    )

    class Meta:
        model = Appointment
        fields = [
            "id",
            "patient_name",
            "patient_phone",
            "patient_info",
            "appointment_date",
            "status",
            "patient_symptoms",
            "consultation_type",
            "session_duration",
            "priority",
            "notes",
        ]


###


class PrescriptionCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Prescription
        fields = [
            "medication_name",
            "dosage",
            "duration",
        ]


###


class SaveDiagnosisSerializer(serializers.Serializer):

    diagnosis = serializers.CharField()

    notes = serializers.CharField()

    prescriptions = PrescriptionCreateSerializer(many=True)


###


class PrescriptionDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = Prescription
        fields = [
            "id",
            "medication_name",
            "dosage",
            "duration",
        ]


###


class DiagnosisDetailsSerializer(serializers.ModelSerializer):

    prescriptions = PrescriptionDetailSerializer(many=True, read_only=True)

    patient_name = serializers.CharField(source="appointment.patient.user.username")

    appointment_date = serializers.DateTimeField(source="appointment.appointment_date")

    class Meta:
        model = MedicalRecord
        fields = [
            "id",
            "patient_name",
            "appointment_date",
            "diagnosis",
            "notes",
            "created_at",
            "prescriptions",
        ]


####


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


###


class DoctorSettingsSerializer(serializers.ModelSerializer):

    class Meta:
        model = DoctorSettings
        fields = "__all__"
        read_only_fields = ["doctor"]


###


class DoctorPublicProfileSerializer(serializers.ModelSerializer):

    username = serializers.CharField(source="user.username", required=False)

    class Meta:
        model = Doctor
        fields = [
            "username",
            "specialization",
            "bio",
            "clinic_address",
            "image",
        ]


###
