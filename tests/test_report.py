from app.report import build_daily_report, trend_arrow
from app.stats import DailyNodeStat, HistoryNodeStat


def test_trend_arrow():
    assert trend_arrow(101, 100) == " 🔺"
    assert trend_arrow(99, 100) == " 🔻"
    assert trend_arrow(100, 100) == ""
    assert trend_arrow(100, None) == ""


def test_build_daily_report_groups_by_country_and_prints_each_node_separately():
    today = [
        DailyNodeStat(
            date="2026-06-23",
            node_uuid="fin-1",
            node_name="Finland 1",
            country_code="finland",
            max_online=100,
            sum_online=110,
            samples_count=2,
        ),
        DailyNodeStat(
            date="2026-06-23",
            node_uuid="fin-2",
            node_name="Finland 2",
            country_code="finland",
            max_online=3,
            sum_online=4,
            samples_count=2,
        ),
        DailyNodeStat(
            date="2026-06-23",
            node_uuid="ger-1",
            node_name="Germany 1",
            country_code="germany",
            max_online=100,
            sum_online=100,
            samples_count=2,
        ),
    ]
    yesterday = {
        "fin-1": HistoryNodeStat(
            date="2026-06-22",
            node_uuid="fin-1",
            node_name="Finland 1",
            country_code="finland",
            max_online=90,
            avg_online=60,
        ),
        "fin-2": HistoryNodeStat(
            date="2026-06-22",
            node_uuid="fin-2",
            node_name="Finland 2",
            country_code="finland",
            max_online=5,
            avg_online=2,
        ),
        "ger-1": HistoryNodeStat(
            date="2026-06-22",
            node_uuid="ger-1",
            node_name="Germany 1",
            country_code="germany",
            max_online=100,
            avg_online=40,
        ),
    }

    assert build_daily_report(today, yesterday) == (
        "finland:\n\n"
        "Finland 1:\n"
        "Максимальный онлайн: 100 🔺\n"
        "Средний онлайн: 55 🔻\n\n"
        "Finland 2:\n"
        "Максимальный онлайн: 3 🔻\n"
        "Средний онлайн: 2\n\n"
        "germany:\n\n"
        "Germany 1:\n"
        "Максимальный онлайн: 100\n"
        "Средний онлайн: 50 🔺"
    )


def test_build_daily_report_omits_arrows_when_no_yesterday_data():
    today = [
        DailyNodeStat(
            date="2026-06-23",
            node_uuid="unknown-1",
            node_name="Unknown 1",
            country_code="unknown",
            max_online=3,
            sum_online=5,
            samples_count=2,
        )
    ]

    assert build_daily_report(today, {}) == (
        "unknown:\n\n"
        "Unknown 1:\n"
        "Максимальный онлайн: 3\n"
        "Средний онлайн: 2.5"
    )
