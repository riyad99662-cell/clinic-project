from django.urls import path, include

from .views import AnalyzeSymptomsView, ClinicalInsightView

urlpatterns = [
    path(
        "analyze_symptoms/",
        AnalyzeSymptomsView.as_view(),  # POSt
    ),
    path(
        "clinical_insight/<appointment_id>/",
        ClinicalInsightView.as_view(),
    ),
    # api/ai/clinical_insight/<appointment_id>/
]
