# Remnawave Online Advisor

Telegram-бот на aiogram 3, который каждые 30 секунд получает список нод из Remnawave, фильтрует ноды по тегам, хранит дневные агрегаты в SQLite и отправляет ежедневный отчёт в Telegram.

Главная логика отчёта: данные группируются по `countryCode` и **каждая нода внутри страны выводится отдельно**.

## Возможности

- GET `/api/nodes` от `API_BASE_URL`.
- Авторизация через HTTP-заголовок `Authorization: Bearer <API_TOKEN>`.
- Таймаут API: 10 секунд по умолчанию.
- До 3 повторов при временных ошибках: timeout, сетевые ошибки, HTTP 429/5xx.
- Фильтрация нод по `EXCLUDED_TAGS`.
- Нормализация `countryCode`: пустой код попадает в `unknown`.
- Хранение дневных агрегатов **по каждой ноде**: `max_online`, `sum_online`, `samples_count`.
- Группировка отчёта по `countryCode`, внутри каждой группы — отдельные ноды по `name`.
- Ежедневный отчёт в Telegram-группу в 23:59 `Europe/Moscow`.
- После успешной отправки отчёта агрегаты переносятся в `daily_history`, а текущий день очищается.
- Docker, Docker Compose v2, Railway config.
- Pytest-тесты для статистики, фильтрации, БД и стрелок в отчёте.

## Настройка

Скопируйте пример переменных окружения:

```bash
cp .env.example .env
```

Заполните `.env`:

```env
TELEGRAM_BOT_TOKEN=123456:telegram-bot-token
TELEGRAM_CHAT_ID=-1001234567890
TELEGRAM_MESSAGE_THREAD_ID=

API_BASE_URL=https://example.com
API_TOKEN=change-me

EXCLUDED_TAGS=internal,test
DATABASE_PATH=data/online_advisor.sqlite3
```

`EXCLUDED_TAGS` можно задавать как строку через запятую:

```env
EXCLUDED_TAGS=internal,test,disabled
```

или как JSON-массив:

```env
EXCLUDED_TAGS=["internal", "test", "disabled"]
```

## Локальный запуск без Docker

```bash
python3.14 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.main
```

## Запуск через Docker Compose v2

```bash
docker compose up --build -d
```

Логи:

```bash
docker compose logs -f online-advisor
```

Остановка:

```bash
docker compose down
```

## Railway

Проект содержит `railway.json` и `Dockerfile`. На Railway нужно добавить переменные окружения из `.env.example` в Variables. SQLite-файл по умолчанию хранится в `data/online_advisor.sqlite3`; для production лучше подключить volume и указать `DATABASE_PATH` внутри примонтированной директории.

## Формат отчёта

```text
finland:

Finland Node 1:
Максимальный онлайн: 100 🔺
Средний онлайн: 55 🔻

Finland Node 2:
Максимальный онлайн: 3 🔻
Средний онлайн: 1

germany:

Germany Node 1:
Максимальный онлайн: 100 🔺
Средний онлайн: 55
```

Стрелка ставится при сравнении с данными этой же ноды за вчерашний день из `daily_history`:

- `🔺` — сегодняшнее значение больше вчерашнего.
- `🔻` — сегодняшнее значение меньше вчерашнего.
- нет знака — значения равны или вчерашних данных нет.

## Тесты

```bash
pytest
```
