from __future__ import annotations

from collections.abc import Mapping

from aware_meta.semantic_operation_resolution import (
    META_CLASS_CREATE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
    META_CLASS_DELETE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
    META_CLASS_DESCRIPTION_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
    META_OBJECT_CONFIG_GRAPH_CLASS_CREATE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_CLASS_DELETE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_CLASS_DESCRIPTION_UPDATE_OPERATION,
    MetaSemanticOperationResolution,
    _blocked_resolution,
    _class_config_id_for_class_update,
    _class_fqn_from_class_semantic_key,
    _class_fqn_from_package_context,
    _class_name_from_class_semantic_key,
    _enum_create_graph_object_id,
    _enum_create_graph_source_object_id,
    _first_text,
    _graph_semantic_key_from_class_semantic_key,
    _graph_semantic_key_from_operation_package_context,
    _mapping_value,
    _optional_text,
    _semantic_key,
    _set_missing_text,
    _stable_class_config_id_for_create,
    _stable_object_config_graph_node_id_for_class_create,
    _string_value,
    _tuple_values,
)


def resolve_class_config_semantic_operation(
    *,
    operation: Mapping[str, object],
    operation_group: tuple[Mapping[str, object], ...],
    current_objects: Mapping[str, str],
    current_object_identities: Mapping[str, Mapping[str, object]],
) -> MetaSemanticOperationResolution:
    del operation_group
    operation_type = _string_value(operation.get("semantic_operation_type"))
    if operation_type == META_OBJECT_CONFIG_GRAPH_CLASS_CREATE_OPERATION:
        return _resolve_class_create(
            operation=operation,
            current_objects=current_objects,
            current_object_identities=current_object_identities,
        )
    if operation_type == META_OBJECT_CONFIG_GRAPH_CLASS_DELETE_OPERATION:
        return _resolve_class_delete(
            operation=operation,
            current_objects=current_objects,
            current_object_identities=current_object_identities,
        )
    if operation_type == META_OBJECT_CONFIG_GRAPH_CLASS_DESCRIPTION_UPDATE_OPERATION:
        return _resolve_class_description_update(
            operation=operation,
            current_objects=current_objects,
        )
    return _blocked_resolution(
        operation=operation,
        reason="meta_ocg_class_operation_type_not_supported",
        blockers=(f"unsupported_operation_type:{operation_type or 'unknown'}",),
    )


def _resolve_class_description_update(
    *,
    operation: Mapping[str, object],
    current_objects: Mapping[str, str],
) -> MetaSemanticOperationResolution:
    if _string_value(operation.get("operation_family")) not in {"update", "upsert"}:
        return _blocked_resolution(
            operation=operation,
            reason="meta_ocg_class_description_update_requires_update_family",
            blockers=(
                "unsupported_operation_family:"
                f"{_string_value(operation.get('operation_family')) or 'unknown'}",
            ),
        )
    if _string_value(operation.get("semantic_subject_type")) not in {
        "ClassConfig",
        "aware_meta.ClassConfig",
    }:
        return _blocked_resolution(
            operation=operation,
            reason="meta_ocg_class_description_update_subject_not_supported",
            blockers=(
                "unsupported_semantic_subject_type:"
                f"{_string_value(operation.get('semantic_subject_type')) or 'unknown'}",
            ),
        )
    if _optional_text(operation.get("field_path")) not in {
        None,
        "description",
        "class_description",
    }:
        return _blocked_resolution(
            operation=operation,
            reason="meta_ocg_class_description_update_field_not_supported",
            blockers=(
                "unsupported_field_path:"
                f"{_string_value(operation.get('field_path')) or 'unknown'}",
            ),
        )

    semantic_key = _semantic_key(operation)
    before_payload = _mapping_value(operation.get("before_payload"))
    after_payload = _mapping_value(operation.get("after_payload"))
    class_name = _first_text(
        after_payload.get("class_name"),
        before_payload.get("class_name"),
        _class_name_from_class_semantic_key(semantic_key),
    )
    description = _first_text(
        after_payload.get("description"),
        after_payload.get("class_description"),
    )
    blockers = tuple(
        blocker
        for blocker, value in (
            ("missing_class_name", class_name),
            ("missing_description", description),
        )
        if value is None
    )
    receiver_semantic_key = (
        f"meta.class:{class_name}" if class_name is not None else semantic_key
    )
    receiver_object_id = _class_config_id_for_class_update(
        operation=operation,
        current_objects=current_objects,
        class_name=class_name,
        receiver_semantic_key=receiver_semantic_key,
    )
    provider_delta_typed_operation_metadata = (
        _provider_delta_typed_operation_metadata_for_class_description_update(
            operation=operation,
            class_config_id=receiver_object_id,
        )
    )
    metadata: dict[str, object] = {
        "source": "aware_meta.semantic_operation_resolution",
        "semantic_apply_boundary": "provider_delta_ontology_operation_executor",
        "provider_delta_handler_key": "class.object_config_graph_node_function_calls",
        "provider_operation_type": "meta_ocg.class.update",
        "requires_baseline_object_identity": True,
        "execution_ready": not blockers and receiver_object_id is not None,
        "execution_preconditions": ("provider_delta_ontology_operation_executor",),
        "preview_only": True,
        "receiver_semantic_key": receiver_semantic_key,
        "receiver_object_id": receiver_object_id,
        **provider_delta_typed_operation_metadata,
    }
    if class_name is not None:
        metadata["class_name"] = class_name
    return _blocked_resolution(
        operation=operation,
        reason=(
            "meta_ocg_class_description_update_requires_provider_delta_"
            "ontology_operation_executor"
        ),
        blockers=(
            *blockers,
            "semantic_plan_single_function_call_preview_not_supported",
            "provider_delta_class_update_operation_executor_required",
        ),
        metadata=metadata,
    )


def _provider_delta_typed_operation_metadata_for_class_description_update(
    *,
    operation: Mapping[str, object],
    class_config_id: str | None,
) -> dict[str, object]:
    from aware_meta.materialization.deltas.source_projection import (  # noqa: WPS433,E501
        typed_operation_plan_from_semantic_source_meaning,
    )

    typed_operation_plan = typed_operation_plan_from_semantic_source_meaning(
        semantic_status={},
        typed_operations=(operation,),
    )
    if class_config_id is not None:
        typed_operation_plan = _class_update_typed_operation_plan_with_identity(
            typed_operation_plan=typed_operation_plan,
            class_config_id=class_config_id,
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
            "class_description_provider_delta_operation_ready"
            if ready
            else "class_description_provider_delta_operation_blocked"
        ),
        "provider_delta_typed_operation_plan": typed_operation_plan,
    }
    if typed_operation is not None:
        metadata["provider_delta_typed_operation"] = dict(typed_operation)
    if not ready:
        metadata["provider_delta_typed_operation_blockers"] = (
            "class_description_provider_delta_typed_operation_unavailable",
        )
    metadata.update(
        _class_description_generated_materialization_intent_metadata(
            typed_operation_plan=typed_operation_plan,
            typed_operation=typed_operation,
            ready=ready,
        )
    )
    return metadata


def _class_description_generated_materialization_intent_metadata(
    *,
    typed_operation_plan: Mapping[str, object],
    typed_operation: Mapping[str, object] | None,
    ready: bool,
) -> dict[str, object]:
    blockers: tuple[str, ...] = (
        ()
        if ready
        else ("class_description_generated_materialization_typed_plan_unavailable",)
    )
    status = (
        "generated_materialization_intent_ready"
        if ready
        else "generated_materialization_intent_blocked"
    )
    reason = (
        "class_description_generated_materialization_intent_ready"
        if ready
        else "class_description_generated_materialization_intent_blocked"
    )
    intent: dict[str, object] = {
        "intent_kind": "meta_class_description_generated_materialization_intent",
        "contract_version": (
            META_CLASS_DESCRIPTION_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION
        ),
        "status": status,
        "reason": reason,
        "generated_materialization_provider_key": "aware_meta",
        "blockers": blockers,
        "provider_delta_typed_operation_plan": dict(typed_operation_plan),
    }
    metadata: dict[str, object] = {
        "generated_materialization_intent_status": status,
        "generated_materialization_intent_reason": reason,
        "generated_materialization_intent_blockers": blockers,
        "generated_materialization_intent": intent,
    }
    if ready:
        metadata["provider_delta_generated_materialization_typed_operation_plan"] = (
            dict(typed_operation_plan)
        )
    if typed_operation is not None:
        typed_operation_payload = dict(typed_operation)
        intent["provider_delta_typed_operation"] = typed_operation_payload
        if ready:
            metadata["provider_delta_generated_materialization_typed_operation"] = (
                typed_operation_payload
            )
    return metadata


def _class_update_typed_operation_plan_with_identity(
    *,
    typed_operation_plan: Mapping[str, object],
    class_config_id: str,
) -> dict[str, object]:
    enriched_plan = dict(typed_operation_plan)
    enriched_plan["typed_operations"] = tuple(
        (
            _class_update_typed_operation_with_identity(
                typed_operation=item,
                class_config_id=class_config_id,
            )
            if isinstance(item, Mapping)
            else item
        )
        for item in _tuple_values(typed_operation_plan.get("typed_operations"))
    )
    return enriched_plan


def _class_update_typed_operation_with_identity(
    *,
    typed_operation: Mapping[str, object],
    class_config_id: str,
) -> dict[str, object]:
    enriched = dict(typed_operation)
    current = _mapping_value(enriched.get("current"))
    payload = _mapping_value(current.get("payload"))
    current.setdefault("entity_id", class_config_id)
    current.setdefault("class_config_id", class_config_id)
    payload.setdefault("entity_id", class_config_id)
    payload.setdefault("class_config_id", class_config_id)
    if payload:
        current["payload"] = payload
    enriched["current"] = current
    return enriched


def _resolve_class_create(
    *,
    operation: Mapping[str, object],
    current_objects: Mapping[str, str],
    current_object_identities: Mapping[str, Mapping[str, object]],
) -> MetaSemanticOperationResolution:
    operation_family = _string_value(operation.get("operation_family"))
    if operation_family not in {"create", "upsert"}:
        return _blocked_resolution(
            operation=operation,
            reason="meta_ocg_class_create_requires_create_family",
            blockers=(
                "unsupported_operation_family:" f"{operation_family or 'unknown'}",
            ),
        )
    subject_type = _string_value(operation.get("semantic_subject_type"))
    if subject_type not in {
        "ClassConfig",
        "aware_meta.ClassConfig",
        "ObjectConfigGraphNode",
        "aware_meta.ObjectConfigGraphNode",
    }:
        return _blocked_resolution(
            operation=operation,
            reason="meta_ocg_class_create_subject_not_supported",
            blockers=(
                "unsupported_semantic_subject_type:" f"{subject_type or 'unknown'}",
            ),
        )

    semantic_key = _semantic_key(operation)
    after_payload = _mapping_value(operation.get("after_payload"))
    class_name = _first_text(
        after_payload.get("class_name"),
        after_payload.get("name"),
        _class_name_from_class_semantic_key(semantic_key),
    )
    raw_class_fqn = _first_text(
        after_payload.get("class_fqn"),
        after_payload.get("node_key"),
        _class_fqn_from_class_semantic_key(semantic_key),
        class_name,
    )
    class_fqn = _class_fqn_from_package_context(
        class_name=class_name,
        raw_class_fqn=raw_class_fqn,
        operation=operation,
    )
    graph_semantic_key = _first_text(
        after_payload.get("graph_semantic_key"),
        operation.get("graph_semantic_key"),
        _graph_semantic_key_from_class_semantic_key(semantic_key),
        _graph_semantic_key_from_operation_package_context(operation),
    )
    graph_receiver_object_id = _enum_create_graph_object_id(
        operation=operation,
        current_objects=current_objects,
        graph_semantic_key=graph_semantic_key,
    )
    graph_source_object_id = _enum_create_graph_source_object_id(
        operation=operation,
        current_object_identities=current_object_identities,
        graph_semantic_key=graph_semantic_key,
        fallback_object_id=graph_receiver_object_id,
    )
    object_config_graph_node_id = _stable_object_config_graph_node_id_for_class_create(
        graph_object_id=graph_source_object_id,
        class_fqn=class_fqn,
    )
    class_config_id = _stable_class_config_id_for_create(
        object_config_graph_node_id=object_config_graph_node_id,
        class_fqn=class_fqn,
    )
    blockers = tuple(
        blocker
        for blocker, value in (
            ("missing_class_name", class_name),
            ("missing_class_fqn", class_fqn),
            ("missing_graph_semantic_key", graph_semantic_key),
            ("missing_object_config_graph_id", graph_source_object_id),
            ("missing_object_config_graph_node_id", object_config_graph_node_id),
            ("missing_class_config_id", class_config_id),
        )
        if value is None
    )
    provider_delta_typed_operation_metadata = (
        _provider_delta_typed_operation_metadata_for_class_create(
            operation=operation,
            graph_semantic_key=graph_semantic_key,
            graph_object_id=graph_source_object_id,
            object_config_graph_node_id=object_config_graph_node_id,
            class_config_id=class_config_id,
            class_name=class_name,
            class_fqn=class_fqn,
        )
    )
    metadata: dict[str, object] = {
        "source": "aware_meta.semantic_operation_resolution",
        "semantic_apply_boundary": "provider_delta_ontology_operation_executor",
        "provider_delta_handler_key": "class.object_config_graph_node_function_calls",
        "provider_operation_type": "meta_ocg.class.create",
        "requires_baseline_object_identity": False,
        "requires_graph_semantic_object_identity": True,
        "execution_ready": not blockers,
        "execution_preconditions": ("provider_delta_ontology_operation_executor",),
        "preview_only": True,
        "receiver_semantic_key": graph_semantic_key,
        "receiver_object_id": graph_source_object_id,
        "result_semantic_key": semantic_key,
        "result_object_id": class_config_id,
        "object_config_graph_node_id": object_config_graph_node_id,
        **provider_delta_typed_operation_metadata,
    }
    if (
        graph_receiver_object_id is not None
        and graph_receiver_object_id != graph_source_object_id
    ):
        metadata["semantic_apply_receiver_object_id"] = graph_receiver_object_id
        metadata["semantic_source_object_id"] = graph_source_object_id
    if class_name is not None:
        metadata["class_name"] = class_name
    if class_fqn is not None:
        metadata["class_fqn"] = class_fqn
    return _blocked_resolution(
        operation=operation,
        reason=(
            "meta_ocg_class_create_requires_provider_delta_"
            "ontology_operation_executor"
        ),
        blockers=(
            *blockers,
            "semantic_plan_single_function_call_preview_not_supported",
            "provider_delta_class_create_operation_executor_required",
        ),
        metadata=metadata,
    )


def _provider_delta_typed_operation_metadata_for_class_create(
    *,
    operation: Mapping[str, object],
    graph_semantic_key: str | None,
    graph_object_id: str | None,
    object_config_graph_node_id: str | None,
    class_config_id: str | None,
    class_name: str | None,
    class_fqn: str | None,
) -> dict[str, object]:
    from aware_meta.materialization.deltas.source_projection import (  # noqa: WPS433,E501
        typed_operation_plan_from_semantic_source_meaning,
    )

    typed_operation_plan = typed_operation_plan_from_semantic_source_meaning(
        semantic_status={},
        typed_operations=(operation,),
    )
    if (
        graph_semantic_key is not None
        and graph_object_id is not None
        and object_config_graph_node_id is not None
        and class_config_id is not None
    ):
        typed_operation_plan = _class_create_typed_operation_plan_with_identity(
            typed_operation_plan=typed_operation_plan,
            graph_semantic_key=graph_semantic_key,
            graph_object_id=graph_object_id,
            object_config_graph_node_id=object_config_graph_node_id,
            class_config_id=class_config_id,
            class_name=class_name,
            class_fqn=class_fqn,
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
    generated_materialization_metadata = (
        _class_create_generated_materialization_intent_metadata(
            typed_operation_plan=typed_operation_plan,
            typed_operation=typed_operation,
            ready=ready,
        )
    )
    metadata: dict[str, object] = {
        "provider_delta_typed_operation_status": (
            "provider_delta_typed_operation_ready"
            if ready
            else "provider_delta_typed_operation_blocked"
        ),
        "provider_delta_typed_operation_reason": (
            "class_create_provider_delta_operation_ready"
            if ready
            else "class_create_provider_delta_operation_blocked"
        ),
        "provider_delta_typed_operation_plan": typed_operation_plan,
        **generated_materialization_metadata,
    }
    if typed_operation is not None:
        metadata["provider_delta_typed_operation"] = dict(typed_operation)
    if not ready:
        metadata["provider_delta_typed_operation_blockers"] = (
            "class_create_provider_delta_typed_operation_unavailable",
        )
    return metadata


def _class_create_generated_materialization_intent_metadata(
    *,
    typed_operation_plan: Mapping[str, object],
    typed_operation: Mapping[str, object] | None,
    ready: bool,
) -> dict[str, object]:
    blockers: tuple[str, ...] = (
        ("class_create_generated_materialization_typed_plan_unavailable",)
        if not ready
        else ()
    )
    status = (
        "generated_materialization_intent_ready"
        if ready
        else "generated_materialization_intent_blocked"
    )
    reason = (
        "class_create_generated_materialization_typed_plan_unavailable"
        if not ready
        else "class_create_generated_materialization_intent_ready"
    )
    intent: dict[str, object] = {
        "intent_kind": "meta_class_create_generated_materialization_intent",
        "contract_version": (
            META_CLASS_CREATE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION
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
                "renderer_key": "python.orm.class",
                "policy_key": "aware_meta.python_orm.class.create",
                "materialization_target": "python_orm_class",
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


def _class_create_typed_operation_plan_with_identity(
    *,
    typed_operation_plan: Mapping[str, object],
    graph_semantic_key: str,
    graph_object_id: str,
    object_config_graph_node_id: str,
    class_config_id: str,
    class_name: str | None,
    class_fqn: str | None,
) -> dict[str, object]:
    enriched_plan = dict(typed_operation_plan)
    enriched_plan["typed_operations"] = tuple(
        (
            _class_create_typed_operation_with_identity(
                typed_operation=item,
                graph_semantic_key=graph_semantic_key,
                graph_object_id=graph_object_id,
                object_config_graph_node_id=object_config_graph_node_id,
                class_config_id=class_config_id,
                class_name=class_name,
                class_fqn=class_fqn,
            )
            if isinstance(item, Mapping)
            else item
        )
        for item in _tuple_values(typed_operation_plan.get("typed_operations"))
    )
    semantic_object_anchors = tuple(
        _tuple_values(typed_operation_plan.get("semantic_object_anchors"))
    )
    enriched_plan["semantic_object_anchors"] = (
        *semantic_object_anchors,
        {
            "operation_kind": "meta_ocg_provider_delta_semantic_object_anchor",
            "operation_key": f"meta_ocg.graph.anchor:{graph_semantic_key}",
            "operation_family": "anchor",
            "provider_operation_type": "meta_ocg.graph.anchor",
            "semantic_key": graph_semantic_key,
            "ontology_subject_kind": "graph",
            "baseline": {
                "object_id": graph_object_id,
                "entity_id": graph_object_id,
            },
            "current": {
                "entity_id": graph_object_id,
                "object_id": graph_object_id,
                "payload": {
                    "entity_id": graph_object_id,
                    "object_id": graph_object_id,
                },
            },
            "source_refs": (),
        },
    )
    return enriched_plan


def _class_create_typed_operation_with_identity(
    *,
    typed_operation: Mapping[str, object],
    graph_semantic_key: str,
    graph_object_id: str,
    object_config_graph_node_id: str,
    class_config_id: str,
    class_name: str | None,
    class_fqn: str | None,
) -> dict[str, object]:
    enriched = dict(typed_operation)
    current = _mapping_value(enriched.get("current"))
    payload = _mapping_value(current.get("payload"))
    for target in (current, payload):
        _set_missing_text(target, "graph_semantic_key", graph_semantic_key)
        _set_missing_text(target, "graph_object_id", graph_object_id)
        _set_missing_text(target, "object_config_graph_id", graph_object_id)
        target["object_config_graph_node_id"] = object_config_graph_node_id
        target["node_id"] = object_config_graph_node_id
        target["class_config_id"] = class_config_id
        target["entity_id"] = class_config_id
        if class_name is not None:
            _set_missing_text(target, "name", class_name)
            _set_missing_text(target, "entity_name", class_name)
        if class_fqn is not None:
            target["class_fqn"] = class_fqn
            target["node_key"] = class_fqn
    if payload:
        current["payload"] = payload
    enriched["current"] = current
    return enriched


def _provider_delta_typed_operation_metadata_for_class_delete(
    *,
    operation: Mapping[str, object],
    graph_semantic_key: str | None,
    graph_object_id: str | None,
    object_config_graph_node_id: str | None,
    class_config_id: str | None,
    class_name: str | None,
    class_fqn: str | None,
) -> dict[str, object]:
    from aware_meta.materialization.deltas.source_projection import (  # noqa: WPS433,E501
        typed_operation_plan_from_semantic_source_meaning,
    )

    typed_operation_plan = typed_operation_plan_from_semantic_source_meaning(
        semantic_status={},
        typed_operations=(operation,),
    )
    if (
        graph_semantic_key is not None
        and graph_object_id is not None
        and object_config_graph_node_id is not None
    ):
        typed_operation_plan = _class_delete_typed_operation_plan_with_identity(
            typed_operation_plan=typed_operation_plan,
            graph_semantic_key=graph_semantic_key,
            graph_object_id=graph_object_id,
            object_config_graph_node_id=object_config_graph_node_id,
            class_config_id=class_config_id,
            class_name=class_name,
            class_fqn=class_fqn,
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
    generated_materialization_metadata = (
        _class_delete_generated_materialization_intent_metadata(
            typed_operation_plan=typed_operation_plan,
            typed_operation=typed_operation,
            ready=ready,
        )
    )
    metadata: dict[str, object] = {
        "provider_delta_typed_operation_status": (
            "provider_delta_typed_operation_ready"
            if ready
            else "provider_delta_typed_operation_blocked"
        ),
        "provider_delta_typed_operation_reason": (
            "class_delete_provider_delta_operation_ready"
            if ready
            else "class_delete_provider_delta_operation_blocked"
        ),
        "provider_delta_typed_operation_plan": typed_operation_plan,
        **generated_materialization_metadata,
    }
    if typed_operation is not None:
        metadata["provider_delta_typed_operation"] = dict(typed_operation)
    if not ready:
        metadata["provider_delta_typed_operation_blockers"] = (
            "class_delete_provider_delta_typed_operation_unavailable",
        )
    return metadata


def _class_delete_generated_materialization_intent_metadata(
    *,
    typed_operation_plan: Mapping[str, object],
    typed_operation: Mapping[str, object] | None,
    ready: bool,
) -> dict[str, object]:
    blockers: tuple[str, ...] = (
        ("class_delete_generated_materialization_typed_plan_unavailable",)
        if not ready
        else ()
    )
    status = (
        "generated_materialization_intent_ready"
        if ready
        else "generated_materialization_intent_blocked"
    )
    reason = (
        "class_delete_generated_materialization_typed_plan_unavailable"
        if not ready
        else "class_delete_generated_materialization_intent_ready"
    )
    intent: dict[str, object] = {
        "intent_kind": "meta_class_delete_generated_materialization_intent",
        "contract_version": (
            META_CLASS_DELETE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION
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
                "renderer_key": "python.orm.class",
                "policy_key": "aware_meta.python_orm.class.delete",
                "materialization_target": "python_orm_class",
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


def _class_delete_typed_operation_plan_with_identity(
    *,
    typed_operation_plan: Mapping[str, object],
    graph_semantic_key: str,
    graph_object_id: str,
    object_config_graph_node_id: str,
    class_config_id: str | None,
    class_name: str | None,
    class_fqn: str | None,
) -> dict[str, object]:
    enriched_plan = dict(typed_operation_plan)
    enriched_plan["typed_operations"] = tuple(
        (
            _class_delete_typed_operation_with_identity(
                typed_operation=item,
                graph_semantic_key=graph_semantic_key,
                graph_object_id=graph_object_id,
                object_config_graph_node_id=object_config_graph_node_id,
                class_config_id=class_config_id,
                class_name=class_name,
                class_fqn=class_fqn,
            )
            if isinstance(item, Mapping)
            else item
        )
        for item in _tuple_values(typed_operation_plan.get("typed_operations"))
    )
    semantic_object_anchors = tuple(
        _tuple_values(typed_operation_plan.get("semantic_object_anchors"))
    )
    enriched_plan["semantic_object_anchors"] = (
        *semantic_object_anchors,
        {
            "operation_kind": "meta_ocg_provider_delta_semantic_object_anchor",
            "operation_key": f"meta_ocg.graph.anchor:{graph_semantic_key}",
            "operation_family": "anchor",
            "provider_operation_type": "meta_ocg.graph.anchor",
            "semantic_key": graph_semantic_key,
            "ontology_subject_kind": "graph",
            "baseline": {
                "object_id": graph_object_id,
                "entity_id": graph_object_id,
            },
            "current": {
                "entity_id": graph_object_id,
                "object_id": graph_object_id,
                "payload": {
                    "entity_id": graph_object_id,
                    "object_id": graph_object_id,
                },
            },
            "source_refs": (),
        },
    )
    return enriched_plan


def _class_delete_typed_operation_with_identity(
    *,
    typed_operation: Mapping[str, object],
    graph_semantic_key: str,
    graph_object_id: str,
    object_config_graph_node_id: str,
    class_config_id: str | None,
    class_name: str | None,
    class_fqn: str | None,
) -> dict[str, object]:
    enriched = dict(typed_operation)
    current = _mapping_value(enriched.get("current"))
    payload = _mapping_value(current.get("payload"))
    baseline = _mapping_value(enriched.get("baseline"))
    baseline_object = _mapping_value(baseline.get("object"))
    for target in (current, payload, baseline_object):
        _set_missing_text(target, "graph_semantic_key", graph_semantic_key)
        _set_missing_text(target, "graph_object_id", graph_object_id)
        _set_missing_text(target, "object_config_graph_id", graph_object_id)
        target["object_config_graph_node_id"] = object_config_graph_node_id
        target["node_id"] = object_config_graph_node_id
        if class_config_id is not None:
            target["class_config_id"] = class_config_id
            target["entity_id"] = class_config_id
        if class_name is not None:
            _set_missing_text(target, "name", class_name)
            _set_missing_text(target, "entity_name", class_name)
        if class_fqn is not None:
            target["class_fqn"] = class_fqn
            target["node_key"] = class_fqn
    if payload:
        current["payload"] = payload
    if baseline_object:
        baseline["object"] = baseline_object
    enriched["current"] = current
    enriched["baseline"] = baseline
    return enriched


def _resolve_class_delete(
    *,
    operation: Mapping[str, object],
    current_objects: Mapping[str, str],
    current_object_identities: Mapping[str, Mapping[str, object]],
) -> MetaSemanticOperationResolution:
    operation_family = _string_value(operation.get("operation_family"))
    if operation_family != "delete":
        return _blocked_resolution(
            operation=operation,
            reason="meta_ocg_class_delete_requires_delete_family",
            blockers=(
                "unsupported_operation_family:" f"{operation_family or 'unknown'}",
            ),
        )
    subject_type = _string_value(operation.get("semantic_subject_type"))
    if subject_type not in {
        "ClassConfig",
        "aware_meta.ClassConfig",
        "ObjectConfigGraph",
        "aware_meta.ObjectConfigGraph",
    }:
        return _blocked_resolution(
            operation=operation,
            reason="meta_ocg_class_delete_subject_not_supported",
            blockers=(
                "unsupported_semantic_subject_type:" f"{subject_type or 'unknown'}",
            ),
        )

    semantic_key = _semantic_key(operation)
    before_payload = _mapping_value(operation.get("before_payload"))
    after_payload = _mapping_value(operation.get("after_payload"))
    class_name = _first_text(
        before_payload.get("class_name"),
        before_payload.get("name"),
        after_payload.get("class_name"),
        after_payload.get("name"),
        _class_name_from_class_semantic_key(semantic_key),
    )
    raw_class_fqn = _first_text(
        before_payload.get("class_fqn"),
        before_payload.get("node_key"),
        after_payload.get("class_fqn"),
        after_payload.get("node_key"),
        _class_fqn_from_class_semantic_key(semantic_key),
        class_name,
    )
    class_fqn = _class_fqn_from_package_context(
        class_name=class_name,
        raw_class_fqn=raw_class_fqn,
        operation=operation,
    )
    graph_semantic_key = _first_text(
        before_payload.get("graph_semantic_key"),
        after_payload.get("graph_semantic_key"),
        operation.get("graph_semantic_key"),
        _graph_semantic_key_from_class_semantic_key(semantic_key),
        _graph_semantic_key_from_operation_package_context(operation),
    )
    graph_receiver_object_id = _enum_create_graph_object_id(
        operation=operation,
        current_objects=current_objects,
        graph_semantic_key=graph_semantic_key,
    )
    graph_source_object_id = _enum_create_graph_source_object_id(
        operation=operation,
        current_object_identities=current_object_identities,
        graph_semantic_key=graph_semantic_key,
        fallback_object_id=graph_receiver_object_id,
    )
    object_config_graph_node_id = _first_text(
        before_payload.get("object_config_graph_node_id"),
        before_payload.get("node_id"),
        after_payload.get("object_config_graph_node_id"),
        after_payload.get("node_id"),
        _stable_object_config_graph_node_id_for_class_create(
            graph_object_id=graph_source_object_id,
            class_fqn=class_fqn,
        ),
    )
    class_config_id = _first_text(
        current_objects.get(semantic_key),
        before_payload.get("class_config_id"),
        before_payload.get("entity_id"),
        after_payload.get("class_config_id"),
        after_payload.get("entity_id"),
        _stable_class_config_id_for_create(
            object_config_graph_node_id=object_config_graph_node_id,
            class_fqn=class_fqn,
        ),
    )
    blockers = tuple(
        blocker
        for blocker, value in (
            ("missing_class_name", class_name),
            ("missing_class_fqn", class_fqn),
            ("missing_graph_semantic_key", graph_semantic_key),
            ("missing_object_config_graph_id", graph_source_object_id),
            ("missing_object_config_graph_node_id", object_config_graph_node_id),
        )
        if value is None
    )
    provider_delta_typed_operation_metadata = (
        _provider_delta_typed_operation_metadata_for_class_delete(
            operation=operation,
            graph_semantic_key=graph_semantic_key,
            graph_object_id=graph_source_object_id,
            object_config_graph_node_id=object_config_graph_node_id,
            class_config_id=class_config_id,
            class_name=class_name,
            class_fqn=class_fqn,
        )
    )
    metadata: dict[str, object] = {
        "source": "aware_meta.semantic_operation_resolution",
        "semantic_apply_boundary": "provider_delta_ontology_operation_executor",
        "provider_delta_handler_key": "class.object_config_graph_node_function_calls",
        "provider_operation_type": "meta_ocg.class.delete",
        "requires_baseline_object_identity": True,
        "requires_graph_semantic_object_identity": True,
        "execution_ready": not blockers,
        "execution_preconditions": ("provider_delta_ontology_operation_executor",),
        "preview_only": True,
        "receiver_semantic_key": graph_semantic_key,
        "receiver_object_id": graph_source_object_id,
        "result_semantic_key": semantic_key,
        "result_object_id": object_config_graph_node_id,
        "class_config_id": class_config_id,
        "object_config_graph_node_id": object_config_graph_node_id,
        **provider_delta_typed_operation_metadata,
    }
    if (
        graph_receiver_object_id is not None
        and graph_receiver_object_id != graph_source_object_id
    ):
        metadata["semantic_apply_receiver_object_id"] = graph_receiver_object_id
        metadata["semantic_source_object_id"] = graph_source_object_id
    if class_name is not None:
        metadata["class_name"] = class_name
    if class_fqn is not None:
        metadata["class_fqn"] = class_fqn
    return _blocked_resolution(
        operation=operation,
        reason=(
            "meta_ocg_class_delete_requires_provider_delta_"
            "ontology_operation_executor"
        ),
        blockers=(
            *blockers,
            "semantic_plan_single_function_call_preview_not_supported",
            "provider_delta_class_delete_operation_executor_required",
        ),
        metadata=metadata,
    )

