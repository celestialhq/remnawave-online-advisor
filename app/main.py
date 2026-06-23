from __future__ import annotations

import asyncio
import logging
import signal

from aiogram import Bot

from app.config import get_settings
from app.database import Database
from app.scheduler import create_scheduler, poll_nodes_once


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


async def main() -> None:
    settings = get_settings()
    configure_logging(settings.LOG_LEVEL)
    logger = logging.getLogger(__name__)

    database = Database(settings.DATABASE_PATH)
    database.initialize()

    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    scheduler = create_scheduler(settings, database, bot)

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, stop_event.set)
        except NotImplementedError:
            pass

    logger.info("Online Advisor started")
    await poll_nodes_once(settings, database)
    scheduler.start()

    try:
        await stop_event.wait()
    finally:
        logger.info("Online Advisor is shutting down")
        scheduler.shutdown(wait=False)
        await bot.session.close()
        database.close()


if __name__ == "__main__":
    asyncio.run(main())
