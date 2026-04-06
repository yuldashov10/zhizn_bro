import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from core.logger import ProjectLogger
from decouple import config

from bot.handlers import assessments, cancel, candidates, events, start
from bot.middlewares.auth import AuthMiddleware

logger = ProjectLogger.get_logger("bot", "logs/bot.log")


async def main() -> None:
    bot = Bot(
        token=config("BOT_TOKEN"),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Регистрируем middleware
    dp.message.middleware(AuthMiddleware())
    dp.callback_query.middleware(AuthMiddleware())

    # Регистрируем роутеры
    dp.include_router(cancel.router)
    dp.include_router(start.router)
    dp.include_router(candidates.router)
    dp.include_router(events.router)
    dp.include_router(assessments.router)

    logger.info("Бот запущен")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        logger.info("Бот остановлен")


if __name__ == "__main__":
    asyncio.run(main())
