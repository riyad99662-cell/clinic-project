from django.urls import path
from .views import (
    AddPrescriptionView,
    UpdateAppointmentStatusView,
    DoctorAppointmentsView,
    DoctorDashboardView,
    DoctorPatientsListView,
    DoctorPatientDetailView,
    DoctorScheduleView,
    DoctorAlertsView,
    DoctorEarningsView,
    EditMedicalRecordView,
    UpdatePrescriptionView,
    DeletePrescriptionView,
    DoctorDailyScheduleView,
    AppointmentRequestsView,
    ApproveAppointmentView,
    RejectAppointmentView,
    AppointmentReviewView,
    SaveDiagnosisView,
    DiagnosisDetailsView,
    DoctorBillingView,
    DoctorSettingsView,
    EditDoctorProfileView,
    DoctorNotificationsView,
    RescheduleAppointmentView,
    PatientConsultationDetailsView,
    DoctorUpdatePatientHealthView,
    PrescriptionScreenView,
    AddMedicationView,
    FinalizePrescriptionView,
    PatientMedicalRecordView,
)

urlpatterns = [
    path("add_prescription/", AddPrescriptionView.as_view()),
    path(
        "update_appointment_status/<int:pk>/",
        UpdateAppointmentStatusView.as_view(),
        name="update_appointment_status",
    ),
    path(
        "doctor_appointments/",
        DoctorAppointmentsView.as_view(),
        name="doctor_appointments",
    ),
    path("dashboard/", DoctorDashboardView.as_view()),  # home screen
    path(
        "all_patients/", DoctorPatientsListView.as_view()
    ),  # home screen // view all patients
    # Get /api/doctor/all_patients/?search=mohsenhabeb
    path(
        "patient_details/<int:patient_id>/", DoctorPatientDetailView.as_view()
    ),  # home screen // View Details For Patients
    path("schedule/", DoctorScheduleView.as_view()),
    # GET /api/doctor/schedule/?filter=today
    # GET /api/doctor/schedule/?date=2026-05-10
    # GET /api/doctor/schedule/?filter=upcoming
    path("alerts/", DoctorAlertsView.as_view()),
    path("earnings/", DoctorEarningsView.as_view()),
    path(
        "edit_medical_record/<int:id>/", EditMedicalRecordView.as_view()
    ),  # GET / PATCH
    path("update_prescription/<int:id>/", UpdatePrescriptionView.as_view()),
    path("delete_prescription/<int:id>/", DeletePrescriptionView.as_view()),
    path(
        "daily_schedule/", DoctorDailyScheduleView.as_view()
    ),  # GET /api/doctor/daily_schedule/?date=2026-05-10  يوم معين
    # GET /api/doctor/daily_schedule/ اليوم الحالي
    path("appointment_requests/", AppointmentRequestsView.as_view()),  # GET
    path(
        "approve_appointment/<int:appointment_id>/", ApproveAppointmentView.as_view()
    ),  # POST
    path(
        "reject_appointment/<int:appointment_id>/", RejectAppointmentView.as_view()
    ),  # POST
    path(
        "appointment_review/<int:appointment_id>/", AppointmentReviewView.as_view()
    ),  # GET
    path(
        "appointments/<int:appointment_id>/save_diagnosis/", SaveDiagnosisView.as_view()
    ),  # POST {"diagnosis": "Acute Bronchitis","notes": "Patient reports coughing and fever","prescriptions": [{"medication_name": "Azithromycin","dosage": "500mg daily","duration": "3 days",},{"medication_name": "Paracetamol", "dosage": "500mg", "duration": "5 days"},],},
    path("view_diagnosis/<int:appointment_id>/", DiagnosisDetailsView.as_view()),  # GET
    path("billing/", DoctorBillingView.as_view()),  # GET
    # GET /api/doctor/billing/
    # GET /api/doctor/billing/?date=2026-05-06
    # GET /api/doctor/billing/?method=shamcash
    # GET /api/doctor/billing/?patient=ahmad
    # GET /api/doctor/billing/?patient=ahmad&method=cash
    path("settings/", DoctorSettingsView.as_view()),  # GET / PATCH
    path("edit_profile/", EditDoctorProfileView.as_view()),  # PATCH
    path("notifications/", DoctorNotificationsView.as_view()),  # GET
    # GET /api/doctor/notifications/
    # GET /api/doctor/notifications/?filter=urgent
    # GET /api/doctor/notifications/?filter=read
    path(
        "appointments/<int:appointment_id>/reschedule/",
        RescheduleAppointmentView.as_view(),
    ),  # POST
    path(
        "patient_consultation/<int:patient_id>/",
        PatientConsultationDetailsView.as_view(),
    ),  # GET
    path(
        "patient_consultation/<int:patient_id>/update/",
        DoctorUpdatePatientHealthView.as_view(),
    ),  # POST
    path(
        "prescription_screen/<int:patient_id>/", PrescriptionScreenView.as_view()
    ),  # GET
    path(
        "prescription_screen/<int:patient_id>/add_medication/",
        AddMedicationView.as_view(),  # POST
    ),
    path(
        "prescription_screen/<int:patient_id>/finalize/",
        FinalizePrescriptionView.as_view(),
    ),
    path(
        "patient_medical_record/<int:patient_id>/", PatientMedicalRecordView.as_view()
    ),  # GET
]
