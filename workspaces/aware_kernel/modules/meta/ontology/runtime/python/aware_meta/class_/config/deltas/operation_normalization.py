from __future__ import annotations

from collections.abc import Mapping

from aware_meta.materialization.deltas.typed_operation_contracts import (
    MetaProviderDeltaTypedOperation,
)


CLASS_CREATE_PROVIDER_OPERATION_TYPE = "meta_ocg.class.create"
CLASS_UPDATE_PROVIDER_OPERATION_TYPE = "meta_ocg.class.update"
CLASS_DELETE_PROVIDER_OPERATION_TYPE = "meta_ocg.class.delete"
CLASS_CREATE_SEMANTIC_OPERATION_TYPE = "aware_meta.object_config_graph.class.create"
CLASS_DELETE_SEMANTIC_OPERATION_TYPE = "aware_meta.object_config_graph.class.delete"
CLASS_DESCRIPTION_UPDATE_SEMANTIC_OPERATION_TYPE = (
    "aware_meta.object_config_graph.class.description.update"
)


def coalesced_class_create_update_typed_operations(
    *,
    operations: tuple[MetaProviderDeltaTypedOperation, ...],
) -> tuple[MetaProviderDeltaTypedOperation, ...]:
    created_class_keys = _created_class_keys_from_typed_operations(
        operations=operations,
    )
    if not created_class_keys:
        return operations
    return tuple(
        operation
        for operation in operations
        if not _is_update_typed_operation_of_created_class(
            operation=operation,
            created_class_keys=created_class_keys,
        )
    )


def coalesced_class_aggregate_delete_typed_operations(
    *,
    operations: tuple[MetaProviderDeltaTypedOperation, ...],
) -> tuple[MetaProviderDeltaTypedOperation, ...]:
    deleted_class_keys = _deleted_class_keys_from_typed_operations(
        operations=operations,
    )
    if not deleted_class_keys:
        return operations
    return tuple(
        operation
        for operation in operations
        if not _is_update_typed_operation_of_deleted_class(
            operation=operation,
            deleted_class_keys=deleted_class_keys,
        )
    )


def coalesced_class_create_update_source_operations(
    *,
    operations: tuple[Mapping[str, object], ...],
) -> tuple[Mapping[str, object], ...]:
    created_class_keys = _created_class_keys_from_source_operations(
        operations=operations,
    )
    if not created_class_keys:
        return operations
    return tuple(
        operation
        for operation in operations
        if not _is_update_source_operation_of_created_class(
            operation=operation,
            created_class_keys=created_class_keys,
        )
    )


def coalesced_class_aggregate_delete_source_operations(
    *,
    operations: tuple[Mapping[str, object], ...],
) -> tuple[Mapping[str, object], ...]:
    deleted_class_keys = _deleted_class_keys_from_source_operations(
        operations=operations,
    )
    if not deleted_class_keys:
        return operations
    return tuple(
        operation
        for operation in operations
        if not _is_update_source_operation_of_deleted_class(
            operation=operation,
            deleted_class_keys=deleted_class_keys,
        )
    )


def coalesced_class_create_update_executor_requests(
    *,
    requests: tuple[Mapping[str, object], ...],
) -> tuple[Mapping[str, object], ...]:
    created_class_keys = _created_class_keys_from_executor_requests(
        requests=requests,
    )
    if not created_class_keys:
        return requests
    return tuple(
        request
        for request in requests
        if not _is_update_executor_request_of_created_class(
            request=request,
            created_class_keys=created_class_keys,
        )
    )


def coalesced_class_aggregate_delete_executor_requests(
    *,
    requests: tuple[Mapping[str, object], ...],
) -> tuple[Mapping[str, object], ...]:
    deleted_class_keys = _deleted_class_keys_from_executor_requests(
        requests=requests,
    )
    if not deleted_class_keys:
        return requests
    return tuple(
        request
        for request in requests
        if not _is_update_executor_request_of_deleted_class(
            request=request,
            deleted_class_keys=deleted_class_keys,
        )
    )


def _deleted_class_keys_from_typed_operations(
    *,
    operations: tuple[MetaProviderDeltaTypedOperation, ...],
) -> frozenset[str]:
    keys: set[str] = set()
    for operation in operations:
        if operation.provider_operation_type != CLASS_DELETE_PROVIDER_OPERATION_TYPE:
            continue
        keys.update(
            _class_operation_key_candidates(
                operation={
                    "semantic_key": operation.semantic_key,
                    "current": operation.current,
                    "baseline": operation.baseline,
                },
            )
        )
    return frozenset(keys)


def _created_class_keys_from_typed_operations(
    *,
    operations: tuple[MetaProviderDeltaTypedOperation, ...],
) -> frozenset[str]:
    keys: set[str] = set()
    for operation in operations:
        if operation.provider_operation_type != CLASS_CREATE_PROVIDER_OPERATION_TYPE:
            continue
        keys.update(
            _class_operation_key_candidates(
                operation={
                    "semantic_key": operation.semantic_key,
                    "current": operation.current,
                    "baseline": operation.baseline,
                },
            )
        )
    return frozenset(keys)


def _created_class_keys_from_source_operations(
    *,
    operations: tuple[Mapping[str, object], ...],
) -> frozenset[str]:
    keys: set[str] = set()
    for operation in operations:
        if (
            _optional_text(operation.get("semantic_operation_type"))
            != CLASS_CREATE_SEMANTIC_OPERATION_TYPE
        ):
            continue
        keys.update(_class_operation_key_candidates(operation=operation))
    return frozenset(keys)


def _deleted_class_keys_from_source_operations(
    *,
    operations: tuple[Mapping[str, object], ...],
) -> frozenset[str]:
    keys: set[str] = set()
    for operation in operations:
        if (
            _optional_text(operation.get("semantic_operation_type"))
            != CLASS_DELETE_SEMANTIC_OPERATION_TYPE
        ):
            continue
        keys.update(_class_operation_key_candidates(operation=operation))
    return frozenset(keys)


def _created_class_keys_from_executor_requests(
    *,
    requests: tuple[Mapping[str, object], ...],
) -> frozenset[str]:
    keys: set[str] = set()
    for request in requests:
        for operation in _typed_operation_payloads_from_request(request=request):
            if (
                _optional_text(operation.get("provider_operation_type"))
                != CLASS_CREATE_PROVIDER_OPERATION_TYPE
            ):
                continue
            keys.update(_class_operation_key_candidates(operation=operation))
    return frozenset(keys)


def _deleted_class_keys_from_executor_requests(
    *,
    requests: tuple[Mapping[str, object], ...],
) -> frozenset[str]:
    keys: set[str] = set()
    for request in requests:
        for operation in _typed_operation_payloads_from_request(request=request):
            if (
                _optional_text(operation.get("provider_operation_type"))
                != CLASS_DELETE_PROVIDER_OPERATION_TYPE
            ):
                continue
            keys.update(_class_operation_key_candidates(operation=operation))
    return frozenset(keys)


def _is_update_typed_operation_of_created_class(
    *,
    operation: MetaProviderDeltaTypedOperation,
    created_class_keys: frozenset[str],
) -> bool:
    if operation.provider_operation_type != CLASS_UPDATE_PROVIDER_OPERATION_TYPE:
        return False
    return bool(
        created_class_keys.intersection(
            _class_operation_key_candidates(
                operation={
                    "semantic_key": operation.semantic_key,
                    "current": operation.current,
                    "baseline": operation.baseline,
                },
            )
        )
    )


def _is_update_typed_operation_of_deleted_class(
    *,
    operation: MetaProviderDeltaTypedOperation,
    deleted_class_keys: frozenset[str],
) -> bool:
    if operation.provider_operation_type != CLASS_UPDATE_PROVIDER_OPERATION_TYPE:
        return False
    return bool(
        deleted_class_keys.intersection(
            _class_operation_key_candidates(
                operation={
                    "semantic_key": operation.semantic_key,
                    "current": operation.current,
                    "baseline": operation.baseline,
                },
            )
        )
    )


def _is_update_source_operation_of_created_class(
    *,
    operation: Mapping[str, object],
    created_class_keys: frozenset[str],
) -> bool:
    if (
        _optional_text(operation.get("semantic_operation_type"))
        != CLASS_DESCRIPTION_UPDATE_SEMANTIC_OPERATION_TYPE
    ):
        return False
    return bool(
        created_class_keys.intersection(
            _class_operation_key_candidates(operation=operation),
        )
    )


def _is_update_source_operation_of_deleted_class(
    *,
    operation: Mapping[str, object],
    deleted_class_keys: frozenset[str],
) -> bool:
    if (
        _optional_text(operation.get("semantic_operation_type"))
        != CLASS_DESCRIPTION_UPDATE_SEMANTIC_OPERATION_TYPE
    ):
        return False
    return bool(
        deleted_class_keys.intersection(
            _class_operation_key_candidates(operation=operation),
        )
    )


def _is_update_executor_request_of_created_class(
    *,
    request: Mapping[str, object],
    created_class_keys: frozenset[str],
) -> bool:
    operations = _typed_operation_payloads_from_request(request=request)
    if not operations:
        return False
    update_operations = tuple(
        operation
        for operation in operations
        if _optional_text(operation.get("provider_operation_type"))
        == CLASS_UPDATE_PROVIDER_OPERATION_TYPE
        and created_class_keys.intersection(
            _class_operation_key_candidates(operation=operation),
        )
    )
    return bool(update_operations) and len(update_operations) == len(operations)


def _is_update_executor_request_of_deleted_class(
    *,
    request: Mapping[str, object],
    deleted_class_keys: frozenset[str],
) -> bool:
    operations = _typed_operation_payloads_from_request(request=request)
    if not operations:
        return False
    update_operations = tuple(
        operation
        for operation in operations
        if _optional_text(operation.get("provider_operation_type"))
        == CLASS_UPDATE_PROVIDER_OPERATION_TYPE
        and deleted_class_keys.intersection(
            _class_operation_key_candidates(operation=operation),
        )
    )
    return bool(update_operations) and len(update_operations) == len(operations)


def _typed_operation_payloads_from_request(
    *,
    request: Mapping[str, object],
) -> tuple[Mapping[str, object], ...]:
    typed_plan = _mapping_value(request.get("provider_delta_typed_operation_plan"))
    operations = typed_plan.get("typed_operations")
    if isinstance(operations, (tuple, list)):
        payloads = tuple(
            _mapping_value(operation)
            for operation in operations
            if isinstance(operation, Mapping)
        )
        if payloads:
            return payloads
    typed_operation = _mapping_value(request.get("typed_operation"))
    return (typed_operation,) if typed_operation else ()


def _class_operation_key_candidates(
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
        _optional_text(operation.get("class_semantic_key")),
        _optional_text(before_payload.get("class_semantic_key")),
        _optional_text(after_payload.get("class_semantic_key")),
        _optional_text(operation.get("class_fqn")),
        _optional_text(before_payload.get("class_fqn")),
        _optional_text(after_payload.get("class_fqn")),
        _optional_text(baseline_object.get("class_fqn")),
        _optional_text(current.get("class_fqn")),
        _optional_text(current_payload.get("class_fqn")),
        _optional_text(operation.get("node_key")),
        _optional_text(before_payload.get("node_key")),
        _optional_text(after_payload.get("node_key")),
        _optional_text(baseline_object.get("node_key")),
        _optional_text(current.get("node_key")),
        _optional_text(current_payload.get("node_key")),
        _optional_text(operation.get("class_name")),
        _optional_text(operation.get("name")),
        _optional_text(before_payload.get("class_name")),
        _optional_text(before_payload.get("name")),
        _optional_text(after_payload.get("class_name")),
        _optional_text(after_payload.get("name")),
        _optional_text(baseline_object.get("class_name")),
        _optional_text(baseline_object.get("name")),
        _optional_text(current.get("class_name")),
        _optional_text(current.get("name")),
        _optional_text(current_payload.get("class_name")),
        _optional_text(current_payload.get("name")),
    }
    if semantic_key is not None:
        candidates.add(_class_name_from_class_semantic_key(semantic_key))
        candidates.add(_class_fqn_from_class_semantic_key(semantic_key))
    return frozenset(value for value in candidates if value is not None)


def _payload_mapping(
    operation: Mapping[str, object],
    field_name: str,
) -> Mapping[str, object]:
    payload = operation.get(field_name)
    if payload is None:
        return {}
    return _mapping_value(payload)


def _class_name_from_class_semantic_key(value: str | None) -> str | None:
    if value is None:
        return None
    _, separator, class_key = value.partition("meta.class:")
    if separator:
        return _optional_text(class_key.split("/", maxsplit=1)[0].rsplit(".", 1)[-1])
    _, separator, class_key = value.partition("/node:")
    if separator:
        return _optional_text(class_key.split("/", maxsplit=1)[0].rsplit(".", 1)[-1])
    return None


def _class_fqn_from_class_semantic_key(value: str | None) -> str | None:
    if value is None:
        return None
    _, separator, class_key = value.partition("meta.class:")
    if separator:
        return _optional_text(class_key.split("/", maxsplit=1)[0])
    _, separator, class_key = value.partition("/node:")
    if separator:
        return _optional_text(class_key.split("/", maxsplit=1)[0])
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
    "CLASS_DELETE_PROVIDER_OPERATION_TYPE",
    "CLASS_DELETE_SEMANTIC_OPERATION_TYPE",
    "coalesced_class_aggregate_delete_executor_requests",
    "coalesced_class_aggregate_delete_source_operations",
    "coalesced_class_aggregate_delete_typed_operations",
    "coalesced_class_create_update_executor_requests",
    "coalesced_class_create_update_source_operations",
    "coalesced_class_create_update_typed_operations",
]
