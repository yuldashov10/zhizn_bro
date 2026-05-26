from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from api.v1.assessments.serializers import (
    AttachmentTestDetailSerializer,
    AttachmentTestSerializer,
    UserAnswerSerializer,
    UserTestSessionSerializer,
)
from apps.assessments.models import AttachmentTest, UserAnswer, UserTestSession
from apps.users.models import UserProfile
from core.pagination import StandardPagination


class AttachmentTestListView(APIView):
    """Список доступных тестов привязанности."""

    pagination_class = StandardPagination

    def get(self, request: Request) -> Response:
        tests = AttachmentTest.objects.filter(is_active=True)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(tests, request)
        serializer = AttachmentTestSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class AttachmentTestDetailView(APIView):
    """Детали теста с вопросами."""

    def get(self, request: Request, pk: int) -> Response:
        test = get_object_or_404(AttachmentTest, pk=pk, is_active=True)
        serializer = AttachmentTestDetailSerializer(test)
        return Response(serializer.data)


class TestStartView(APIView):
    """Начать прохождение теста."""

    def post(self, request: Request, pk: int) -> Response:
        test = get_object_or_404(AttachmentTest, pk=pk, is_active=True)

        # Проверяем нет ли незавершённой сессии
        existing = UserTestSession.objects.filter(
            user=request.user,
            test=test,
            completed_at__isnull=True,
        ).first()

        if existing:
            serializer = UserTestSessionSerializer(existing)
            return Response(serializer.data, status=status.HTTP_200_OK)

        session = UserTestSession.objects.create(
            user=request.user,
            test=test,
        )
        serializer = UserTestSessionSerializer(session)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TestSessionDetailView(APIView):
    """Детали сессии теста."""

    def get(self, request: Request, pk: int) -> Response:
        session = get_object_or_404(
            UserTestSession,
            pk=pk,
            user=request.user,
        )
        serializer = UserTestSessionSerializer(session)
        return Response(serializer.data)


class TestSessionAnswerView(APIView):
    """Ответить на вопрос в сессии теста."""

    def post(self, request: Request, pk: int) -> Response:
        session = get_object_or_404(
            UserTestSession,
            pk=pk,
            user=request.user,
        )

        if session.is_completed():
            return Response(
                {"detail": "Сессия уже завершена."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = UserAnswerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        question = serializer.validated_data["question"]

        # Проверяем что вопрос принадлежит этому тесту
        if question.test != session.test:
            return Response(
                {"detail": "Вопрос не принадлежит этому тесту."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        UserAnswer.objects.update_or_create(
            session=session,
            question=question,
            defaults={"answer": serializer.validated_data["answer"]},
        )

        # Проверяем завершён ли тест
        answered = session.answers.count()
        total = session.test.questions_count

        if answered >= total:
            result = self._calculate_result(session)
            session.result_type = result
            session.completed_at = timezone.now()
            session.save(update_fields=["result_type", "completed_at"])

            # Обновляем профиль пользователя
            UserProfile.objects.filter(user=request.user).update(
                attachment_type=result,
                attachment_source=UserProfile.AttachmentSource.BOT_TEST,
                test_session=session,
            )

        return Response(
            UserTestSessionSerializer(session).data,
            status=status.HTTP_200_OK,
        )

    def _calculate_result(
        self,
        session: UserTestSession,
    ) -> str:
        """
        Рассчитывает тип привязанности на основе ответов.
        Усредняет баллы по измерениям anxiety и avoidance.
        """
        answers = session.answers.select_related("question").all()

        anxiety_scores = []
        avoidance_scores = []

        for answer in answers:
            if answer.question.dimension == "anxiety":
                anxiety_scores.append(answer.answer * answer.question.weight)
            else:
                avoidance_scores.append(answer.answer * answer.question.weight)

        avg_anxiety = (
            sum(anxiety_scores) / len(anxiety_scores) if anxiety_scores else 0
        )
        avg_avoidance = (
            sum(avoidance_scores) / len(avoidance_scores)
            if avoidance_scores
            else 0
        )

        if avg_anxiety <= 3 and avg_avoidance <= 3:
            return UserTestSession.AttachmentResult.SECURE
        elif avg_anxiety > 3 and avg_avoidance <= 3:
            return UserTestSession.AttachmentResult.ANXIOUS
        elif avg_anxiety <= 3 and avg_avoidance > 3:
            return UserTestSession.AttachmentResult.AVOIDANT
        else:
            return UserTestSession.AttachmentResult.DISORGANIZED


class TestSessionResultView(APIView):
    """Результат завершённой сессии теста."""

    def get(self, request: Request, pk: int) -> Response:
        session = get_object_or_404(
            UserTestSession,
            pk=pk,
            user=request.user,
        )
        if not session.is_completed():
            return Response(
                {"detail": "Тест ещё не завершён."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = UserTestSessionSerializer(session)
        return Response(serializer.data)
