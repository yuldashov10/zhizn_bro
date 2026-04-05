from api.v1.criteria.serializers import CriterionSerializer, HardStopSerializer
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.criteria.models import Criterion, HardStop


class HardStopListView(APIView):
    """Список Hard Stops — системных и пользовательских."""

    def get(self, request: Request) -> Response:
        hard_stops = HardStop.objects.filter(
            Q(is_default=True) | Q(user=request.user),
            is_active=True,
        )
        serializer = HardStopSerializer(hard_stops, many=True)
        return Response(serializer.data)

    def post(self, request: Request) -> Response:
        serializer = HardStopSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user, is_default=False)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class HardStopDetailView(APIView):
    """Детали и управление конкретным Hard Stop."""

    def get_object(self, pk: int, user) -> HardStop:
        from django.db.models import Q

        return get_object_or_404(
            HardStop,
            Q(is_default=True) | Q(user=user),
            pk=pk,
        )

    def patch(self, request: Request, pk: int) -> Response:
        hard_stop = self.get_object(pk, request.user)
        serializer = HardStopSerializer(
            hard_stop,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request: Request, pk: int) -> Response:
        hard_stop = self.get_object(pk, request.user)
        if hard_stop.is_default:
            return Response(
                {"detail": "Системный Hard Stop нельзя удалить."},
                status=status.HTTP_403_FORBIDDEN,
            )
        hard_stop.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CriterionListView(APIView):
    """Список критериев — системных и пользовательских."""

    def get(self, request: Request) -> Response:
        criteria = Criterion.objects.filter(
            Q(is_default=True) | Q(user=request.user),
            is_active=True,
        )
        serializer = CriterionSerializer(criteria, many=True)
        return Response(serializer.data)

    def post(self, request: Request) -> Response:
        serializer = CriterionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user, is_default=False)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CriterionDetailView(APIView):
    """Детали и управление конкретным критерием."""

    def get_object(self, pk: int, user) -> Criterion:
        from django.db.models import Q

        return get_object_or_404(
            Criterion,
            Q(is_default=True) | Q(user=user),
            pk=pk,
        )

    def patch(self, request: Request, pk: int) -> Response:
        criterion = self.get_object(pk, request.user)
        serializer = CriterionSerializer(
            criterion,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request: Request, pk: int) -> Response:
        criterion = self.get_object(pk, request.user)
        if criterion.is_default:
            return Response(
                {"detail": "Системный критерий нельзя удалить."},
                status=status.HTTP_403_FORBIDDEN,
            )
        criterion.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
