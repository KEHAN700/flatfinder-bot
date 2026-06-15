"""Точка входа: Bot, Dispatcher, роутеры, фоновая джоба уведомлений, polling."""
from __future__ import annotations

import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import settings
from database.engine import init_db
from handlers import register_handlers
from services.notifications import run_notifications

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


async def start_keepalive_server() -> web.AppRunner | None:
    """Поднимает крошечный HTTP-сервер на $PORT.

    Нужен только хостингам, которые держат сервис «живым» по открытому порту и
    HTTP-пингу (например, бесплатный Render Web Service). Локально, где PORT не
    задан, сервер не запускается — бот остаётся чистым long-polling процессом.
    """
    port = os.getenv("PORT")
    if not port:
        return None

    async def health(_: web.Request) -> web.Response:
        return web.Response(text="Estate bot is running ✅")

    app = web.Application()
    app.router.add_get("/", health)
    app.router.add_get("/health", health)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(port))
    await site.start()
    logger.info("Keep-alive HTTP-сервер слушает порт %s", port)
    return runner


async def main() -> None:
    await init_db()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())
    register_handlers(dp)

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        run_notifications,
        trigger="interval",
        minutes=settings.notify_interval_min,
        args=(bot,),
        id="notify",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(
        "Бот запущен. Джоба уведомлений каждые %s мин.", settings.notify_interval_min
    )

    runner = await start_keepalive_server()

    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown(wait=False)
        if runner is not None:
            await runner.cleanup()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Остановка бота.")
