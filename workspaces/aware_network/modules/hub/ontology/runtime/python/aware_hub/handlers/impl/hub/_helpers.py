from __future__ import annotations

from typing import Any, Iterable, TypeVar
from uuid import UUID

from aware_code.types import JsonObject
from aware_meta.runtime.handler_context import current_handler_session

T = TypeVar("T")


def clean_required(value: str | None, field_name: str) -> str:
    text = (value or "").strip()
    if not text:
        raise RuntimeError(f"Hub handler requires non-empty {field_name}")
    return text


def clean_optional(value: str | None) -> str | None:
    return (value or "").strip() or None


def enum_value(value: object) -> str:
    return str(getattr(value, "value", value))


def json_object(value: object | None) -> JsonObject:
    return JsonObject(value or {})


def handler_session_or_none() -> Any | None:
    try:
        return current_handler_session()
    except RuntimeError:
        return None


def append_if_missing(items: list[T], item: T) -> None:
    item_id = getattr(item, "id", None)
    if all(getattr(existing, "id", None) != item_id for existing in items):
        items.append(item)


def first_by_id(items: Iterable[T], object_id: UUID) -> T | None:
    for item in items:
        if getattr(item, "id", None) == object_id:
            return item
    return None


def derived_provenance_key(
    *,
    explicit_key: str | None,
    revision_id: str,
    producer_revision_id: str | None,
    source_revision_kind: str | None,
    source_revision_id: str | None,
    materialization_ref: str | None,
    build_ref: str | None,
) -> str:
    explicit = clean_optional(explicit_key)
    if explicit is not None:
        return explicit
    parts = [
        clean_optional(producer_revision_id),
        clean_optional(source_revision_kind),
        clean_optional(source_revision_id),
        clean_optional(materialization_ref),
        clean_optional(build_ref),
    ]
    compact = [part for part in parts if part]
    return "|".join(compact) if compact else clean_required(revision_id, "revision_id")


def receipt_key_for(*, operation: str, artifact_family: str, artifact_key: str, revision_id: str) -> str:
    operation_norm = clean_required(operation, "operation")
    return (
        f"{operation_norm}:"
        f"{clean_required(artifact_family, 'artifact_family')}:"
        f"{clean_required(artifact_key, 'artifact_key')}:"
        f"{clean_required(revision_id, 'revision_id')}"
    )
