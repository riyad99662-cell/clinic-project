from django.urls import path
from .views import (
    RegisterView,
    LoginView,
    ChangePasswordView,
    AIAnalysisView,
    SendOTPView,
    VerifyOTPView,
    ForgotPasswordView,
    VerifyResetCodeView,
    ResetPasswordView,
    ProfileView,
    MedicalRecordsView,
    AvailableSlotsView,
    LogoutView,
    AppointmentDetailView,
    SecuritySettingsView,
    TrustedDevicesView,
    LogoutAllDevicesView,
    NotificationUnreadCountView,
    MarkNotificationReadView,
    DismissNotificationView,
    MarkAllNotificationsReadView,
    SaveDeviceTokenView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path(
        "login/", LoginView.as_view(), name="login"
    ),  # {"email": "test@test.com","password": "123456",
    # "device_name": "Samsung A55","device_type": "mobile","location": "London"}
    path("logout/", LogoutView.as_view()),
    path("change_password/", ChangePasswordView.as_view()),
    path("ai_analysis/", AIAnalysisView.as_view(), name="ai_analysis"),
    path("send_otp/", SendOTPView.as_view()),
    path("verify_otp/", VerifyOTPView.as_view()),
    path("forgot_password/", ForgotPasswordView.as_view()),
    path("verify_reset_code/", VerifyResetCodeView.as_view()),
    path("reset_password/", ResetPasswordView.as_view()),
    path("profile/", ProfileView.as_view()),
    path("records/", MedicalRecordsView.as_view()),
    path("available_slots/", AvailableSlotsView.as_view()),
    path("appointment/<int:id>/", AppointmentDetailView.as_view()),
    path("security_settings/", SecuritySettingsView.as_view()),  # GET / PATCH
    path("trusted_devices/", TrustedDevicesView.as_view()),  # GET
    path("logout_all_devices/", LogoutAllDevicesView.as_view()),  # POST
    path("notifications_count/", NotificationUnreadCountView.as_view()),  # GET
    path(
        "notifications/read/<int:notification_id>/",
        MarkNotificationReadView.as_view(),  # POST
    ),
    path(
        "notifications/dismiss/<int:notification_id>/",
        DismissNotificationView.as_view(),
    ),
    path(
        "notifications/read_all/",
        MarkAllNotificationsReadView.as_view(),
    ),
    path(
        "save_device_token/",
        SaveDeviceTokenView.as_view(),
    ),
]
