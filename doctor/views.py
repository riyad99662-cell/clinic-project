from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, NotFound
from rest_framework import status
from rest_framework import generics
from rest_framework.generics import RetrieveAPIView, ListAPIView
from datetime import timedelta, datetime
from django.utils.timezone import now
from django.db.models import Count, Sum, Max, Q
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils.translation import gettext_lazy as _
from ai.serializers import AIAnalysisSerializer
from users.utils import create_notification

from users.models import (
    AIAnalysis,
    MedicalRecord,
    Prescription,
    Doctor,
    Appointment,
    Patient,
    Vital,
    Scan,
    Invoice,
    Payment,
    DoctorSettings,
    Notification,
    MedicalCondition,
)
from patient.serializers import AppointmentSerializer
from users.serializers import NotificationSerializer

from .serializers import (
    PatientBasicSerializer,
    MedicalRecordSerializer,
    VitalSerializer,
    PrescriptionSerializer,
    ScanSerializer,
    EditMedicalRecordSerializer,
    UpdateMedicalRecordSerializer,
    PrescriptionCreateSerializer,
    PrescriptionUpdateSerializer,
    DailyScheduleSerializer,
    AppointmentRequestSerializer,
    AppointmentReviewSerializer,
    SaveDiagnosisSerializer,
    DiagnosisDetailsSerializer,
    BillingTransactionSerializer,
    DoctorPaymentSerializer,
    DoctorScheduleSerializer,
    DoctorPatientSerializer,
    DoctorSettingsSerializer,
    DoctorPublicProfileSerializer,
)

###


class UpdateAppointmentStatusView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):

        try:
            doctor = Doctor.objects.get(user=request.user)
        except Doctor.DoesNotExist:
            raise NotFound(_("Doctor profile not found."))

        try:
            appointment = Appointment.objects.get(
                id=pk,
                doctor=doctor,
            )
        except Appointment.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": _("Appointment not found."),
                },
                status=404,
            )

        status_value = request.data.get("status")

        allowed_statuses = ["approved", "rejected"]

        if status_value not in allowed_statuses:
            raise ValidationError(
                {
                    "status": _(
                        "Invalid status. Allowed values are "
                        "'approved' or 'rejected'."
                    )
                }
            )

        appointment.status = status_value
        appointment.save(update_fields=["status"])

        notification_messages = {
            "approved": _("Your appointment has been approved by Dr. %(doctor_name)s."),
            "rejected": _("Your appointment has been rejected by Dr. %(doctor_name)s."),
        }

        create_notification(
            patient=appointment.patient,
            title=_("Appointment Status Updated"),
            message=notification_messages[status_value]
            % {
                "doctor_name": doctor.user.username,
            },
            notification_type="appointment",
        )

        status_messages = {
            "approved": _("approved"),
            "rejected": _("rejected"),
            "cancelled": _("cancelled"),
        }

        return Response(
            {
                "success": True,
                "message": _("Appointment %(status)s successfully.")
                % {"status": status_messages.get(status_value, status_value)},
            }
        )


# ------------------------------------------------------------------


class DoctorAppointmentsView(generics.ListAPIView):

    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        try:
            doctor = Doctor.objects.get(user=self.request.user)
        except Doctor.DoesNotExist:
            raise NotFound(_("Doctor profile not found."))

        return (
            Appointment.objects.filter(doctor=doctor)
            .select_related("patient__user")
            .order_by("-appointment_date")
        )


# ------------------------------------------------------------------


class DoctorDashboardView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        today = now().date()

        # 🟢 Statistics
        total_patients = Patient.objects.count()

        appointments_today = Appointment.objects.filter(
            appointment_date__date=today
        ).count()

        # 🟢 Revenue
        revenue = (
            Payment.objects.filter(payment_status="paid").aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )

        # 🟢 Today's Schedule
        appointments = (
            Appointment.objects.filter(appointment_date__date=today)
            .select_related("patient__user")
            .order_by("appointment_date")
        )

        schedule_data = [
            {
                "id": appointment.id,
                "time": appointment.appointment_date,
                "patient_name": appointment.patient.user.username,
                "status": appointment.status,
            }
            for appointment in appointments
        ]

        return Response(
            {
                "success": True,
                "message": _("Dashboard data retrieved successfully."),
                "data": {
                    "stats": {
                        "total_patients": total_patients,
                        "appointments_today": appointments_today,
                    },
                    "revenue": revenue,
                    "schedule": schedule_data,
                    "alerts": [],
                },
            }
        )


# ------------------------------------------------------------------


class DoctorPatientsListView(ListAPIView):

    serializer_class = DoctorPatientSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        try:
            doctor = Doctor.objects.get(user=self.request.user)
        except Doctor.DoesNotExist:
            raise NotFound(_("Doctor profile not found."))

        queryset = (
            Patient.objects.filter(appointment__doctor=doctor)
            .annotate(
                total_visits=Count("appointment"),
                last_appointment=Max("appointment__appointment_date"),
            )
            .select_related("user")
            .distinct()
        )

        # 🟢 Search by patient username
        search = self.request.query_params.get("search")

        if search:
            queryset = queryset.filter(Q(user__username__icontains=search))

        return queryset


# --------------------------------


class DoctorPatientDetailView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, patient_id):

        # 🟢 Validate doctor profile
        try:
            doctor = Doctor.objects.get(user=request.user)
        except Doctor.DoesNotExist:
            raise NotFound(_("Doctor profile not found."))

        # 🟢 Validate patient
        try:
            patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": _("Patient not found."),
                },
                status=404,
            )

        # 🟢 Ensure doctor has access to this patient
        has_access = patient.appointment_set.filter(doctor=doctor).exists()

        if not has_access:
            return Response(
                {
                    "success": False,
                    "message": _("You are not allowed to access this patient."),
                },
                status=403,
            )

        ai_analyses = AIAnalysis.objects.filter(patient=patient).order_by("-created_at")

        # 🟢 Patient basic data
        patient_data = PatientBasicSerializer(patient).data

        # 🟢 Medical records
        records = MedicalRecord.objects.filter(appointment__patient=patient)

        # 🟢 Vitals
        vitals = Vital.objects.filter(patient=patient)

        # 🟢 Prescriptions
        prescriptions = Prescription.objects.filter(
            medical_record__appointment__patient=patient
        )

        # 🟢 Scans
        scans = Scan.objects.filter(patient=patient)

        return Response(
            {
                "success": True,
                "message": _("Patient details retrieved successfully."),
                "data": {
                    "patient": patient_data,
                    "ai_analyses": AIAnalysisSerializer(
                        ai_analyses,
                        many=True,
                    ).data,
                    "medical_records": MedicalRecordSerializer(
                        records,
                        many=True,
                    ).data,
                    "vitals": VitalSerializer(
                        vitals,
                        many=True,
                    ).data,
                    "prescriptions": PrescriptionSerializer(
                        prescriptions,
                        many=True,
                    ).data,
                    "scans": ScanSerializer(
                        scans,
                        many=True,
                    ).data,
                },
            }
        )


# ------------------------------------------------------------------


class DoctorScheduleView(ListAPIView):

    serializer_class = DoctorScheduleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        try:
            doctor = Doctor.objects.get(user=self.request.user)
        except Doctor.DoesNotExist:
            raise NotFound(_("Doctor profile not found."))

        queryset = Appointment.objects.filter(doctor=doctor)

        filter_type = self.request.query_params.get("filter")
        date = self.request.query_params.get("date")

        today = now().date()

        # 🟢 Filter today's appointments
        if filter_type == "today":

            queryset = queryset.filter(appointment_date__date=today)

        # 🟢 Filter upcoming appointments
        elif filter_type == "upcoming":

            queryset = queryset.filter(appointment_date__date__gte=today)

        # 🟢 Filter by specific date
        if date:

            queryset = queryset.filter(appointment_date__date=date)

        return queryset.select_related("patient__user").order_by("appointment_date")


# ------------------------------------------------------------------


class DoctorAlertsView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        try:
            doctor = Doctor.objects.get(user=request.user)
        except Doctor.DoesNotExist:
            raise NotFound(_("Doctor profile not found."))

        current_time = now()

        alerts = []

        # 🟢 Upcoming appointments within one hour
        upcoming_appointments = Appointment.objects.filter(
            doctor=doctor,
            appointment_date__gte=current_time,
            appointment_date__lte=(current_time + timedelta(hours=1)),
        ).select_related("patient__user")

        for appointment in upcoming_appointments:

            alerts.append(
                {
                    "type": "upcoming",
                    "message": _("Appointment with %(username)s is scheduled soon.")
                    % {
                        "username": appointment.patient.user.username,
                    },
                    "time": appointment.appointment_date,
                }
            )

        # 🟢 Missed appointments
        missed_appointments = Appointment.objects.filter(
            doctor=doctor,
            appointment_date__lt=current_time,
            status="pending",
        ).select_related("patient__user")
        for appointment in missed_appointments:

            alerts.append(
                {
                    "type": "missed",
                    "message": _("Missed appointment with %(username)s.")
                    % {
                        "username": appointment.patient.user.username,
                    },
                    "time": appointment.appointment_date,
                }
            )
        # 🟢 Pending payments
        pending_payments = Payment.objects.filter(
            appointment__doctor=doctor,
            payment_status="pending",
        )
        for payment in pending_payments:

            alerts.append(
                {
                    "type": "payment",
                    "message": _("Pending payment for appointment #%(appointment_id)s.")
                    % {
                        "appointment_id": payment.appointment.id,
                    },
                    "amount": payment.amount,
                }
            )

        return Response(
            {
                "success": True,
                "message": _("Alerts retrieved successfully."),
                "data": {
                    "alerts": alerts,
                },
            }
        )


# ------------------------------------------------------------------


class DoctorEarningsView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        try:
            doctor = Doctor.objects.get(user=request.user)
        except Doctor.DoesNotExist:
            raise NotFound(_("Doctor profile not found."))

        today = now().date()

        # 🟢 Paid payments only
        payments = Payment.objects.filter(
            appointment__doctor=doctor,
            payment_status="paid",
        )

        # 🟢 Today's earnings
        total_today = (
            payments.filter(created_at__date=today).aggregate(total=Sum("amount"))[
                "total"
            ]
            or 0
        )

        # 🟢 Monthly earnings
        total_month = (
            payments.filter(created_at__month=today.month).aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )

        # 🟢 Payments list
        payments_data = DoctorPaymentSerializer(
            payments.order_by("-created_at"),
            many=True,
        ).data

        return Response(
            {
                "success": True,
                "message": _("Earnings retrieved successfully."),
                "data": {
                    "total_today": total_today,
                    "total_month": total_month,
                    "payments": payments_data,
                },
            }
        )


# ------------------------------------------------------------------


class EditMedicalRecordView(RetrieveAPIView):

    permission_classes = [IsAuthenticated]

    lookup_field = "id"

    queryset = Patient.objects.all()

    # -------------------------
    # Serializer selection
    # -------------------------

    def get_serializer_class(self):

        if self.request.method in ["PATCH", "PUT"]:
            return UpdateMedicalRecordSerializer

        return EditMedicalRecordSerializer

    # -------------------------
    # Doctor access protection
    # -------------------------

    def get_queryset(self):

        try:
            doctor = Doctor.objects.get(user=self.request.user)
        except Doctor.DoesNotExist:
            raise NotFound(_("Doctor profile not found."))

        return Patient.objects.filter(appointment__doctor=doctor).distinct()

    # -------------------------
    # PATCH
    # -------------------------

    def patch(self, request, *args, **kwargs):

        patient = self.get_object()

        serializer = self.get_serializer(
            data=request.data,
            partial=True,
        )

        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        # -------------------------
        # Latest vital signs
        # -------------------------

        vital = Vital.objects.filter(patient=patient).order_by("-created_at").first()

        if not vital:

            vital = Vital.objects.create(
                patient=patient,
                blood_pressure=data.get("blood_pressure"),
                heart_rate=data.get("heart_rate"),
                glucose=data.get("glucose"),
            )

        else:

            vital.blood_pressure = data.get(
                "blood_pressure",
                vital.blood_pressure,
            )

            vital.heart_rate = data.get(
                "heart_rate",
                vital.heart_rate,
            )

            vital.glucose = data.get(
                "glucose",
                vital.glucose,
            )

            vital.save()

        # -------------------------
        # Update patient weight
        # -------------------------

        patient.weight = data.get(
            "weight",
            patient.weight,
        )

        patient.save(update_fields=["weight"])

        # -------------------------
        # Latest medical record
        # -------------------------

        record = (
            MedicalRecord.objects.filter(appointment__patient=patient)
            .order_by("-created_at")
            .first()
        )

        if not record:

            latest_appointment = (
                Appointment.objects.filter(patient=patient)
                .order_by("-appointment_date")
                .first()
            )

            if not latest_appointment:

                raise ValidationError(
                    {"appointment": _("No appointment found for this patient.")}
                )

            record = MedicalRecord.objects.create(
                appointment=latest_appointment,
                diagnosis=data.get("diagnosis", ""),
                notes=data.get("notes", ""),
            )

        else:

            record.diagnosis = data.get(
                "diagnosis",
                record.diagnosis,
            )

            record.notes = data.get(
                "notes",
                record.notes,
            )

            record.save()

        return Response(
            {
                "success": True,
                "message": _("Medical record updated successfully."),
            }
        )


# ------------------------------------------------------------------


class AddPrescriptionView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        record_id = request.data.get("record_id")
        prescriptions = request.data.get("prescriptions")

        if not record_id or not prescriptions:

            raise ValidationError(
                {"detail": _("record_id and prescriptions " "are required.")}
            )

        # 🟢 Doctor validation
        try:
            doctor = Doctor.objects.get(user=request.user)
        except Doctor.DoesNotExist:
            raise NotFound(_("Doctor profile not found."))

        # 🟢 Medical record validation
        try:

            record = MedicalRecord.objects.get(
                id=record_id,
                appointment__doctor=doctor,
            )

        except MedicalRecord.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": _("Medical record not found."),
                },
                status=404,
            )

        created_prescriptions = []

        # 🟢 Create prescriptions
        for item in prescriptions:

            serializer = PrescriptionCreateSerializer(data=item)

            serializer.is_valid(raise_exception=True)

            prescription = serializer.save(medical_record=record)

            created_prescriptions.append(
                PrescriptionCreateSerializer(prescription).data
            )

        create_notification(
            patient=record.appointment.patient,
            title=_("New Prescription"),
            message=_("A new prescription has been added."),
            notification_type="prescription",
        )

        return Response(
            {
                "success": True,
                "message": _("Prescriptions added successfully."),
                "data": created_prescriptions,
            }
        )


# ------------------------------------------------------------------


class UpdatePrescriptionView(APIView):

    permission_classes = [IsAuthenticated]

    def patch(self, request, id):

        # 🟢 Doctor validation
        try:
            doctor = Doctor.objects.get(user=request.user)
        except Doctor.DoesNotExist:
            raise NotFound(_("Doctor profile not found."))

        # 🟢 Prescription validation
        try:

            prescription = Prescription.objects.get(
                id=id,
                medical_record__appointment__doctor=doctor,
            )

        except Prescription.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": _("Prescription not found."),
                },
                status=404,
            )

        # 🟢 Serializer
        serializer = PrescriptionUpdateSerializer(
            prescription,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(raise_exception=True)

        serializer.save()

        return Response(
            {
                "success": True,
                "message": _("Prescription updated successfully."),
                "data": serializer.data,
            }
        )


# ------------------------------------------------------------------


class DeletePrescriptionView(APIView):

    permission_classes = [IsAuthenticated]

    def delete(self, request, id):

        # 🟢 Doctor validation
        try:
            doctor = Doctor.objects.get(user=request.user)
        except Doctor.DoesNotExist:
            raise NotFound(_("Doctor profile not found."))

        # 🟢 Prescription validation
        try:

            prescription = Prescription.objects.get(
                id=id,
                medical_record__appointment__doctor=doctor,
            )

        except Prescription.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": _("Prescription not found."),
                },
                status=404,
            )

        prescription.delete()

        return Response(
            {
                "success": True,
                "message": _("Prescription deleted successfully."),
            }
        )


# ------------------------------------------------------------------


class DoctorDailyScheduleView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        # 🟢 Current doctor
        try:
            doctor = Doctor.objects.get(user=request.user)
        except Doctor.DoesNotExist:
            raise NotFound(_("Doctor profile not found."))

        # 🟢 Selected date from frontend
        selected_date = request.GET.get("date")

        # 🟢 Validate selected date
        if selected_date:

            try:
                date = datetime.strptime(
                    selected_date,
                    "%Y-%m-%d",
                ).date()

            except ValueError:

                raise ValidationError(
                    {"date": _("Invalid date format. " "Use YYYY-MM-DD.")}
                )

        else:
            date = now().date()

        # 🟢 Appointments for selected day
        appointments = (
            Appointment.objects.filter(
                doctor=doctor,
                appointment_date__date=date,
            )
            .select_related("patient__user")
            .order_by("appointment_date")
        )

        # 🟢 Calendar strip
        calendar_days = []

        for i in range(-2, 5):

            current_day = date + timedelta(days=i)

            calendar_days.append(
                {
                    "date": current_day,
                    "day_name": current_day.strftime("%a"),
                    "day_number": current_day.day,
                    "is_selected": current_day == date,
                }
            )

        return Response(
            {
                "success": True,
                "message": _("Daily schedule retrieved successfully."),
                "data": {
                    "selected_date": date,
                    "sessions_count": appointments.count(),
                    "calendar_days": calendar_days,
                    "appointments": (
                        DailyScheduleSerializer(
                            appointments,
                            many=True,
                        ).data
                    ),
                },
            }
        )


# ------------------------------------------------------------------


class AppointmentRequestsView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        try:
            doctor = Doctor.objects.get(user=request.user)
        except Doctor.DoesNotExist:
            raise NotFound(_("Doctor profile not found."))

        requests = (
            Appointment.objects.filter(
                doctor=doctor,
                status="pending",
            )
            .select_related("patient__user")
            .order_by("appointment_date")
        )

        pending_count = Appointment.objects.filter(
            doctor=doctor,
            status="pending",
        ).count()

        approved_count = Appointment.objects.filter(
            doctor=doctor,
            status="approved",
        ).count()

        next_slot = (
            Appointment.objects.filter(
                doctor=doctor,
                status="approved",
            )
            .order_by("appointment_date")
            .first()
        )

        return Response(
            {
                "success": True,
                "message": _("Appointment requests retrieved successfully."),
                "data": {
                    "pending_count": pending_count,
                    "approved_count": approved_count,
                    "next_slot": (next_slot.appointment_date if next_slot else None),
                    "requests": (
                        AppointmentRequestSerializer(
                            requests,
                            many=True,
                        ).data
                    ),
                },
            }
        )


# ------------------------------------------------------------------


class ApproveAppointmentView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, appointment_id):

        doctor = getattr(
            request.user,
            "doctor",
            None,
        )

        if not doctor:

            return Response(
                {
                    "success": False,
                    "message": _("Doctor profile not found."),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:

            appointment = Appointment.objects.get(
                id=appointment_id,
                doctor=doctor,
            )

        except Appointment.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": _("Appointment not found."),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if appointment.status != "pending":

            return Response(
                {
                    "success": False,
                    "message": _("Only pending appointments can be approved."),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        appointment.status = "approved"

        appointment.save(update_fields=["status"])

        create_notification(
            patient=appointment.patient,
            title=_("Appointment Approved"),
            message=_("Your appointment has been approved."),
            notification_type="appointment",
        )

        return Response(
            {
                "success": True,
                "message": _("Appointment approved successfully."),
            },
            status=status.HTTP_200_OK,
        )


# ------------------------------------------------------------------


class RejectAppointmentView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, appointment_id):

        try:
            doctor = Doctor.objects.get(user=request.user)
        except Doctor.DoesNotExist:
            raise NotFound(_("Doctor profile not found."))

        try:

            appointment = Appointment.objects.get(
                id=appointment_id,
                doctor=doctor,
            )

        except Appointment.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": _("Appointment not found."),
                },
                status=404,
            )

        if appointment.status == "completed":

            return Response(
                {
                    "success": False,
                    "message": _("Completed appointments " "cannot be modified."),
                },
                status=400,
            )

        appointment.status = "rejected"

        appointment.save(update_fields=["status"])

        create_notification(
            patient=appointment.patient,
            title=_("Appointment Rejected"),
            message=_("Your appointment has been rejected."),
            notification_type="appointment",
        )

        return Response(
            {
                "success": True,
                "message": _("Appointment rejected successfully."),
            }
        )


# ------------------------------------------------------------------


class AppointmentReviewView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, appointment_id):

        try:
            doctor = Doctor.objects.get(user=request.user)
        except Doctor.DoesNotExist:
            raise NotFound(_("Doctor profile not found."))

        try:

            appointment = Appointment.objects.select_related("patient__user").get(
                id=appointment_id,
                doctor=doctor,
            )

        except Appointment.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": _("Appointment not found."),
                },
                status=404,
            )

        serializer = AppointmentReviewSerializer(appointment)
        analysis = appointment.ai_analyses.first()
        # 🟢 Last completed visit
        last_visit = (
            Appointment.objects.filter(
                patient=appointment.patient,
                status="completed",
            )
            .exclude(id=appointment.id)
            .order_by("-appointment_date")
            .first()
        )

        return Response(
            {
                "success": True,
                "message": _("Appointment review retrieved successfully."),
                "data": {
                    "appointment": serializer.data,
                    "last_visit": (last_visit.appointment_date if last_visit else None),
                    "ai_analysis": (
                        AIAnalysisSerializer(analysis).data if analysis else None
                    ),
                    "recent_activity": [
                        {
                            "type": "appointment",
                            "message": _("New appointment request."),
                        },
                        {
                            "type": "payment",
                            "message": _("Payment completed."),
                        },
                    ],
                },
            }
        )


# ------------------------------------------------------------------


class SaveDiagnosisView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, appointment_id):

        try:
            doctor = Doctor.objects.get(user=request.user)
        except Doctor.DoesNotExist:
            raise NotFound(_("Doctor profile not found."))

        try:

            appointment = Appointment.objects.get(
                id=appointment_id,
                doctor=doctor,
            )

        except Appointment.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": _("Appointment not found."),
                },
                status=404,
            )

        serializer = SaveDiagnosisSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        ai_analysis = AIAnalysis.objects.filter(appointment=appointment).first()

        # 🟢 Create medical record
        medical_record = MedicalRecord.objects.create(
            appointment=appointment,
            symptoms=(ai_analysis.symptoms if ai_analysis else None),
            ai_diagnosis=(ai_analysis.ai_diagnosis if ai_analysis else None),
            diagnosis=serializer.validated_data["diagnosis"],
            notes=serializer.validated_data["notes"],
        )

        # 🟢 Create prescriptions
        prescriptions = serializer.validated_data["prescriptions"]

        for item in prescriptions:

            Prescription.objects.create(
                medical_record=medical_record,
                medication_name=item["medication_name"],
                dosage=item["dosage"],
                duration=item["duration"],
            )

        # 🟢 Mark appointment as completed
        appointment.status = "completed"

        appointment.save(update_fields=["status"])

        return Response(
            {
                "success": True,
                "message": _("Diagnosis saved successfully."),
            }
        )


# ------------------------------------------------------------------


class DiagnosisDetailsView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, appointment_id):

        try:
            doctor = Doctor.objects.get(user=request.user)
        except Doctor.DoesNotExist:
            raise NotFound(_("Doctor profile not found."))

        try:

            medical_record = (
                MedicalRecord.objects.select_related("appointment")
                .prefetch_related("prescriptions")
                .get(
                    appointment__id=appointment_id,
                    appointment__doctor=doctor,
                )
            )

        except MedicalRecord.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": _("Diagnosis not found."),
                },
                status=404,
            )

        serializer = DiagnosisDetailsSerializer(medical_record)

        return Response(
            {
                "success": True,
                "message": _("Diagnosis details retrieved successfully."),
                "data": serializer.data,
            }
        )


# ------------------------------------------------------------------


class DoctorBillingView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        try:
            doctor = Doctor.objects.get(user=request.user)
        except Doctor.DoesNotExist:
            raise NotFound(_("Doctor profile not found."))

        payments = Payment.objects.filter(
            appointment__doctor=doctor,
            payment_status="paid",
        ).select_related(
            "appointment",
            "appointment__patient__user",
        )

        # 🟢 Filter by patient name
        patient_name = request.query_params.get("patient")

        if patient_name:

            payments = payments.filter(
                appointment__patient__user__username__icontains=patient_name
            )

        # 🟢 Filter by payment method
        payment_method = request.query_params.get("method")

        if payment_method:

            payments = payments.filter(payment_method=payment_method)

        # 🟢 Filter by date
        date = request.query_params.get("date")

        if date:

            payments = payments.filter(created_at__date=date)

        payments = payments.order_by("-created_at")

        # 🟢 Statistics
        total_earnings = payments.aggregate(total=Sum("amount"))["total"] or 0

        total_invoices = Invoice.objects.filter(appointment__doctor=doctor).count()

        monthly_earnings = (
            payments.filter(created_at__month=now().month).aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )

        serializer = BillingTransactionSerializer(
            payments,
            many=True,
        )

        return Response(
            {
                "success": True,
                "message": _("Billing data retrieved successfully."),
                "data": {
                    "total_earnings": total_earnings,
                    "monthly_earnings": monthly_earnings,
                    "total_invoices": total_invoices,
                    "transactions": serializer.data,
                },
            }
        )


# ------------------------------------------------------------------


class DoctorSettingsView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        try:
            doctor = Doctor.objects.get(user=request.user)
        except Doctor.DoesNotExist:
            raise NotFound(_("Doctor profile not found."))

        settings_obj, created = DoctorSettings.objects.get_or_create(doctor=doctor)

        serializer = DoctorSettingsSerializer(settings_obj)

        return Response(
            {
                "success": True,
                "message": _("Doctor settings retrieved successfully."),
                "data": serializer.data,
            },
            status=200,
        )

    def patch(self, request):

        try:
            doctor = Doctor.objects.get(user=request.user)
        except Doctor.DoesNotExist:
            raise NotFound(_("Doctor profile not found."))

        settings_obj, created = DoctorSettings.objects.get_or_create(doctor=doctor)

        serializer = DoctorSettingsSerializer(
            settings_obj,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(raise_exception=True)

        serializer.save()

        return Response(
            {
                "success": True,
                "message": _("Doctor settings updated successfully."),
                "data": serializer.data,
            },
            status=200,
        )


# ------------------------------------------------------------------


class EditDoctorProfileView(APIView):

    permission_classes = [IsAuthenticated]

    parser_classes = [
        MultiPartParser,
        FormParser,
    ]

    def patch(self, request):

        try:
            doctor = Doctor.objects.get(user=request.user)
        except Doctor.DoesNotExist:
            raise NotFound(_("Doctor profile not found."))

        serializer = DoctorPublicProfileSerializer(
            doctor,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(raise_exception=True)

        # 🟢 Update username
        username = request.data.get("username")

        if username:

            doctor.user.username = username

            doctor.user.save(update_fields=["username"])

        serializer.save()

        return Response(
            {
                "success": True,
                "message": _("Profile updated successfully."),
                "data": serializer.data,
            },
            status=200,
        )


# ------------------------------------------------------------------


class DoctorNotificationsView(ListAPIView):

    serializer_class = NotificationSerializer

    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        doctor = Doctor.objects.get(user=self.request.user)

        queryset = (
            Notification.objects.filter(doctor=doctor)
            .select_related(
                "patient__user",
                "doctor__user",
            )
            .order_by("-created_at")
        )

        filter_type = self.request.query_params.get("filter")

        # 🟢 unread
        if filter_type == "unread":

            queryset = queryset.filter(is_read=False)

        # 🟢 urgent
        elif filter_type == "urgent":

            queryset = queryset.filter(is_urgent=True)

        # 🟢 read
        elif filter_type == "read":

            queryset = queryset.filter(is_read=True)

        return queryset


# ------------------------------------------------------------------


class RescheduleAppointmentView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, appointment_id):

        try:
            doctor = Doctor.objects.get(user=request.user)
        except Doctor.DoesNotExist:
            raise NotFound(_("Doctor profile not found."))

        new_date = request.data.get("appointment_date")

        if not new_date:

            raise ValidationError(
                {"appointment_date": _("appointment_date is required.")}
            )

        try:

            appointment = Appointment.objects.get(
                id=appointment_id,
                doctor=doctor,
            )

        except Appointment.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": _("Appointment not found."),
                },
                status=404,
            )

        appointment.appointment_date = new_date

        appointment.status = "rescheduled"

        appointment.save(
            update_fields=[
                "appointment_date",
                "status",
            ]
        )

        appointment_date = datetime.fromisoformat(appointment.appointment_date) 
        
        create_notification(
            patient=appointment.patient,
            title=_("Appointment Rescheduled"),
            message=_(
                "Dr. %(doctor_name)s has rescheduled your appointment to %(appointment_date)s."
            )
            % {
                "doctor_name": doctor.user.username,
                "appointment_date": appointment_date.strftime(
                    "%Y-%m-%d %H:%M"
                ),
            },
            notification_type="appointment",
        )

        return Response(
            {
                "success": True,
                "message": _("Appointment rescheduled successfully."),
            }
        )


# ------------------------------------------------------------------


class PatientConsultationDetailsView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, patient_id):

        # 🟢 Doctor validation
        try:

            doctor = Doctor.objects.get(user=request.user)

        except Doctor.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": _("Doctor profile not found."),
                },
                status=404,
            )

        # 🟢 Patient validation
        try:

            patient = Patient.objects.get(id=patient_id)

        except Patient.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": _("Patient not found."),
                },
                status=404,
            )

        # 🟢 Medical conditions
        conditions = MedicalCondition.objects.filter(patient=patient)

        # 🟢 Latest vitals
        latest_vital = (
            Vital.objects.filter(patient=patient).order_by("-created_at").first()
        )

        return Response(
            {
                "success": True,
                "message": _("Consultation details retrieved successfully."),
                "data": {
                    "patient": {
                        "id": patient.id,
                        "name": patient.user.username,
                        "blood_type": patient.blood_type,
                        "height": patient.height,
                        "weight": patient.weight,
                    },
                    "conditions": [
                        {
                            "id": condition.id,
                            "name": condition.name,
                            "status": condition.status,
                            "diagnosed_date": (condition.diagnosed_date),
                        }
                        for condition in conditions
                    ],
                    "recent_vitals": {
                        "heart_rate": (
                            latest_vital.heart_rate if latest_vital else None
                        ),
                        "blood_pressure": (
                            latest_vital.blood_pressure if latest_vital else None
                        ),
                        "glucose": (latest_vital.glucose if latest_vital else None),
                        "created_at": (
                            latest_vital.created_at if latest_vital else None
                        ),
                    },
                },
            }
        )


# ------------------------------------------------------------------


class DoctorUpdatePatientHealthView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, patient_id):

        try:

            doctor = Doctor.objects.get(user=request.user)

        except Doctor.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": _("Doctor profile not found."),
                },
                status=404,
            )

        try:

            patient = Patient.objects.get(id=patient_id)

        except Patient.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": _("Patient not found."),
                },
                status=404,
            )

        # 🟢 Update patient info
        patient.blood_type = request.data.get(
            "blood_type",
            patient.blood_type,
        )

        patient.height = request.data.get(
            "height",
            patient.height,
        )

        patient.weight = request.data.get(
            "weight",
            patient.weight,
        )

        patient.save()

        # 🟢 Create new vital record
        Vital.objects.create(
            patient=patient,
            blood_pressure=request.data.get("blood_pressure"),
            heart_rate=request.data.get("heart_rate"),
            glucose=request.data.get("glucose"),
        )

        return Response(
            {
                "success": True,
                "message": _("Patient health updated successfully."),
            }
        )


# ------------------------------------------------------------------


class PrescriptionScreenView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, patient_id):

        # 🟢 Doctor validation
        try:

            doctor = Doctor.objects.get(user=request.user)

        except Doctor.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": _("Doctor profile not found."),
                },
                status=404,
            )

        # 🟢 Patient validation
        try:

            patient = Patient.objects.get(id=patient_id)

        except Patient.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": _("Patient not found."),
                },
                status=404,
            )

        # 🟢 Latest medical record
        medical_record = (
            MedicalRecord.objects.filter(appointment__patient=patient)
            .order_by("-created_at")
            .first()
        )

        # 🟢 Prescriptions
        prescriptions = []

        if medical_record:

            prescriptions = Prescription.objects.filter(medical_record=medical_record)

        return Response(
            {
                "success": True,
                "message": _("Prescription data retrieved successfully."),
                "data": {
                    "patient": {
                        "id": patient.id,
                        "name": patient.user.username,
                        "gender": patient.gender,
                        "age": (patient.age if hasattr(patient, "age") else None),
                    },
                    "prescriptions": [
                        {
                            "id": prescription.id,
                            "medication_name": (prescription.medication_name),
                            "dosage": prescription.dosage,
                            "frequency": (prescription.duration),
                            "route": "oral",
                        }
                        for prescription in prescriptions
                    ],
                    "doctor": {"name": doctor.user.username},
                },
            }
        )


# ------------------------------------------------------------------


class AddMedicationView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, patient_id):

        medication_name = request.data.get("medication_name")

        dosage = request.data.get("dosage")

        duration = request.data.get("duration")

        if not medication_name:

            return Response(
                {
                    "success": False,
                    "message": _("Medication name is required."),
                },
                status=400,
            )

        try:

            patient = Patient.objects.get(id=patient_id)

        except Patient.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": _("Patient not found."),
                },
                status=404,
            )

        # 🟢 Latest medical record
        medical_record = (
            MedicalRecord.objects.filter(appointment__patient=patient)
            .order_by("-created_at")
            .first()
        )

        if not medical_record:

            return Response(
                {
                    "success": False,
                    "message": _("No medical record found."),
                },
                status=404,
            )

        prescription = Prescription.objects.create(
            medical_record=medical_record,
            medication_name=medication_name,
            dosage=dosage,
            duration=duration,
        )

        return Response(
            {
                "success": True,
                "message": _("Medication added successfully."),
                "data": {
                    "prescription_id": prescription.id,
                },
            }
        )


# ------------------------------------------------------------------


class FinalizePrescriptionView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, patient_id):

        instructions = request.data.get("instructions")

        try:

            patient = Patient.objects.get(id=patient_id)

        except Patient.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": _("Patient not found."),
                },
                status=404,
            )

        medical_record = (
            MedicalRecord.objects.filter(appointment__patient=patient)
            .order_by("-created_at")
            .first()
        )

        if not medical_record:

            return Response(
                {
                    "success": False,
                    "message": _("Medical record not found."),
                },
                status=404,
            )

        medical_record.notes = instructions

        medical_record.save(update_fields=["notes"])

        return Response(
            {
                "success": True,
                "message": _("Prescription finalized successfully."),
            }
        )


# ------------------------------------------------------------------


class PatientMedicalRecordView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, patient_id):

        # 🟢 Doctor validation
        try:

            doctor = Doctor.objects.get(user=request.user)

        except Doctor.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": _("Doctor profile not found."),
                },
                status=404,
            )

        # 🟢 Patient validation
        try:

            patient = Patient.objects.get(id=patient_id)

        except Patient.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": _("Patient not found."),
                },
                status=404,
            )

        # 🟢 Clinical history
        medical_records = MedicalRecord.objects.filter(
            appointment__patient=patient
        ).order_by("-created_at")

        # 🟢 Diagnoses
        conditions = MedicalCondition.objects.filter(patient=patient)

        # 🟢 Medications
        prescriptions = Prescription.objects.filter(
            medical_record__appointment__patient=patient
        ).order_by("-id")

        return Response(
            {
                "success": True,
                "message": _("Patient medical record retrieved successfully."),
                "data": {
                    # 🟢 Patient profile
                    "patient": {
                        "id": patient.id,
                        "name": patient.user.username,
                        "blood_type": patient.blood_type,
                        "gender": patient.gender,
                        "height": patient.height,
                        "weight": patient.weight,
                    },
                    # 🟢 Clinical history
                    "clinical_history": [
                        {
                            "id": record.id,
                            "symptoms": record.symptoms,
                            "ai_diagnosis": record.ai_diagnosis,
                            "diagnosis": record.diagnosis,
                            "notes": record.notes,
                            "doctor": (record.appointment.doctor.user.username),
                            "created_at": record.created_at,
                        }
                        for record in medical_records
                    ],
                    # 🟢 Active diagnoses
                    "diagnoses": [
                        {
                            "id": condition.id,
                            "name": condition.name,
                            "status": condition.status,
                            "diagnosed_date": (condition.diagnosed_date),
                        }
                        for condition in conditions
                    ],
                    # 🟢 Active medications
                    "medications": [
                        {
                            "id": prescription.id,
                            "medication_name": (prescription.medication_name),
                            "dosage": prescription.dosage,
                            "duration": prescription.duration,
                        }
                        for prescription in prescriptions
                    ],
                },
            }
        )
