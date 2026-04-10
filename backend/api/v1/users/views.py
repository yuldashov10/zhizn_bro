from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from api.v1.users.serializers import (
    TelegramAuthSerializer,
    UserSerializer,
    UserTokenLimitSerializer,
    UserUpdateSerializer,
)
from apps.users.models import User, UserProfile, UserTokenLimit


class TelegramAuthView(APIView):
    """
    Аутентификация через Telegram.
    Создаёт пользователя если не существует, возвращает токен.
    """

    permission_classes = [AllowAny]
    throttle_classes = []

    def post(self, request: Request) -> Response:
        serializer = TelegramAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        telegram_id = serializer.validated_data["telegram_id"]
        username = serializer.validated_data.get("username")

        user, created = User.objects.get_or_create(
            telegram_id=telegram_id,
            defaults={"username": username},
        )

        if not created and username and user.username != username:
            user.username = username
            user.save(update_fields=["username"])

        # Создаём связанные объекты если пользователь новый
        if created:
            UserProfile.objects.create(user=user)
            UserTokenLimit.objects.create(user=user)

        token, _ = Token.objects.get_or_create(user=user)

        return Response(
            {
                "token": token.key,
                "created": created,
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class MeView(APIView):
    """Профиль текущего пользователя."""

    def get(self, request: Request) -> Response:
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request: Request) -> Response:
        user_serializer = UserUpdateSerializer(
            request.user,
            data=request.data,
            partial=True,
        )
        user_serializer.is_valid(raise_exception=True)
        user_serializer.save()

        attachment_type = request.data.get("attachment_type")
        attachment_source = request.data.get("attachment_source")

        if attachment_type:
            from apps.users.models import UserProfile

            UserProfile.objects.filter(user=request.user).update(
                attachment_type=attachment_type,
                attachment_source=attachment_source
                or UserProfile.AttachmentSource.USER_DEFINED,
            )

        return Response(UserSerializer(request.user).data)


class TokenLimitView(APIView):
    """Лимиты токенов текущего пользователя."""

    def get(self, request: Request) -> Response:
        token_limit = getattr(request.user, "token_limit", None)
        if not token_limit:
            return Response(
                {"detail": "Лимиты токенов не найдены."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = UserTokenLimitSerializer(token_limit)
        return Response(serializer.data)
