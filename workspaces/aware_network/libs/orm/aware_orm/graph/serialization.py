"""Serialization helpers for GraphPlan bundles."""

from __future__ import annotations

import hashlib
from typing import Iterable, cast
from uuid import UUID

import msgpack

from .plan_cache import GraphPlan, PlanStep


BUNDLE_VERSION = 1


def plan_to_dict(plan: GraphPlan) -> dict:
    return {
        "root_table_key": plan.root_table_key,
        "steps": [
            {
                "table_key": step.table_key,
                "relationship_id": (str(step.via_relationship_id) if step.via_relationship_id else None),
                "uses_collection": step.uses_collection,
                "join_condition": step.join_condition,
                "projection_fields": list(step.projection_fields),
                "parent_table_key": step.parent_table_key,
                "depth": step.depth,
            }
            for step in plan.steps
        ],
        "diagnostics": list(plan.diagnostics),
        "root_projection_fields": list(plan.root_projection_fields),
    }


def dict_to_plan(payload: dict) -> GraphPlan:
    steps = []
    for step_payload in payload.get("steps", []):
        relationship_id = step_payload.get("relationship_id")
        steps.append(
            PlanStep(
                table_key=step_payload["table_key"],
                via_relationship_id=(None if relationship_id is None else UUID(relationship_id)),
                uses_collection=step_payload.get("uses_collection", False),
                join_condition=step_payload.get("join_condition"),
                projection_fields=tuple(step_payload.get("projection_fields", [])),
                parent_table_key=step_payload.get("parent_table_key"),
                depth=int(step_payload.get("depth", 1)),
            )
        )
    return GraphPlan(
        root_table_key=payload["root_table_key"],
        steps=tuple(steps),
        diagnostics=tuple(payload.get("diagnostics", [])),
        root_projection_fields=tuple(payload.get("root_projection_fields", [])),
    )


def serialize_plans(plans: Iterable[GraphPlan]) -> bytes:
    bundle = {
        "version": BUNDLE_VERSION,
        "plans": [plan_to_dict(plan) for plan in plans],
    }
    return cast(bytes, msgpack.packb(bundle, use_bin_type=True))


def deserialize_plans(payload: bytes) -> list[GraphPlan]:
    bundle = msgpack.unpackb(payload, raw=False)
    if bundle.get("version") != BUNDLE_VERSION:
        raise ValueError(f"Unsupported GraphSQL plan bundle version: {bundle.get('version')}")
    return [dict_to_plan(plan) for plan in bundle.get("plans", [])]


def sha256_hex(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()
