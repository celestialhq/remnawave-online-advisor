from app.stats import DailyAggregate, aggregate_nodes_by_country_and_node, update_aggregate


def test_aggregate_nodes_filters_excluded_tags_and_keeps_each_node_separate():
    nodes = [
        {
            "uuid": "1",
            "name": "Finland 1",
            "countryCode": "finland",
            "tags": ["public"],
            "usersOnline": 10,
        },
        {
            "uuid": "2",
            "name": "Finland 2",
            "countryCode": "Finland",
            "tags": ["internal"],
            "usersOnline": 999,
        },
        {
            "uuid": "3",
            "name": "Finland 3",
            "countryCode": "FINLAND",
            "tags": [],
            "usersOnline": 7,
        },
        {
            "uuid": "4",
            "name": "Unknown 1",
            "countryCode": "",
            "tags": ["public"],
            "usersOnline": 3,
        },
    ]

    result = aggregate_nodes_by_country_and_node(nodes, excluded_tags=["internal"])

    assert [(row.country_code, row.node_uuid, row.node_name, row.users_online) for row in result] == [
        ("finland", "1", "Finland 1", 10),
        ("finland", "3", "Finland 3", 7),
        ("unknown", "4", "Unknown 1", 3),
    ]


def test_aggregate_nodes_does_not_sum_nodes_inside_country_group():
    nodes = [
        {"uuid": "1", "name": "Finland 1", "countryCode": "finland", "tags": [], "usersOnline": 10},
        {"uuid": "2", "name": "Finland 2", "countryCode": "finland", "tags": [], "usersOnline": 15},
        {"uuid": "3", "name": "Germany 1", "countryCode": "germany", "tags": [], "usersOnline": 4},
    ]

    result = aggregate_nodes_by_country_and_node(nodes, excluded_tags=[])

    assert [(row.country_code, row.node_name, row.users_online) for row in result] == [
        ("finland", "Finland 1", 10),
        ("finland", "Finland 2", 15),
        ("germany", "Germany 1", 4),
    ]


def test_update_aggregate_keeps_daily_max_sum_count_and_average():
    aggregate = update_aggregate(None, 10)
    aggregate = update_aggregate(aggregate, 5)
    aggregate = update_aggregate(aggregate, 30)

    assert aggregate == DailyAggregate(max_online=30, sum_online=45, samples_count=3)
    assert aggregate.avg_online == 15
