from api.v1.reports.serializers import (
    ReportGenerateSerializer,
    ReportLogSerializer,
)
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.candidates.models import Candidate
from apps.reports.models import ReportLog


class ReportListView(APIView):
    """История отчётов текущего пользователя."""

    def get(self, request: Request) -> Response:
        reports = ReportLog.objects.filter(user=request.user)
        serializer = ReportLogSerializer(reports, many=True)
        return Response(serializer.data)


class ReportGenerateView(APIView):
    """Сгенерировать отчёт."""

    def post(self, request: Request) -> Response:
        serializer = ReportGenerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        candidate = None
        candidate_id = serializer.validated_data.get("candidate_id")

        if candidate_id:
            candidate = get_object_or_404(
                Candidate,
                pk=candidate_id,
                user=request.user,
            )

        report = ReportLog.objects.create(
            user=request.user,
            candidate=candidate,
            report_type=serializer.validated_data["report_type"],
            trigger=ReportLog.Trigger.MANUAL,
        )

        # TODO: запустить генерацию файла (реализуем в feature/reports)
        # ReportService.generate(report)

        return Response(
            ReportLogSerializer(report).data,
            status=status.HTTP_201_CREATED,
        )
