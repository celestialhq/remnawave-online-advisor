from __future__ import annotations

from aiogram import Bot


async def send_telegram_report(
    bot: Bot,
    chat_id: str,
    text: str,
    message_thread_id: int | None = None,
) -> None:
    kwargs = {}
    if message_thread_id is not None:
        kwargs["message_thread_id"] = message_thread_id
    await bot.send_message(chat_id=chat_id, text=text, **kwargs)
