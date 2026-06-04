from __future__ import annotations

import json

import pytest

from aware_orm.runtime.plan_registry import (
    GraphSQLPlanRegistry,
    build_graph_config_registry,
    load_plan_registry_from_payload,
)


@pytest.fixture
def plan_registry_payload() -> bytes:
    """Make a plan registry payload."""
    payload = {
        "version": "1.1.0",
        "planner_version": "deadbeef",
        "plans": {
            "sql": [
                {
                    "table_key": "public.orders",
                    "projection_fields": ["id", "status"],
                    "diagnostics": [],
                    "plan_hash": "abcd1234",
                    "steps": [
                        {
                            "table_key": "public.customers",
                            "via_relationship_id": "11111111-1111-1111-1111-111111111111",
                            "uses_collection": False,
                            "join_condition": "orders.customer_id = customers.id",
                            "projection_fields": ["id"],
                        }
                    ],
                }
            ]
        },
    }
    return json.dumps(payload).encode("utf-8")


def test_load_plan_registry_parses_descriptors(plan_registry_payload: bytes) -> None:
    registry = load_plan_registry_from_payload(plan_registry_payload)
    assert isinstance(registry, GraphSQLPlanRegistry)
    assert registry.planner_version == "deadbeef"

    descriptor = registry.get("public.orders")
    assert descriptor is not None
    assert descriptor.plan_hash == "abcd1234"
    assert descriptor.projection_fields == ("id", "status")
    assert descriptor.steps and descriptor.steps[0].table_key == "public.customers"


def test_build_graph_config_registry_uses_projection_fields(
    monkeypatch: pytest.MonkeyPatch, plan_registry_payload: bytes
) -> None:
    registry = load_plan_registry_from_payload(plan_registry_payload)
    assert registry is not None

    # Ensure SQL metadata lookup returns None so we fall back to projection fields
    monkeypatch.setattr(
        "aware_orm.runtime.plan_registry.get_sql_metadata_for_table",
        lambda _: None,
    )

    config_registry = build_graph_config_registry(plan_registry=registry)
    assert config_registry is not None

    descriptor = config_registry.require("public.orders")
    assert descriptor.table_schema == "public"
    assert descriptor.table_name == "orders"
    assert descriptor.attributes == ("id", "status")
