from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from api.v1.criteria.serializers import (
    CriterionSerializer,
    HardStopSerializer,
    HardStopSuggestionSerializer,
)
from apps.criteria.models import Criterion, HardStop, UserCriterionSettings
from apps.criteria.services import CriteriaWeightService


class HardStopListView(APIView):
    """Список Hard Stops — системных и пользовательских."""

    def get(self, request: Request) -> Response:
        hard_stops = HardStop.objects.filter(is_default=True)
        serializer = HardStopSerializer(hard_stops, many=True)
        return Response(serializer.data)


class HardStopDetailView(APIView):
    """Детали и управление конкретным Hard Stop."""

    def get(self, request: Request, pk: int) -> Response:
        hard_stop = get_object_or_404(HardStop, pk=pk, is_default=True)
        return Response(HardStopSerializer(hard_stop).data)


class HardStopToggleView(APIView):
    """Включить / выключить Hard Stop для пользователя."""

    def post(self, request: Request, pk: int) -> Response:
        hard_stop = get_object_or_404(HardStop, pk=pk, is_default=True)

        from apps.criteria.models import UserHardStopSettings

        settings, created = UserHardStopSettings.objects.get_or_create(
            user=request.user,
            hard_stop=hard_stop,
            defaults={"is_active": True},
        )

        if not created:
            settings.is_active = not settings.is_active
            settings.save(update_fields=["is_active"])

        return Response(
            {
                "id": hard_stop.pk,
                "name": hard_stop.name,
                "is_active": settings.is_active,
            }
        )


class HardStopSuggestView(APIView):
    """Предложить новый Hard Stop."""

    def post(self, request: Request) -> Response:
        serializer = HardStopSuggestionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CriterionListView(APIView):
    """Список системных критериев с эффективными весами."""

    def get(self, request: Request) -> Response:
        criteria = Criterion.objects.filter(is_default=True)
        serializer = CriterionSerializer(
            criteria,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data)


class CriterionDetailView(APIView):
    """Детали критерия."""

    def get(self, request: Request, pk: int) -> Response:
        criterion = get_object_or_404(Criterion, pk=pk, is_default=True)
        return Response(
            CriterionSerializer(
                criterion,
                context={"request": request},
            ).data
        )


class CriterionToggleView(APIView):
    """Включить / выключить критерий для пользователя."""

    def post(self, request: Request, pk: int) -> Response:
        criterion = get_object_or_404(Criterion, pk=pk, is_default=True)

        from apps.criteria.models import UserCriterionSettings

        settings, created = UserCriterionSettings.objects.get_or_create(
            user=request.user,
            criterion=criterion,
            defaults={"is_active": True},
        )

        if not created:
            # Проверяем можно ли отключить
            if settings.is_active:
                active_criteria = self._get_active_criteria(request.user)
                if not CriteriaWeightService.can_disable(active_criteria):
                    return Response(
                        {
                            "detail": f"Нельзя отключить — минимум "
                            f"{CriteriaWeightService.MIN_CRITERIA} критерия."
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            settings.is_active = not settings.is_active
            settings.save(update_fields=["is_active"])

        active_criteria = self._get_active_criteria(request.user)
        try:
            weights = CriteriaWeightService.get_effective_weights(
                active_criteria
            )
        except ValueError:
            weights = {}

        return Response(
            {
                "id": criterion.pk,
                "name": criterion.name,
                "is_active": settings.is_active,
                "effective_weight": (
                    f"{weights.get(criterion.name, 0) * 100:.1f}%"
                ),
            }
        )

    def _get_active_criteria(self, user) -> list:

        all_criteria = list(Criterion.objects.filter(is_default=True))
        user_settings = {
            s.criterion_id: s.is_active
            for s in UserCriterionSettings.objects.filter(user=user)
        }
        return [c for c in all_criteria if user_settings.get(c.pk, True)]
