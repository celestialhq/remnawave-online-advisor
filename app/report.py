from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from decimal import Decimal, ROUND_HALF_UP

from app.stats import DailyNodeStat, HistoryNodeStat


def format_number(value: float | int) -> str:
    decimal_value = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if decimal_value == decimal_value.to_integral():
        return str(int(decimal_value))
    return format(decimal_value.normalize(), "f")


def trend_arrow(today: float | int, yesterday: float | int | None) -> str:
    if yesterday is None:
        return ""
    if today > yesterday:
        return " 🔺"
    if today < yesterday:
        return " 🔻"
    return ""


def build_daily_report(
    today_stats: Iterable[DailyNodeStat],
    yesterday_stats: Mapping[str, HistoryNodeStat],
) -> str:
    rows = sorted(today_stats, key=lambda row: (row.country_code, row.node_name, row.node_uuid))
    if not rows:
        return "Нет данных за сегодня."

    grouped: dict[str, list[DailyNodeStat]] = defaultdict(list)
    for row in rows:
        grouped[row.country_code].append(row)

    country_blocks: list[str] = []
    for country_code in sorted(grouped):
        lines = [f"{country_code}:"]
        for row in grouped[country_code]:
            yesterday = yesterday_stats.get(row.node_uuid)
            yesterday_max = yesterday.max_online if yesterday else None
            yesterday_avg = yesterday.avg_online if yesterday else None

            lines.extend(
                [
                    "",
                    f"{row.node_name}:",
                    f"Максимальный онлайн: {format_number(row.max_online)}{trend_arrow(row.max_online, yesterday_max)}",
                    f"Средний онлайн: {format_number(row.avg_online)}{trend_arrow(row.avg_online, yesterday_avg)}",
                ]
            )
        country_blocks.append("\n".join(lines))

    return "\n\n".join(country_blocks)
