from __future__ import annotations

from collections.abc import Mapping

from aware_meta.materialization.deltas.typed_operation_contracts import (
    MetaProviderDeltaTypedOperation,
)


_ATTRIBUTE_SCALAR_SIGNATURE_FIELDS = (
    "name",
    "attribute_config_name",
    "description",
    "default_value",
    "is_primary",
    "is_public",
    "is_required",
    "is_unique",
    "is_virtual",
    "exclude_serialization",
    "type_descriptor",
)
ATTRIBUTE_CONFIG_SUBJECT_KIND = "attribute"
ATTRIBUTE_CONFIG_SUBJECT_TYPE = "aware_meta.AttributeConfig"


def attribute_config_create_typed_operation(
    *,
    semantic_key: str,
    attribute_config_id: str,
    owner_semantic_key: str,
    attribute_name: str,
    source_refs: tuple[str, ...],
    primitive_base_type: str = "string",
    description: str | None = None,
) -> MetaProviderDeltaTypedOperation:
    return MetaProviderDeltaTypedOperation(
        operation_kind="meta_ocg_provider_delta_typed_operation",
        operation_key=f"meta_ocg.attribute.create:{semantic_key}",
        operation_family="create",
        provider_operation_type="meta_ocg.attribute.create",
        semantic_key=semantic_key,
        ontology_subject_kind=ATTRIBUTE_CONFIG_SUBJECT_KIND,
        semantic_subject_type=ATTRIBUTE_CONFIG_SUBJECT_TYPE,
        source_refs=source_refs,
        baseline={},
        current={
            "semantic_key": semantic_key,
            "object_kind": ATTRIBUTE_CONFIG_SUBJECT_KIND,
            "entity_id": attribute_config_id,
            "owner_semantic_key": owner_semantic_key,
            "attribute_name": attribute_name,
            "attribute_signature": {
                "name": attribute_name,
                "position": 0,
                "description": description,
                "is_required": True,
                "is_public": True,
                "type_descriptor": {
                    "kind": "primitive",
                    "primitive_base_type": primitive_base_type,
                },
            },
        },
        would_execute=True,
        would_persist=True,
    )


_CLASS_ATTRIBUTE_MEMBERSHIP_IDENTITY_FIELDS = (
    "owner_kind",
    "class_config_id",
    "attribute_config_id",
)
_CLASS_ATTRIBUTE_MEMBERSHIP_MUTABLE_FIELDS = (
    "position",
    "is_identity_key",
)
_CLASS_ATTRIBUTE_MEMBERSHIP_SIGNATURE_FIELDS = (
    *_CLASS_ATTRIBUTE_MEMBERSHIP_IDENTITY_FIELDS,
    *_CLASS_ATTRIBUTE_MEMBERSHIP_MUTABLE_FIELDS,
)
_FUNCTION_ATTRIBUTE_MEMBERSHIP_IDENTITY_FIELDS = (
    "owner_kind",
    "function_config_id",
    "attribute_config_id",
    "name",
    "type",
)
_FUNCTION_ATTRIBUTE_MEMBERSHIP_MUTABLE_FIELDS = (
    "position",
    "is_identity_key",
    "identity_key_origin",
)
_FUNCTION_ATTRIBUTE_MEMBERSHIP_SIGNATURE_FIELDS = (
    *_FUNCTION_ATTRIBUTE_MEMBERSHIP_IDENTITY_FIELDS,
    *_FUNCTION_ATTRIBUTE_MEMBERSHIP_MUTABLE_FIELDS,
)


def split_attribute_update_entry(
    *,
    entry: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    membership_changed = _attribute_membership_signature_changed(entry=entry)
    membership_replacement_required = (
        _attribute_membership_identity_replacement_required(entry=entry)
        if membership_changed
        else False
    )
    scalar_changed = _attribute_scalar_signature_changed(entry=entry)
    entries: list[dict[str, object]] = []
    if (scalar_changed and not membership_replacement_required) or (
        not membership_changed
    ):
        entries.append(dict(entry))
    if membership_changed:
        entries.append(_attribute_membership_dirty_entry(entry=entry))
    return tuple(entries)


def _attribute_scalar_signature_changed(*, entry: Mapping[str, object]) -> bool:
    current_signature = _field_projection(
        _attribute_current_signature(entry=entry),
        fields=_ATTRIBUTE_SCALAR_SIGNATURE_FIELDS,
    )
    baseline_signature = _field_projection(
        _attribute_baseline_signature(entry=entry),
        fields=_ATTRIBUTE_SCALAR_SIGNATURE_FIELDS,
    )
    if not current_signature:
        return False
    return current_signature != baseline_signature


def _attribute_membership_signature_changed(*, entry: Mapping[str, object]) -> bool:
    owner_kind = _attribute_membership_owner_kind(entry=entry)
    fields = _attribute_membership_signature_fields(owner_kind=owner_kind)
    current_signature = _field_projection(
        _attribute_current_membership_signature(entry=entry, owner_kind=owner_kind),
        fields=fields,
    )
    baseline_signature = _field_projection(
        _attribute_baseline_membership_signature(entry=entry, owner_kind=owner_kind),
        fields=fields,
    )
    if not current_signature or not baseline_signature:
        return False
    comparable_fields = tuple(
        field
        for field in fields
        if field in current_signature and field in baseline_signature
    )
    if not comparable_fields:
        return False
    return any(
        current_signature[field] != baseline_signature[field]
        for field in comparable_fields
    )


def _attribute_membership_identity_replacement_required(
    *,
    entry: Mapping[str, object],
) -> bool:
    owner_kind = _attribute_membership_owner_kind(entry=entry)
    current_signature = _attribute_current_membership_signature(
        entry=entry,
        owner_kind=owner_kind,
    )
    baseline_signature = _attribute_baseline_membership_signature(
        entry=entry,
        owner_kind=owner_kind,
    )
    return any(
        field in _attribute_membership_identity_fields(owner_kind=owner_kind)
        for field in _attribute_membership_changed_fields(
            current_signature=current_signature,
            baseline_signature=baseline_signature,
            owner_kind=owner_kind,
        )
    )


def _attribute_membership_dirty_entry(
    *,
    entry: Mapping[str, object],
) -> dict[str, object]:
    payload = dict(_mapping_value(entry.get("payload")))
    owner_kind = _attribute_membership_owner_kind(entry=entry)
    current_signature = _attribute_current_membership_signature(
        entry=entry,
        owner_kind=owner_kind,
    )
    baseline_signature = _attribute_baseline_membership_signature(
        entry=entry,
        owner_kind=owner_kind,
    )
    baseline_object = dict(_mapping_value(entry.get("baseline_object")))
    membership_semantic_key = _attribute_membership_semantic_key(
        entry=entry,
        owner_kind=owner_kind,
    )
    changed_fields = _attribute_membership_changed_fields(
        current_signature=current_signature,
        baseline_signature=baseline_signature,
        owner_kind=owner_kind,
    )
    replacement_fields = tuple(
        field
        for field in changed_fields
        if field in _attribute_membership_identity_fields(owner_kind=owner_kind)
    )
    mutable_fields = tuple(
        field
        for field in changed_fields
        if field in _attribute_membership_mutable_fields(owner_kind=owner_kind)
    )
    membership_object_id = _attribute_membership_object_id(
        entry=entry,
        payload=payload,
        baseline_object=baseline_object,
        owner_kind=owner_kind,
    )
    edge_id_field = _attribute_membership_edge_id_field(owner_kind=owner_kind)
    membership_payload = dict(payload)
    membership_payload.update(
        {
            "semantic_key": membership_semantic_key,
            "object_kind": "attribute_membership",
            "ontology_subject_kind": "attribute_membership",
            "entity_id": membership_object_id,
            edge_id_field: membership_object_id,
            "attribute_config_id": _first_text(
                entry.get("attribute_config_id"),
                payload.get("attribute_config_id"),
                current_signature.get("attribute_config_id"),
            ),
            "attribute_semantic_key": _optional_text(entry.get("semantic_key")),
            "attribute_membership_owner_kind": owner_kind,
            "attribute_membership_semantic_key": membership_semantic_key,
            "attribute_membership_signature": current_signature,
            "attribute_membership_changed_fields": changed_fields,
            "attribute_membership_mutable_update_fields": mutable_fields,
            "attribute_membership_identity_replacement_fields": replacement_fields,
            "attribute_membership_replacement_required": bool(replacement_fields),
        }
    )
    if owner_kind == "class":
        membership_payload["class_config_id"] = _first_text(
            entry.get("class_config_id"),
            payload.get("class_config_id"),
            current_signature.get("class_config_id"),
        )
    else:
        membership_payload["function_config_id"] = _first_text(
            entry.get("function_config_id"),
            payload.get("function_config_id"),
            current_signature.get("function_config_id"),
        )
        membership_payload["function_attribute_type"] = _first_text(
            entry.get("function_attribute_type"),
            payload.get("function_attribute_type"),
            current_signature.get("type"),
        )

    baseline_object.update(
        {
            "object_id": membership_object_id,
            "object_kind": "attribute_membership",
            edge_id_field: membership_object_id,
            "attribute_config_id": baseline_signature.get("attribute_config_id"),
            "attribute_membership_owner_kind": owner_kind,
            "attribute_membership_semantic_key": membership_semantic_key,
            "attribute_membership_signature": baseline_signature,
        }
    )
    if owner_kind == "class":
        baseline_object["class_config_id"] = baseline_signature.get(
            "class_config_id"
        )
    else:
        baseline_object["function_config_id"] = baseline_signature.get(
            "function_config_id"
        )
        baseline_object["function_attribute_type"] = baseline_signature.get("type")

    updated = dict(entry)
    updated.update(
        {
            "semantic_key": membership_semantic_key,
            "source_delta_key": (
                "aware_meta.runtime_delta.attribute_membership:"
                f"{membership_semantic_key}"
            ),
            "semantic_subject_type": _attribute_membership_subject_type(
                owner_kind=owner_kind,
            ),
            "ontology_subject_kind": "attribute_membership",
            "object_kind": "attribute_membership",
            "node_type": "attribute_membership",
            "entity_id": membership_object_id,
            edge_id_field: membership_object_id,
            "attribute_config_id": membership_payload.get("attribute_config_id"),
            "attribute_semantic_key": _optional_text(entry.get("semantic_key")),
            "attribute_membership_owner_kind": owner_kind,
            "attribute_membership_semantic_key": membership_semantic_key,
            "attribute_membership_signature": current_signature,
            "attribute_membership_changed_fields": changed_fields,
            "attribute_membership_mutable_update_fields": mutable_fields,
            "attribute_membership_identity_replacement_fields": replacement_fields,
            "attribute_membership_replacement_required": bool(replacement_fields),
            "payload": membership_payload,
            "baseline_object_id": membership_object_id,
            "baseline_object_kind": "attribute_membership",
            "baseline_object": baseline_object,
        }
    )
    if owner_kind == "class":
        updated["class_config_id"] = membership_payload.get("class_config_id")
    else:
        updated["function_config_id"] = membership_payload.get(
            "function_config_id"
        )
        updated["function_attribute_type"] = membership_payload.get(
            "function_attribute_type"
        )
    return updated


def _attribute_current_signature(
    *,
    entry: Mapping[str, object],
) -> dict[str, object]:
    payload = _mapping_value(entry.get("payload"))
    return _mapping_value(
        entry.get("attribute_signature") or payload.get("attribute_signature")
    )


def _attribute_baseline_signature(
    *,
    entry: Mapping[str, object],
) -> dict[str, object]:
    baseline_object = _mapping_value(entry.get("baseline_object"))
    return _mapping_value(
        entry.get("baseline_attribute_signature")
        or baseline_object.get("attribute_signature")
    )


def _attribute_current_membership_signature(
    *,
    entry: Mapping[str, object],
    owner_kind: str,
) -> dict[str, object]:
    payload = _mapping_value(entry.get("payload"))
    signature = _mapping_value(
        entry.get("attribute_membership_signature")
        or payload.get("attribute_membership_signature")
    )
    if signature:
        return signature
    attribute_signature = _attribute_current_signature(entry=entry)
    return _field_projection(
        {
            **attribute_signature,
            "owner_kind": owner_kind,
            "class_config_id": _first_text(
                entry.get("class_config_id"),
                payload.get("class_config_id"),
                attribute_signature.get("class_config_id"),
            ),
            "function_config_id": _first_text(
                entry.get("function_config_id"),
                payload.get("function_config_id"),
                attribute_signature.get("function_config_id"),
            ),
            "attribute_config_id": _first_text(
                entry.get("attribute_config_id"),
                payload.get("attribute_config_id"),
                attribute_signature.get("attribute_config_id"),
            ),
            "type": _first_text(
                entry.get("function_attribute_type"),
                payload.get("function_attribute_type"),
                attribute_signature.get("type"),
            ),
        },
        fields=_attribute_membership_signature_fields(owner_kind=owner_kind),
    )


def _attribute_baseline_membership_signature(
    *,
    entry: Mapping[str, object],
    owner_kind: str,
) -> dict[str, object]:
    baseline_object = _mapping_value(entry.get("baseline_object"))
    signature = _mapping_value(
        entry.get("baseline_attribute_membership_signature")
        or baseline_object.get("attribute_membership_signature")
    )
    if signature:
        return signature
    attribute_signature = _attribute_baseline_signature(entry=entry)
    return _field_projection(
        {
            **attribute_signature,
            "owner_kind": owner_kind,
            "class_config_id": _first_text(
                baseline_object.get("class_config_id"),
                attribute_signature.get("class_config_id"),
            ),
            "function_config_id": _first_text(
                baseline_object.get("function_config_id"),
                attribute_signature.get("function_config_id"),
            ),
            "attribute_config_id": _first_text(
                baseline_object.get("attribute_config_id"),
                attribute_signature.get("attribute_config_id"),
            ),
            "type": _first_text(
                baseline_object.get("function_attribute_type"),
                attribute_signature.get("type"),
            ),
        },
        fields=_attribute_membership_signature_fields(owner_kind=owner_kind),
    )


def _attribute_membership_semantic_key(
    *,
    entry: Mapping[str, object],
    owner_kind: str,
) -> str:
    payload = _mapping_value(entry.get("payload"))
    semantic_key = _optional_text(
        entry.get("attribute_membership_semantic_key")
        or payload.get("attribute_membership_semantic_key")
    )
    if semantic_key is not None:
        return semantic_key
    return (
        f"{_string_value(entry.get('semantic_key'))}"
        f"/membership:{owner_kind}_config"
    )


def _attribute_membership_owner_kind(*, entry: Mapping[str, object]) -> str:
    payload = _mapping_value(entry.get("payload"))
    signature = _mapping_value(
        entry.get("attribute_membership_signature")
        or payload.get("attribute_membership_signature")
    )
    owner_kind = _optional_text(
        entry.get("attribute_membership_owner_kind")
        or payload.get("attribute_membership_owner_kind")
        or signature.get("owner_kind")
    )
    if owner_kind in {"class", "function"}:
        return owner_kind
    if any(
        _optional_text(value) is not None
        for value in (
            entry.get("function_config_attribute_config_id"),
            payload.get("function_config_attribute_config_id"),
            entry.get("function_config_id"),
            payload.get("function_config_id"),
            entry.get("function_attribute_type"),
            payload.get("function_attribute_type"),
            signature.get("function_config_id"),
        )
    ):
        return "function"
    return "class"


def _attribute_membership_signature_fields(
    *,
    owner_kind: str,
) -> tuple[str, ...]:
    if owner_kind == "function":
        return _FUNCTION_ATTRIBUTE_MEMBERSHIP_SIGNATURE_FIELDS
    return _CLASS_ATTRIBUTE_MEMBERSHIP_SIGNATURE_FIELDS


def _attribute_membership_identity_fields(
    *,
    owner_kind: str,
) -> tuple[str, ...]:
    if owner_kind == "function":
        return _FUNCTION_ATTRIBUTE_MEMBERSHIP_IDENTITY_FIELDS
    return _CLASS_ATTRIBUTE_MEMBERSHIP_IDENTITY_FIELDS


def _attribute_membership_mutable_fields(
    *,
    owner_kind: str,
) -> tuple[str, ...]:
    if owner_kind == "function":
        return _FUNCTION_ATTRIBUTE_MEMBERSHIP_MUTABLE_FIELDS
    return _CLASS_ATTRIBUTE_MEMBERSHIP_MUTABLE_FIELDS


def _attribute_membership_changed_fields(
    *,
    current_signature: Mapping[str, object],
    baseline_signature: Mapping[str, object],
    owner_kind: str,
) -> tuple[str, ...]:
    return tuple(
        field
        for field in _attribute_membership_signature_fields(owner_kind=owner_kind)
        if (
            field in current_signature
            and field in baseline_signature
            and current_signature[field] != baseline_signature[field]
        )
    )


def _attribute_membership_object_id(
    *,
    entry: Mapping[str, object],
    payload: Mapping[str, object],
    baseline_object: Mapping[str, object],
    owner_kind: str,
) -> str | None:
    edge_id_field = _attribute_membership_edge_id_field(owner_kind=owner_kind)
    return _first_text(
        baseline_object.get(edge_id_field),
        entry.get(edge_id_field),
        payload.get(edge_id_field),
        baseline_object.get("object_id"),
        entry.get("entity_id"),
        payload.get("entity_id"),
    )


def _attribute_membership_edge_id_field(*, owner_kind: str) -> str:
    if owner_kind == "function":
        return "function_config_attribute_config_id"
    return "class_config_attribute_config_id"


def _attribute_membership_subject_type(*, owner_kind: str) -> str:
    if owner_kind == "function":
        return "aware_meta.FunctionConfigAttributeConfig"
    return "aware_meta.ClassConfigAttributeConfig"


def _field_projection(
    value: Mapping[str, object],
    *,
    fields: tuple[str, ...],
) -> dict[str, object]:
    return {field: value[field] for field in fields if field in value}


def _mapping_value(value: object) -> dict[str, object]:
    if not isinstance(value, Mapping):
        return {}
    return {str(key): item for key, item in value.items()}


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _first_text(*values: object) -> str | None:
    for value in values:
        text = _optional_text(value)
        if text is not None:
            return text
    return None


def _string_value(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


__all__ = [
    "ATTRIBUTE_CONFIG_SUBJECT_KIND",
    "ATTRIBUTE_CONFIG_SUBJECT_TYPE",
    "attribute_config_create_typed_operation",
    "split_attribute_update_entry",
]
