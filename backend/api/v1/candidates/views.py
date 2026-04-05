from api.v1.candidates.serializers import (
    CandidateDetailSerializer,
    CandidateScoreSerializer,
    CandidateSerializer,
    CandidateStatusHistorySerializer,
    CandidateStatusUpdateSerializer,
)
from core.filters import CandidateFilter
from core.pagination import StandardPagination
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.filters import OrderingFilter
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.candidates.models import Candidate, CandidateStatusHistory
from apps.events.models import Event
from apps.events.services import ScoringService


class CandidateListView(APIView):
    """Список кандидатов текущего пользователя."""

    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = CandidateFilter
    ordering_fields = ["created_at", "name", "age"]
    ordering = ["-created_at"]

    def get(self, request: Request) -> Response:
        candidates = Candidate.objects.filter(user=request.user)

        # Фильтрация
        filterset = CandidateFilter(request.GET, queryset=candidates)
        if not filterset.is_valid():
            return Response(
                filterset.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Сортировка
        ordering = request.query_params.get("ordering", "-created_at")
        queryset = filterset.qs.order_by(ordering)

        # Пагинация
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        serializer = CandidateSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request: Request) -> Response:
        serializer = CandidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CandidateDetailView(APIView):
    """Детали конкретного кандидата."""

    def get_object(self, pk: int, user) -> Candidate:
        return get_object_or_404(Candidate, pk=pk, user=user)

    def get(self, request: Request, pk: int) -> Response:
        candidate = self.get_object(pk, request.user)
        serializer = CandidateDetailSerializer(candidate)
        return Response(serializer.data)

    def patch(self, request: Request, pk: int) -> Response:
        candidate = self.get_object(pk, request.user)
        serializer = CandidateSerializer(
            candidate,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class CandidateArchiveView(APIView):
    """Архивировать кандидата."""

    def post(self, request: Request, pk: int) -> Response:
        candidate = get_object_or_404(Candidate, pk=pk, user=request.user)

        if not candidate.is_active:
            return Response(
                {"detail": "Кандидат уже в архиве."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        candidate.archive()
        return Response(
            {"detail": "Кандидат перемещён в архив."},
            status=status.HTTP_200_OK,
        )


class CandidateScoreView(APIView):
    """Итоговый скор кандидата."""

    def get(self, request: Request, pk: int) -> Response:
        candidate = get_object_or_404(Candidate, pk=pk, user=request.user)
        score = ScoringService.calculate(candidate)
        events_count = Event.objects.filter(candidate=candidate).count()

        serializer = CandidateScoreSerializer(
            {
                "candidate_id": candidate.pk,
                "candidate_name": candidate.name,
                "score": score,
                "events_count": events_count,
            }
        )
        return Response(serializer.data)


class CandidateStatusHistoryView(APIView):
    """История статусов кандидата."""

    def get(self, request: Request, pk: int) -> Response:
        candidate = get_object_or_404(Candidate, pk=pk, user=request.user)
        history = candidate.status_history.all()
        serializer = CandidateStatusHistorySerializer(history, many=True)
        return Response(serializer.data)


class CandidateStatusUpdateView(APIView):
    """Сменить статус кандидата."""

    def post(self, request: Request, pk: int) -> Response:
        candidate = get_object_or_404(Candidate, pk=pk, user=request.user)
        serializer = CandidateStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        CandidateStatusHistory.objects.create(
            candidate=candidate,
            status=serializer.validated_data["status"],
            note=serializer.validated_data.get("note", ""),
        )

        return Response(
            {"detail": "Статус обновлён."},
            status=status.HTTP_201_CREATED,
        )
