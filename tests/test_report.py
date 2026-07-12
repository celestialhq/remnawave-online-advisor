from app.report import build_daily_report, country_flag, trend_arrow
from app.stats import DailyNodeStat, HistoryNodeStat


def test_trend_arrow():
    assert trend_arrow(101, 100) == " 🔺"
    assert trend_arrow(99, 100) == " 🔻"
    assert trend_arrow(100, 100) == ""
    assert trend_arrow(100, None) == ""


def test_country_flag_supports_codes_and_names():
    assert country_flag("fi") == "🇫🇮"
    assert country_flag("finland") == "🇫🇮"
    assert country_flag("unknown-country") == "🌐"


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

    assert build_daily_report(today, yesterday, report_date="2026-06-23") == (
        "📊 <b>Online Advisor</b>\n"
        "🗓 <code>2026-06-23</code>\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🇫🇮 <b>FINLAND</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "▫️ <b>Finland 1</b>\n"
        "├ Max online: <b>100</b> 🔺\n"
        "└ Avg online: <b>55</b> 🔻\n\n"
        "▫️ <b>Finland 2</b>\n"
        "├ Max online: <b>3</b> 🔻\n"
        "└ Avg online: <b>2</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🇩🇪 <b>GERMANY</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "▫️ <b>Germany 1</b>\n"
        "├ Max online: <b>100</b>\n"
        "└ Avg online: <b>50</b> 🔺"
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
        "📊 <b>Online Advisor</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🌐 <b>UNKNOWN</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "▫️ <b>Unknown 1</b>\n"
        "├ Max online: <b>3</b>\n"
        "└ Avg online: <b>2.5</b>"
    )


def test_build_daily_report_escapes_html_in_node_and_country_names():
    today = [
        DailyNodeStat(
            date="2026-06-23",
            node_uuid="bad-html",
            node_name="Node <main> & backup",
            country_code="x<y",
            max_online=1,
            sum_online=1,
            samples_count=1,
        )
    ]

    report = build_daily_report(today, {})

    assert "<b>X&lt;Y</b>" in report
    assert "<b>Node &lt;main&gt; &amp; backup</b>" in report
