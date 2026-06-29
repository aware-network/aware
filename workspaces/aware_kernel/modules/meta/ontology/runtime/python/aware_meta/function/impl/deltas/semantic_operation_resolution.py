from __future__ import annotations

from collections.abc import Mapping

from aware_meta.semantic_operation_resolution import (
    MetaSemanticOperationResolution,
    _blocked_resolution,
    _class_name_from_function_impl_semantic_key,
    _first_text,
    _function_name_from_function_impl_semantic_key,
    _mapping_value,
    _optional_text,
    _semantic_key,
    _string_value,
    _tuple_values,
)


def resolve_function_impl_semantic_operation(
    *,
    operation: Mapping[str, object],
    operation_group: tuple[Mapping[str, object], ...],
    current_objects: Mapping[str, str],
    current_object_identities: Mapping[str, Mapping[str, object]],
) -> MetaSemanticOperationResolution:
    del operation_group
    return _resolve_function_impl_body_update(
        operation=operation,
        current_objects=current_objects,
        current_object_identities=current_object_identities,
    )


def _resolve_function_impl_body_update(
    *,
    operation: Mapping[str, object],
    current_objects: Mapping[str, str],
    current_object_identities: Mapping[str, Mapping[str, object]],
) -> MetaSemanticOperationResolution:
    if _string_value(operation.get("operation_family")) not in {"update", "upsert"}:
        return _blocked_resolution(
            operation=operation,
            reason="meta_ocg_function_impl_body_requires_update_family",
            blockers=(
                "unsupported_operation_family:"
                f"{_string_value(operation.get('operation_family')) or 'unknown'}",
            ),
        )
    if _string_value(operation.get("semantic_subject_type")) not in {
        "FunctionImpl",
        "aware_meta.FunctionImpl",
    }:
        return _blocked_resolution(
            operation=operation,
            reason="meta_ocg_function_impl_body_subject_not_supported",
            blockers=(
                "unsupported_semantic_subject_type:"
                f"{_string_value(operation.get('semantic_subject_type')) or 'unknown'}",
            ),
        )
    if _optional_text(operation.get("field_path")) not in {None, "body_text"}:
        return _blocked_resolution(
            operation=operation,
            reason="meta_ocg_function_impl_body_field_not_supported",
            blockers=(
                "unsupported_field_path:"
                f"{_string_value(operation.get('field_path')) or 'unknown'}",
            ),
        )

    after_payload = _mapping_value(operation.get("after_payload"))
    function_name = _first_text(
        after_payload.get("function_name"),
        _function_name_from_function_impl_semantic_key(_semantic_key(operation)),
    )
    class_name = _first_text(
        after_payload.get("class_name"),
        _class_name_from_function_impl_semantic_key(_semantic_key(operation)),
    )
    blockers = tuple(
        blocker
        for blocker, value in (
            ("missing_class_name", class_name),
            ("missing_function_name", function_name),
        )
        if value is None
    )
    semantic_key = _semantic_key(operation)
    from aware_meta.function.impl.deltas.typed_operations import (  # noqa: WPS433
        build_function_impl_body_generated_materialization_intent,
        normalize_function_impl_body_source_meaning_provider_delta_operation,
    )

    normalization = (
        normalize_function_impl_body_source_meaning_provider_delta_operation(
            operation=operation,
            function_impl_object_id=current_objects.get(semantic_key),
            function_impl_source_object_id=_function_impl_source_object_id(
                operation=operation,
                current_objects=current_objects,
                current_object_identities=current_object_identities,
                semantic_key=semantic_key,
            ),
            current_semantic_object_ids=current_objects,
            current_semantic_source_object_ids=(
                _semantic_source_object_ids(
                    current_objects=current_objects,
                    current_object_identities=current_object_identities,
                )
            ),
        )
    )
    generated_materialization_intent = (
        build_function_impl_body_generated_materialization_intent(
            operation=operation,
            current_semantic_object_ids=current_objects,
        )
    )
    normalization_payload = normalization.evidence_payload()
    generated_materialization_intent_payload = (
        generated_materialization_intent.evidence_payload()
    )
    provider_delta_blockers = tuple(
        str(item)
        for item in _tuple_values(normalization_payload.get("blockers"))
        if str(item).strip()
    )
    generated_materialization_blockers = tuple(
        str(item)
        for item in _tuple_values(
            generated_materialization_intent_payload.get("blockers")
        )
        if str(item).strip()
    )
    metadata: dict[str, object] = {
        "source": "aware_meta.function.impl.deltas.semantic_operation_resolution",
        "semantic_apply_boundary": "provider_delta_ontology_operation_executor",
        "requires_multi_invocation_ontology_operation": True,
        "provider_delta_handler_key": "function_impl.additive_instruction_body",
        "execution_ready": normalization.ready,
        "execution_preconditions": ("provider_delta_ontology_operation_executor",),
        "preview_only": True,
        "provider_delta_typed_operation_status": normalization.status,
        "provider_delta_typed_operation_reason": normalization.reason,
        "provider_delta_typed_operation_blockers": provider_delta_blockers,
        "provider_delta_operation_normalization": normalization_payload,
        "generated_materialization_intent_status": (
            generated_materialization_intent.status
        ),
        "generated_materialization_intent_reason": (
            generated_materialization_intent.reason
        ),
        "generated_materialization_intent_blockers": (
            generated_materialization_blockers
        ),
        "generated_materialization_intent": (generated_materialization_intent_payload),
    }
    provider_delta_typed_operation = normalization_payload.get(
        "provider_delta_typed_operation"
    )
    provider_delta_typed_operation_plan = normalization_payload.get(
        "provider_delta_typed_operation_plan"
    )
    if isinstance(provider_delta_typed_operation, Mapping):
        metadata["provider_delta_typed_operation"] = dict(
            provider_delta_typed_operation
        )
    if isinstance(provider_delta_typed_operation_plan, Mapping):
        metadata["provider_delta_typed_operation_plan"] = dict(
            provider_delta_typed_operation_plan
        )
    generated_materialization_typed_operation = (
        generated_materialization_intent_payload.get("provider_delta_typed_operation")
    )
    generated_materialization_typed_operation_plan = (
        generated_materialization_intent_payload.get(
            "provider_delta_typed_operation_plan"
        )
    )
    if isinstance(generated_materialization_typed_operation, Mapping):
        metadata["provider_delta_generated_materialization_typed_operation"] = dict(
            generated_materialization_typed_operation
        )
    if isinstance(generated_materialization_typed_operation_plan, Mapping):
        metadata["provider_delta_generated_materialization_typed_operation_plan"] = (
            dict(generated_materialization_typed_operation_plan)
        )
    if class_name is not None and function_name is not None:
        metadata["receiver_semantic_key"] = (
            f"meta.function:{class_name}.{function_name}"
        )
        metadata["function_impl_semantic_key"] = semantic_key
    return _blocked_resolution(
        operation=operation,
        reason=(
            "meta_ocg_function_impl_body_requires_provider_delta_"
            "ontology_operation_executor"
        ),
        blockers=(
            *blockers,
            *provider_delta_blockers,
            "semantic_plan_single_function_call_preview_not_supported",
            "provider_delta_function_impl_operation_executor_required",
        ),
        metadata=metadata,
    )


def _function_impl_source_object_id(
    *,
    operation: Mapping[str, object],
    current_objects: Mapping[str, str],
    current_object_identities: Mapping[str, Mapping[str, object]],
    semantic_key: str,
) -> str | None:
    after_payload = _mapping_value(operation.get("after_payload"))
    before_payload = _mapping_value(operation.get("before_payload"))
    identity = current_object_identities.get(semantic_key)
    return _first_text(
        after_payload.get("semantic_source_object_id"),
        after_payload.get("source_object_id"),
        after_payload.get("function_impl_id"),
        before_payload.get("semantic_source_object_id"),
        before_payload.get("source_object_id"),
        before_payload.get("function_impl_id"),
        None if identity is None else identity.get("semantic_source_object_id"),
        None if identity is None else identity.get("source_object_id"),
        None if identity is None else identity.get("function_impl_id"),
        None if identity is None else identity.get("object_id"),
        None if identity is None else identity.get("entity_id"),
        current_objects.get(semantic_key),
    )


def _semantic_source_object_ids(
    *,
    current_objects: Mapping[str, str],
    current_object_identities: Mapping[str, Mapping[str, object]],
) -> dict[str, str]:
    source_ids = dict(current_objects)
    for semantic_key, identity in current_object_identities.items():
        source_id = _first_text(
            identity.get("semantic_source_object_id"),
            identity.get("source_object_id"),
            identity.get("function_impl_id"),
            identity.get("function_config_attribute_config_id"),
            identity.get("class_config_attribute_config_id"),
            identity.get("attribute_config_id"),
            identity.get("function_config_id"),
            identity.get("class_config_id"),
            identity.get("object_id"),
            identity.get("entity_id"),
            current_objects.get(semantic_key),
        )
        if source_id is not None:
            source_ids[semantic_key] = source_id
    return source_ids


__all__ = [
    "resolve_function_impl_semantic_operation",
]
