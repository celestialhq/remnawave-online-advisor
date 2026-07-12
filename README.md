# Remnawave Online Advisor

A Telegram bot (aiogram 3) that polls the Remnawave node list every 30 seconds,
filters nodes by tags, stores daily aggregates in SQLite, and posts a daily
report to Telegram.

Report logic: data is grouped by `countryCode`, and **each node inside a country
is reported separately**.

## Features

- Reads a single endpoint — `GET /api/nodes` from `API_BASE_URL` (see [API key permissions (RBAC)](#api-key-permissions-rbac)).
- Authentication via the `Authorization: Bearer <API_TOKEN>` header.
- API timeout: 10 seconds by default.
- Up to 3 retries on transient errors: timeouts, network errors, HTTP 429/5xx.
- Node filtering by `EXCLUDED_TAGS`.
- `countryCode` normalization: an empty code falls back to `unknown`.
- Per-node daily aggregates: `max_online`, `sum_online`, `samples_count`.
- Report grouped by `countryCode`, with separate nodes by `name` inside each group.
- Daily report to a Telegram group at 23:59 `Europe/Moscow`.
- After a successful report, aggregates are moved to `daily_history` and the current day is cleared.
- Docker, Docker Compose v2, Railway config.
- Prebuilt image published to GHCR via GitHub Actions.
- Pytest tests for stats, filtering, storage, and report trend arrows.

## API key permissions (RBAC)

Remnawave now supports RBAC API tokens: access is granted per endpoint rather
than "all or nothing". The advisor only needs **read access to a single
endpoint** — the rest of the API is unnecessary.

| Controller | Method | Endpoint     | Scope  | Why                                                                     |
| ---------- | ------ | ------------ | ------ | ----------------------------------------------------------------------- |
| **Nodes**  | `GET`  | `/api/nodes` | `Read` | Fetch the node list: `name`, `countryCode`, `usersOnline`, `tags`, `uuid` |

The advisor **does not** write anything to Remnawave and never touches users,
HWID devices, subscriptions, etc. The token needs no `Write` scope and no other
controllers.

### Creating a minimal token

1. In the Remnawave panel, open **Create API token**.
2. Set a **Token name** (e.g. `online-advisor`) and a **Lifetime (days)**.
3. Do **not** click "Full access". Instead, expand the **Nodes** controller and
   enable **`Read`** on the `GET /api/nodes` endpoint only. (Granting `Read` on
   the whole Nodes controller is also fine — it exposes nothing beyond the node
   list.)
4. Click **Create** and copy the token — it is shown only once.
5. Put it into `.env`:

   ```env
   API_TOKEN=<the-copied-token>
   ```

The advisor prepends `Bearer ` automatically, so `API_TOKEN` only needs the raw
token (a value that already starts with `Bearer ` is also accepted and won't be
duplicated).

## Configuration

Copy the environment example:

```bash
cp .env.example .env
```

Fill in `.env`:

```env
TELEGRAM_BOT_TOKEN=123456:telegram-bot-token
TELEGRAM_CHAT_ID=-1001234567890
TELEGRAM_MESSAGE_THREAD_ID=

API_BASE_URL=https://example.com
API_TOKEN=change-me

EXCLUDED_TAGS=internal,test
DATABASE_PATH=data/online_advisor.sqlite3
```

`EXCLUDED_TAGS` can be a comma-separated string:

```env
EXCLUDED_TAGS=internal,test,disabled
```

or a JSON array:

```env
EXCLUDED_TAGS=["internal", "test", "disabled"]
```

## Local run (uv)

The project uses [uv](https://docs.astral.sh/uv/) for dependency management.

```bash
uv sync            # create the venv and install dependencies from uv.lock
uv run python -m app.main
```

## Run with Docker Compose v2

By default `docker-compose.yml` pulls the prebuilt image from GHCR:

```bash
docker compose up -d
```

To build locally instead, uncomment `build: .` in `docker-compose.yml` and run
`docker compose up --build -d`.

Logs:

```bash
docker compose logs -f remnawave-online-advisor
```

Stop:

```bash
docker compose down
```

## Prebuilt image (GHCR)

Every push to `main` builds and publishes an image to the GitHub Container
Registry via [`.github/workflows/docker-publish.yml`](.github/workflows/docker-publish.yml):

```bash
docker pull ghcr.io/celestialhq/remnawave-online-advisor:latest
```

## Railway

The project ships `railway.json` and a `Dockerfile`. On Railway, add the
variables from `.env.example` to Variables. The SQLite file defaults to
`data/online_advisor.sqlite3`; for production, attach a volume and point
`DATABASE_PATH` inside the mounted directory.

## Report format

```text
━━━━━━━━━━━━━━━━━━━━
🇫🇮 FINLAND
━━━━━━━━━━━━━━━━━━━━
▫️ Finland Node 1
├ Max online: 100 🔺
└ Avg online: 55 🔻

▫️ Finland Node 2
├ Max online: 3 🔻
└ Avg online: 1
```

The arrow compares against the same node's values from yesterday in `daily_history`:

- `🔺` — today's value is higher than yesterday's.
- `🔻` — today's value is lower than yesterday's.
- no arrow — values are equal or there is no data for yesterday.

## Tests

```bash
uv run pytest
```
