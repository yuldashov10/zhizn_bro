from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView


class IsOwner(BasePermission):
    """
    Разрешает доступ только владельцу объекта.
    Объект должен иметь поле user или candidate.user.
    """

    message = "У вас нет доступа к этому объекту."

    def has_object_permission(
        self,
        request: Request,
        view: APIView,
        obj,
    ) -> bool:
        if hasattr(obj, "user"):
            return obj.user == request.user
        if hasattr(obj, "candidate"):
            return obj.candidate.user == request.user
        return False


class IsOwnerOrReadOnly(BasePermission):
    """
    Разрешает чтение всем авторизованным.
    Запись — только владельцу.
    """

    message = "У вас нет прав для изменения этого объекта."

    def has_object_permission(
        self,
        request: Request,
        view: APIView,
        obj,
    ) -> bool:
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        if hasattr(obj, "user"):
            return obj.user == request.user
        return False
