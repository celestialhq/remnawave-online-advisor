from __future__ import annotations

import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from app.stats import DailyNodeStat, HistoryNodeStat, NodeOnline

logger = logging.getLogger(__name__)

CURRENT_DAILY_STATS_SCHEMA = """
CREATE TABLE IF NOT EXISTS current_daily_stats (
    date TEXT NOT NULL,
    node_uuid TEXT NOT NULL,
    node_name TEXT NOT NULL,
    country_code TEXT NOT NULL,
    max_online INTEGER NOT NULL DEFAULT 0,
    sum_online INTEGER NOT NULL DEFAULT 0,
    samples_count INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (date, node_uuid)
)
"""

DAILY_HISTORY_SCHEMA = """
CREATE TABLE IF NOT EXISTS daily_history (
    date TEXT NOT NULL,
    node_uuid TEXT NOT NULL,
    node_name TEXT NOT NULL,
    country_code TEXT NOT NULL,
    max_online INTEGER NOT NULL,
    avg_online REAL NOT NULL,
    PRIMARY KEY (date, node_uuid)
)
"""


class Database:
    def __init__(self, database_path: str) -> None:
        self.database_path = database_path
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(database_path, isolation_level=None)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA journal_mode=WAL")
        self._connection.execute("PRAGMA foreign_keys=ON")

    def initialize(self) -> None:
        with self._connection:
            self._ensure_table(
                table_name="current_daily_stats",
                schema_sql=CURRENT_DAILY_STATS_SCHEMA,
                required_columns={"date", "node_uuid", "node_name", "country_code", "max_online", "sum_online", "samples_count"},
            )
            self._ensure_table(
                table_name="daily_history",
                schema_sql=DAILY_HISTORY_SCHEMA,
                required_columns={"date", "node_uuid", "node_name", "country_code", "max_online", "avg_online"},
            )

    def _ensure_table(self, table_name: str, schema_sql: str, required_columns: set[str]) -> None:
        columns = self._table_columns(table_name)
        if not columns:
            self._connection.execute(schema_sql)
            return
        if required_columns.issubset(columns):
            return

        # The previous country-level schema cannot be safely converted to node-level rows,
        # because it did not store node_uuid/node_name. Keep it as a backup and create the new schema.
        suffix = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        backup_table_name = f"{table_name}_legacy_country_{suffix}"
        logger.warning(
            "Backing up incompatible %s schema to %s and creating node-level schema",
            table_name,
            backup_table_name,
        )
        self._connection.execute(f'ALTER TABLE "{table_name}" RENAME TO "{backup_table_name}"')
        self._connection.execute(schema_sql)

    def _table_columns(self, table_name: str) -> set[str]:
        rows = self._connection.execute(f'PRAGMA table_info("{table_name}")').fetchall()
        return {str(row["name"]) for row in rows}

    def update_current_daily_stats(self, date: str, node_online_rows: Iterable[NodeOnline]) -> None:
        rows = list(node_online_rows)
        if not rows:
            logger.info("No node online data to store for %s", date)
            return

        with self._connection:
            for row in rows:
                self._connection.execute(
                    """
                    INSERT INTO current_daily_stats (
                        date,
                        node_uuid,
                        node_name,
                        country_code,
                        max_online,
                        sum_online,
                        samples_count
                    )
                    VALUES (?, ?, ?, ?, ?, ?, 1)
                    ON CONFLICT(date, node_uuid) DO UPDATE SET
                        node_name = excluded.node_name,
                        country_code = excluded.country_code,
                        max_online = MAX(current_daily_stats.max_online, excluded.max_online),
                        sum_online = current_daily_stats.sum_online + excluded.sum_online,
                        samples_count = current_daily_stats.samples_count + 1
                    """,
                    (
                        date,
                        row.node_uuid,
                        row.node_name,
                        row.country_code,
                        row.users_online,
                        row.users_online,
                    ),
                )

    def get_current_daily_stats(self, date: str) -> list[DailyNodeStat]:
        rows = self._connection.execute(
            """
            SELECT date, node_uuid, node_name, country_code, max_online, sum_online, samples_count
            FROM current_daily_stats
            WHERE date = ?
            ORDER BY country_code, node_name, node_uuid
            """,
            (date,),
        ).fetchall()
        return [
            DailyNodeStat(
                date=row["date"],
                node_uuid=row["node_uuid"],
                node_name=row["node_name"],
                country_code=row["country_code"],
                max_online=int(row["max_online"]),
                sum_online=int(row["sum_online"]),
                samples_count=int(row["samples_count"]),
            )
            for row in rows
        ]

    def get_history_for_date(self, date: str) -> dict[str, HistoryNodeStat]:
        rows = self._connection.execute(
            """
            SELECT date, node_uuid, node_name, country_code, max_online, avg_online
            FROM daily_history
            WHERE date = ?
            """,
            (date,),
        ).fetchall()
        return {
            row["node_uuid"]: HistoryNodeStat(
                date=row["date"],
                node_uuid=row["node_uuid"],
                node_name=row["node_name"],
                country_code=row["country_code"],
                max_online=int(row["max_online"]),
                avg_online=float(row["avg_online"]),
            )
            for row in rows
        }

    def finalize_day(self, date: str) -> list[DailyNodeStat]:
        stats = self.get_current_daily_stats(date)
        with self._connection:
            for row in stats:
                self._connection.execute(
                    """
                    INSERT INTO daily_history (date, node_uuid, node_name, country_code, max_online, avg_online)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(date, node_uuid) DO UPDATE SET
                        node_name = excluded.node_name,
                        country_code = excluded.country_code,
                        max_online = excluded.max_online,
                        avg_online = excluded.avg_online
                    """,
                    (row.date, row.node_uuid, row.node_name, row.country_code, row.max_online, row.avg_online),
                )
            self._connection.execute("DELETE FROM current_daily_stats WHERE date = ?", (date,))
        return stats

    def close(self) -> None:
        self._connection.close()
