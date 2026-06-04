from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from users.ai_service import analyze_symptoms, generate_clinical_insight
from rest_framework.response import Response
from rest_framework import status
from django.utils.translation import gettext_lazy as _

from users.models import (
    AIAnalysis,
    Appointment,
    ClinicalInsight,
    Doctor,
    MedicalRecord,
    Patient,
    Vital,
)


class AnalyzeSymptomsView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        symptoms = request.data.get("symptoms")

        if not symptoms:

            return Response(
                {
                    "success": False,
                    "message": _("Symptoms are required."),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            patient = Patient.objects.get(user=request.user)

        except Patient.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": _("Patient profile not found."),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # AI
        ai_analysis = analyze_symptoms(symptoms)

        if not ai_analysis:

            return Response(
                {
                    "success": False,
                    "message": _("AI analysis failed."),
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # save
        analysis = AIAnalysis.objects.create(
            patient=patient,
            symptoms=symptoms,
            ai_response=ai_analysis,
            severity=ai_analysis.get("severity"),
        )

        return Response(
            {
                "success": True,
                "analysis_id": analysis.id,
                "symptoms": symptoms,
                "ai_analysis": ai_analysis,
            },
            status=status.HTTP_200_OK,
        )


###


class ClinicalInsightView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, appointment_id):

        try:
            doctor = Doctor.objects.get(user=request.user)

        except Doctor.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": _("Doctor profile not found."),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

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
                status=status.HTTP_404_NOT_FOUND,
            )

        # existing insight
        existing_insight = appointment.clinical_insights.first()

        if existing_insight:

            return Response(
                {
                    "success": True,
                    "cached": True,
                    "data": existing_insight.ai_response,
                }
            )

        patient = appointment.patient

        # vitals
        latest_vital = (
            Vital.objects.filter(patient=patient).order_by("-created_at").first()
        )

        # medical records
        records = MedicalRecord.objects.filter(appointment__patient=patient).order_by(
            "-created_at"
        )[:5]

        # ai analysis
        ai_analysis = appointment.ai_analyses.first()

        # build context
        context_data = {
            "patient": {
                "name": patient.user.username,
                "gender": patient.gender,
                "blood_type": patient.blood_type,
                "height": patient.height,
                "weight": patient.weight,
            },
            "symptoms": (ai_analysis.symptoms if ai_analysis else ""),
            "pre_analysis": (ai_analysis.ai_response if ai_analysis else {}),
            "vitals": {
                "blood_pressure": (
                    latest_vital.blood_pressure if latest_vital else None
                ),
                "heart_rate": (latest_vital.heart_rate if latest_vital else None),
                "glucose": (latest_vital.glucose if latest_vital else None),
            },
            "medical_history": [
                {
                    "diagnosis": record.diagnosis,
                    "notes": record.notes,
                }
                for record in records
            ],
        }

        # AI
        ai_result = generate_clinical_insight(context_data)

        # save
        insight = ClinicalInsight.objects.create(
            appointment=appointment,
            ai_response=ai_result,
            risk_score=ai_result.get("risk_score"),
        )

        return Response(
            {
                "success": True,
                "cached": False,
                "data": insight.ai_response,
            }
        )
