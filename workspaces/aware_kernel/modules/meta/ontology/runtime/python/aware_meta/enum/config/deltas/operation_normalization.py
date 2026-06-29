from __future__ import annotations

from collections.abc import Mapping

from aware_meta.materialization.deltas.typed_operation_contracts import (
    MetaProviderDeltaTypedOperation,
)


ENUM_DELETE_PROVIDER_OPERATION_TYPE = "meta_ocg.enum.delete"
ENUM_OPTION_CHILD_PROVIDER_OPERATION_TYPES = {
    "meta_ocg.enum_option.create",
    "meta_ocg.enum_option.update",
    "meta_ocg.enum_option.delete",
}
ENUM_DELETE_SEMANTIC_OPERATION_TYPE = "aware_meta.object_config_graph.enum.delete"
ENUM_OPTION_CHILD_SEMANTIC_OPERATION_TYPES = {
    "aware_meta.object_config_graph.enum_option.create",
    "aware_meta.object_config_graph.enum_option.position.update",
    "aware_meta.object_config_graph.enum_option.delete",
}


def coalesced_enum_aggregate_delete_typed_operations(
    *,
    operations: tuple[MetaProviderDeltaTypedOperation, ...],
) -> tuple[MetaProviderDeltaTypedOperation, ...]:
    deleted_enum_keys = _deleted_enum_keys_from_typed_operations(
        operations=operations,
    )
    if not deleted_enum_keys:
        return operations
    return tuple(
        operation
        for operation in operations
        if not _is_child_typed_operation_of_deleted_enum(
            operation=operation,
            deleted_enum_keys=deleted_enum_keys,
        )
    )


def coalesced_enum_aggregate_delete_source_operations(
    *,
    operations: tuple[Mapping[str, object], ...],
) -> tuple[Mapping[str, object], ...]:
    deleted_enum_keys = _deleted_enum_keys_from_source_operations(
        operations=operations,
    )
    if not deleted_enum_keys:
        return operations
    return tuple(
        operation
        for operation in operations
        if not _is_child_source_operation_of_deleted_enum(
            operation=operation,
            deleted_enum_keys=deleted_enum_keys,
        )
    )


def coalesced_enum_aggregate_delete_executor_requests(
    *,
    requests: tuple[Mapping[str, object], ...],
) -> tuple[Mapping[str, object], ...]:
    deleted_enum_keys = _deleted_enum_keys_from_executor_requests(
        requests=requests,
    )
    if not deleted_enum_keys:
        return requests
    return tuple(
        request
        for request in requests
        if not _is_child_executor_request_of_deleted_enum(
            request=request,
            deleted_enum_keys=deleted_enum_keys,
        )
    )


def _deleted_enum_keys_from_typed_operations(
    *,
    operations: tuple[MetaProviderDeltaTypedOperation, ...],
) -> frozenset[str]:
    keys: set[str] = set()
    for operation in operations:
        if operation.provider_operation_type != ENUM_DELETE_PROVIDER_OPERATION_TYPE:
            continue
        keys.update(
            _enum_operation_key_candidates(
                operation={
                    "semantic_key": operation.semantic_key,
                    "current": operation.current,
                    "baseline": operation.baseline,
                },
            )
        )
    return frozenset(keys)


def _deleted_enum_keys_from_executor_requests(
    *,
    requests: tuple[Mapping[str, object], ...],
) -> frozenset[str]:
    keys: set[str] = set()
    for request in requests:
        for operation in _typed_operation_payloads_from_request(request=request):
            if (
                _optional_text(operation.get("provider_operation_type"))
                != ENUM_DELETE_PROVIDER_OPERATION_TYPE
            ):
                continue
            keys.update(_enum_operation_key_candidates(operation=operation))
    return frozenset(keys)


def _deleted_enum_keys_from_source_operations(
    *,
    operations: tuple[Mapping[str, object], ...],
) -> frozenset[str]:
    keys: set[str] = set()
    for operation in operations:
        if (
            _optional_text(operation.get("semantic_operation_type"))
            != ENUM_DELETE_SEMANTIC_OPERATION_TYPE
        ):
            continue
        keys.update(_enum_operation_key_candidates(operation=operation))
    return frozenset(keys)


def _is_child_typed_operation_of_deleted_enum(
    *,
    operation: MetaProviderDeltaTypedOperation,
    deleted_enum_keys: frozenset[str],
) -> bool:
    if operation.provider_operation_type not in ENUM_OPTION_CHILD_PROVIDER_OPERATION_TYPES:
        return False
    return bool(
        deleted_enum_keys.intersection(
            _enum_option_operation_parent_key_candidates(
                operation={
                    "semantic_key": operation.semantic_key,
                    "current": operation.current,
                    "baseline": operation.baseline,
                },
            )
        )
    )


def _is_child_executor_request_of_deleted_enum(
    *,
    request: Mapping[str, object],
    deleted_enum_keys: frozenset[str],
) -> bool:
    operations = _typed_operation_payloads_from_request(request=request)
    if not operations:
        return False
    child_operations = tuple(
        operation
        for operation in operations
        if _optional_text(operation.get("provider_operation_type"))
        in ENUM_OPTION_CHILD_PROVIDER_OPERATION_TYPES
        and deleted_enum_keys.intersection(
            _enum_option_operation_parent_key_candidates(operation=operation)
        )
    )
    return bool(child_operations) and len(child_operations) == len(operations)


def _is_child_source_operation_of_deleted_enum(
    *,
    operation: Mapping[str, object],
    deleted_enum_keys: frozenset[str],
) -> bool:
    if (
        _optional_text(operation.get("semantic_operation_type"))
        not in ENUM_OPTION_CHILD_SEMANTIC_OPERATION_TYPES
    ):
        return False
    return bool(
        deleted_enum_keys.intersection(
            _enum_option_operation_parent_key_candidates(operation=operation)
        )
    )


def _typed_operation_payloads_from_request(
    *,
    request: Mapping[str, object],
) -> tuple[Mapping[str, object], ...]:
    typed_plan = _mapping_value(request.get("provider_delta_typed_operation_plan"))
    operations = typed_plan.get("typed_operations")
    if isinstance(operations, tuple | list):
        payloads = tuple(
            _mapping_value(operation)
            for operation in operations
            if isinstance(operation, Mapping)
        )
        if payloads:
            return payloads
    typed_operation = _mapping_value(request.get("typed_operation"))
    return (typed_operation,) if typed_operation else ()


def _enum_operation_key_candidates(
    *,
    operation: Mapping[str, object],
) -> frozenset[str]:
    before_payload = _payload_mapping(operation, "before_payload")
    after_payload = _payload_mapping(operation, "after_payload")
    baseline = _mapping_value(operation.get("baseline"))
    current = _mapping_value(operation.get("current"))
    baseline_object = _mapping_value(baseline.get("object"))
    current_payload = _mapping_value(current.get("payload"))
    semantic_key = _optional_text(operation.get("semantic_key"))
    candidates = {
        semantic_key,
        _optional_text(operation.get("enum_semantic_key")),
        _optional_text(before_payload.get("enum_semantic_key")),
        _optional_text(after_payload.get("enum_semantic_key")),
        _optional_text(operation.get("enum_fqn")),
        _optional_text(before_payload.get("enum_fqn")),
        _optional_text(after_payload.get("enum_fqn")),
        _optional_text(baseline_object.get("enum_fqn")),
        _optional_text(current.get("enum_fqn")),
        _optional_text(current_payload.get("enum_fqn")),
        _optional_text(operation.get("node_key")),
        _optional_text(before_payload.get("node_key")),
        _optional_text(after_payload.get("node_key")),
        _optional_text(baseline_object.get("node_key")),
        _optional_text(current.get("node_key")),
        _optional_text(current_payload.get("node_key")),
        _optional_text(operation.get("enum_name")),
        _optional_text(operation.get("name")),
        _optional_text(before_payload.get("enum_name")),
        _optional_text(before_payload.get("name")),
        _optional_text(after_payload.get("enum_name")),
        _optional_text(after_payload.get("name")),
        _optional_text(baseline_object.get("enum_name")),
        _optional_text(baseline_object.get("name")),
        _optional_text(current.get("enum_name")),
        _optional_text(current.get("name")),
        _optional_text(current_payload.get("enum_name")),
        _optional_text(current_payload.get("name")),
    }
    if semantic_key is not None:
        candidates.add(_enum_name_from_enum_semantic_key(semantic_key))
        candidates.add(_enum_fqn_from_enum_semantic_key(semantic_key))
    return frozenset(value for value in candidates if value is not None)


def _enum_option_operation_parent_key_candidates(
    *,
    operation: Mapping[str, object],
) -> frozenset[str]:
    before_payload = _payload_mapping(operation, "before_payload")
    after_payload = _payload_mapping(operation, "after_payload")
    baseline = _mapping_value(operation.get("baseline"))
    current = _mapping_value(operation.get("current"))
    baseline_object = _mapping_value(baseline.get("object"))
    current_payload = _mapping_value(current.get("payload"))
    semantic_key = _optional_text(operation.get("semantic_key"))
    enum_semantic_key = _first_text(
        operation.get("enum_semantic_key"),
        operation.get("parent_semantic_key"),
        before_payload.get("enum_semantic_key"),
        before_payload.get("parent_semantic_key"),
        after_payload.get("enum_semantic_key"),
        after_payload.get("parent_semantic_key"),
        baseline_object.get("enum_semantic_key"),
        baseline_object.get("parent_semantic_key"),
        current.get("enum_semantic_key"),
        current.get("parent_semantic_key"),
        current_payload.get("enum_semantic_key"),
        current_payload.get("parent_semantic_key"),
        _enum_semantic_key_from_option_semantic_key(semantic_key or ""),
    )
    candidates = {
        enum_semantic_key,
        _optional_text(operation.get("enum_fqn")),
        _optional_text(before_payload.get("enum_fqn")),
        _optional_text(after_payload.get("enum_fqn")),
        _optional_text(baseline_object.get("enum_fqn")),
        _optional_text(current.get("enum_fqn")),
        _optional_text(current_payload.get("enum_fqn")),
        _optional_text(operation.get("enum_name")),
        _optional_text(before_payload.get("enum_name")),
        _optional_text(after_payload.get("enum_name")),
        _optional_text(baseline_object.get("enum_name")),
        _optional_text(current.get("enum_name")),
        _optional_text(current_payload.get("enum_name")),
    }
    if enum_semantic_key is not None:
        candidates.add(_enum_name_from_enum_semantic_key(enum_semantic_key))
        candidates.add(_enum_fqn_from_enum_semantic_key(enum_semantic_key))
    return frozenset(value for value in candidates if value is not None)


def _payload_mapping(
    operation: Mapping[str, object],
    field_name: str,
) -> Mapping[str, object]:
    payload = operation.get(field_name)
    if payload is None:
        return {}
    return _mapping_value(payload)


def _enum_name_from_enum_semantic_key(value: str | None) -> str | None:
    if value is None:
        return None
    _, separator, enum_key = value.partition("meta.enum:")
    if separator:
        return _optional_text(enum_key.split("/", maxsplit=1)[0].rsplit(".", 1)[-1])
    _, separator, enum_key = value.partition("/node:")
    if separator:
        return _optional_text(enum_key.split("/", maxsplit=1)[0].rsplit(".", 1)[-1])
    return None


def _enum_fqn_from_enum_semantic_key(value: str | None) -> str | None:
    if value is None:
        return None
    _, separator, enum_key = value.partition("meta.enum:")
    if separator:
        return _optional_text(enum_key.split("/", maxsplit=1)[0])
    _, separator, enum_key = value.partition("/node:")
    if separator:
        return _optional_text(enum_key.split("/", maxsplit=1)[0])
    return None


def _enum_semantic_key_from_option_semantic_key(value: str) -> str | None:
    enum_key, separator, _ = value.partition("/option:")
    if not separator:
        return None
    return _optional_text(enum_key)


def _first_text(*values: object) -> str | None:
    for value in values:
        text = _optional_text(value)
        if text is not None:
            return text
    return None


def _mapping_value(value: object) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    return {}


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


__all__ = [
    "coalesced_enum_aggregate_delete_executor_requests",
    "coalesced_enum_aggregate_delete_source_operations",
    "coalesced_enum_aggregate_delete_typed_operations",
]
