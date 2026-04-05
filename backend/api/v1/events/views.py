from ai import AIAnalysisService
from api.v1.events.serializers import (
    EventCreateSerializer,
    EventCriterionScoreConfirmSerializer,
    EventDetailSerializer,
    EventSerializer,
)
from core.exceptions.base import ProviderError
from core.filters import EventFilter
from core.pagination import StandardPagination
from core.throttling import AIRateThrottle
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.candidates.models import Candidate
from apps.events.models import Event, EventCriterionScore


class EventListView(APIView):
    """Список событий с фильтрацией и пагинацией."""

    pagination_class = StandardPagination

    def get(self, request: Request) -> Response:
        candidate_id = request.query_params.get("candidate")
        if not candidate_id:
            return Response(
                {"detail": "Параметр candidate обязателен."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        candidate = get_object_or_404(
            Candidate,
            pk=candidate_id,
            user=request.user,
        )

        events = Event.objects.filter(candidate=candidate)

        # Фильтрация
        filterset = EventFilter(request.GET, queryset=events)
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
        serializer = EventSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request: Request) -> Response:
        serializer = EventCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        candidate = serializer.validated_data["candidate"]
        if candidate.user != request.user:
            return Response(
                {"detail": "Кандидат не найден."},
                status=status.HTTP_404_NOT_FOUND,
            )

        event = serializer.save()

        try:
            AIAnalysisService.analyze(event)
        except ProviderError:
            return Response(
                {"detail": "Ошибка AI анализа. Попробуйте позже."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            EventDetailSerializer(event).data,
            status=status.HTTP_201_CREATED,
        )

    def get_throttles(self):
        if self.request.method == "POST":
            return [AIRateThrottle()]
        return super().get_throttles()


class EventDetailView(APIView):
    """Детали конкретного события."""

    def get_object(self, pk: int, user) -> Event:
        return get_object_or_404(
            Event,
            pk=pk,
            candidate__user=user,
        )

    def get(self, request: Request, pk: int) -> Response:
        event = self.get_object(pk, request.user)
        serializer = EventDetailSerializer(event)
        return Response(serializer.data)


class EventConfirmView(APIView):
    """Подтвердить или скорректировать оценку ИИ."""

    def patch(self, request: Request, pk: int) -> Response:
        event = get_object_or_404(
            Event,
            pk=pk,
            candidate__user=request.user,
        )

        criterion_id = request.data.get("criterion")
        if not criterion_id:
            return Response(
                {"detail": "Параметр criterion обязателен."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        score = get_object_or_404(
            EventCriterionScore,
            event=event,
            criterion_id=criterion_id,
        )

        serializer = EventCriterionScoreConfirmSerializer(
            score,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
