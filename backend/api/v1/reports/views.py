from api.v1.reports.serializers import (
    ReportGenerateSerializer,
    ReportLogSerializer,
)
from core.filters import ReportFilter
from core.pagination import SmallPagination
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.candidates.models import Candidate
from apps.reports.models import ReportLog
from apps.reports.services.report import ReportService
from apps.reports.tasks import generate_report_task


class ReportListView(APIView):
    """История отчётов с фильтрацией и пагинацией."""

    pagination_class = SmallPagination

    def get(self, request: Request) -> Response:
        reports = ReportLog.objects.filter(user=request.user)

        filterset = ReportFilter(request.GET, queryset=reports)
        if not filterset.is_valid():
            return Response(
                filterset.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(filterset.qs, request)
        serializer = ReportLogSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class ReportGenerateView(APIView):
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

        report_type = serializer.validated_data["report_type"]
        report = ReportLog.objects.create(
            user=request.user,
            candidate=candidate,
            report_type=report_type,
            trigger=ReportLog.Trigger.MANUAL,
        )

        if report_type == ReportLog.ReportType.TEXT:
            # Текстовый отчёт генерируем сразу
            text = ReportService.generate_text_report(candidate)
            return Response(
                {
                    "report": ReportLogSerializer(report).data,
                    "text": text,
                },
                status=status.HTTP_201_CREATED,
            )
        else:
            # Файловые отчёты — через Celery
            generate_report_task.delay(report.pk)
            return Response(
                ReportLogSerializer(report).data,
                status=status.HTTP_201_CREATED,
            )


class ReportDetailView(APIView):
    """Детали конкретного отчёта."""

    def get(self, request: Request, pk: int) -> Response:
        report = get_object_or_404(ReportLog, pk=pk, user=request.user)
        return Response(ReportLogSerializer(report).data)
