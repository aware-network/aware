from __future__ import annotations

from datetime import datetime
from typing import cast
from uuid import UUID

from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType
from aware_meta_ontology.attribute.attribute_enums import AttributeCollectionType
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
    AttributeTypeDescriptorRole,
)

from aware_meta.graph.instance.commit.contract import (
    JsonObject,
    ObjectInstanceGraphCommitGraphHashSource,
)
from aware_meta.graph.instance.commit.fs_backend import _coerce_json_object


def _json_optional_string(payload: JsonObject, key: str) -> str | None:
    value = payload.get(key)
    if isinstance(value, str):
        return value
    return None


def _json_graph_hash_source(
    payload: JsonObject,
) -> ObjectInstanceGraphCommitGraphHashSource:
    value = _json_optional_string(payload, "graph_hash_source") or "state_hash"
    if value not in ("state_hash", "witness_hash", "witness_cursor_hash"):
        raise ValueError(f"Unsupported graph_hash_source: {value!r}")
    return cast(ObjectInstanceGraphCommitGraphHashSource, value)


def _json_optional_uuid(payload: JsonObject, key: str) -> UUID | None:
    value = _json_optional_string(payload, key)
    if value is None:
        return None
    return UUID(value)


def _json_optional_int(payload: JsonObject, key: str) -> int | None:
    value = payload.get(key)
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    return None


def _json_required_int(payload: JsonObject, key: str) -> int:
    value = _json_optional_int(payload, key)
    if value is None:
        raise ValueError(f"Missing required JSON integer: {key}")
    return value


def _json_optional_object(payload: JsonObject, key: str) -> JsonObject | None:
    value = payload.get(key)
    if value is None:
        return None
    if isinstance(value, dict):
        return cast(JsonObject, value)
    raise ValueError(f"Expected optional JSON object: {key}")


def _json_required_list(payload: JsonObject, key: str) -> list[object]:
    value = payload.get(key)
    if not isinstance(value, list):
        raise ValueError(f"Missing required JSON list: {key}")
    return value


def _json_required_attribute_type_descriptor_kind(
    payload: JsonObject,
    key: str,
) -> AttributeTypeDescriptorKind:
    return AttributeTypeDescriptorKind(_json_required_string(payload, key))


def _json_required_attribute_type_descriptor_role(
    payload: JsonObject,
    key: str,
) -> AttributeTypeDescriptorRole:
    return AttributeTypeDescriptorRole(_json_required_string(payload, key))


def _json_optional_attribute_collection_type(
    payload: JsonObject,
    key: str,
) -> AttributeCollectionType | None:
    value = _json_optional_string(payload, key)
    return AttributeCollectionType(value) if value is not None else None


def _json_required_code_primitive_base_type(
    payload: JsonObject,
    key: str,
) -> CodePrimitiveBaseType:
    return CodePrimitiveBaseType(_json_required_string(payload, key))


def _json_required_string(payload: JsonObject, key: str) -> str:
    value = _json_optional_string(payload, key)
    if value is None:
        raise ValueError(f"Missing required JSON string: {key}")
    return value


def _json_required_uuid(payload: JsonObject, key: str) -> UUID:
    value = _json_optional_uuid(payload, key)
    if value is None:
        raise ValueError(f"Missing required JSON UUID: {key}")
    return value


def _json_required_datetime(payload: JsonObject, key: str) -> datetime:
    value = _json_required_string(payload, key)
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    return datetime.fromisoformat(normalized)


def _json_mapping(payload: JsonObject, key: str) -> JsonObject:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"Missing required JSON object: {key}")
    return _coerce_json_object(
        value,
        error_message=f"Invalid JSON object for key: {key}",
    )


def _enum_json_value(value: object) -> str:
    raw_value = getattr(value, "value", value)
    return str(raw_value)


def _datetime_json_value(value: datetime) -> str:
    text = value.isoformat()
    return text[:-6] + "Z" if text.endswith("+00:00") else text
