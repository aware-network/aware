"""Serialization helpers for ProjectionPlan bundles."""

from __future__ import annotations

import hashlib
from typing import Iterable, Literal, cast
from uuid import UUID

import msgpack

from .plan import (
    ProjectionAssociationPlan,
    ProjectionColumnPlan,
    ProjectionPlan,
    ProjectionTablePlan,
)

BUNDLE_VERSION = 1


def plan_to_dict(plan: ProjectionPlan) -> dict:
    return {
        "projection_hash": plan.projection_hash,
        "opg_name": plan.opg_name,
        "dialect": plan.dialect,
        "tables": [
            {
                "table_key": t.table_key,
                "class_config_id": (str(t.class_config_id) if t.class_config_id else None),
                "primary_key": list(t.primary_key),
                "columns": [
                    {
                        "column_name": c.column_name,
                        "source": c.source,
                        "attribute_config_id": (str(c.attribute_config_id) if c.attribute_config_id else None),
                        "relationship_id": (str(c.relationship_id) if c.relationship_id else None),
                        "direction": c.direction,
                        "sql_type_hint": c.sql_type_hint,
                        "nullable": bool(c.nullable),
                    }
                    for c in t.columns
                ],
            }
            for t in plan.tables
        ],
        "associations": [
            {
                "association_table_key": a.association_table_key,
                "relationship_id": str(a.relationship_id),
                "source_fk_column": a.source_fk_column,
                "target_fk_column": a.target_fk_column,
            }
            for a in plan.associations
        ],
    }


def dict_to_plan(payload: dict) -> ProjectionPlan:
    tables = []
    for t in payload.get("tables", []) or []:
        cols = []
        for c in t.get("columns", []) or []:
            cols.append(
                ProjectionColumnPlan(
                    column_name=c["column_name"],
                    source=c["source"],
                    attribute_config_id=(
                        None if c.get("attribute_config_id") is None else UUID(c["attribute_config_id"])
                    ),
                    relationship_id=(None if c.get("relationship_id") is None else UUID(c["relationship_id"])),
                    direction=c.get("direction"),
                    sql_type_hint=c.get("sql_type_hint"),
                    nullable=bool(c.get("nullable", True)),
                )
            )

        tables.append(
            ProjectionTablePlan(
                table_key=t["table_key"],
                class_config_id=(None if t.get("class_config_id") is None else UUID(t["class_config_id"])),
                primary_key=tuple(t.get("primary_key") or ()),
                columns=tuple(cols),
            )
        )

    associations = []
    for a in payload.get("associations", []) or []:
        associations.append(
            ProjectionAssociationPlan(
                association_table_key=a["association_table_key"],
                relationship_id=UUID(a["relationship_id"]),
                source_fk_column=a["source_fk_column"],
                target_fk_column=a["target_fk_column"],
            )
        )

    dialect: Literal["sqlite", "postgres"] = payload["dialect"]
    return ProjectionPlan(
        projection_hash=payload["projection_hash"],
        opg_name=payload.get("opg_name") or "",
        dialect=dialect,
        tables=tuple(tables),
        associations=tuple(associations),
    )


def serialize_projection_plans(plans: Iterable[ProjectionPlan]) -> bytes:
    bundle = {
        "version": BUNDLE_VERSION,
        "plans": [plan_to_dict(plan) for plan in plans],
    }
    return cast(bytes, msgpack.packb(bundle, use_bin_type=True))


def deserialize_projection_plans(payload: bytes) -> list[ProjectionPlan]:
    bundle = msgpack.unpackb(payload, raw=False)
    if bundle.get("version") != BUNDLE_VERSION:
        raise ValueError(f"Unsupported ProjectionPlan bundle version: {bundle.get('version')}")
    return [dict_to_plan(plan) for plan in bundle.get("plans", [])]


def sha256_hex(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


__all__ = [
    "BUNDLE_VERSION",
    "deserialize_projection_plans",
    "dict_to_plan",
    "plan_to_dict",
    "serialize_projection_plans",
    "sha256_hex",
]
