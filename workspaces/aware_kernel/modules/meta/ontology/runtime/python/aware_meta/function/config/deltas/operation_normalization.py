from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace

from aware_meta.materialization.deltas.typed_operation_contracts import (
    MetaProviderDeltaTypedOperation,
)


FUNCTION_UPDATE_PROVIDER_OPERATION_TYPE = "meta_ocg.function.update"
ATTRIBUTE_CREATE_PROVIDER_OPERATION_TYPE = "meta_ocg.attribute.create"
ATTRIBUTE_DELETE_PROVIDER_OPERATION_TYPE = "meta_ocg.attribute.delete"
FUNCTION_ATTRIBUTE_PROVIDER_OPERATION_TYPES = (
    ATTRIBUTE_CREATE_PROVIDER_OPERATION_TYPE,
    ATTRIBUTE_DELETE_PROVIDER_OPERATION_TYPE,
)


def coalesced_function_signature_child_attribute_typed_operations(
    *,
    operations: tuple[MetaProviderDeltaTypedOperation, ...],
) -> tuple[MetaProviderDeltaTypedOperation, ...]:
    child_operations_by_function_key = _function_child_attribute_operations(
        operations=operations,
    )
    if not child_operations_by_function_key:
        return operations
    coalesced: list[MetaProviderDeltaTypedOperation] = []
    for operation in operations:
        if operation.provider_operation_type != FUNCTION_UPDATE_PROVIDER_OPERATION_TYPE:
            coalesced.append(operation)
            continue
        child_operations = child_operations_by_function_key.get(
            operation.semantic_key,
            (),
        )
        if not child_operations:
            coalesced.append(operation)
            continue
        merged_signature = _function_signature_with_child_attributes(
            operation=operation,
            child_operations=child_operations,
        )
        if not merged_signature:
            coalesced.append(operation)
            continue
        current = dict(operation.current)
        current["function_signature"] = merged_signature
        baseline = _baseline_with_owner_class_fqn(operation=operation)
        coalesced.append(replace(operation, baseline=baseline, current=current))
    return tuple(coalesced)


def _function_child_attribute_operations(
    *,
    operations: tuple[MetaProviderDeltaTypedOperation, ...],
) -> dict[str, tuple[MetaProviderDeltaTypedOperation, ...]]:
    grouped: dict[str, list[MetaProviderDeltaTypedOperation]] = {}
    for operation in operations:
        if operation.provider_operation_type not in (
            FUNCTION_ATTRIBUTE_PROVIDER_OPERATION_TYPES
        ):
            continue
        parent_key = _function_parent_semantic_key(operation=operation)
        if parent_key is None:
            continue
        grouped.setdefault(parent_key, []).append(operation)
    return {
        parent_key: tuple(child_operations)
        for parent_key, child_operations in grouped.items()
    }


def _function_signature_with_child_attributes(
    *,
    operation: MetaProviderDeltaTypedOperation,
    child_operations: tuple[MetaProviderDeltaTypedOperation, ...],
) -> dict[str, object]:
    baseline_signature = _function_signature(operation.baseline)
    current_signature = _function_signature(operation.current)
    if not baseline_signature and not current_signature:
        return {}
    merged_signature = dict(baseline_signature)
    merged_signature.update(current_signature)
    if "inputs" not in current_signature:
        merged_signature["inputs"] = tuple(
            dict(item) for item in _tuple_mappings(baseline_signature.get("inputs"))
        )
    if "outputs" not in current_signature:
        merged_signature["outputs"] = tuple(
            dict(item) for item in _tuple_mappings(baseline_signature.get("outputs"))
        )
    for child_operation in child_operations:
        attribute_type = _function_attribute_type(operation=child_operation)
        if attribute_type not in {"input", "output"}:
            continue
        field_name = "inputs" if attribute_type == "input" else "outputs"
        attributes = list(_tuple_mappings(merged_signature.get(field_name)))
        if child_operation.provider_operation_type == ATTRIBUTE_DELETE_PROVIDER_OPERATION_TYPE:
            delete_name = _function_attribute_name(operation=child_operation)
            if delete_name is not None:
                attributes = [
                    item
                    for item in attributes
                    if _attribute_name(item) != delete_name
                ]
        elif (
            child_operation.provider_operation_type
            == ATTRIBUTE_CREATE_PROVIDER_OPERATION_TYPE
        ):
            attribute_signature = _function_attribute_signature(
                operation=child_operation,
            )
            if attribute_signature:
                attribute_name = _attribute_name(attribute_signature)
                if attribute_name is not None:
                    attributes = [
                        item
                        for item in attributes
                        if _attribute_name(item) != attribute_name
                    ]
                    attributes.append(attribute_signature)
        merged_signature[field_name] = tuple(
            sorted(attributes, key=_attribute_sort_key)
        )
    return _signature_with_owner_class_fqn(
        signature=merged_signature,
        operation=operation,
    )


def _function_parent_semantic_key(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> str | None:
    parent_key = _optional_text(operation.current.get("owner_semantic_key"))
    if parent_key is not None:
        return parent_key
    parent_key = _optional_text(operation.current.get("parent_semantic_key"))
    if parent_key is not None:
        return parent_key
    baseline_object = _mapping_value(operation.baseline.get("object"))
    parent_key = _optional_text(baseline_object.get("owner_semantic_key"))
    if parent_key is not None:
        return parent_key
    marker = "/attribute:"
    if marker in operation.semantic_key:
        return operation.semantic_key.split(marker, maxsplit=1)[0]
    return None


def _function_signature(payload: Mapping[str, object]) -> dict[str, object]:
    signature = _mapping_value(payload.get("function_signature"))
    if signature:
        return signature
    nested_payload = _mapping_value(payload.get("payload"))
    signature = _mapping_value(nested_payload.get("function_signature"))
    if signature:
        return signature
    object_payload = _mapping_value(payload.get("object"))
    signature = _mapping_value(object_payload.get("function_signature"))
    if signature:
        return signature
    baseline_object = _mapping_value(payload.get("baseline_object"))
    return _mapping_value(baseline_object.get("function_signature"))


def _function_attribute_signature(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> dict[str, object]:
    signature = _attribute_signature(operation.current)
    if not signature:
        signature = _attribute_signature(_mapping_value(operation.current.get("payload")))
    if not signature:
        return {}
    attribute_name = (
        _attribute_name(signature)
        or _optional_text(operation.current.get("attribute_name"))
        or _optional_text(operation.current.get("entity_name"))
        or _attribute_name_from_semantic_key(operation.semantic_key)
    )
    updated = dict(signature)
    if attribute_name is not None:
        updated.setdefault("name", attribute_name)
        updated.setdefault("attribute_config_name", attribute_name)
    attribute_type = _function_attribute_type(operation=operation)
    if attribute_type is not None:
        updated.setdefault("type", attribute_type)
        updated.setdefault("function_attribute_type", attribute_type)
    return updated


def _attribute_signature(payload: Mapping[str, object]) -> dict[str, object]:
    return _mapping_value(payload.get("attribute_signature"))


def _function_attribute_type(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> str | None:
    for payload in (
        operation.current,
        _mapping_value(operation.current.get("payload")),
        _mapping_value(operation.baseline.get("object")),
    ):
        attribute_type = _optional_text(payload.get("function_attribute_type"))
        if attribute_type in {"input", "output"}:
            return attribute_type
        attribute_type = _optional_text(payload.get("type"))
        if attribute_type in {"input", "output"}:
            return attribute_type
        membership_signature = _mapping_value(
            payload.get("attribute_membership_signature")
        )
        attribute_type = _optional_text(membership_signature.get("type"))
        if attribute_type in {"input", "output"}:
            return attribute_type
        signature = _attribute_signature(payload)
        attribute_type = _optional_text(
            signature.get("function_attribute_type") or signature.get("type")
        )
        if attribute_type in {"input", "output"}:
            return attribute_type
    semantic_key = operation.semantic_key
    if "/attribute:input:" in semantic_key:
        return "input"
    if "/attribute:output:" in semantic_key:
        return "output"
    return None


def _function_attribute_name(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> str | None:
    for payload in (
        operation.current,
        _mapping_value(operation.current.get("payload")),
        _mapping_value(operation.baseline.get("object")),
    ):
        name = (
            _optional_text(payload.get("attribute_name"))
            or _optional_text(payload.get("entity_name"))
            or _attribute_name(_attribute_signature(payload))
        )
        if name is not None:
            return name
    return _attribute_name_from_semantic_key(operation.semantic_key)


def _attribute_name(signature: Mapping[str, object]) -> str | None:
    return _optional_text(
        signature.get("name") or signature.get("attribute_config_name")
    )


def _attribute_name_from_semantic_key(semantic_key: str) -> str | None:
    marker = "/attribute:"
    if marker not in semantic_key:
        return None
    suffix = semantic_key.split(marker, maxsplit=1)[1]
    parts = suffix.split(":")
    if len(parts) < 2:
        return None
    return _optional_text(parts[-1])


def _attribute_sort_key(signature: Mapping[str, object]) -> tuple[int, str]:
    position = signature.get("position")
    resolved_position = position if isinstance(position, int) else 0
    return (resolved_position, _attribute_name(signature) or "")


def _signature_with_owner_class_fqn(
    *,
    signature: Mapping[str, object],
    operation: MetaProviderDeltaTypedOperation,
) -> dict[str, object]:
    owner_class_config_id = _owner_class_config_id(operation=operation)
    owner_key = _owner_key(operation=operation)
    if owner_class_config_id is None or owner_key is None:
        return dict(signature)
    updated = dict(signature)
    for field_name in ("inputs", "outputs"):
        attributes = tuple(
            _attribute_signature_with_owner_class_fqn(
                signature=item,
                owner_class_config_id=owner_class_config_id,
                owner_key=owner_key,
            )
            for item in _tuple_mappings(updated.get(field_name))
        )
        if attributes:
            updated[field_name] = attributes
    return updated


def _baseline_with_owner_class_fqn(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> dict[str, object]:
    baseline_signature = _function_signature(operation.baseline)
    if not baseline_signature:
        return dict(operation.baseline)
    updated_signature = _signature_with_owner_class_fqn(
        signature=baseline_signature,
        operation=operation,
    )
    baseline = dict(operation.baseline)
    baseline_object = _mapping_value(baseline.get("object"))
    if baseline_object:
        baseline_object["function_signature"] = updated_signature
        baseline["object"] = baseline_object
    else:
        baseline["function_signature"] = updated_signature
    return baseline


def _attribute_signature_with_owner_class_fqn(
    *,
    signature: Mapping[str, object],
    owner_class_config_id: str,
    owner_key: str,
) -> dict[str, object]:
    descriptor = _mapping_value(signature.get("type_descriptor"))
    if (
        _optional_text(descriptor.get("kind")) != "class"
        or _optional_text(descriptor.get("class_fqn")) is not None
        or _optional_text(descriptor.get("class_config_id")) != owner_class_config_id
    ):
        return dict(signature)
    updated_descriptor = dict(descriptor)
    updated_descriptor["class_fqn"] = owner_key
    updated = dict(signature)
    updated["type_descriptor"] = updated_descriptor
    updated.setdefault("class_fqn", owner_key)
    return updated


def _owner_class_config_id(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> str | None:
    for payload in (
        operation.current,
        _mapping_value(operation.current.get("payload")),
        _mapping_value(operation.baseline.get("object")),
    ):
        class_config_id = _optional_text(payload.get("class_config_id"))
        if class_config_id is not None:
            return class_config_id
    return None


def _owner_key(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> str | None:
    signature = _function_signature(operation.current)
    owner_key = _optional_text(
        operation.current.get("owner_key") or signature.get("owner_key")
    )
    if owner_key is not None:
        return owner_key
    baseline_signature = _function_signature(operation.baseline)
    return _optional_text(baseline_signature.get("owner_key"))


def _tuple_mappings(value: object) -> tuple[dict[str, object], ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(_mapping_value(item) for item in value if isinstance(item, Mapping))


def _mapping_value(value: object) -> dict[str, object]:
    if not isinstance(value, Mapping):
        return {}
    return {str(key): item for key, item in value.items()}


def _optional_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


__all__ = [
    "coalesced_function_signature_child_attribute_typed_operations",
]
