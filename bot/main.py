import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from decouple import config

from bot.handlers import (
    assessments,
    cancel,
    candidates,
    events,
    reports,
    settings,
    start,
)
from bot.middlewares.auth import AuthMiddleware

logger = logging.getLogger("bot")


async def main() -> None:
    bot = Bot(
        token=config("BOT_TOKEN"),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp.message.middleware(AuthMiddleware())
    dp.callback_query.middleware(AuthMiddleware())

    dp.include_router(cancel.router)
    dp.include_router(start.router)
    dp.include_router(candidates.router)
    dp.include_router(events.router)
    dp.include_router(assessments.router)
    dp.include_router(settings.router)
    dp.include_router(reports.router)

    logger.info("Бот запущен")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        logger.info("Бот остановлен")


if __name__ == "__main__":
    asyncio.run(main())
