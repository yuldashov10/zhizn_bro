import pytest
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from tests.factories import (
    CriterionFactory,
    HardStopFactory,
    UserFactory,
    UserProfileFactory,
    UserTokenLimitFactory,
)


@pytest.fixture
def user(db):
    """Базовый пользователь."""
    u = UserFactory()
    UserProfileFactory(user=u)
    UserTokenLimitFactory(user=u)
    return u


@pytest.fixture
def another_user(db):
    """Второй пользователь для проверки изоляции данных."""
    u = UserFactory()
    UserProfileFactory(user=u)
    UserTokenLimitFactory(user=u)
    return u


@pytest.fixture
def api_client(user):
    """Авторизованный API клиент."""
    token, _ = Token.objects.get_or_create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return client


@pytest.fixture
def another_client(another_user):
    """API клиент второго пользователя."""
    token, _ = Token.objects.get_or_create(user=another_user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return client


@pytest.fixture
def anon_client():
    """Неавторизованный API клиент."""
    return APIClient()


@pytest.fixture
def system_criteria(db):
    """Системные критерии."""
    data = [
        ("Доверие", 0.30),
        ("Эмоц. стабильность", 0.25),
        ("Уважение", 0.20),
        ("Открытость", 0.15),
        ("Интеллект", 0.10),
    ]
    return [
        CriterionFactory(name=name, weight=weight) for name, weight in data
    ]


@pytest.fixture
def system_hard_stops(db):
    """Системные Hard Stops."""
    names = [
        "Ложь / обман",
        "Разведена с детьми",
        "Курение",
        "Алкоголь / психотропные вещества",
        "Эзотерика / астрология",
        "Дезорганизованный тип привязанности",
    ]
    return [HardStopFactory(name=name) for name in names]
