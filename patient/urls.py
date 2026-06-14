from django.urls import path
from .views import (
    CreateAppointmentView,
    HasMedicalRecordView,
    MyAppointmentsView,
    MyInvoicesView,
    MedicalRecordDetailView,
    NextAppointmentView,
    UpdateAppointmentView,
    CreatePaymentView,
    CancelAppointmentView,
    PatientProfileView,
    PatientMedicalRecordsListView,
    CreateVitalView,
    LatestVitalView,
    PatientConditionsView,
    CreateConditionView,
    PatientVitalsHistoryView,
    PatientAllergiesView,
    CreateAllergyView,
    DeleteAllergyView,
    PatientMedicationsView,
    CreateMedicationView,
    UpdateMedicationView,
    DeleteMedicationView,
    UploadScanView,
    ConfirmScanView,
    ExtractScanView,
    PatientPaymentListView,
    PatientPaymentSummaryView,
    UpdateHealthRecordsView,
    ClinicLocationView,
    PatientNotificationsView,
)

urlpatterns = [
    path(
        "create_appointment/",
        CreateAppointmentView.as_view(),
        name="create_appointment",
    ),
    path("my_appointments/", MyAppointmentsView.as_view(), name="my_appointments"),
    path("my_invoices/", MyInvoicesView.as_view()),
    path("medical_record/<int:appointment_id>/", MedicalRecordDetailView.as_view()),
    path("next_appointment/", NextAppointmentView.as_view()),
    path("update_appointment/<int:id>/", UpdateAppointmentView.as_view()),
    path("create_payment/", CreatePaymentView.as_view()),
    path("cancel_appointment/", CancelAppointmentView.as_view()),
    path("patient_profile/", PatientProfileView.as_view()),
    path("medical_records/", PatientMedicalRecordsListView.as_view()),
    path(
        "vitals/", CreateVitalView.as_view()
    ),  # Post {"blood_pressure": "120/80","heart_rate": 72,"glucose": 145}
    path(
        "latest_vitals/", LatestVitalView.as_view()
    ),  # Get {"id": 1,"blood_pressure": "120/80","heart_rate": 72,"glucose": 145,"created_at": "2026-04-27T18:00:00Z"}
    path(
        "conditions/", PatientConditionsView.as_view()
    ),  # [{"id": 1,"condition_name": "Hypertension","condition_status": "high_risk","diagnosed_at": "2022-10-01","notes": "Patient needs monitoring"}]
    path(
        "create_conditions/", CreateConditionView.as_view()
    ),  # Post {"condition_name": "Hypertension","condition_status": "high_risk","diagnosed_at": "2022-10-01","notes": "Patient needs monitoring"}
    path("vitals_history/", PatientVitalsHistoryView.as_view()),
    # Response [{"id": 1,"blood_pressure": "120/80","heart_rate": 72,"glucose": 140,"created_at": "2026-04-20T10:00:00",},
    # {"id": 2,"blood_pressure": "130/85","heart_rate": 75,"glucose": 150,"created_at": "2026-04-21T10:00:00",},],
    path("allergies/", PatientAllergiesView.as_view()),
    path(
        "create_allergies/", CreateAllergyView.as_view()
    ),  # {"allergy_name": "Penicillin","severity": "critical"}
    path("allergies/<int:pk>/", DeleteAllergyView.as_view()),
    path("medications/", PatientMedicationsView.as_view()),
    path("create_medications/", CreateMedicationView.as_view()),
    path("update_medications/<int:pk>/", UpdateMedicationView.as_view()),
    path("delete_medications/<int:pk>/", DeleteMedicationView.as_view()),
    path("scan/upload/", UploadScanView.as_view()),  # Post
    path("scan/extract/", ExtractScanView.as_view()),  # Post -> Body{"scan_id":1}
    path(
        "scan/confirm/", ConfirmScanView.as_view()
    ),  # Post -> Body{"scan_id": 1,"medications": [{"drug_name": "Lisinopril","dosage": "10mg","frequency": "once_daily"}]}]
    path("payments/", PatientPaymentListView.as_view()),
    path("payment_summary/", PatientPaymentSummaryView.as_view()),
    path("update_health_records/", UpdateHealthRecordsView.as_view()),
    path("location/", ClinicLocationView.as_view()),
    path(
        "notifications/",
        PatientNotificationsView.as_view(),
    ),
    path(
        "has_medical_record/",
        HasMedicalRecordView.as_view(),
        name="has_medical_record",
    ),
]
