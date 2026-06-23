from __future__ import annotations

import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.api_client import ApiClientError, NodesApiClient
from app.bot import send_telegram_report
from app.config import Settings
from app.database import Database
from app.report import build_daily_report
from app.stats import aggregate_nodes_by_country_and_node

logger = logging.getLogger(__name__)


def current_report_date(settings: Settings) -> str:
    return datetime.now(ZoneInfo(settings.REPORT_TIMEZONE)).date().isoformat()


def previous_report_date(settings: Settings) -> str:
    today = datetime.now(ZoneInfo(settings.REPORT_TIMEZONE)).date()
    return (today - timedelta(days=1)).isoformat()


async def poll_nodes_once(settings: Settings, database: Database) -> None:
    try:
        client = NodesApiClient(settings)
        nodes = await client.fetch_nodes()
        node_online_rows = aggregate_nodes_by_country_and_node(nodes, settings.EXCLUDED_TAGS)
        report_date = current_report_date(settings)
        database.update_current_daily_stats(report_date, node_online_rows)
        logger.info("Stored API sample for %s: %s node rows", report_date, len(node_online_rows))
    except ApiClientError:
        logger.exception("Nodes API polling failed")
    except Exception:
        logger.exception("Unexpected polling error")


async def send_daily_report_once(settings: Settings, database: Database, bot: Bot) -> None:
    report_date = current_report_date(settings)
    yesterday_date = previous_report_date(settings)

    today_stats = database.get_current_daily_stats(report_date)
    yesterday_stats = database.get_history_for_date(yesterday_date)
    report_text = build_daily_report(today_stats, yesterday_stats, report_date=report_date)

    try:
        await send_telegram_report(
            bot=bot,
            chat_id=settings.TELEGRAM_CHAT_ID,
            text=report_text,
            message_thread_id=settings.TELEGRAM_MESSAGE_THREAD_ID,
        )
        database.finalize_day(report_date)
        logger.info("Daily report for %s sent and finalized", report_date)
    except Exception:
        logger.exception("Daily report sending/finalization failed; current stats were not cleared")


def create_scheduler(settings: Settings, database: Database, bot: Bot) -> AsyncIOScheduler:
    timezone = ZoneInfo(settings.REPORT_TIMEZONE)
    scheduler = AsyncIOScheduler(timezone=timezone)

    scheduler.add_job(
        poll_nodes_once,
        trigger=IntervalTrigger(seconds=settings.POLL_INTERVAL_SECONDS),
        args=(settings, database),
        id="poll_nodes",
        max_instances=1,
        coalesce=True,
        replace_existing=True,
    )
    scheduler.add_job(
        send_daily_report_once,
        trigger=CronTrigger(hour=settings.REPORT_HOUR, minute=settings.REPORT_MINUTE, timezone=timezone),
        args=(settings, database, bot),
        id="daily_report",
        max_instances=1,
        coalesce=True,
        replace_existing=True,
    )
    return scheduler
