from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aiogram import Bot

TELEGRAM_MESSAGE_LIMIT = 4096
SAFE_TELEGRAM_MESSAGE_LIMIT = 3900


def split_telegram_message(text: str, limit: int = SAFE_TELEGRAM_MESSAGE_LIMIT) -> list[str]:
    """Split long reports into Telegram-safe chunks on paragraph boundaries."""
    if len(text) <= limit:
        return [text]

    chunks: list[str] = []
    current = ""
    for paragraph in text.split("\n\n"):
        candidate = paragraph if not current else f"{current}\n\n{paragraph}"
        if len(candidate) <= limit:
            current = candidate
            continue
        if current:
            chunks.append(current)
        current = paragraph

    if current:
        chunks.append(current)

    # Fallback for an extremely long single paragraph/node name.
    result: list[str] = []
    for chunk in chunks:
        if len(chunk) <= TELEGRAM_MESSAGE_LIMIT:
            result.append(chunk)
            continue
        for start in range(0, len(chunk), limit):
            result.append(chunk[start : start + limit])
    return result


async def send_telegram_report(
    bot: Bot,
    chat_id: str,
    text: str,
    message_thread_id: int | None = None,
) -> None:
    kwargs = {"parse_mode": "HTML"}
    if message_thread_id is not None:
        kwargs["message_thread_id"] = message_thread_id

    for chunk in split_telegram_message(text):
        await bot.send_message(chat_id=chat_id, text=chunk, **kwargs)
