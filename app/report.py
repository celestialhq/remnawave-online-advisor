from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from decimal import Decimal, ROUND_HALF_UP
from html import escape

from app.stats import DailyNodeStat, HistoryNodeStat

COUNTRY_FLAGS: dict[str, str] = {
    "ad": "🇦🇩",
    "andorra": "🇦🇩",
    "am": "🇦🇲",
    "armenia": "🇦🇲",
    "at": "🇦🇹",
    "austria": "🇦🇹",
    "au": "🇦🇺",
    "australia": "🇦🇺",
    "be": "🇧🇪",
    "belgium": "🇧🇪",
    "br": "🇧🇷",
    "brazil": "🇧🇷",
    "ca": "🇨🇦",
    "canada": "🇨🇦",
    "ch": "🇨🇭",
    "switzerland": "🇨🇭",
    "cn": "🇨🇳",
    "china": "🇨🇳",
    "cz": "🇨🇿",
    "czech": "🇨🇿",
    "de": "🇩🇪",
    "germany": "🇩🇪",
    "dk": "🇩🇰",
    "denmark": "🇩🇰",
    "ee": "🇪🇪",
    "estonia": "🇪🇪",
    "es": "🇪🇸",
    "spain": "🇪🇸",
    "fi": "🇫🇮",
    "finland": "🇫🇮",
    "fr": "🇫🇷",
    "france": "🇫🇷",
    "gb": "🇬🇧",
    "uk": "🇬🇧",
    "united kingdom": "🇬🇧",
    "ge": "🇬🇪",
    "georgia": "🇬🇪",
    "hu": "🇭🇺",
    "hungary": "🇭🇺",
    "it": "🇮🇹",
    "italy": "🇮🇹",
    "jp": "🇯🇵",
    "japan": "🇯🇵",
    "kz": "🇰🇿",
    "kazakhstan": "🇰🇿",
    "lt": "🇱🇹",
    "lithuania": "🇱🇹",
    "lv": "🇱🇻",
    "latvia": "🇱🇻",
    "nl": "🇳🇱",
    "netherlands": "🇳🇱",
    "no": "🇳🇴",
    "norway": "🇳🇴",
    "pl": "🇵🇱",
    "poland": "🇵🇱",
    "ru": "🇷🇺",
    "russia": "🇷🇺",
    "russian": "🇷🇺",
    "se": "🇸🇪",
    "sweden": "🇸🇪",
    "tr": "🇹🇷",
    "turkey": "🇹🇷",
    "ua": "🇺🇦",
    "ukraine": "🇺🇦",
    "us": "🇺🇸",
    "usa": "🇺🇸",
    "united states": "🇺🇸",
}

COUNTRY_DIVIDER = "━━━━━━━━━━━━━━━━━━━━"
NODE_SEPARATOR = ""


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


def country_flag(country_code: str) -> str:
    return COUNTRY_FLAGS.get(country_code.strip().lower(), "🌐")


def format_country_title(country_code: str) -> str:
    code = country_code.strip() or "unknown"
    return f"{country_flag(code)} <b>{escape(code.upper())}</b>"


def format_metric_line(label: str, value: float | int, arrow: str, is_last: bool = False) -> str:
    branch = "└" if is_last else "├"
    return f"{branch} {label}: <b>{format_number(value)}</b>{arrow}"


def format_node_block(row: DailyNodeStat, yesterday: HistoryNodeStat | None) -> str:
    yesterday_max = yesterday.max_online if yesterday else None
    yesterday_avg = yesterday.avg_online if yesterday else None

    return "\n".join(
        [
            f"▫️ <b>{escape(row.node_name)}</b>",
            format_metric_line(
                "Max online",
                row.max_online,
                trend_arrow(row.max_online, yesterday_max),
            ),
            format_metric_line(
                "Avg online",
                row.avg_online,
                trend_arrow(row.avg_online, yesterday_avg),
                is_last=True,
            ),
        ]
    )


def build_daily_report(
    today_stats: Iterable[DailyNodeStat],
    yesterday_stats: Mapping[str, HistoryNodeStat],
    report_date: str | None = None,
) -> str:
    rows = sorted(today_stats, key=lambda row: (row.country_code, row.node_name, row.node_uuid))
    title_lines = ["📊 <b>Online Advisor</b>"]
    if report_date:
        title_lines.append(f"🗓 <code>{escape(report_date)}</code>")

    if not rows:
        return "\n".join([*title_lines, "", "No data for today."])

    grouped: dict[str, list[DailyNodeStat]] = defaultdict(list)
    for row in rows:
        grouped[row.country_code].append(row)

    country_blocks: list[str] = []
    for country_code in sorted(grouped):
        lines = [COUNTRY_DIVIDER, format_country_title(country_code), COUNTRY_DIVIDER]
        node_blocks = [format_node_block(row, yesterday_stats.get(row.node_uuid)) for row in grouped[country_code]]
        lines.append("\n\n".join(node_blocks))
        country_blocks.append("\n".join(lines))

    return "\n".join(title_lines) + "\n\n" + "\n\n".join(country_blocks)
