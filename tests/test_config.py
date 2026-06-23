from app.config import Settings


BASE_SETTINGS = {
    "TELEGRAM_BOT_TOKEN": "bot-token",
    "TELEGRAM_CHAT_ID": "-100123",
    "API_BASE_URL": "https://example.com/",
    "API_TOKEN": "api-token",
}


def test_excluded_tags_accepts_comma_separated_string():
    settings = Settings(**BASE_SETTINGS, EXCLUDED_TAGS="internal,test, demo ")

    assert settings.EXCLUDED_TAGS == ["internal", "test", "demo"]


def test_excluded_tags_accepts_json_array_string():
    settings = Settings(**BASE_SETTINGS, EXCLUDED_TAGS='["internal", "test"]')

    assert settings.EXCLUDED_TAGS == ["internal", "test"]


def test_excluded_tags_accepts_empty_string():
    settings = Settings(**BASE_SETTINGS, EXCLUDED_TAGS="")

    assert settings.EXCLUDED_TAGS == []
