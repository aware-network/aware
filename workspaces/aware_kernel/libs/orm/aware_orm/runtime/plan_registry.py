from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Iterable, Iterator
from uuid import UUID

from aware_orm.graph.config_registry import GraphConfigRegistry, TableDescriptor
from aware_orm._support import logger

from .sql_metadata import get_sql_metadata_for_table

__all__ = [
    "PlanStepDescriptor",
    "PlanDescriptor",
    "GraphSQLPlanRegistry",
    "load_plan_registry_from_payload",
    "load_plan_registry",
    "build_graph_config_registry",
]


@dataclass(frozen=True)
class PlanStepDescriptor:
    """Serialized representation of a single hop inside a Graph plan."""

    table_key: str
    via_relationship_id: str | None
    uses_collection: bool
    join_condition: str | None
    projection_fields: tuple[str, ...]


@dataclass(frozen=True)
class PlanDescriptor:
    """Root descriptor for a Graph plan keyed by root table."""

    table_key: str
    projection_fields: tuple[str, ...]
    diagnostics: tuple[str, ...]
    plan_hash: str | None
    steps: tuple[PlanStepDescriptor, ...]


class GraphSQLPlanRegistry:
    """In-memory registry of GraphSQL plan descriptors grouped by language."""

    def __init__(
        self,
        *,
        planner_version: str | None,
        plans_by_language: dict[str, dict[str, PlanDescriptor]],
    ) -> None:
        self._planner_version = planner_version
        self._plans_by_language = plans_by_language

    @property
    def planner_version(self) -> str | None:
        return self._planner_version

    def get(self, table_key: str, language: str = "sql") -> PlanDescriptor | None:
        return self._plans_by_language.get(language.lower(), {}).get(table_key)

    def iter_language(self, language: str = "sql") -> Iterator[PlanDescriptor]:
        return iter(self._plans_by_language.get(language.lower(), {}).values())

    def languages(self) -> Iterable[str]:
        return self._plans_by_language.keys()


def load_plan_registry_from_payload(plan_registry: bytes | None) -> GraphSQLPlanRegistry | None:
    """Parse a serialized plan registry payload into runtime descriptors."""

    if not plan_registry:
        return None

    try:
        payload = json.loads(plan_registry.decode("utf-8"))
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive
        logger.warning("Failed to parse GraphSQL plan registry: %s", exc)
        return None
    if not isinstance(payload, dict):
        return None

    planner_version = payload.get("planner_version")
    plans_section = payload.get("plans") or {}
    if not isinstance(plans_section, dict):
        return None
    plans_by_language: dict[str, dict[str, PlanDescriptor]] = {}

    for language, entries in plans_section.items():
        descriptors: dict[str, PlanDescriptor] = {}
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            table_key = entry.get("table_key")
            if not table_key:
                continue
            descriptor = _parse_plan_descriptor(entry)
            descriptors[str(table_key)] = descriptor
        if descriptors:
            plans_by_language[str(language).lower()] = descriptors

    if not plans_by_language:
        return None

    return GraphSQLPlanRegistry(planner_version=planner_version, plans_by_language=plans_by_language)


def load_plan_registry(bundle: Any) -> GraphSQLPlanRegistry | None:
    """Compatibility wrapper for EnvironmentBundle-like objects."""

    return load_plan_registry_from_payload(getattr(bundle, "plan_registry", None))


def _parse_plan_descriptor(entry: dict[str, Any]) -> PlanDescriptor:
    raw_steps = entry.get("steps") or []
    steps_payload = raw_steps if isinstance(raw_steps, list) else []
    steps: tuple[PlanStepDescriptor, ...] = tuple(
        PlanStepDescriptor(
            table_key=str(step.get("table_key") or ""),
            via_relationship_id=(
                str(step["via_relationship_id"]) if step.get("via_relationship_id") is not None else None
            ),
            uses_collection=bool(step.get("uses_collection")),
            join_condition=str(step["join_condition"]) if step.get("join_condition") is not None else None,
            projection_fields=tuple(step.get("projection_fields") or ()),
        )
        for step in steps_payload
        if isinstance(step, dict) and step.get("table_key")
    )

    return PlanDescriptor(
        table_key=str(entry.get("table_key") or ""),
        projection_fields=tuple(entry.get("projection_fields") or ()),
        diagnostics=tuple(entry.get("diagnostics") or ()),
        plan_hash=str(entry["plan_hash"]) if entry.get("plan_hash") is not None else None,
        steps=steps,
    )


def build_graph_config_registry(
    bundle: Any | None = None,
    plan_registry: GraphSQLPlanRegistry | None = None,
) -> GraphConfigRegistry | None:
    """Build a GraphConfigRegistry derived from plan registry descriptors."""

    registry = plan_registry or (load_plan_registry(bundle) if bundle is not None else None)
    if registry is None:
        return None

    descriptors: list[TableDescriptor] = []
    for descriptor in registry.iter_language("sql"):
        if "." not in descriptor.table_key:
            continue
        schema, table = descriptor.table_key.split(".", 1)
        metadata = get_sql_metadata_for_table(descriptor.table_key)
        if metadata:
            class_config_id = metadata.class_config_id
            columns: list[str] = []
            seen: set[str] = set()
            for col in (metadata.column_by_attribute or {}).values():
                if not col:
                    continue
                key = str(col)
                if key in seen:
                    continue
                seen.add(key)
                columns.append(key)
            attributes = tuple(columns) or descriptor.projection_fields
        else:
            class_config_id = UUID(int=0)
            attributes = descriptor.projection_fields
        descriptors.append(
            TableDescriptor(
                class_config_id=class_config_id,
                table_schema=schema,
                table_name=table,
                attributes=attributes,
            )
        )

    if not descriptors:
        logger.debug("GraphSQL plan registry had no descriptors")
        return None

    return GraphConfigRegistry(descriptors)
