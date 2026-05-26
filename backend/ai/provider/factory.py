import logging

from constance import config as constance_config

from .base import BaseAIProvider
from .gemini import GeminiProvider
from .groq import GroqProvider
from core.exceptions import ProviderError

logger = logging.getLogger("ai")


class AIProviderFactory:
    """
    Фабрика ИИ провайдеров.

    Кэширует экземпляр провайдера - не создает новый при каждом вызове.
    """

    _PROVIDERS: dict[str, type[BaseAIProvider]] = {
        "groq": GroqProvider,
        "gemini": GeminiProvider,
    }
    _cache: dict[str, BaseAIProvider] = {}

    @classmethod
    def get_provider(cls) -> BaseAIProvider:
        """
        Возвращает экземпляр ИИ-провайдера.

        Кэширует ИИ-провайдер по имени.
        При смене провайдера через админку изменения применяются сразу.
        """
        provider_name = constance_config.AI_PROVIDER
        if provider_name not in cls._cache:
            provider_class = cls._PROVIDERS.get(provider_name)
            if not provider_class:
                available_providers = ", ".join(cls._PROVIDERS.keys())
                raise ProviderError(
                    f"Неизвестный ИИ-провайдер: {provider_name}. "
                    f"Доступные: {available_providers}"
                )
            cls._cache[provider_name] = provider_class()
            logger.info(f"ИИ-провайдер создан: {provider_name}")

        return cls._cache[provider_name]
