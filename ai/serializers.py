from rest_framework import serializers

from users.models import AIAnalysis


class AIAnalysisSerializer(serializers.ModelSerializer):

    class Meta:

        model = AIAnalysis

        fields = [
            "id",
            "symptoms",
            "ai_response",
            "severity",
            "created_at",
        ]
