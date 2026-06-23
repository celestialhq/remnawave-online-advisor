from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

UNKNOWN_COUNTRY = "unknown"
UNKNOWN_NODE_NAME = "Unnamed node"


@dataclass(frozen=True, slots=True)
class DailyAggregate:
    max_online: int = 0
    sum_online: int = 0
    samples_count: int = 0

    @property
    def avg_online(self) -> float:
        if self.samples_count == 0:
            return 0.0
        return self.sum_online / self.samples_count


@dataclass(frozen=True, slots=True)
class NodeOnline:
    node_uuid: str
    node_name: str
    country_code: str
    users_online: int


@dataclass(frozen=True, slots=True)
class DailyNodeStat:
    date: str
    node_uuid: str
    node_name: str
    country_code: str
    max_online: int
    sum_online: int
    samples_count: int

    @property
    def avg_online(self) -> float:
        if self.samples_count == 0:
            return 0.0
        return self.sum_online / self.samples_count


@dataclass(frozen=True, slots=True)
class HistoryNodeStat:
    date: str
    node_uuid: str
    node_name: str
    country_code: str
    max_online: int
    avg_online: float


def normalize_country_code(country_code: Any) -> str:
    value = "" if country_code is None else str(country_code).strip().lower()
    return value or UNKNOWN_COUNTRY


def normalize_online(value: Any) -> int:
    try:
        online = int(value)
    except (TypeError, ValueError):
        return 0
    return max(online, 0)


def normalize_node_name(name: Any) -> str:
    value = "" if name is None else str(name).strip()
    return value or UNKNOWN_NODE_NAME


def normalize_node_uuid(uuid: Any, country_code: str, node_name: str) -> str:
    value = "" if uuid is None else str(uuid).strip()
    # uuid is expected from the API. Fallback keeps the bot from crashing on a bad payload.
    return value or f"missing-uuid:{country_code}:{node_name}"


def has_excluded_tag(tags: Any, excluded_tags: Iterable[str]) -> bool:
    if not tags:
        return False
    excluded = {str(tag).strip() for tag in excluded_tags if str(tag).strip()}
    if not excluded:
        return False
    if not isinstance(tags, list):
        return False
    return any(str(tag).strip() in excluded for tag in tags)


def filter_nodes(nodes: Iterable[Mapping[str, Any]], excluded_tags: Iterable[str]) -> list[Mapping[str, Any]]:
    return [node for node in nodes if not has_excluded_tag(node.get("tags"), excluded_tags)]


def nodes_to_online_rows(nodes: Iterable[Mapping[str, Any]]) -> list[NodeOnline]:
    rows: list[NodeOnline] = []
    for node in nodes:
        country_code = normalize_country_code(node.get("countryCode"))
        node_name = normalize_node_name(node.get("name"))
        node_uuid = normalize_node_uuid(node.get("uuid"), country_code, node_name)
        rows.append(
            NodeOnline(
                node_uuid=node_uuid,
                node_name=node_name,
                country_code=country_code,
                users_online=normalize_online(node.get("usersOnline")),
            )
        )
    return rows


def aggregate_nodes_by_country_and_node(
    nodes: Iterable[Mapping[str, Any]],
    excluded_tags: Iterable[str],
) -> list[NodeOnline]:
    """Return one normalized online row per node, grouped later by countryCode in reports."""
    filtered_nodes = filter_nodes(nodes, excluded_tags)
    return nodes_to_online_rows(filtered_nodes)


def update_aggregate(previous: DailyAggregate | None, current_online: int) -> DailyAggregate:
    previous = previous or DailyAggregate()
    current_online = normalize_online(current_online)
    return DailyAggregate(
        max_online=max(previous.max_online, current_online),
        sum_online=previous.sum_online + current_online,
        samples_count=previous.samples_count + 1,
    )
