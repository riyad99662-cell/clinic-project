from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid


class User(AbstractUser):

    ROLE_CHOICES = (
        ("doctor", "Doctor"),
        ("patient", "Patient"),
    )

    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    email = models.EmailField(unique=True)
    is_verified = models.BooleanField(default=False)
    verification_code = models.CharField(max_length=6, null=True, blank=True)

    def __str__(self):
        return self.username


###########################################################################################


class Patient(models.Model):

    GENDER_CHOICES = (("male", "Male"), ("female", "Female"))

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    phone = models.CharField(max_length=20)

    address = models.CharField(max_length=255, null=True, blank=True)

    birth_date = models.DateField(null=True, blank=True)

    gender = models.CharField(
        max_length=10, choices=GENDER_CHOICES, null=True, blank=True
    )

    # إضافات جديدة

    medical_id = models.CharField(max_length=50, unique=True, null=True, blank=True)

    blood_type = models.CharField(max_length=5, null=True, blank=True)

    height = models.IntegerField(null=True, blank=True)  # cm

    weight = models.IntegerField(null=True, blank=True)  # kg

    profile_image = models.ImageField(upload_to="profiles/", null=True, blank=True)

    def __str__(self):
        return self.user.username


###


class Doctor(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    specialization = models.CharField(max_length=100)

    clinic_name = models.CharField(max_length=200)

    bio = models.TextField(blank=True, null=True)

    clinic_address = models.CharField(max_length=255, blank=True, null=True)

    image = models.ImageField(upload_to="doctors/", blank=True, null=True)

    def __str__(self):
        return f"Doctor: {self.user.username}"


###


class Appointment(models.Model):

    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("completed", "Completed"),
    )
    PRIORITY_CHOICES = (
        ("routine", "Routine"),
        ("urgent", "Urgent"),
    )

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)

    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)

    appointment_date = models.DateTimeField()

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    patient_symptoms = models.TextField()

    consultation_type = models.CharField(max_length=20, default="in_clinic")

    session_duration = models.IntegerField(null=True, blank=True)

    notes = models.TextField(blank=True, null=True)

    priority = models.CharField(
        max_length=20, choices=PRIORITY_CHOICES, default="routine"
    )

    price = models.DecimalField(max_digits=10, decimal_places=2, default=75000)

    def __str__(self):
        return f"{self.patient.user.username} with {self.doctor.user.username}"


###


class MedicalRecord(models.Model):

    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE,
    )

    symptoms = models.TextField(
        blank=True,
        null=True,
    )

    ai_diagnosis = models.TextField(
        blank=True,
        null=True,
    )

    diagnosis = models.TextField(
        blank=True,
        null=True,
    )
    notes = models.TextField(blank=True, null=True)

    heart_rate = models.IntegerField(null=True, blank=True)
    temperature = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)


###


class Prescription(models.Model):

    medical_record = models.ForeignKey(
        MedicalRecord, on_delete=models.CASCADE, related_name="prescriptions"
    )

    medication_name = models.CharField(max_length=255)
    dosage = models.CharField(max_length=255)
    duration = models.CharField(max_length=255, null=True, blank=True)
    frequency = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        choices=[
            ("once_daily", "Once Daily"),
            ("twice_daily", "Twice Daily"),
            ("three_times", "3 Times Daily"),
            ("as_needed", "As Needed"),
        ],
    )

    def __str__(self):
        return f"{self.medication_name} for {self.medical_record}"


###


class Payment(models.Model):

    METHOD_CHOICES = (
        ("cash", "Cash"),
        ("shamcash", "ShamCash"),
    )

    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    )

    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE)

    amount = models.DecimalField(max_digits=10, decimal_places=2)

    transaction_reference = models.CharField(
        max_length=100, unique=True, blank=True, null=True
    )

    payment_method = models.CharField(max_length=20, choices=METHOD_CHOICES)

    payment_status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):

        if not self.transaction_reference:

            self.transaction_reference = f"TRX-{uuid.uuid4().hex[:8].upper()}"

        super().save(*args, **kwargs)

    def str(self):
        return (
            f"Payment for {self.appointment} - "
            f"{self.transaction_reference} - "
            f"{self.payment_status}"
        )


###


class AIAnalysis(models.Model):

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="ai_analyses",
    )

    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ai_analyses",
    )

    symptoms = models.TextField()

    ai_response = models.JSONField(
        default=dict,
        blank=True,
    )

    severity = models.CharField(
        max_length=20,
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):

        return f"AI Analysis #{self.id}"


###


class DeviceToken(models.Model):

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="device_tokens"
    )

    token = models.TextField(max_length=255, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Token for {self.user.username}"


###


class Invoice(models.Model):

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    ]

    payment = models.OneToOneField(
        Payment, on_delete=models.CASCADE, related_name="invoice"
    )
    patient = models.ForeignKey("Patient", on_delete=models.CASCADE)
    appointment = models.ForeignKey(
        "Appointment", on_delete=models.SET_NULL, null=True, blank=True
    )

    amount = models.DecimalField(max_digits=10, decimal_places=2)

    payment_method = models.CharField(max_length=50, blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    reference = models.CharField(max_length=100, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.reference} - {self.status}"


###


class Vital(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)

    blood_pressure = models.CharField(max_length=20)  # "120/80"
    heart_rate = models.IntegerField()
    glucose = models.FloatField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient} - {self.created_at}"


###


class MedicalCondition(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)

    condition_name = models.CharField(max_length=100)

    condition_status = models.CharField(
        max_length=20,
        choices=[
            ("high_risk", "High Risk"),
            ("managed", "Managed"),
            ("stable", "Stable"),
        ],
    )

    diagnosed_at = models.DateField()

    notes = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.condition_name} - {self.patient}"


###


class Allergy(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)

    allergy_name = models.CharField(max_length=100)

    severity = models.CharField(
        max_length=20,
        choices=[
            ("mild", "Mild"),
            ("moderate", "Moderate"),
            ("critical", "Critical"),
        ],
        default="critical",
    )

    notes = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.allergy_name} - {self.patient}"


###


class Medication(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)

    drug_name = models.CharField(max_length=100)

    dosage = models.CharField(max_length=50)  # 500mg
    frequency = models.CharField(
        max_length=50,
        choices=[
            ("once_daily", "Once Daily"),
            ("twice_daily", "Twice Daily"),
            ("three_times", "3 Times Daily"),
        ],
    )

    notes = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.drug_name} - {self.patient}"


###


class Scan(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)

    image = models.ImageField(upload_to="scans/")

    extracted_data = models.JSONField(null=True, blank=True)

    is_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Scan {self.id} - {self.patient}"


###


class DoctorSettings(models.Model):

    doctor = models.OneToOneField(Doctor, on_delete=models.CASCADE)

    # clinic
    clinic_start_time = models.TimeField(default="08:00")

    clinic_end_time = models.TimeField(default="17:00")

    appointment_buffer = models.IntegerField(default=15)

    # notifications
    new_appointment_alerts = models.BooleanField(default=True)

    emergency_alerts = models.BooleanField(default=True)

    lab_result_alerts = models.BooleanField(default=False)

    # security
    biometric_enabled = models.BooleanField(default=False)

    def __str__(self):
        return f"Settings - {self.doctor.user.username}"


###


class SecuritySettings(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # 🟢 privacy
    data_sharing = models.BooleanField(default=False)

    profile_visibility = models.BooleanField(default=True)

    # 🟢 authentication
    two_factor_enabled = models.BooleanField(default=False)

    biometric_enabled = models.BooleanField(default=False)

    # 🟢 preferences
    language = models.CharField(max_length=20, default="english")

    def __str__(self):
        return f"Security Settings - {self.user.username}"


###


class TrustedDevice(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    device_name = models.CharField(max_length=100)

    device_type = models.CharField(max_length=50, blank=True, null=True)

    location = models.CharField(max_length=100, blank=True, null=True)

    last_seen = models.DateTimeField(auto_now=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.device_name}"


###


class Notification(models.Model):

    TYPE_CHOICES = (
        ("appointment", "Appointment"),
        ("payment", "Payment"),
        ("prescription", "Prescription"),
        ("lab", "Lab"),
        ("emergency", "Emergency"),
        ("entry", "Clinic Entry"),
    )

    doctor = models.ForeignKey(
        "Doctor",
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True,
    )

    patient = models.ForeignKey(
        "Patient",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    notification_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
    )

    title = models.CharField(max_length=255)

    message = models.TextField()

    is_read = models.BooleanField(default=False)

    is_urgent = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:

        ordering = ["-created_at"]

    def __str__(self):

        return self.title


######


class Clinic(models.Model):

    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    address = models.TextField()

    latitude = models.DecimalField(max_digits=9, decimal_places=6)

    longitude = models.DecimalField(max_digits=9, decimal_places=6)

    phone_number = models.CharField(max_length=20, blank=True, null=True)
    opening_time = models.TimeField(blank=True, null=True)
    closing_time = models.TimeField(blank=True, null=True)

    def __str__(self):
        return self.name


###


class ClinicalInsight(models.Model):

    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.CASCADE,
        related_name="clinical_insights",
    )

    ai_response = models.JSONField(
        default=dict,
        blank=True,
    )

    risk_score = models.IntegerField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):

        return f"Clinical Insight #{self.id}"
