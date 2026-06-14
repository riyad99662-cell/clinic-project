from django.shortcuts import render
from httpcore import request
from rest_framework import generics
from users.models import (
    AIAnalysis,
    Patient,
    Doctor,
    Appointment,
    Invoice,
    MedicalRecord,
    Allergy,
    Medication,
    Scan,
    Payment,
    Vital,
    Clinic,
    Notification,
)

from patient.serializers import (
    AppointmentSerializer,
    MedicalRecordSerializer,
    AppointmentSerializer,
    InvoiceSerializer,
    NextAppointmentSerializer,
    PatientProfileSerializer,
    MedicalConditionSerializer,
    AllergySerializer,
    MedicationSerializer,
    ScanSerializer,
    PatientPaymentSerializer,
    MedicalCondition,
    MedicalRecordListSerializer,
    UpdateHealthSerializer,
    ClinicSerializer,
)

from users.serializers import NotificationSerializer

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.views import APIView
from django.conf import settings
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.timezone import make_aware, is_naive
from datetime import datetime
from rest_framework.exceptions import ValidationError
from django.utils.dateparse import parse_datetime
from rest_framework.views import APIView
from rest_framework.exceptions import NotFound
from rest_framework.views import APIView


from rest_framework.generics import CreateAPIView
import uuid

from rest_framework.generics import DestroyAPIView
from rest_framework.generics import ListAPIView
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework.generics import UpdateAPIView
from .serializers import VitalSerializer
from django.utils.translation import gettext_lazy as _
from users.utils import create_notification

###


class CreateAppointmentView(generics.CreateAPIView):

    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):

        #  تحقق من التفعيل
        if not self.request.user.is_verified:
            raise ValidationError(_("Account not verified"))

        #  جلب المريض
        try:
            patient = Patient.objects.get(user=self.request.user)
        except Patient.DoesNotExist:
            raise ValidationError(_("Patient not found"))

        #  الطبيب الوحيد
        doctor = Doctor.objects.first()

        #  جلب التاريخ
        appointment_date = self.request.data.get("appointment_date")

        if not appointment_date:
            raise ValidationError(_("appointment_date is required"))

        try:
            appointment_date = datetime.fromisoformat(appointment_date)
            appointment_date = make_aware(appointment_date)
        except ValueError:
            raise ValidationError(_("Invalid date format"))

        #  منع الماضي
        if appointment_date < timezone.now():
            raise ValidationError(_("Cannot book past time"))

        #  منع التكرار
        if Appointment.objects.filter(
            appointment_date=appointment_date, status="pending"
        ).exists():
            raise ValidationError(_("This slot is already booked"))

        # priority

        priority = self.request.data.get("urgent", "routine")

        # symptoms = request.data.get("symptoms")

        analysis_id = self.request.data.get("analysis_id")

        #  حفظ
        appointment = serializer.save(
            patient=patient,
            doctor=doctor,
            appointment_date=appointment_date,
            priority=priority,
        )

        if analysis_id:
            try:
                analysis = AIAnalysis.objects.get(
                    id=analysis_id,
                    patient=patient,
                )

                analysis.appointment = appointment
                analysis.save()

            except AIAnalysis.DoesNotExist:
                pass

        create_notification(
            doctor=doctor,
            title=_("New Appointment"),
            message=_("%(patient)s booked a new appointment.")
            % {"patient": patient.user.username},
            notification_type="appointment",
        )


###


class MyAppointmentsView(generics.ListAPIView):

    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        try:
            patient = Patient.objects.get(user=self.request.user)
        except Patient.DoesNotExist:
            return Appointment.objects.none()
            # (((or))) raise NotFound("You must create a patient profile first")

        return Appointment.objects.filter(patient=patient).order_by("-appointment_date")


###


class MyInvoicesView(generics.ListAPIView):

    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        try:
            patient = Patient.objects.get(user=self.request.user)
        except Patient.DoesNotExist:
            return Invoice.objects.none()

        return Invoice.objects.filter(patient=patient).order_by("-created_at")


###


class MedicalRecordDetailView(generics.RetrieveAPIView):

    serializer_class = MedicalRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        appointment_id = self.kwargs.get("appointment_id")
        patient = Patient.objects.get(user=self.request.user)

        try:
            return MedicalRecord.objects.get(
                appointment__id=appointment_id, appointment__patient=patient
            )
        except MedicalRecord.DoesNotExist:
            raise NotFound(_("No medical record found for this appointment"))


###


class NextAppointmentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            patient = Patient.objects.get(user=request.user)
        except Patient.DoesNotExist:
            return Response({"error": _("Patient not found")}, status=404)

        appointment = (
            Appointment.objects.filter(
                patient=patient, appointment_date__gte=timezone.now()
            )
            .order_by("appointment_date")
            .first()
        )

        if not appointment:
            return Response({"message": _("No upcoming appointments")})

        serializer = NextAppointmentSerializer(appointment)
        return Response(serializer.data)


###


class UpdateAppointmentView(generics.UpdateAPIView):

    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        # المستخدم فقط يعدل مواعيده
        try:
            patient = Patient.objects.get(user=self.request.user)
        except Patient.DoesNotExist:
            return Appointment.objects.none()

        return Appointment.objects.filter(patient=patient)

    def perform_update(self, serializer):

        appointment = self.get_object()

        appointment_date = self.request.data.get("appointment_date")
        reason = self.request.data.get("reason")
        consultation_type = self.request.data.get("consultation_type")

        if not appointment_date:
            raise ValidationError(_("appointment_date is required"))

        appointment_date = parse_datetime(appointment_date)

        if appointment_date is None:
            raise ValidationError(_("Invalid date format"))

        if is_naive(appointment_date):
            appointment_date = make_aware(appointment_date)

        if appointment_date < timezone.now():
            raise ValidationError(_("Cannot book past time"))

        if (
            Appointment.objects.filter(
                appointment_date=appointment_date,
                status="scheduled",
            )
            .exclude(id=appointment.id)
            .exists()
        ):
            raise ValidationError(_("This slot is already booked"))

        serializer.save(
            appointment_date=appointment_date,
            notes=reason,
            consultation_type=consultation_type,
        )

        create_notification(
            doctor=appointment.doctor,
            title=_("Appointment Updated"),
            message=_(
                "Patient %(patient_name)s changed the appointment date to %(appointment_date)s."
            )
            % {
                "patient_name": appointment.patient.user.username,
                "appointment_date": appointment_date.strftime("%Y-%m-%d %H:%M"),
            },
            notification_type="appointment",
        )


###


class CreatePaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        appointment_id = request.data.get("appointment_id")
        payment_method = request.data.get("payment_method")

        if not appointment_id:
            raise ValidationError(_("appointment_id is required"))

        if not payment_method:
            raise ValidationError(_("payment_method is required"))

        try:
            patient = Patient.objects.get(user=request.user)
            appointment = Appointment.objects.get(id=appointment_id, patient=patient)
        except Appointment.DoesNotExist:
            return Response({"error": _("Invalid appointment")}, status=404)

        # 💰 السعر من السيرفر
        amount = appointment.price

        # 🔒 منع تكرار الدفع لنفس الموعد
        if hasattr(appointment, "payment"):
            raise ValidationError(_("Payment already exists for this appointment"))

        # 🧾 إنشاء Payment
        payment = Payment.objects.create(
            appointment=appointment,
            amount=amount,
            payment_method=payment_method,
            payment_status="paid",  # أو pending حسب النظام
        )

        # 🔢 reference
        reference = f"INV-{uuid.uuid4().hex[:6].upper()}"

        # 🧾 إنشاء Invoice مرتبط بالـ Payment
        invoice = Invoice.objects.create(
            payment=payment,  # 🔥 أهم سطر
            patient=patient,
            appointment=appointment,
            amount=amount,
            payment_method=payment_method,
            status="paid",
            reference=reference,
        )

        create_notification(
            doctor=appointment.doctor,
            title=_("New Payment"),
            message=_("A new payment has been received by Patient %(patient_name)s .")
            % {
                "patient_name": patient.user.username,
            },
            notification_type="payment",
        )

        return Response(
            {
                "message": _("Payment successful"),
                "payment_id": payment.id,
                "invoice_id": invoice.id,
                "reference": invoice.reference,
            }
        )


###


class CancelAppointmentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        appointment_id = request.data.get("appointment_id")

        if not appointment_id:
            return Response({"error": _("appointment_id is required")}, status=400)

        # 🟢 patient
        try:
            patient = Patient.objects.get(user=request.user)

        except Patient.DoesNotExist:
            return Response({"error": _("Patient not found")}, status=404)

        # 🟢 appointment
        try:
            appointment = Appointment.objects.get(id=appointment_id, patient=patient)

        except Appointment.DoesNotExist:
            return Response({"error": _("Appointment not found")}, status=404)

        # 🟢 already cancelled
        if appointment.status == "cancelled":
            return Response({"error": _("Already cancelled")}, status=400)

        # 🟢 completed protection
        if appointment.status == "completed":
            return Response(
                {"error": _("Completed appointment can't be cancelled")}, status=400
            )

        # 🟢 cancel appointment
        appointment.status = "cancelled"
        appointment.save()

        create_notification(
            doctor=appointment.doctor,
            title=_("Appointment Updated"),
            message=_("Patient %(patient_name)s cancelled an appointment.")
            % {
                "patient_name": patient.user.username,
            },
            notification_type="appointment",
        )

        # 🟢 refund
        try:
            payment = appointment.payment

            payment.payment_status = "refunded"
            payment.save()

            invoice = payment.invoice

            invoice.status = "refunded"
            invoice.save()

        except Payment.DoesNotExist:
            pass

        return Response(
            {"success": True, "message": _("Appointment cancelled successfully")}
        )


###


class PatientProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        patient = Patient.objects.get(user=request.user)
        serializer = PatientProfileSerializer(patient)
        return Response(serializer.data)

    def put(self, request):
        patient = Patient.objects.get(user=request.user)
        serializer = PatientProfileSerializer(patient, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=400)


###


class PatientMedicalRecordsListView(ListAPIView):
    serializer_class = MedicalRecordListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        patient = Patient.objects.get(user=self.request.user)

        return MedicalRecord.objects.filter(appointment__patient=patient).order_by(
            "-created_at"
        )


###


class CreateVitalView(CreateAPIView):
    serializer_class = VitalSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        patient = Patient.objects.get(user=self.request.user)
        serializer.save(patient=patient)


###


class LatestVitalView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        patient = Patient.objects.get(user=request.user)

        vital = Vital.objects.filter(patient=patient).order_by("-created_at").first()

        if not vital:
            return Response({"detail": _("No vitals found")}, status=404)

        serializer = VitalSerializer(vital)
        return Response(serializer.data)


###


class PatientConditionsView(ListAPIView):
    serializer_class = MedicalConditionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        patient = Patient.objects.get(user=self.request.user)
        return MedicalCondition.objects.filter(patient=patient)


###


class CreateConditionView(CreateAPIView):
    serializer_class = MedicalConditionSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        patient = Patient.objects.get(user=self.request.user)
        serializer.save(patient=patient)


###


class PatientVitalsHistoryView(ListAPIView):
    serializer_class = VitalSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        patient = Patient.objects.get(user=self.request.user)

        return Vital.objects.filter(patient=patient).order_by(
            "created_at"
        )  # ⬅️ مهم للـ charts


###


class PatientAllergiesView(ListAPIView):
    serializer_class = AllergySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        patient = Patient.objects.get(user=self.request.user)
        return Allergy.objects.filter(patient=patient)


###


class CreateAllergyView(CreateAPIView):
    serializer_class = AllergySerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        patient = Patient.objects.get(user=self.request.user)
        serializer.save(patient=patient)


###


class DeleteAllergyView(DestroyAPIView):
    queryset = Allergy.objects.all()
    permission_classes = [IsAuthenticated]


###


class PatientMedicationsView(ListAPIView):
    serializer_class = MedicationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        patient = Patient.objects.get(user=self.request.user)
        return Medication.objects.filter(patient=patient)


###


class CreateMedicationView(CreateAPIView):
    serializer_class = MedicationSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        patient = Patient.objects.get(user=self.request.user)
        serializer.save(patient=patient)


###


class UpdateMedicationView(UpdateAPIView):
    queryset = Medication.objects.all()
    serializer_class = MedicationSerializer
    permission_classes = [IsAuthenticated]


###


class DeleteMedicationView(DestroyAPIView):
    queryset = Medication.objects.all()
    permission_classes = [IsAuthenticated]


###


class UploadScanView(CreateAPIView):
    serializer_class = ScanSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        patient = Patient.objects.get(user=self.request.user)
        serializer.save(patient=patient)


###


class ExtractScanView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        scan_id = request.data.get("scan_id")

        scan = get_object_or_404(Scan, id=scan_id)

        data = [
            {"drug_name": "Lisinopril", "dosage": "10mg", "frequency": "once_daily"}
        ]

        scan.extracted_data = data
        scan.save()

        return Response({"scan_id": scan.id, "medications": data})


###


class ConfirmScanView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        patient = Patient.objects.get(user=request.user)

        scan_id = request.data.get("scan_id")
        scan = Scan.objects.get(id=scan_id)

        medications = request.data.get("medications", [])

        created = []

        for med in medications:
            obj = Medication.objects.create(
                patient=patient,
                drug_name=med["drug_name"],
                dosage=med["dosage"],
                frequency=med["frequency"],
            )
            created.append(obj.id)

        scan.is_verified = True
        scan.save()

        return Response({"message": _("Medications added"), "created_ids": created})


###


class PatientPaymentListView(ListAPIView):
    serializer_class = PatientPaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        patient = Patient.objects.get(user=self.request.user)

        queryset = Payment.objects.filter(appointment__patient=patient).order_by(
            "-created_at"
        )

        # 🔍 search
        search = self.request.GET.get("search")
        if search:
            queryset = queryset.filter(
                Q(appointment__doctor__user__username__contains=search)
            )

        # 🟡 filter by status
        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        return queryset


###

from django.db.models import Sum


class PatientPaymentSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        patient = Patient.objects.get(user=request.user)

        total_paid = (
            Payment.objects.filter(
                appointment__patient=patient, payment_status="paid"
            ).aggregate(total=Sum("amount"))["total"]
            or 0
        )

        return Response({"total_paid": total_paid})


###


class UpdateHealthRecordsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = UpdateHealthSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        patient = Patient.objects.get(user=request.user)

        data = serializer.validated_data

        # 🟢 تحديث patient
        if "blood_type" in data:
            patient.blood_type = data["blood_type"]

        if "height" in data:
            patient.height = data["height"]

        if "weight" in data:
            patient.weight = data["weight"]

        patient.save()

        # 🟢 إنشاء vital جديد
        has_vital_data = any(
            [
                data.get("blood_pressure"),
                data.get("heart_rate"),
                data.get("glucose"),
            ]
        )

        if has_vital_data:

            Vital.objects.create(
                patient=patient,
                blood_pressure=data.get("blood_pressure"),
                heart_rate=data.get("heart_rate"),
                glucose=data.get("glucose"),
            )

        return Response({"message": _("Health records updated successfully")})


########


class ClinicLocationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        clinic = Clinic.objects.first()

        if not clinic:
            return Response({"error": _("Clinic not found")}, status=404)

        serializer = ClinicSerializer(clinic)

        return Response(serializer.data)


#####


class PatientNotificationsView(ListAPIView):

    serializer_class = NotificationSerializer

    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        patient = Patient.objects.get(user=self.request.user)

        queryset = (
            Notification.objects.filter(patient=patient)
            .select_related(
                "patient__user",
                "doctor__user",
            )
            .order_by("-created_at")
        )

        filter_type = self.request.query_params.get("filter")

        if filter_type == "unread":

            queryset = queryset.filter(is_read=False)

        elif filter_type == "read":

            queryset = queryset.filter(is_read=True)

        return queryset


###


class HasMedicalRecordView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        try:
            patient = Patient.objects.get(user=request.user)

        except Patient.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": _("Patient not found"),
                },
                status=404,
            )

        try:
            medical_record = MedicalRecord.objects.filter(patient=patient).first()

            return Response(
                {
                    "success": True,
                    "has_medical_record": medical_record is not None,
                    "medical_record_id": (medical_record.id if medical_record else None),
                }
            )

        except Exception as e:
            print("🔥 ERROR in has_medical_record:", e)
            raise e
