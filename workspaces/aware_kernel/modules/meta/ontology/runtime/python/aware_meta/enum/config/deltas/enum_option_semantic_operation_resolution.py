from __future__ import annotations

from collections.abc import Mapping

from aware_meta.semantic_operation_resolution import (
    META_ENUM_OPTION_CREATE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
    META_ENUM_OPTION_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
    META_OBJECT_CONFIG_GRAPH_ENUM_OPTION_CREATE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_ENUM_OPTION_DELETE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_ENUM_OPTION_POSITION_UPDATE_OPERATION,
    MetaSemanticOperationResolution,
    _blocked_resolution,
    _enum_config_id_for_structural_enum,
    _enum_fqn_from_enum_semantic_key,
    _enum_fqn_from_package_context,
    _enum_name_from_enum_option_semantic_key,
    _enum_option_id_for_existing,
    _enum_option_value_from_semantic_key,
    _enum_semantic_key_from_enum_option_semantic_key,
    _first_text,
    _int_value,
    _mapping_value,
    _semantic_key,
    _string_value,
    _tuple_values,
    _uuid_value,
)


def resolve_enum_option_semantic_operation(
    *,
    operation: Mapping[str, object],
    operation_group: tuple[Mapping[str, object], ...],
    current_objects: Mapping[str, str],
    current_object_identities: Mapping[str, Mapping[str, object]],
) -> MetaSemanticOperationResolution:
    del operation_group
    operation_type = _string_value(operation.get("semantic_operation_type"))
    if operation_type == META_OBJECT_CONFIG_GRAPH_ENUM_OPTION_CREATE_OPERATION:
        return _resolve_enum_option_create(
            operation=operation,
            current_objects=current_objects,
            current_object_identities=current_object_identities,
        )
    if operation_type == META_OBJECT_CONFIG_GRAPH_ENUM_OPTION_POSITION_UPDATE_OPERATION:
        return _resolve_enum_option_update(
            operation=operation,
            current_objects=current_objects,
            current_object_identities=current_object_identities,
        )
    if operation_type == META_OBJECT_CONFIG_GRAPH_ENUM_OPTION_DELETE_OPERATION:
        return _resolve_enum_option_delete(
            operation=operation,
            current_objects=current_objects,
            current_object_identities=current_object_identities,
        )
    return _blocked_resolution(
        operation=operation,
        reason="meta_ocg_enum_option_operation_type_not_supported",
        blockers=(f"unsupported_operation_type:{operation_type or 'unknown'}",),
    )


def _resolve_enum_option_create(
    *,
    operation: Mapping[str, object],
    current_objects: Mapping[str, str],
    current_object_identities: Mapping[str, Mapping[str, object]],
) -> MetaSemanticOperationResolution:
    operation_family = _string_value(operation.get("operation_family"))
    if operation_family not in {"create", "upsert"}:
        return _blocked_resolution(
            operation=operation,
            reason="meta_ocg_enum_option_create_requires_create_family",
            blockers=(
                "unsupported_operation_family:" f"{operation_family or 'unknown'}",
            ),
        )
    if _string_value(operation.get("semantic_subject_type")) not in {
        "EnumOption",
        "aware_meta.EnumOption",
    }:
        return _blocked_resolution(
            operation=operation,
            reason="meta_ocg_enum_option_create_subject_not_supported",
            blockers=(
                "unsupported_semantic_subject_type:"
                f"{_string_value(operation.get('semantic_subject_type')) or 'unknown'}",
            ),
        )
    semantic_key = _semantic_key(operation)
    after_payload = _mapping_value(operation.get("after_payload"))
    enum_name = _first_text(
        after_payload.get("enum_name"),
        _enum_name_from_enum_option_semantic_key(semantic_key),
    )
    enum_semantic_key = _first_text(
        after_payload.get("enum_semantic_key"),
        after_payload.get("parent_semantic_key"),
        _enum_semantic_key_from_enum_option_semantic_key(semantic_key),
    )
    if enum_semantic_key is None and enum_name is not None:
        enum_semantic_key = f"meta.enum:{enum_name}"
    raw_enum_fqn = _first_text(
        after_payload.get("enum_fqn"),
        _enum_fqn_from_enum_semantic_key(enum_semantic_key or semantic_key),
        enum_name,
    )
    enum_fqn = _enum_fqn_from_package_context(
        enum_name=enum_name,
        raw_enum_fqn=raw_enum_fqn,
        operation=operation,
    )
    option_value = _first_text(
        after_payload.get("value"),
        after_payload.get("enum_option_value"),
        _enum_option_value_from_semantic_key(semantic_key),
    )
    enum_config_id = _enum_config_id_for_structural_enum(
        operation=operation,
        current_objects=current_objects,
        current_object_identities=current_object_identities,
        enum_name=enum_name,
        enum_fqn=enum_fqn,
        enum_semantic_key=enum_semantic_key or semantic_key,
    )
    enum_option_id = _stable_enum_option_id_for_create(
        enum_config_id=enum_config_id,
        option_value=option_value,
    )
    blockers = tuple(
        blocker
        for blocker, value in (
            ("missing_enum_name", enum_name),
            ("missing_enum_option_value", option_value),
            ("missing_enum_config_id", enum_config_id),
            ("missing_enum_option_id", enum_option_id),
        )
        if value is None
    )
    provider_delta_typed_operation_metadata = (
        _provider_delta_typed_operation_metadata_for_enum_option_create(
            operation=operation,
            enum_config_id=enum_config_id,
            enum_option_id=enum_option_id,
            enum_name=enum_name,
            enum_fqn=enum_fqn,
            option_value=option_value,
        )
    )
    metadata: dict[str, object] = {
        "source": "aware_meta.semantic_operation_resolution",
        "semantic_apply_boundary": "provider_delta_ontology_operation_executor",
        "provider_delta_handler_key": "enum.object_config_graph_node_function_calls",
        "provider_operation_type": "meta_ocg.enum_option.create",
        "requires_baseline_object_identity": False,
        "requires_parent_semantic_object_identity": True,
        "execution_ready": not blockers,
        "execution_preconditions": ("provider_delta_ontology_operation_executor",),
        "preview_only": True,
        "receiver_semantic_key": enum_semantic_key,
        "receiver_object_id": enum_config_id,
        "result_semantic_key": semantic_key,
        "result_object_id": enum_option_id,
        **provider_delta_typed_operation_metadata,
    }
    if enum_name is not None:
        metadata["enum_name"] = enum_name
    if enum_fqn is not None:
        metadata["enum_fqn"] = enum_fqn
    if option_value is not None:
        metadata["enum_option_value"] = option_value
    return _blocked_resolution(
        operation=operation,
        reason=(
            "meta_ocg_enum_option_create_requires_provider_delta_"
            "ontology_operation_executor"
        ),
        blockers=(
            *blockers,
            "semantic_plan_single_function_call_preview_not_supported",
            "provider_delta_enum_option_create_operation_executor_required",
        ),
        metadata=metadata,
    )


def _resolve_enum_option_update(
    *,
    operation: Mapping[str, object],
    current_objects: Mapping[str, str],
    current_object_identities: Mapping[str, Mapping[str, object]],
) -> MetaSemanticOperationResolution:
    operation_family = _string_value(operation.get("operation_family"))
    if operation_family not in {"update", "upsert"}:
        return _blocked_resolution(
            operation=operation,
            reason="meta_ocg_enum_option_update_requires_update_family",
            blockers=(
                "unsupported_operation_family:" f"{operation_family or 'unknown'}",
            ),
        )
    subject_type = _string_value(operation.get("semantic_subject_type"))
    if subject_type not in {"EnumOption", "aware_meta.EnumOption"}:
        return _blocked_resolution(
            operation=operation,
            reason="meta_ocg_enum_option_update_subject_not_supported",
            blockers=(
                "unsupported_semantic_subject_type:" f"{subject_type or 'unknown'}",
            ),
        )
    semantic_key = _semantic_key(operation)
    before_payload = _mapping_value(operation.get("before_payload"))
    after_payload = _mapping_value(operation.get("after_payload"))
    enum_name = _first_text(
        after_payload.get("enum_name"),
        before_payload.get("enum_name"),
        _enum_name_from_enum_option_semantic_key(semantic_key),
    )
    enum_semantic_key = _first_text(
        after_payload.get("enum_semantic_key"),
        after_payload.get("parent_semantic_key"),
        before_payload.get("enum_semantic_key"),
        before_payload.get("parent_semantic_key"),
        _enum_semantic_key_from_enum_option_semantic_key(semantic_key),
    )
    if enum_semantic_key is None and enum_name is not None:
        enum_semantic_key = f"meta.enum:{enum_name}"
    raw_enum_fqn = _first_text(
        after_payload.get("enum_fqn"),
        before_payload.get("enum_fqn"),
        _enum_fqn_from_enum_semantic_key(enum_semantic_key or semantic_key),
        enum_name,
    )
    enum_fqn = _enum_fqn_from_package_context(
        enum_name=enum_name,
        raw_enum_fqn=raw_enum_fqn,
        operation=operation,
    )
    option_value = _first_text(
        after_payload.get("value"),
        after_payload.get("enum_option_value"),
        before_payload.get("value"),
        before_payload.get("enum_option_value"),
        _enum_option_value_from_semantic_key(semantic_key),
    )
    position = _int_value(after_payload.get("position"))
    enum_config_id = _enum_config_id_for_structural_enum(
        operation=operation,
        current_objects=current_objects,
        current_object_identities=current_object_identities,
        enum_name=enum_name,
        enum_fqn=enum_fqn,
        enum_semantic_key=enum_semantic_key or semantic_key,
    )
    enum_option_id = _enum_option_id_for_existing(
        operation=operation,
        current_objects=current_objects,
        semantic_key=semantic_key,
        option_value=option_value,
    )
    if enum_option_id is None:
        enum_option_id = _stable_enum_option_id_for_create(
            enum_config_id=enum_config_id,
            option_value=option_value,
        )
    blockers = tuple(
        blocker
        for blocker, value in (
            ("missing_enum_name", enum_name),
            ("missing_enum_option_value", option_value),
            ("missing_enum_config_id", enum_config_id),
            ("missing_enum_option_id", enum_option_id),
            ("missing_enum_option_position", position),
        )
        if value is None
    )
    provider_delta_typed_operation_metadata = (
        _provider_delta_typed_operation_metadata_for_enum_option(
            operation=operation,
            operation_family="update",
            enum_config_id=enum_config_id,
            enum_option_id=enum_option_id,
            enum_name=enum_name,
            enum_fqn=enum_fqn,
            option_value=option_value,
        )
    )
    metadata = _enum_option_provider_delta_boundary_metadata(
        provider_operation_type="meta_ocg.enum_option.update",
        enum_semantic_key=enum_semantic_key,
        enum_config_id=enum_config_id,
        semantic_key=semantic_key,
        enum_option_id=enum_option_id,
        blockers=blockers,
        provider_delta_typed_operation_metadata=(
            provider_delta_typed_operation_metadata
        ),
    )
    if enum_name is not None:
        metadata["enum_name"] = enum_name
    if enum_fqn is not None:
        metadata["enum_fqn"] = enum_fqn
    if option_value is not None:
        metadata["enum_option_value"] = option_value
    return _blocked_resolution(
        operation=operation,
        reason=(
            "meta_ocg_enum_option_update_requires_provider_delta_"
            "ontology_operation_executor"
        ),
        blockers=(
            *blockers,
            "semantic_plan_single_function_call_preview_not_supported",
            "provider_delta_enum_option_update_operation_executor_required",
        ),
        metadata=metadata,
    )


def _resolve_enum_option_delete(
    *,
    operation: Mapping[str, object],
    current_objects: Mapping[str, str],
    current_object_identities: Mapping[str, Mapping[str, object]],
) -> MetaSemanticOperationResolution:
    operation_family = _string_value(operation.get("operation_family"))
    if operation_family != "delete":
        return _blocked_resolution(
            operation=operation,
            reason="meta_ocg_enum_option_delete_requires_delete_family",
            blockers=(
                "unsupported_operation_family:" f"{operation_family or 'unknown'}",
            ),
        )
    subject_type = _string_value(operation.get("semantic_subject_type"))
    if subject_type not in {"EnumOption", "aware_meta.EnumOption"}:
        return _blocked_resolution(
            operation=operation,
            reason="meta_ocg_enum_option_delete_subject_not_supported",
            blockers=(
                "unsupported_semantic_subject_type:" f"{subject_type or 'unknown'}",
            ),
        )
    semantic_key = _semantic_key(operation)
    before_payload = _mapping_value(operation.get("before_payload"))
    after_payload = _mapping_value(operation.get("after_payload"))
    enum_name = _first_text(
        before_payload.get("enum_name"),
        after_payload.get("enum_name"),
        _enum_name_from_enum_option_semantic_key(semantic_key),
    )
    enum_semantic_key = _first_text(
        before_payload.get("enum_semantic_key"),
        before_payload.get("parent_semantic_key"),
        after_payload.get("enum_semantic_key"),
        after_payload.get("parent_semantic_key"),
        _enum_semantic_key_from_enum_option_semantic_key(semantic_key),
    )
    if enum_semantic_key is None and enum_name is not None:
        enum_semantic_key = f"meta.enum:{enum_name}"
    raw_enum_fqn = _first_text(
        before_payload.get("enum_fqn"),
        after_payload.get("enum_fqn"),
        _enum_fqn_from_enum_semantic_key(enum_semantic_key or semantic_key),
        enum_name,
    )
    enum_fqn = _enum_fqn_from_package_context(
        enum_name=enum_name,
        raw_enum_fqn=raw_enum_fqn,
        operation=operation,
    )
    option_value = _first_text(
        before_payload.get("value"),
        before_payload.get("enum_option_value"),
        after_payload.get("value"),
        after_payload.get("enum_option_value"),
        _enum_option_value_from_semantic_key(semantic_key),
    )
    enum_config_id = _enum_config_id_for_structural_enum(
        operation=operation,
        current_objects=current_objects,
        current_object_identities=current_object_identities,
        enum_name=enum_name,
        enum_fqn=enum_fqn,
        enum_semantic_key=enum_semantic_key or semantic_key,
    )
    enum_option_id = _enum_option_id_for_existing(
        operation=operation,
        current_objects=current_objects,
        semantic_key=semantic_key,
        option_value=option_value,
    )
    blockers = tuple(
        blocker
        for blocker, value in (
            ("missing_enum_name", enum_name),
            ("missing_enum_option_value", option_value),
            ("missing_enum_config_id", enum_config_id),
            ("missing_enum_option_id", enum_option_id),
        )
        if value is None
    )
    provider_delta_typed_operation_metadata = (
        _provider_delta_typed_operation_metadata_for_enum_option(
            operation=operation,
            operation_family="delete",
            enum_config_id=enum_config_id,
            enum_option_id=enum_option_id,
            enum_name=enum_name,
            enum_fqn=enum_fqn,
            option_value=option_value,
        )
    )
    metadata = _enum_option_provider_delta_boundary_metadata(
        provider_operation_type="meta_ocg.enum_option.delete",
        enum_semantic_key=enum_semantic_key,
        enum_config_id=enum_config_id,
        semantic_key=semantic_key,
        enum_option_id=enum_option_id,
        blockers=blockers,
        provider_delta_typed_operation_metadata=(
            provider_delta_typed_operation_metadata
        ),
    )
    if enum_name is not None:
        metadata["enum_name"] = enum_name
    if enum_fqn is not None:
        metadata["enum_fqn"] = enum_fqn
    if option_value is not None:
        metadata["enum_option_value"] = option_value
    return _blocked_resolution(
        operation=operation,
        reason=(
            "meta_ocg_enum_option_delete_requires_provider_delta_"
            "ontology_operation_executor"
        ),
        blockers=(
            *blockers,
            "semantic_plan_single_function_call_preview_not_supported",
            "provider_delta_enum_option_delete_operation_executor_required",
        ),
        metadata=metadata,
    )


def _resolve_enum_option_unsupported_fallback(
    *,
    operation: Mapping[str, object],
    reason: str,
    blockers: tuple[str, ...],
) -> MetaSemanticOperationResolution:
    operation_family = _string_value(operation.get("operation_family")) or "unknown"
    semantic_key = _semantic_key(operation)
    before_payload = _mapping_value(operation.get("before_payload"))
    after_payload = _mapping_value(operation.get("after_payload"))
    enum_name = _first_text(
        after_payload.get("enum_name"),
        before_payload.get("enum_name"),
        _enum_name_from_enum_option_semantic_key(semantic_key),
    )
    option_value = _first_text(
        after_payload.get("value"),
        after_payload.get("enum_option_value"),
        before_payload.get("value"),
        before_payload.get("enum_option_value"),
        _enum_option_value_from_semantic_key(semantic_key),
    )
    metadata: dict[str, object] = {
        "source": "aware_meta.semantic_operation_resolution",
        "semantic_apply_boundary": "provider_delta_ontology_operation_executor",
        "provider_delta_handler_key": "enum.object_config_graph_node_function_calls",
        "provider_operation_type": (
            "meta_ocg.enum_option.delete"
            if operation_family == "delete"
            else "meta_ocg.enum_option.update"
        ),
        "execution_ready": False,
        "execution_preconditions": ("explicit_fallback_required",),
        "preview_only": True,
        "fallback_required": True,
        "fallback_mode": "render_all_required",
        "generated_materialization_intent_status": (
            "generated_materialization_intent_blocked"
        ),
        "generated_materialization_intent_reason": reason,
        "generated_materialization_intent_blockers": blockers,
        "generated_materialization_intent": {
            "intent_kind": "meta_enum_option_fallback_required",
            "contract_version": (
                META_ENUM_OPTION_CREATE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION
            ),
            "status": "generated_materialization_intent_blocked",
            "reason": reason,
            "generated_materialization_provider_key": "aware_meta",
            "blockers": blockers,
            "fallback_mode": "render_all_required",
        },
    }
    if enum_name is not None:
        metadata["enum_name"] = enum_name
    if option_value is not None:
        metadata["enum_option_value"] = option_value
    return _blocked_resolution(
        operation=operation,
        reason=reason,
        blockers=blockers,
        metadata=metadata,
    )


def _provider_delta_typed_operation_metadata_for_enum_option_create(
    *,
    operation: Mapping[str, object],
    enum_config_id: str | None,
    enum_option_id: str | None,
    enum_name: str | None,
    enum_fqn: str | None,
    option_value: str | None,
) -> dict[str, object]:
    from aware_meta.materialization.deltas.source_projection import (  # noqa: WPS433,E501
        typed_operation_plan_from_semantic_source_meaning,
    )

    typed_operation_plan = typed_operation_plan_from_semantic_source_meaning(
        semantic_status={},
        typed_operations=(operation,),
    )
    if enum_config_id is not None and enum_option_id is not None:
        typed_operation_plan = _enum_option_create_typed_operation_plan_with_identity(
            typed_operation_plan=typed_operation_plan,
            enum_config_id=enum_config_id,
            enum_option_id=enum_option_id,
            enum_name=enum_name,
            enum_fqn=enum_fqn,
            option_value=option_value,
        )
    typed_operations = tuple(
        _tuple_values(typed_operation_plan.get("typed_operations"))
    )
    typed_operation = next(
        (item for item in typed_operations if isinstance(item, Mapping)),
        None,
    )
    status = _string_value(typed_operation_plan.get("status"))
    ready = status == "typed_operation_plan_ready" and typed_operation is not None
    metadata: dict[str, object] = {
        "provider_delta_typed_operation_status": (
            "provider_delta_typed_operation_ready"
            if ready
            else "provider_delta_typed_operation_blocked"
        ),
        "provider_delta_typed_operation_reason": (
            "enum_option_create_provider_delta_operation_ready"
            if ready
            else "enum_option_create_provider_delta_operation_blocked"
        ),
        "provider_delta_typed_operation_plan": typed_operation_plan,
    }
    if typed_operation is not None:
        metadata["provider_delta_typed_operation"] = dict(typed_operation)
    if not ready:
        metadata["provider_delta_typed_operation_blockers"] = (
            "enum_option_create_provider_delta_typed_operation_unavailable",
        )
    metadata.update(
        _enum_option_create_generated_materialization_intent_metadata(
            typed_operation_plan=typed_operation_plan,
            typed_operation=typed_operation,
            ready=ready,
        )
    )
    return metadata


def _provider_delta_typed_operation_metadata_for_enum_option(
    *,
    operation: Mapping[str, object],
    operation_family: str,
    enum_config_id: str | None,
    enum_option_id: str | None,
    enum_name: str | None,
    enum_fqn: str | None,
    option_value: str | None,
) -> dict[str, object]:
    from aware_meta.materialization.deltas.source_projection import (  # noqa: WPS433,E501
        typed_operation_plan_from_semantic_source_meaning,
    )

    typed_operation_plan = typed_operation_plan_from_semantic_source_meaning(
        semantic_status={},
        typed_operations=(operation,),
    )
    if enum_config_id is not None and enum_option_id is not None:
        typed_operation_plan = _enum_option_typed_operation_plan_with_identity(
            typed_operation_plan=typed_operation_plan,
            enum_config_id=enum_config_id,
            enum_option_id=enum_option_id,
            enum_name=enum_name,
            enum_fqn=enum_fqn,
            option_value=option_value,
        )
    typed_operations = tuple(
        _tuple_values(typed_operation_plan.get("typed_operations"))
    )
    typed_operation = next(
        (item for item in typed_operations if isinstance(item, Mapping)),
        None,
    )
    status = _string_value(typed_operation_plan.get("status"))
    ready = status == "typed_operation_plan_ready" and typed_operation is not None
    metadata: dict[str, object] = {
        "provider_delta_typed_operation_status": (
            "provider_delta_typed_operation_ready"
            if ready
            else "provider_delta_typed_operation_blocked"
        ),
        "provider_delta_typed_operation_reason": (
            f"enum_option_{operation_family}_provider_delta_operation_ready"
            if ready
            else f"enum_option_{operation_family}_provider_delta_operation_blocked"
        ),
        "provider_delta_typed_operation_plan": typed_operation_plan,
    }
    if typed_operation is not None:
        metadata["provider_delta_typed_operation"] = dict(typed_operation)
    if not ready:
        metadata["provider_delta_typed_operation_blockers"] = (
            f"enum_option_{operation_family}_provider_delta_typed_operation_unavailable",
        )
    metadata.update(
        _enum_option_generated_materialization_intent_metadata(
            typed_operation_plan=typed_operation_plan,
            typed_operation=typed_operation,
            operation_family=operation_family,
            ready=ready,
        )
    )
    return metadata


def _enum_option_provider_delta_boundary_metadata(
    *,
    provider_operation_type: str,
    enum_semantic_key: str | None,
    enum_config_id: str | None,
    semantic_key: str,
    enum_option_id: str | None,
    blockers: tuple[str, ...],
    provider_delta_typed_operation_metadata: Mapping[str, object],
) -> dict[str, object]:
    return {
        "source": "aware_meta.semantic_operation_resolution",
        "semantic_apply_boundary": "provider_delta_ontology_operation_executor",
        "provider_delta_handler_key": "enum.object_config_graph_node_function_calls",
        "provider_operation_type": provider_operation_type,
        "requires_baseline_object_identity": True,
        "requires_parent_semantic_object_identity": True,
        "execution_ready": not blockers,
        "execution_preconditions": ("provider_delta_ontology_operation_executor",),
        "preview_only": True,
        "receiver_semantic_key": enum_semantic_key,
        "receiver_object_id": enum_config_id,
        "result_semantic_key": semantic_key,
        "result_object_id": enum_option_id,
        **dict(provider_delta_typed_operation_metadata),
    }


def _enum_option_create_generated_materialization_intent_metadata(
    *,
    typed_operation_plan: Mapping[str, object],
    typed_operation: Mapping[str, object] | None,
    ready: bool,
) -> dict[str, object]:
    blockers: tuple[str, ...] = (
        ("enum_option_create_generated_materialization_typed_plan_unavailable",)
        if not ready
        else ()
    )
    status = (
        "generated_materialization_intent_ready"
        if ready
        else "generated_materialization_intent_blocked"
    )
    reason = (
        "enum_option_create_generated_materialization_typed_plan_unavailable"
        if not ready
        else "enum_option_create_generated_materialization_intent_ready"
    )
    intent: dict[str, object] = {
        "intent_kind": "meta_enum_option_create_generated_materialization_intent",
        "contract_version": (
            META_ENUM_OPTION_CREATE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION
        ),
        "status": status,
        "reason": reason,
        "generated_materialization_provider_key": "aware_meta",
        "blockers": blockers,
        "provider_delta_typed_operation_plan": dict(typed_operation_plan),
    }
    if ready:
        intent.update(
            {
                "renderer_key": "python.orm.enum",
                "policy_key": "aware_meta.python_orm.enum.option_line",
                "materialization_target": "python_enum_option_line",
            }
        )
    metadata: dict[str, object] = {
        "generated_materialization_intent_status": status,
        "generated_materialization_intent_reason": reason,
        "generated_materialization_intent_blockers": blockers,
        "generated_materialization_intent": intent,
    }
    if ready:
        metadata["provider_delta_generated_materialization_typed_operation_plan"] = (
            typed_operation_plan
        )
    if typed_operation is not None:
        typed_operation_payload = dict(typed_operation)
        intent["provider_delta_typed_operation"] = typed_operation_payload
    return metadata


def _enum_option_generated_materialization_intent_metadata(
    *,
    typed_operation_plan: Mapping[str, object],
    typed_operation: Mapping[str, object] | None,
    operation_family: str,
    ready: bool,
) -> dict[str, object]:
    blockers: tuple[str, ...] = (
        (
            f"enum_option_{operation_family}_generated_materialization_"
            "typed_plan_unavailable",
        )
        if not ready
        else ()
    )
    status = (
        "generated_materialization_intent_ready"
        if ready
        else "generated_materialization_intent_blocked"
    )
    reason = (
        f"enum_option_{operation_family}_generated_materialization_typed_plan_unavailable"
        if not ready
        else f"enum_option_{operation_family}_generated_materialization_intent_ready"
    )
    intent: dict[str, object] = {
        "intent_kind": f"meta_enum_option_{operation_family}_generated_materialization_intent",
        "contract_version": (
            META_ENUM_OPTION_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION
        ),
        "status": status,
        "reason": reason,
        "generated_materialization_provider_key": "aware_meta",
        "blockers": blockers,
        "provider_delta_typed_operation_plan": dict(typed_operation_plan),
    }
    if ready:
        intent.update(
            {
                "renderer_key": "python.orm.enum",
                "policy_key": "aware_meta.python_orm.enum.option_line",
                "materialization_target": "python_enum_option_line",
            }
        )
    metadata: dict[str, object] = {
        "generated_materialization_intent_status": status,
        "generated_materialization_intent_reason": reason,
        "generated_materialization_intent_blockers": blockers,
        "generated_materialization_intent": intent,
    }
    if ready:
        metadata["provider_delta_generated_materialization_typed_operation_plan"] = (
            typed_operation_plan
        )
    if typed_operation is not None:
        typed_operation_payload = dict(typed_operation)
        intent["provider_delta_typed_operation"] = typed_operation_payload
    return metadata


def _enum_option_create_typed_operation_plan_with_identity(
    *,
    typed_operation_plan: Mapping[str, object],
    enum_config_id: str,
    enum_option_id: str,
    enum_name: str | None,
    enum_fqn: str | None,
    option_value: str | None,
) -> dict[str, object]:
    enriched_plan = dict(typed_operation_plan)
    enriched_plan["typed_operations"] = tuple(
        (
            _enum_option_create_typed_operation_with_identity(
                typed_operation=item,
                enum_config_id=enum_config_id,
                enum_option_id=enum_option_id,
                enum_name=enum_name,
                enum_fqn=enum_fqn,
                option_value=option_value,
            )
            if isinstance(item, Mapping)
            else item
        )
        for item in _tuple_values(typed_operation_plan.get("typed_operations"))
    )
    return enriched_plan


def _enum_option_create_typed_operation_with_identity(
    *,
    typed_operation: Mapping[str, object],
    enum_config_id: str,
    enum_option_id: str,
    enum_name: str | None,
    enum_fqn: str | None,
    option_value: str | None,
) -> dict[str, object]:
    enriched = dict(typed_operation)
    current = _mapping_value(enriched.get("current"))
    payload = _mapping_value(current.get("payload"))
    for target in (current, payload):
        target.setdefault("enum_config_id", enum_config_id)
        target.setdefault("enum_option_id", enum_option_id)
        target.setdefault("entity_id", enum_option_id)
        if enum_name is not None:
            target.setdefault("enum_name", enum_name)
        if enum_fqn is not None:
            target.setdefault("enum_fqn", enum_fqn)
        if option_value is not None:
            target.setdefault("value", option_value)
            target.setdefault("entity_name", option_value)
    if payload:
        current["payload"] = payload
    enriched["current"] = current
    return enriched


def _enum_option_typed_operation_plan_with_identity(
    *,
    typed_operation_plan: Mapping[str, object],
    enum_config_id: str,
    enum_option_id: str,
    enum_name: str | None,
    enum_fqn: str | None,
    option_value: str | None,
) -> dict[str, object]:
    enriched_plan = dict(typed_operation_plan)
    enriched_plan["typed_operations"] = tuple(
        (
            _enum_option_typed_operation_with_identity(
                typed_operation=item,
                enum_config_id=enum_config_id,
                enum_option_id=enum_option_id,
                enum_name=enum_name,
                enum_fqn=enum_fqn,
                option_value=option_value,
            )
            if isinstance(item, Mapping)
            else item
        )
        for item in _tuple_values(typed_operation_plan.get("typed_operations"))
    )
    return enriched_plan


def _enum_option_typed_operation_with_identity(
    *,
    typed_operation: Mapping[str, object],
    enum_config_id: str,
    enum_option_id: str,
    enum_name: str | None,
    enum_fqn: str | None,
    option_value: str | None,
) -> dict[str, object]:
    enriched = dict(typed_operation)
    current = _mapping_value(enriched.get("current"))
    current_payload = _mapping_value(current.get("payload"))
    baseline = _mapping_value(enriched.get("baseline"))
    baseline_object = _mapping_value(baseline.get("object"))
    baseline_payload = _mapping_value(baseline_object.get("payload"))
    for target in (current, current_payload, baseline_object, baseline_payload):
        target.setdefault("enum_config_id", enum_config_id)
        target.setdefault("enum_option_id", enum_option_id)
        target.setdefault("entity_id", enum_option_id)
        if enum_name is not None:
            target.setdefault("enum_name", enum_name)
        if enum_fqn is not None:
            target.setdefault("enum_fqn", enum_fqn)
        if option_value is not None:
            target.setdefault("value", option_value)
            target.setdefault("entity_name", option_value)
    if current_payload:
        current["payload"] = current_payload
    if baseline_payload:
        baseline_object["payload"] = baseline_payload
    if baseline_object:
        baseline["object"] = baseline_object
    enriched["baseline"] = baseline
    enriched["current"] = current
    return enriched


def _stable_enum_option_id_for_create(
    *,
    enum_config_id: str | None,
    option_value: str | None,
) -> str | None:
    enum_config_uuid = _uuid_value(enum_config_id)
    if enum_config_uuid is None or option_value is None:
        return None
    from aware_meta.graph.config.stable_ids import (  # noqa: WPS433
        stable_enum_option_id,
    )

    return str(
        stable_enum_option_id(enum_config_id=enum_config_uuid, value=option_value)
    )

