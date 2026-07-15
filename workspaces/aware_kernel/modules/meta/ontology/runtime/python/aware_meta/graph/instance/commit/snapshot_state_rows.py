from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
from typing import Literal, cast
from uuid import UUID

from aware_code_ontology.primitive.code_primitive_type import CodePrimitiveType
from aware_meta_ontology.attribute.attribute import Attribute
from aware_meta_ontology.attribute.attribute_enums import AttributeCollectionType
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_value import AttributeValue
from aware_meta_ontology.attribute.attribute_value_link import AttributeValueLink
from aware_meta_ontology.class_.class_instance import ClassInstance
from aware_meta_ontology.class_.class_instance_attribute import ClassInstanceAttribute
from aware_meta_ontology.class_.class_instance_relationship import (
    ClassInstanceRelationship,
)
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta_ontology.enum.enum_option import EnumOption
from aware_meta_ontology.primitive.primitive_config import PrimitiveConfig

from aware_meta.graph.instance.commit.contract import JsonObject
from aware_meta.graph.instance.commit.fs_backend import _coerce_json_object_view
from aware_meta.graph.instance.commit.fs_session_cache import _SnapshotStateRowsRead
from aware_meta.graph.instance.commit.json_payload import (
    _datetime_json_value,
    _enum_json_value,
    _json_mapping,
    _json_optional_attribute_collection_type,
    _json_optional_int,
    _json_optional_object,
    _json_optional_string,
    _json_optional_uuid,
    _json_required_attribute_type_descriptor_kind,
    _json_required_attribute_type_descriptor_role,
    _json_required_code_primitive_base_type,
    _json_required_list,
    _json_required_string,
    _json_required_uuid,
)
from aware_meta.graph.instance.commit.state_index import (
    CommitStateRow,
    CommitStateRowMaps,
)


OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_ROWS_PAYLOAD_HASH_ALGORITHM = "sha256"


@dataclass(frozen=True, slots=True)
class ObjectInstanceGraphSnapshotStateSelection:
    payload: JsonObject
    state_rows: tuple[CommitStateRow, ...]
    class_instances_by_id: Mapping[UUID, ClassInstance]
    state_row_maps: CommitStateRowMaps | None = None


def _snapshot_state_json_value(value: object) -> object:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return _datetime_json_value(value)
    if isinstance(value, list):
        return [_snapshot_state_json_value(item) for item in value]
    if isinstance(value, tuple):
        return [_snapshot_state_json_value(item) for item in value]
    if isinstance(value, dict):
        return {
            str(key): _snapshot_state_json_value(item)
            for key, item in value.items()
            if isinstance(key, str)
        }
    return value


def _snapshot_state_uuid_value(value: object, *, field_name: str) -> str:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, str) and value:
        return value
    raise ValueError(f"Missing required snapshot UUID field: {field_name}")


def _snapshot_state_optional_uuid_value(value: object) -> str | None:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, str) and value:
        return value
    return None


def _snapshot_state_payload_without_none(
    payload: Mapping[str, object | None],
) -> JsonObject:
    return {
        key: _snapshot_state_json_value(value)
        for key, value in payload.items()
        if value is not None
    }


def _attribute_value_snapshot_state_payload(value: object) -> JsonObject:
    child_links = [
        _attribute_value_link_snapshot_state_payload(link)
        for link in (getattr(value, "child_links", None) or ())
    ]
    type_descriptor = getattr(value, "type_descriptor", None)
    if type_descriptor is None:
        raise ValueError("Missing required snapshot AttributeValue.type_descriptor")
    payload = _snapshot_state_payload_without_none(
        {
            "id": _snapshot_state_optional_uuid_value(getattr(value, "id", None)),
            "type_descriptor": _attribute_type_descriptor_snapshot_state_payload(
                type_descriptor
            ),
            "type_descriptor_id": _snapshot_state_uuid_value(
                getattr(value, "type_descriptor_id", None),
                field_name="type_descriptor_id",
            ),
            "enum_option_id": _snapshot_state_optional_uuid_value(
                getattr(value, "enum_option_id", None)
            ),
            "class_instance_id": _snapshot_state_optional_uuid_value(
                getattr(value, "class_instance_id", None)
            ),
            "inline_value_instance_id": _snapshot_state_optional_uuid_value(
                getattr(value, "inline_value_instance_id", None)
            ),
            "primitive_value": _snapshot_state_json_value(
                getattr(value, "primitive_value", None)
            ),
        }
    )
    payload["child_links"] = child_links
    return payload


def _attribute_value_link_snapshot_state_payload(link: object) -> JsonObject:
    child = getattr(link, "child", None)
    if child is None:
        raise ValueError("Missing required snapshot AttributeValueLink.child")
    return _snapshot_state_payload_without_none(
        {
            "id": _snapshot_state_optional_uuid_value(getattr(link, "id", None)),
            "child": _attribute_value_snapshot_state_payload(child),
            "role": _enum_json_value(getattr(link, "role", None)),
            "position": getattr(link, "position", None),
            "identity_key": getattr(link, "identity_key", None),
            "attribute_value_id": _snapshot_state_uuid_value(
                getattr(link, "attribute_value_id", None),
                field_name="attribute_value_id",
            ),
            "child_id": _snapshot_state_optional_uuid_value(
                getattr(link, "child_id", None)
            ),
        }
    )


def _attribute_type_descriptor_snapshot_state_payload(descriptor: object) -> JsonObject:
    kind = getattr(descriptor, "kind", None)
    if kind is None:
        raise ValueError("Missing required snapshot AttributeTypeDescriptor.kind")
    collection_kind = getattr(descriptor, "collection_kind", None)
    return _snapshot_state_payload_without_none(
        {
            "id": _snapshot_state_optional_uuid_value(getattr(descriptor, "id", None)),
            "collection_kind": (
                None if collection_kind is None else _enum_json_value(collection_kind)
            ),
            "kind": _enum_json_value(kind),
            "class_config_id": _snapshot_state_optional_uuid_value(
                getattr(descriptor, "class_config_id", None)
            ),
            "enum_config_id": _snapshot_state_optional_uuid_value(
                getattr(descriptor, "enum_config_id", None)
            ),
            "primitive_config_id": _snapshot_state_optional_uuid_value(
                getattr(descriptor, "primitive_config_id", None)
            ),
        }
    )


def _attribute_snapshot_state_payload(attribute: object) -> JsonObject:
    value_root = getattr(attribute, "value_root", None)
    if value_root is None:
        raise ValueError("Missing required snapshot Attribute.value_root")
    return _snapshot_state_payload_without_none(
        {
            "id": _snapshot_state_optional_uuid_value(getattr(attribute, "id", None)),
            "value_root": _attribute_value_snapshot_state_payload(value_root),
            "owner_key": getattr(attribute, "owner_key", None),
            "attribute_config_id": _snapshot_state_uuid_value(
                getattr(attribute, "attribute_config_id", None),
                field_name="attribute_config_id",
            ),
            "value_root_id": _snapshot_state_optional_uuid_value(
                getattr(attribute, "value_root_id", None)
            ),
        }
    )


def _class_instance_attribute_snapshot_state_payload(link: object) -> JsonObject:
    attribute = getattr(link, "attribute", None)
    if attribute is None:
        raise ValueError("Missing required snapshot ClassInstanceAttribute.attribute")
    return _snapshot_state_payload_without_none(
        {
            "id": _snapshot_state_optional_uuid_value(getattr(link, "id", None)),
            "attribute": _attribute_snapshot_state_payload(attribute),
            "attribute_id": _snapshot_state_optional_uuid_value(
                getattr(link, "attribute_id", None)
            ),
            "class_instance_id": _snapshot_state_uuid_value(
                getattr(link, "class_instance_id", None),
                field_name="class_instance_id",
            ),
        }
    )


def _class_instance_snapshot_state_payload(
    class_instance: ClassInstance,
) -> JsonObject:
    return _snapshot_state_payload_without_none(
        {
            "id": _snapshot_state_optional_uuid_value(
                getattr(class_instance, "id", None)
            ),
            "source_object_id": _snapshot_state_uuid_value(
                getattr(class_instance, "source_object_id", None),
                field_name="source_object_id",
            ),
            "object_instance_graph_id": _snapshot_state_uuid_value(
                getattr(class_instance, "object_instance_graph_id", None),
                field_name="object_instance_graph_id",
            ),
            "class_config_id": _snapshot_state_uuid_value(
                getattr(class_instance, "class_config_id", None),
                field_name="class_config_id",
            ),
            "class_instance_attributes": [
                _class_instance_attribute_snapshot_state_payload(link)
                for link in (
                    getattr(class_instance, "class_instance_attributes", None) or ()
                )
            ],
        }
    )


def _class_instance_relationship_snapshot_state_payload(
    relationship: ClassInstanceRelationship,
) -> JsonObject:
    return _snapshot_state_payload_without_none(
        {
            "id": _snapshot_state_optional_uuid_value(
                getattr(relationship, "id", None)
            ),
            "object_instance_graph_id": _snapshot_state_uuid_value(
                getattr(relationship, "object_instance_graph_id", None),
                field_name="object_instance_graph_id",
            ),
            "class_config_relationship_id": _snapshot_state_uuid_value(
                getattr(relationship, "class_config_relationship_id", None),
                field_name="class_config_relationship_id",
            ),
            "class_instance_relationship_identity_id": (
                _snapshot_state_optional_uuid_value(
                    getattr(
                        relationship,
                        "class_instance_relationship_identity_id",
                        None,
                    )
                )
            ),
            "source_class_instance_id": _snapshot_state_uuid_value(
                getattr(relationship, "source_class_instance_id", None),
                field_name="source_class_instance_id",
            ),
            "target_class_instance_id": _snapshot_state_uuid_value(
                getattr(relationship, "target_class_instance_id", None),
                field_name="target_class_instance_id",
            ),
        }
    )


def _trusted_class_instance_from_snapshot_state_payload(
    payload: object,
) -> ClassInstance:
    class_instance_payload = _coerce_json_object_view(
        payload,
        error_message="ClassInstance state snapshot payload must be a JSON object",
    )
    attributes_payload = _json_required_list(
        class_instance_payload,
        "class_instance_attributes",
    )
    return ClassInstance.model_construct(
        id=_json_optional_uuid(class_instance_payload, "id"),
        source_object_id=_json_required_uuid(
            class_instance_payload,
            "source_object_id",
        ),
        object_instance_graph_id=_json_required_uuid(
            class_instance_payload,
            "object_instance_graph_id",
        ),
        class_config_id=_json_required_uuid(class_instance_payload, "class_config_id"),
        class_config=None,
        class_instance_changes=[],
        class_instance_attributes=[
            _trusted_class_instance_attribute_from_snapshot_state_payload(item)
            for item in attributes_payload
        ],
    )


def _trusted_class_instance_attribute_from_snapshot_state_payload(
    payload: object,
) -> ClassInstanceAttribute:
    link_payload = _coerce_json_object_view(
        payload,
        error_message=(
            "ClassInstanceAttribute state snapshot payload must be a JSON object"
        ),
    )
    attribute = _trusted_attribute_from_snapshot_state_payload(
        _json_mapping(link_payload, "attribute")
    )
    return ClassInstanceAttribute.model_construct(
        id=_json_optional_uuid(link_payload, "id"),
        attribute=attribute,
        attribute_id=_json_optional_uuid(link_payload, "attribute_id"),
        class_instance_id=_json_required_uuid(link_payload, "class_instance_id"),
    )


def _trusted_attribute_from_snapshot_state_payload(payload: object) -> Attribute:
    attribute_payload = _coerce_json_object_view(
        payload,
        error_message="Attribute state snapshot payload must be a JSON object",
    )
    value_root = _trusted_attribute_value_from_snapshot_state_payload(
        _json_mapping(attribute_payload, "value_root")
    )
    return Attribute.model_construct(
        id=_json_optional_uuid(attribute_payload, "id"),
        attribute_config=None,
        attribute_changes=[],
        value_root=value_root,
        owner_key=_json_required_uuid(attribute_payload, "owner_key"),
        attribute_config_id=_json_required_uuid(
            attribute_payload,
            "attribute_config_id",
        ),
        value_root_id=_json_optional_uuid(attribute_payload, "value_root_id"),
    )


def _trusted_attribute_value_from_snapshot_state_payload(
    payload: object,
) -> AttributeValue:
    value_payload = _coerce_json_object_view(
        payload,
        error_message="AttributeValue state snapshot payload must be a JSON object",
    )
    type_descriptor = _trusted_attribute_type_descriptor_from_snapshot_state_payload(
        _json_mapping(value_payload, "type_descriptor")
    )
    child_links_payload = _json_required_list(value_payload, "child_links")
    primitive_value = value_payload.get("primitive_value")
    if primitive_value is not None and not isinstance(primitive_value, dict):
        raise ValueError("AttributeValue primitive_value must be a JSON object")
    return AttributeValue.model_construct(
        id=_json_optional_uuid(value_payload, "id"),
        attribute_value_changes=[],
        type_descriptor=type_descriptor,
        child_links=[
            _trusted_attribute_value_link_from_snapshot_state_payload(item)
            for item in child_links_payload
        ],
        enum_option=None,
        class_instance=None,
        inline_value_instance=None,
        primitive_value=cast(JsonObject | None, primitive_value),
        type_descriptor_id=_json_required_uuid(value_payload, "type_descriptor_id"),
        enum_option_id=_json_optional_uuid(value_payload, "enum_option_id"),
        class_instance_id=_json_optional_uuid(value_payload, "class_instance_id"),
        inline_value_instance_id=_json_optional_uuid(
            value_payload,
            "inline_value_instance_id",
        ),
    )


def _trusted_attribute_value_link_from_snapshot_state_payload(
    payload: object,
) -> AttributeValueLink:
    link_payload = _coerce_json_object_view(
        payload,
        error_message="AttributeValueLink state snapshot payload must be a JSON object",
    )
    child = _trusted_attribute_value_from_snapshot_state_payload(
        _json_mapping(link_payload, "child")
    )
    return AttributeValueLink.model_construct(
        id=_json_optional_uuid(link_payload, "id"),
        attribute_value_link_changes=[],
        child=child,
        role=_json_required_attribute_type_descriptor_role(link_payload, "role"),
        position=_json_optional_int(link_payload, "position"),
        identity_key=_json_optional_string(link_payload, "identity_key"),
        attribute_value_id=_json_required_uuid(link_payload, "attribute_value_id"),
        child_id=_json_optional_uuid(link_payload, "child_id"),
    )


def _trusted_attribute_type_descriptor_from_snapshot_state_payload(
    payload: object,
) -> AttributeTypeDescriptor:
    descriptor_payload = _coerce_json_object_view(
        payload,
        error_message=(
            "AttributeTypeDescriptor state snapshot payload must be a JSON object"
        ),
    )
    collection_kind = _json_optional_attribute_collection_type(
        descriptor_payload,
        "collection_kind",
    )
    primitive_config_payload = descriptor_payload.get("primitive_config")
    primitive_config = (
        _trusted_primitive_config_from_snapshot_state_payload(primitive_config_payload)
        if primitive_config_payload is not None
        else None
    )
    enum_config_payload = descriptor_payload.get("enum_config")
    enum_config_id = _json_optional_uuid(descriptor_payload, "enum_config_id")
    enum_config = (
        _trusted_enum_config_from_snapshot_state_payload(enum_config_payload)
        if enum_config_payload is not None
        else _trusted_enum_config_stub(enum_config_id)
    )
    return AttributeTypeDescriptor.model_construct(
        id=_json_optional_uuid(descriptor_payload, "id"),
        class_config=None,
        enum_config=enum_config,
        primitive_config=primitive_config,
        child_links=[],
        collection_kind=collection_kind or AttributeCollectionType.single,
        kind=_json_required_attribute_type_descriptor_kind(descriptor_payload, "kind"),
        class_config_id=_json_optional_uuid(descriptor_payload, "class_config_id"),
        enum_config_id=enum_config_id,
        primitive_config_id=_json_optional_uuid(
            descriptor_payload,
            "primitive_config_id",
        ),
    )


def _trusted_enum_config_from_snapshot_state_payload(payload: object) -> EnumConfig:
    enum_payload = _coerce_json_object_view(
        payload,
        error_message="EnumConfig state snapshot payload must be a JSON object",
    )
    return EnumConfig.model_construct(
        id=_json_optional_uuid(enum_payload, "id"),
        enum_options=[
            _trusted_enum_option_from_snapshot_state_payload(item)
            for item in _json_required_list(enum_payload, "enum_options")
        ],
        code_section_enum=None,
        enum_fqn=_json_required_string(enum_payload, "enum_fqn"),
        name=_json_required_string(enum_payload, "name"),
        description=_json_optional_string(enum_payload, "description"),
        object_config_graph_node_id=_json_optional_uuid(
            enum_payload,
            "object_config_graph_node_id",
        ),
        code_section_enum_id=_json_optional_uuid(enum_payload, "code_section_enum_id"),
    )


def _trusted_enum_config_stub(enum_config_id: UUID | None) -> EnumConfig | None:
    if enum_config_id is None:
        return None
    return EnumConfig.model_construct(
        id=enum_config_id,
        enum_options=[],
        code_section_enum=None,
        enum_fqn="",
        name="",
        description=None,
        object_config_graph_node_id=None,
        code_section_enum_id=None,
    )


def _trusted_enum_option_from_snapshot_state_payload(payload: object) -> EnumOption:
    enum_option_payload = _coerce_json_object_view(
        payload,
        error_message="EnumOption state snapshot payload must be a JSON object",
    )
    return EnumOption.model_construct(
        id=_json_optional_uuid(enum_option_payload, "id"),
        value=_json_required_string(enum_option_payload, "value"),
        label=_json_optional_string(enum_option_payload, "label"),
        description=_json_optional_string(enum_option_payload, "description"),
        position=_json_optional_int(enum_option_payload, "position") or 0,
        enum_config_id=_json_required_uuid(enum_option_payload, "enum_config_id"),
    )


def _trusted_primitive_config_from_snapshot_state_payload(
    payload: object,
) -> PrimitiveConfig:
    primitive_config_payload = _coerce_json_object_view(
        payload,
        error_message="PrimitiveConfig state snapshot payload must be a JSON object",
    )
    primitive_type = _trusted_code_primitive_type_from_snapshot_state_payload(
        _json_mapping(primitive_config_payload, "primitive_type")
    )
    return PrimitiveConfig.model_construct(
        id=_json_optional_uuid(primitive_config_payload, "id"),
        primitive_type=primitive_type,
        primitive_type_id=_json_required_uuid(
            primitive_config_payload,
            "primitive_type_id",
        ),
    )


def _trusted_code_primitive_type_from_snapshot_state_payload(
    payload: object,
) -> CodePrimitiveType:
    primitive_type_payload = _coerce_json_object_view(
        payload,
        error_message="CodePrimitiveType state snapshot payload must be a JSON object",
    )
    return CodePrimitiveType.model_construct(
        id=_json_optional_uuid(primitive_type_payload, "id"),
        item_type=_trusted_optional_code_primitive_type_from_snapshot_state_payload(
            primitive_type_payload.get("item_type")
        ),
        key_type=_trusted_optional_code_primitive_type_from_snapshot_state_payload(
            primitive_type_payload.get("key_type")
        ),
        value_type=_trusted_optional_code_primitive_type_from_snapshot_state_payload(
            primitive_type_payload.get("value_type")
        ),
        signature=_json_required_string(primitive_type_payload, "signature"),
        base_type=_json_required_code_primitive_base_type(
            primitive_type_payload,
            "base_type",
        ),
        constraints=_json_optional_object(primitive_type_payload, "constraints"),
        item_type_id=_json_optional_uuid(primitive_type_payload, "item_type_id"),
        key_type_id=_json_optional_uuid(primitive_type_payload, "key_type_id"),
        value_type_id=_json_optional_uuid(primitive_type_payload, "value_type_id"),
        code_primitive_type_element_types=[],
        code_primitive_type_union_types=[],
    )


def _trusted_optional_code_primitive_type_from_snapshot_state_payload(
    payload: object,
) -> CodePrimitiveType | None:
    if payload is None:
        return None
    return _trusted_code_primitive_type_from_snapshot_state_payload(payload)


def _trusted_relationship_from_snapshot_state_payload(
    payload: object,
) -> ClassInstanceRelationship:
    relationship_payload = _coerce_json_object_view(
        payload,
        error_message=(
            "ClassInstanceRelationship state snapshot payload must be a JSON object"
        ),
    )
    return ClassInstanceRelationship.model_construct(
        id=_json_optional_uuid(relationship_payload, "id"),
        class_config_relationship=None,
        class_instance_relationship_identity=None,
        source_class_instance=None,
        target_class_instance=None,
        object_instance_graph_id=_json_required_uuid(
            relationship_payload,
            "object_instance_graph_id",
        ),
        class_config_relationship_id=_json_required_uuid(
            relationship_payload,
            "class_config_relationship_id",
        ),
        class_instance_relationship_identity_id=_json_optional_uuid(
            relationship_payload,
            "class_instance_relationship_identity_id",
        ),
        source_class_instance_id=_json_required_uuid(
            relationship_payload,
            "source_class_instance_id",
        ),
        target_class_instance_id=_json_required_uuid(
            relationship_payload,
            "target_class_instance_id",
        ),
    )


_SNAPSHOT_STATE_ROWS_PAYLOAD_INTEGRITY_KEYS = (
    "v",
    "schema",
    "branch_id",
    "projection_hash",
    "commit_id",
    "object_instance_graph_id",
    "graph_hash",
    "graph",
    "class_instances",
    "class_instance_relationships",
    "state_rows_text",
    "state_hash",
    "node_count",
    "attribute_count",
    "edge_count",
)


def _snapshot_state_rows_payload_hash(payload: JsonObject) -> str:
    return hashlib.sha256(
        _snapshot_state_rows_integrity_json(payload).encode("utf-8"),
    ).hexdigest()


@dataclass(frozen=True, slots=True)
class _SnapshotStateRowsPayloadWrite:
    payload: JsonObject
    data: str


def _snapshot_state_rows_payload_write(
    payload: JsonObject,
) -> _SnapshotStateRowsPayloadWrite:
    payload.pop("payload_hash_algorithm", None)
    payload.pop("payload_sha256", None)
    member_json_by_key = {
        key: _snapshot_state_rows_member_json(key, value)
        for key, value in payload.items()
    }
    integrity_json = _snapshot_state_rows_integrity_json_from_members(
        member_json_by_key,
    )
    payload["payload_hash_algorithm"] = (
        OBJECT_INSTANCE_GRAPH_SNAPSHOT_STATE_ROWS_PAYLOAD_HASH_ALGORITHM
    )
    payload["payload_sha256"] = hashlib.sha256(
        integrity_json.encode("utf-8"),
    ).hexdigest()
    member_json_by_key["payload_hash_algorithm"] = _snapshot_state_rows_member_json(
        "payload_hash_algorithm",
        payload["payload_hash_algorithm"],
    )
    member_json_by_key["payload_sha256"] = _snapshot_state_rows_member_json(
        "payload_sha256",
        payload["payload_sha256"],
    )
    return _SnapshotStateRowsPayloadWrite(
        payload=payload,
        data=_snapshot_state_rows_object_json_from_members(member_json_by_key),
    )


def _snapshot_state_rows_integrity_json(payload: JsonObject) -> str:
    return _snapshot_state_rows_integrity_json_from_members(
        {
            key: _snapshot_state_rows_member_json(key, payload[key])
            for key in _SNAPSHOT_STATE_ROWS_PAYLOAD_INTEGRITY_KEYS
            if key in payload
        },
    )


def _snapshot_state_rows_integrity_json_from_members(
    member_json_by_key: Mapping[str, str],
) -> str:
    return _snapshot_state_rows_object_json_from_members(
        {
            key: member_json_by_key[key]
            for key in _SNAPSHOT_STATE_ROWS_PAYLOAD_INTEGRITY_KEYS
            if key in member_json_by_key
        },
    )


def _snapshot_state_rows_object_json_from_members(
    member_json_by_key: Mapping[str, str],
) -> str:
    return (
        "{"
        + ",".join(member_json_by_key[key] for key in sorted(member_json_by_key))
        + "}"
    )


def _snapshot_state_rows_member_json(key: str, value: object) -> str:
    return (
        json.dumps(key, separators=(",", ":"), sort_keys=True)
        + ":"
        + json.dumps(value, separators=(",", ":"), sort_keys=True)
    )


def _commit_state_rows_read_from_snapshot_payload(
    payload: JsonObject,
    *,
    include_state_row_maps: bool = False,
) -> _SnapshotStateRowsRead | None:
    rows_payload = payload.get("state_rows_text")
    if not isinstance(rows_payload, str):
        return None
    text_read = _commit_state_rows_read_from_text(
        rows_payload,
        include_state_row_maps=include_state_row_maps,
    )
    if text_read is None:
        return None
    state_rows, state_row_maps = text_read
    return _SnapshotStateRowsRead(
        payload=payload,
        state_rows=state_rows,
        state_row_maps=state_row_maps,
    )


def _commit_state_rows_read_from_text(
    rows_payload: str,
    *,
    include_state_row_maps: bool = False,
) -> tuple[tuple[CommitStateRow, ...], CommitStateRowMaps | None] | None:
    rows: list[CommitStateRow] = []
    class_config_ids_by_raw_id: dict[str, UUID] = {}
    class_state_row_lists_by_raw_id: dict[str, list[CommitStateRow]] = {}
    relationship_keys: set[tuple[UUID, UUID, UUID]] = set()
    for item in rows_payload.splitlines():
        if not item:
            return None
        parts = item.split("\t")
        if len(parts) != 3:
            return None
        raw_kind, raw_key, raw_value = parts
        if raw_kind not in {"NODE", "ATTR", "EDGE"}:
            return None
        if not raw_key or not raw_value:
            return None
        if "\n" in raw_key or "\r" in raw_key or "\n" in raw_value or "\r" in raw_value:
            return None
        rows.append(
            row := CommitStateRow(
                kind=cast(Literal["NODE", "ATTR", "EDGE"], raw_kind),
                key=raw_key,
                value=raw_value,
            )
        )
        if not include_state_row_maps:
            continue
        if row.kind == "NODE":
            try:
                class_config_id = UUID(row.key)
                class_instance_id = UUID(row.value)
            except Exception:
                return None
            raw_class_instance_id = str(class_instance_id)
            previous_class_config_id = class_config_ids_by_raw_id.get(
                raw_class_instance_id,
            )
            if (
                previous_class_config_id is not None
                and previous_class_config_id != class_config_id
            ):
                return None
            class_config_ids_by_raw_id[raw_class_instance_id] = class_config_id
            class_state_row_lists_by_raw_id.setdefault(
                raw_class_instance_id,
                [],
            ).append(row)
            continue
        if row.kind == "ATTR":
            class_state_row_lists_by_raw_id.setdefault(row.key, []).append(row)
            continue
        if row.kind == "EDGE":
            raw_source_id, separator, raw_target_id = row.value.partition("->")
            if not separator:
                return None
            try:
                relationship_keys.add(
                    (UUID(row.key), UUID(raw_source_id), UUID(raw_target_id)),
                )
            except Exception:
                return None

    state_rows = tuple(rows)
    state_row_maps: CommitStateRowMaps | None = None
    if include_state_row_maps:
        class_state_rows_by_raw_id = {
            class_instance_id: tuple(member_rows)
            for class_instance_id, member_rows in (
                class_state_row_lists_by_raw_id.items()
            )
        }
        try:
            state_row_maps = CommitStateRowMaps(
                class_config_ids_by_class_instance_id={
                    UUID(class_instance_id): class_config_id
                    for class_instance_id, class_config_id in (
                        class_config_ids_by_raw_id.items()
                    )
                },
                class_state_rows_by_id={
                    UUID(class_instance_id): member_rows
                    for class_instance_id, member_rows in (
                        class_state_rows_by_raw_id.items()
                    )
                },
                class_state_rows_by_raw_id=class_state_rows_by_raw_id,
                relationship_keys=frozenset(relationship_keys),
            )
        except Exception:
            return None
    return state_rows, state_row_maps


def _commit_state_rows_from_snapshot_payload(
    payload: JsonObject,
) -> tuple[CommitStateRow, ...] | None:
    read = _commit_state_rows_read_from_snapshot_payload(payload)
    return read.state_rows if read is not None else None
