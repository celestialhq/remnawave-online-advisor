from app.database import Database
from app.stats import NodeOnline


def test_database_stores_daily_aggregates_per_node(tmp_path):
    database = Database(str(tmp_path / "test.sqlite3"))
    database.initialize()

    database.update_current_daily_stats(
        "2026-06-23",
        [
            NodeOnline(node_uuid="fin-1", node_name="Finland 1", country_code="finland", users_online=10),
            NodeOnline(node_uuid="fin-2", node_name="Finland 2", country_code="finland", users_online=0),
        ],
    )
    database.update_current_daily_stats(
        "2026-06-23",
        [
            NodeOnline(node_uuid="fin-1", node_name="Finland 1", country_code="finland", users_online=30),
            NodeOnline(node_uuid="fin-2", node_name="Finland 2", country_code="finland", users_online=2),
        ],
    )

    stats = database.get_current_daily_stats("2026-06-23")
    database.close()

    assert [(row.node_uuid, row.max_online, row.sum_online, row.samples_count, row.avg_online) for row in stats] == [
        ("fin-1", 30, 40, 2, 20),
        ("fin-2", 2, 2, 2, 1),
    ]
