from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from api.v1.reports.serializers import (
    ReportGenerateSerializer,
    ReportLogSerializer,
)
from apps.candidates.models import Candidate
from apps.reports.models import ReportLog
from apps.reports.services.report import ReportService
from apps.reports.tasks import generate_report_task
from core.filters import ReportFilter
from core.pagination import SmallPagination


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
            if not candidate.events.exists():
                return Response(
                    {"detail": "У кандидата нет событий для отчёта."},
                    status=status.HTTP_400_BAD_REQUEST,
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
            import base64

            photo_bytes = None
            photo_b64 = request.data.get("photo_b64")
            if photo_b64:
                try:
                    photo_bytes = base64.b64decode(photo_b64)
                except Exception:
                    pass

            generate_report_task.delay(report.pk, photo_bytes=photo_bytes)
            return Response(
                ReportLogSerializer(report).data,
                status=status.HTTP_201_CREATED,
            )


class ReportDetailView(APIView):
    """Детали конкретного отчёта."""

    def get(self, request: Request, pk: int) -> Response:
        report = get_object_or_404(ReportLog, pk=pk, user=request.user)
        return Response(ReportLogSerializer(report).data)
