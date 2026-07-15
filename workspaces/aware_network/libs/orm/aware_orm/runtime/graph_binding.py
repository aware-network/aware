"""SSOT: ORM graph artifact binding core."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

import msgpack

from aware_orm._support import logger
from aware_orm.models.base_model import BaseORMModel
from aware_orm.runtime.graph_artifacts import OrmEntitySpec, OrmGraphBindingSnapshot


@dataclass(slots=True)
class CanonicalBindResult:
    bound_count: int
    missing_classes: list[str]
    missing_entities: list[str]


def _canonicalize_for_msgpack(value: Any) -> Any:
    """Canonicalize a JSON-friendly payload for deterministic msgpack bytes."""
    if isinstance(value, dict):
        def _k(k: Any) -> tuple[str, str]:
            return (type(k).__name__, str(k))

        return {k: _canonicalize_for_msgpack(value[k]) for k in sorted(value.keys(), key=_k)}
    if isinstance(value, list):
        return [_canonicalize_for_msgpack(v) for v in value]
    return value


def _token(value: Any) -> str:
    raw = getattr(value, "value", value)
    return str(raw).rsplit(".", 1)[-1].lower()


def dump_orm_graph_binding_snapshot_msgpack(*, snapshot: OrmGraphBindingSnapshot) -> bytes:
    """Dump an ORM-native graph binding snapshot to deterministic msgpack bytes."""

    normalized = snapshot.model_copy(deep=True)
    normalized.entities.sort(key=lambda entity: str(entity.id))
    for entity in normalized.entities:
        entity.field_bindings.sort(
            key=lambda link: (
                link.position if link.position is not None else 10**9,
                str(link.binding_role or ""),
                str(link.field_id or ""),
                str(link.id or ""),
            )
        )
        entity.function_bindings.sort(
            key=lambda link: (
                link.position if link.position is not None else 10**9,
                str(link.function_id or ""),
                str(link.id or ""),
            )
        )
        for function_link in entity.function_bindings:
            if function_link.function is not None:
                function_link.function.field_bindings.sort(
                    key=lambda link: (
                        link.position if link.position is not None else 10**9,
                        str(link.binding_role or ""),
                        str(link.field_id or ""),
                        str(link.id or ""),
                    )
                )
        entity.relationships.sort(
            key=lambda rel: (
                str(rel.relationship_type),
                str(rel.target_entity_id),
                str(rel.id),
            )
        )
        for rel in entity.relationships:
            rel.fields.sort(
                key=lambda field: (
                    str(field.direction),
                    str(field.role),
                    str(field.field_id),
                    str(field.id),
                )
            )

    payload = normalized.model_dump(mode="json", exclude_none=True)
    payload = _canonicalize_for_msgpack(payload)
    packed = msgpack.packb(payload, use_bin_type=True)
    if not isinstance(packed, (bytes, bytearray)):
        raise TypeError("msgpack.packb returned non-bytes payload")
    return bytes(packed)


def index_entities_from_msgpack(graph_binding_bytes: bytes) -> dict[str, OrmEntitySpec]:
    """Index ORM entity specs by id from a package graph binding snapshot."""

    payload: Any = msgpack.unpackb(graph_binding_bytes, raw=False)
    if not isinstance(payload, dict):
        raise TypeError("ORM graph binding snapshot must be an object")

    snapshot = OrmGraphBindingSnapshot.model_validate(payload)
    entity_index: dict[str, OrmEntitySpec] = {}
    for entity in snapshot.entities:
        if entity.id is None:
            continue
        entity_index[str(entity.id)] = entity
    return entity_index


def bind_entities_by_fqn(
    *,
    bindings: Iterable[tuple[str, str]],
    entity_index: dict[str, OrmEntitySpec],
    strict: bool,
) -> CanonicalBindResult:
    """Bind ORM entity specs to model classes by `(class_fqn, entity_id)`."""
    from aware_orm.registry import ORMModelRegistry

    bound = 0
    missing_classes: list[str] = []
    missing_entities: list[str] = []

    for class_fqn, entity_id in bindings:
        entity = entity_index.get(entity_id)
        if entity is None:
            missing_entities.append(entity_id)
            continue

        if _token(getattr(entity, "value_mode", "")) == "inline_value":
            continue

        model_class = ORMModelRegistry.get_class_by_fqn(class_fqn)
        if model_class is None or not issubclass(model_class, BaseORMModel):
            missing_classes.append(class_fqn)
            continue

        entity = _entity_with_existing_runtime_function_bindings(
            entity=entity,
            existing_entity=model_class.get_class_config(),
        )

        model_class.bind_class_config(entity)
        ORMModelRegistry.attach_class_config(class_fqn, entity)
        bound += 1

    if strict and missing_classes:
        raise RuntimeError(f"Missing Python classes for canonical binding: {missing_classes}")
    if strict and missing_entities:
        raise RuntimeError(f"Missing ORM entities for canonical binding: {missing_entities}")

    ORMModelRegistry.set_initialized()
    return CanonicalBindResult(
        bound_count=bound,
        missing_classes=missing_classes,
        missing_entities=missing_entities,
    )


def _entity_with_existing_runtime_function_bindings(
    *,
    entity: OrmEntitySpec,
    existing_entity: Any | None,
) -> OrmEntitySpec:
    if existing_entity is None:
        return entity

    existing_functions = getattr(existing_entity, "class_config_function_configs", None)
    if not existing_functions:
        return entity

    existing_by_id = {
        getattr(link, "function_config_id", None): link
        for link in existing_functions
        if getattr(link, "function_config_id", None) is not None
    }
    current_ids = {
        getattr(link, "function_config_id", None)
        for link in entity.function_bindings
        if getattr(link, "function_config_id", None) is not None
    }
    for function_id, link in existing_by_id.items():
        if function_id in current_ids:
            continue
        try:
            entity.function_bindings.append(link)
        except Exception as exc:
            logger.debug("Skipping stale runtime function binding merge: %s", exc)
    return entity


__all__ = [
    "CanonicalBindResult",
    "bind_entities_by_fqn",
    "dump_orm_graph_binding_snapshot_msgpack",
    "index_entities_from_msgpack",
]
