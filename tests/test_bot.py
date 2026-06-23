from app.bot import SAFE_TELEGRAM_MESSAGE_LIMIT, split_telegram_message


def test_split_telegram_message_keeps_short_text_unchanged():
    assert split_telegram_message("hello") == ["hello"]


def test_split_telegram_message_splits_long_text_on_paragraphs():
    paragraph = "x" * 1000
    text = "\n\n".join([paragraph] * 5)

    chunks = split_telegram_message(text, limit=2500)

    assert len(chunks) == 3
    assert all(len(chunk) <= SAFE_TELEGRAM_MESSAGE_LIMIT for chunk in chunks)
    assert chunks[0] == f"{paragraph}\n\n{paragraph}"
