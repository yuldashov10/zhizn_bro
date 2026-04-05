import pytest

from apps.users.models import User, UserProfile, UserTokenLimit


@pytest.fixture
def user(db):
    return User.objects.create_user(
        telegram_id=123456789, username="test_user"
    )


@pytest.fixture
def token_limit(user):
    return UserTokenLimit.objects.create(
        user=user,
        daily_limit=100,
        monthly_limit=1000,
        used_today=0,
        used_this_month=0,
        tier=UserTokenLimit.Tier.FREE,
    )


@pytest.fixture
def profile(user):
    return UserProfile.objects.create(
        user=user,
        attachment_type=UserProfile.AttachmentType.SECURE,
        attachment_source=UserProfile.AttachmentSource.BOT_TEST,
        correction_coefficient=1.0,
    )


class TestUser:
    def test_str_with_username(self, user):
        assert str(user) == "@test_user"

    def test_str_without_username(self, db):
        user = User.objects.create_user(telegram_id=987654321)
        assert str(user) == "tg:987654321"

    def test_create_user_without_telegram_id_raises(self, db):
        with pytest.raises(ValueError, match="Telegram ID обязателен"):
            User.objects.create_user(telegram_id=None)

    def test_user_has_unusable_password(self, user):
        assert not user.has_usable_password()


class TestUserTokenLimit:
    def test_daily_limit_not_exceeded(self, token_limit):
        token_limit.used_today = 50
        assert not token_limit.is_daily_limit_exceeded()

    def test_daily_limit_exceeded(self, token_limit):
        token_limit.used_today = 100
        assert token_limit.is_daily_limit_exceeded()

    def test_daily_limit_exceeded_over(self, token_limit):
        token_limit.used_today = 150
        assert token_limit.is_daily_limit_exceeded()

    def test_monthly_limit_not_exceeded(self, token_limit):
        token_limit.used_this_month = 500
        assert not token_limit.is_monthly_limit_exceeded()

    def test_monthly_limit_exceeded(self, token_limit):
        token_limit.used_this_month = 1000
        assert token_limit.is_monthly_limit_exceeded()


class TestUserProfile:
    def test_str(self, profile):
        assert "test_user" in str(profile)

    def test_default_correction_coefficient(self, profile):
        assert profile.correction_coefficient == 1.0

    def test_attachment_type_choices(self, profile):
        assert profile.attachment_type in [
            UserProfile.AttachmentType.SECURE,
            UserProfile.AttachmentType.ANXIOUS,
            UserProfile.AttachmentType.AVOIDANT,
            UserProfile.AttachmentType.DISORGANIZED,
        ]
