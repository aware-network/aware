from __future__ import annotations

from collections.abc import Mapping

from aware_meta.semantic_operation_resolution import (
    META_OBJECT_CONFIG_GRAPH_RELATIONSHIP_CREATE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_RELATIONSHIP_DELETE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_RELATIONSHIP_LOAD_POLICY_UPDATE_OPERATION,
    META_RELATIONSHIP_CREATE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
    META_RELATIONSHIP_DELETE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
    META_RELATIONSHIP_LOAD_POLICY_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
    MetaSemanticOperationResolution,
    _blocked_resolution,
    _class_fqn_from_package_context,
    _first_text,
    _mapping_value,
    _optional_text,
    _relationship_class_from_semantic_key,
    _relationship_key_from_semantic_key,
    _relationship_target_class_fqn_from_payload,
    _semantic_key,
    _stable_relationship_config_id_for_create,
    _string_value,
    _tuple_values,
)


def resolve_relationship_config_semantic_operation(
    *,
    operation: Mapping[str, object],
    operation_group: tuple[Mapping[str, object], ...],
    current_objects: Mapping[str, str],
    current_object_identities: Mapping[str, Mapping[str, object]],
) -> MetaSemanticOperationResolution:
    del operation_group, current_object_identities
    operation_type = _string_value(operation.get("semantic_operation_type"))
    if operation_type == META_OBJECT_CONFIG_GRAPH_RELATIONSHIP_LOAD_POLICY_UPDATE_OPERATION:
        return _resolve_relationship_load_policy_update(
            operation=operation,
            current_objects=current_objects,
        )
    if operation_type == META_OBJECT_CONFIG_GRAPH_RELATIONSHIP_CREATE_OPERATION:
        return _resolve_relationship_create(
            operation=operation,
            current_objects=current_objects,
        )
    if operation_type == META_OBJECT_CONFIG_GRAPH_RELATIONSHIP_DELETE_OPERATION:
        return _resolve_relationship_delete(
            operation=operation,
            current_objects=current_objects,
        )
    return _blocked_resolution(
        operation=operation,
        reason="meta_ocg_relationship_operation_type_not_supported",
        blockers=(f"unsupported_operation_type:{operation_type or 'unknown'}",),
    )


def _resolve_relationship_load_policy_update(
    *,
    operation: Mapping[str, object],
    current_objects: Mapping[str, str],
) -> MetaSemanticOperationResolution:
    if _string_value(operation.get("operation_family")) not in {"update", "upsert"}:
        return _blocked_resolution(
            operation=operation,
            reason="meta_ocg_relationship_load_policy_update_requires_update_family",
            blockers=(
                "unsupported_operation_family:"
                f"{_string_value(operation.get('operation_family')) or 'unknown'}",
            ),
        )
    if _string_value(operation.get("semantic_subject_type")) not in {
        "ClassConfigRelationship",
        "aware_meta.ClassConfigRelationship",
    }:
        return _blocked_resolution(
            operation=operation,
            reason=("meta_ocg_relationship_load_policy_update_subject_not_supported"),
            blockers=(
                "unsupported_semantic_subject_type:"
                f"{_string_value(operation.get('semantic_subject_type')) or 'unknown'}",
            ),
        )
    if _optional_text(operation.get("field_path")) not in {
        None,
        "load_policy_args",
        "load_policy",
        "forward_loading_strategy",
        "reverse_loading_strategy",
    }:
        return _blocked_resolution(
            operation=operation,
            reason=("meta_ocg_relationship_load_policy_update_field_not_supported"),
            blockers=(
                "unsupported_field_path:"
                f"{_string_value(operation.get('field_path')) or 'unknown'}",
            ),
        )

    semantic_key = _semantic_key(operation)
    after_payload = _mapping_value(operation.get("after_payload"))
    before_payload = _mapping_value(operation.get("before_payload"))
    class_name = _first_text(
        after_payload.get("class_name"),
        before_payload.get("class_name"),
        _relationship_class_from_semantic_key(semantic_key),
    )
    relationship_key = _first_text(
        after_payload.get("relationship_key"),
        after_payload.get("attribute_name"),
        before_payload.get("relationship_key"),
        before_payload.get("attribute_name"),
        _relationship_key_from_semantic_key(semantic_key),
    )
    relationship_type = _first_text(
        after_payload.get("relationship_type"),
        before_payload.get("relationship_type"),
    )
    blockers = tuple(
        blocker
        for blocker, value in (
            ("missing_class_name", class_name),
            ("missing_relationship_key", relationship_key),
            ("missing_relationship_type", relationship_type),
        )
        if value is None
    )
    receiver_semantic_key = (
        f"meta.relationship:{class_name}.{relationship_key}"
        if class_name is not None and relationship_key is not None
        else semantic_key
    )
    receiver_object_id = current_objects.get(receiver_semantic_key)
    provider_delta_typed_operation_metadata = (
        _provider_delta_typed_operation_metadata_for_relationship_update(
            operation=operation,
            relationship_config_id=receiver_object_id,
        )
    )
    metadata: dict[str, object] = {
        "source": "aware_meta.semantic_operation_resolution",
        "semantic_apply_boundary": "provider_delta_ontology_operation_executor",
        "provider_delta_handler_key": "relationship.class_config_function_calls",
        "provider_operation_type": "meta_ocg.relationship.update",
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
    if relationship_key is not None:
        metadata["relationship_key"] = relationship_key
    if relationship_type is not None:
        metadata["relationship_type"] = relationship_type
    return _blocked_resolution(
        operation=operation,
        reason=(
            "meta_ocg_relationship_load_policy_update_requires_provider_delta_"
            "ontology_operation_executor"
        ),
        blockers=(
            *blockers,
            "semantic_plan_single_function_call_preview_not_supported",
            "provider_delta_relationship_update_operation_executor_required",
        ),
        metadata=metadata,
    )


def _provider_delta_typed_operation_metadata_for_relationship_update(
    *,
    operation: Mapping[str, object],
    relationship_config_id: str | None,
) -> dict[str, object]:
    from aware_meta.materialization.deltas.source_projection import (  # noqa: WPS433,E501
        typed_operation_plan_from_semantic_source_meaning,
    )

    typed_operation_plan = typed_operation_plan_from_semantic_source_meaning(
        semantic_status={},
        typed_operations=(operation,),
    )
    if relationship_config_id is not None:
        typed_operation_plan = _relationship_update_typed_operation_plan_with_identity(
            typed_operation_plan=typed_operation_plan,
            relationship_config_id=relationship_config_id,
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
            "relationship_load_policy_provider_delta_operation_ready"
            if ready
            else "relationship_load_policy_provider_delta_operation_blocked"
        ),
        "provider_delta_typed_operation_plan": typed_operation_plan,
    }
    if typed_operation is not None:
        metadata["provider_delta_typed_operation"] = dict(typed_operation)
    if not ready:
        metadata["provider_delta_typed_operation_blockers"] = (
            "relationship_load_policy_provider_delta_typed_operation_unavailable",
        )
    metadata.update(
        _relationship_load_policy_generated_materialization_intent_metadata(
            typed_operation_plan=typed_operation_plan,
            typed_operation=typed_operation,
            ready=ready,
        )
    )
    return metadata


def _relationship_load_policy_generated_materialization_intent_metadata(
    *,
    typed_operation_plan: Mapping[str, object],
    typed_operation: Mapping[str, object] | None,
    ready: bool,
) -> dict[str, object]:
    blockers: tuple[str, ...] = (
        ()
        if ready
        else (
            "relationship_load_policy_generated_materialization_typed_plan_"
            "unavailable",
        )
    )
    status = (
        "generated_materialization_intent_ready"
        if ready
        else "generated_materialization_intent_blocked"
    )
    reason = (
        "relationship_load_policy_generated_materialization_intent_ready"
        if ready
        else "relationship_load_policy_generated_materialization_intent_blocked"
    )
    intent: dict[str, object] = {
        "intent_kind": (
            "meta_relationship_load_policy_generated_materialization_intent"
        ),
        "contract_version": (
            META_RELATIONSHIP_LOAD_POLICY_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION
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


def _relationship_update_typed_operation_plan_with_identity(
    *,
    typed_operation_plan: Mapping[str, object],
    relationship_config_id: str,
) -> dict[str, object]:
    enriched_plan = dict(typed_operation_plan)
    enriched_plan["typed_operations"] = tuple(
        (
            _relationship_update_typed_operation_with_identity(
                typed_operation=item,
                relationship_config_id=relationship_config_id,
            )
            if isinstance(item, Mapping)
            else item
        )
        for item in _tuple_values(typed_operation_plan.get("typed_operations"))
    )
    return enriched_plan


def _relationship_update_typed_operation_with_identity(
    *,
    typed_operation: Mapping[str, object],
    relationship_config_id: str,
) -> dict[str, object]:
    enriched = dict(typed_operation)
    current = _mapping_value(enriched.get("current"))
    payload = _mapping_value(current.get("payload"))
    baseline = _mapping_value(enriched.get("baseline"))
    baseline_object = _mapping_value(baseline.get("object"))
    for target in (current, payload, baseline_object):
        target.setdefault("entity_id", relationship_config_id)
        target.setdefault("relationship_config_id", relationship_config_id)
        target.setdefault("class_config_relationship_id", relationship_config_id)
    if payload:
        current["payload"] = payload
    if baseline_object:
        baseline["object"] = baseline_object
    enriched["current"] = current
    enriched["baseline"] = baseline
    return enriched


def _resolve_relationship_create(
    *,
    operation: Mapping[str, object],
    current_objects: Mapping[str, str],
) -> MetaSemanticOperationResolution:
    operation_family = _string_value(operation.get("operation_family"))
    if operation_family not in {"create", "upsert"}:
        return _blocked_resolution(
            operation=operation,
            reason="meta_ocg_relationship_create_requires_create_family",
            blockers=(
                "unsupported_operation_family:" f"{operation_family or 'unknown'}",
            ),
        )
    subject_type = _string_value(operation.get("semantic_subject_type"))
    if subject_type not in {
        "ClassConfigRelationship",
        "aware_meta.ClassConfigRelationship",
    }:
        return _blocked_resolution(
            operation=operation,
            reason="meta_ocg_relationship_create_subject_not_supported",
            blockers=(
                "unsupported_semantic_subject_type:" f"{subject_type or 'unknown'}",
            ),
        )
    after_payload = _mapping_value(operation.get("after_payload"))
    semantic_key = _semantic_key(operation)
    class_name = _first_text(
        after_payload.get("class_name"),
        _relationship_class_from_semantic_key(semantic_key),
    )
    raw_source_class_fqn = _first_text(
        after_payload.get("source_class_fqn"),
        after_payload.get("class_fqn"),
        class_name,
    )
    source_class_fqn = _class_fqn_from_package_context(
        class_name=class_name,
        raw_class_fqn=raw_source_class_fqn,
        operation=operation,
    )
    relationship_key = _first_text(
        after_payload.get("relationship_key"),
        after_payload.get("attribute_name"),
        _relationship_key_from_semantic_key(semantic_key),
    )
    relationship_type = _first_text(after_payload.get("relationship_type"))
    target_class_fqn = _relationship_target_class_fqn_from_payload(
        payload=after_payload,
        source_class_fqn=source_class_fqn,
    )
    source_semantic_key = (
        f"meta.class:{class_name}" if class_name is not None else None
    )
    target_class_name = (
        target_class_fqn.rsplit(".", maxsplit=1)[-1]
        if target_class_fqn is not None
        else _optional_text(after_payload.get("target_class_name"))
    )
    target_semantic_key = (
        f"meta.class:{target_class_name}" if target_class_name is not None else None
    )
    source_class_config_id = (
        current_objects.get(source_semantic_key)
        if source_semantic_key is not None
        else None
    )
    target_class_config_id = (
        current_objects.get(target_semantic_key)
        if target_semantic_key is not None
        else None
    )
    relationship_config_id = _first_text(
        after_payload.get("relationship_config_id"),
        after_payload.get("class_config_relationship_id"),
        after_payload.get("entity_id"),
        _stable_relationship_config_id_for_create(
            source_class_config_id=source_class_config_id,
            target_class_config_id=target_class_config_id,
            relationship_key=relationship_key,
        ),
    )
    blockers = tuple(
        blocker
        for blocker, value in (
            ("missing_class_name", class_name),
            ("missing_source_class_fqn", source_class_fqn),
            ("missing_relationship_key", relationship_key),
            ("missing_relationship_type", relationship_type),
            ("missing_target_class_fqn", target_class_fqn),
            ("missing_source_semantic_key", source_semantic_key),
            ("missing_source_class_config_id", source_class_config_id),
            ("missing_target_semantic_key", target_semantic_key),
            ("missing_target_class_config_id", target_class_config_id),
            ("missing_relationship_config_id", relationship_config_id),
        )
        if value is None
    )
    provider_delta_typed_operation_metadata = (
        _provider_delta_typed_operation_metadata_for_relationship_structural(
            operation=operation,
            operation_kind="create",
            relationship_config_id=relationship_config_id,
            source_class_config_id=source_class_config_id,
            target_class_config_id=target_class_config_id,
        )
    )
    metadata: dict[str, object] = {
        "source": "aware_meta.semantic_operation_resolution",
        "semantic_apply_boundary": "provider_delta_ontology_operation_executor",
        "provider_delta_handler_key": "relationship.class_config_function_calls",
        "provider_operation_type": "meta_ocg.relationship.create",
        "requires_baseline_object_identity": False,
        "requires_owner_semantic_object_identity": True,
        "execution_ready": not blockers,
        "execution_preconditions": ("provider_delta_ontology_operation_executor",),
        "preview_only": True,
        "receiver_semantic_key": source_semantic_key,
        "receiver_object_id": source_class_config_id,
        "result_semantic_key": semantic_key,
        "result_object_id": relationship_config_id,
        **provider_delta_typed_operation_metadata,
    }
    if class_name is not None:
        metadata["class_name"] = class_name
    if source_class_fqn is not None:
        metadata["source_class_fqn"] = source_class_fqn
    if target_class_fqn is not None:
        metadata["target_class_fqn"] = target_class_fqn
    if relationship_key is not None:
        metadata["relationship_key"] = relationship_key
    if relationship_type is not None:
        metadata["relationship_type"] = relationship_type
    return _blocked_resolution(
        operation=operation,
        reason=(
            "meta_ocg_relationship_create_requires_provider_delta_"
            "ontology_operation_executor"
        ),
        blockers=(
            *blockers,
            "semantic_plan_single_function_call_preview_not_supported",
            "provider_delta_relationship_create_operation_executor_required",
        ),
        metadata=metadata,
    )


def _resolve_relationship_delete(
    *,
    operation: Mapping[str, object],
    current_objects: Mapping[str, str],
) -> MetaSemanticOperationResolution:
    operation_family = _string_value(operation.get("operation_family"))
    if operation_family != "delete":
        return _blocked_resolution(
            operation=operation,
            reason="meta_ocg_relationship_delete_requires_delete_family",
            blockers=(
                "unsupported_operation_family:" f"{operation_family or 'unknown'}",
            ),
        )
    subject_type = _string_value(operation.get("semantic_subject_type"))
    if subject_type not in {
        "ClassConfigRelationship",
        "aware_meta.ClassConfigRelationship",
    }:
        return _blocked_resolution(
            operation=operation,
            reason="meta_ocg_relationship_delete_subject_not_supported",
            blockers=(
                "unsupported_semantic_subject_type:" f"{subject_type or 'unknown'}",
            ),
        )
    before_payload = _mapping_value(operation.get("before_payload"))
    after_payload = _mapping_value(operation.get("after_payload"))
    semantic_key = _semantic_key(operation)
    class_name = _first_text(
        before_payload.get("class_name"),
        after_payload.get("class_name"),
        _relationship_class_from_semantic_key(semantic_key),
    )
    raw_source_class_fqn = _first_text(
        before_payload.get("source_class_fqn"),
        before_payload.get("class_fqn"),
        after_payload.get("source_class_fqn"),
        after_payload.get("class_fqn"),
        class_name,
    )
    source_class_fqn = _class_fqn_from_package_context(
        class_name=class_name,
        raw_class_fqn=raw_source_class_fqn,
        operation=operation,
    )
    relationship_key = _first_text(
        before_payload.get("relationship_key"),
        before_payload.get("attribute_name"),
        after_payload.get("relationship_key"),
        after_payload.get("attribute_name"),
        _relationship_key_from_semantic_key(semantic_key),
    )
    relationship_type = _first_text(
        before_payload.get("relationship_type"),
        after_payload.get("relationship_type"),
    )
    target_class_fqn = _relationship_target_class_fqn_from_payload(
        payload=before_payload or after_payload,
        source_class_fqn=source_class_fqn,
    )
    source_semantic_key = (
        f"meta.class:{class_name}" if class_name is not None else None
    )
    source_class_config_id = (
        current_objects.get(source_semantic_key)
        if source_semantic_key is not None
        else None
    )
    relationship_config_id = _first_text(
        current_objects.get(semantic_key),
        before_payload.get("relationship_config_id"),
        before_payload.get("class_config_relationship_id"),
        before_payload.get("entity_id"),
        after_payload.get("relationship_config_id"),
        after_payload.get("class_config_relationship_id"),
        after_payload.get("entity_id"),
    )
    blockers = tuple(
        blocker
        for blocker, value in (
            ("missing_class_name", class_name),
            ("missing_source_class_fqn", source_class_fqn),
            ("missing_relationship_key", relationship_key),
            ("missing_relationship_type", relationship_type),
            ("missing_source_semantic_key", source_semantic_key),
            ("missing_source_class_config_id", source_class_config_id),
            ("missing_relationship_config_id", relationship_config_id),
        )
        if value is None
    )
    provider_delta_typed_operation_metadata = (
        _provider_delta_typed_operation_metadata_for_relationship_structural(
            operation=operation,
            operation_kind="delete",
            relationship_config_id=relationship_config_id,
            source_class_config_id=source_class_config_id,
            target_class_config_id=None,
        )
    )
    metadata: dict[str, object] = {
        "source": "aware_meta.semantic_operation_resolution",
        "semantic_apply_boundary": "provider_delta_ontology_operation_executor",
        "provider_delta_handler_key": "relationship.class_config_function_calls",
        "provider_operation_type": "meta_ocg.relationship.delete",
        "requires_baseline_object_identity": True,
        "requires_owner_semantic_object_identity": True,
        "execution_ready": not blockers,
        "execution_preconditions": ("provider_delta_ontology_operation_executor",),
        "preview_only": True,
        "receiver_semantic_key": source_semantic_key,
        "receiver_object_id": source_class_config_id,
        "result_semantic_key": semantic_key,
        "result_object_id": relationship_config_id,
        **provider_delta_typed_operation_metadata,
    }
    if class_name is not None:
        metadata["class_name"] = class_name
    if source_class_fqn is not None:
        metadata["source_class_fqn"] = source_class_fqn
    if target_class_fqn is not None:
        metadata["target_class_fqn"] = target_class_fqn
    if relationship_key is not None:
        metadata["relationship_key"] = relationship_key
    if relationship_type is not None:
        metadata["relationship_type"] = relationship_type
    return _blocked_resolution(
        operation=operation,
        reason=(
            "meta_ocg_relationship_delete_requires_provider_delta_"
            "ontology_operation_executor"
        ),
        blockers=(
            *blockers,
            "semantic_plan_single_function_call_preview_not_supported",
            "provider_delta_relationship_delete_operation_executor_required",
        ),
        metadata=metadata,
    )


def _provider_delta_typed_operation_metadata_for_relationship_structural(
    *,
    operation: Mapping[str, object],
    operation_kind: str,
    relationship_config_id: str | None,
    source_class_config_id: str | None,
    target_class_config_id: str | None,
) -> dict[str, object]:
    from aware_meta.materialization.deltas.source_projection import (  # noqa: WPS433,E501
        typed_operation_plan_from_semantic_source_meaning,
    )

    typed_operation_plan = typed_operation_plan_from_semantic_source_meaning(
        semantic_status={},
        typed_operations=(operation,),
    )
    if relationship_config_id is not None or source_class_config_id is not None:
        typed_operation_plan = (
            _relationship_structural_typed_operation_plan_with_identity(
                typed_operation_plan=typed_operation_plan,
                relationship_config_id=relationship_config_id,
                source_class_config_id=source_class_config_id,
                target_class_config_id=target_class_config_id,
            )
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
        _relationship_structural_generated_materialization_intent_metadata(
            typed_operation_plan=typed_operation_plan,
            typed_operation=typed_operation,
            operation_kind=operation_kind,
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
            f"relationship_{operation_kind}_provider_delta_operation_ready"
            if ready
            else f"relationship_{operation_kind}_provider_delta_operation_blocked"
        ),
        "provider_delta_typed_operation_plan": typed_operation_plan,
        **generated_materialization_metadata,
    }
    if typed_operation is not None:
        metadata["provider_delta_typed_operation"] = dict(typed_operation)
    if not ready:
        metadata["provider_delta_typed_operation_blockers"] = (
            f"relationship_{operation_kind}_provider_delta_typed_operation_unavailable",
        )
    return metadata


def _relationship_structural_generated_materialization_intent_metadata(
    *,
    typed_operation_plan: Mapping[str, object],
    typed_operation: Mapping[str, object] | None,
    operation_kind: str,
    ready: bool,
) -> dict[str, object]:
    blockers: tuple[str, ...] = (
        ()
        if ready
        else (
            f"relationship_{operation_kind}_generated_materialization_"
            "typed_plan_unavailable",
        )
    )
    status = (
        "generated_materialization_intent_ready"
        if ready
        else "generated_materialization_intent_blocked"
    )
    reason = (
        f"relationship_{operation_kind}_generated_materialization_intent_ready"
        if ready
        else f"relationship_{operation_kind}_generated_materialization_intent_blocked"
    )
    contract_version = (
        META_RELATIONSHIP_CREATE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION
        if operation_kind == "create"
        else META_RELATIONSHIP_DELETE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION
    )
    intent: dict[str, object] = {
        "intent_kind": (
            f"meta_relationship_{operation_kind}_generated_materialization_intent"
        ),
        "contract_version": contract_version,
        "status": status,
        "reason": reason,
        "generated_materialization_provider_key": "aware_meta",
        "blockers": blockers,
        "provider_delta_typed_operation_plan": dict(typed_operation_plan),
    }
    if ready:
        intent.update(
            {
                "renderer_key": "python.orm.relationship.load_policy",
                "policy_key": f"aware_meta.python_orm.relationship.{operation_kind}",
                "materialization_target": "python_orm_relationship_field",
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


def _relationship_structural_typed_operation_plan_with_identity(
    *,
    typed_operation_plan: Mapping[str, object],
    relationship_config_id: str | None,
    source_class_config_id: str | None,
    target_class_config_id: str | None,
) -> dict[str, object]:
    enriched_plan = dict(typed_operation_plan)
    enriched_plan["typed_operations"] = tuple(
        (
            _relationship_structural_typed_operation_with_identity(
                typed_operation=item,
                relationship_config_id=relationship_config_id,
                source_class_config_id=source_class_config_id,
                target_class_config_id=target_class_config_id,
            )
            if isinstance(item, Mapping)
            else item
        )
        for item in _tuple_values(typed_operation_plan.get("typed_operations"))
    )
    return enriched_plan


def _relationship_structural_typed_operation_with_identity(
    *,
    typed_operation: Mapping[str, object],
    relationship_config_id: str | None,
    source_class_config_id: str | None,
    target_class_config_id: str | None,
) -> dict[str, object]:
    enriched = dict(typed_operation)
    current = _mapping_value(enriched.get("current"))
    payload = _mapping_value(current.get("payload"))
    baseline = _mapping_value(enriched.get("baseline"))
    baseline_object = _mapping_value(baseline.get("object"))
    targets = (current, payload, baseline, baseline_object)
    for target in targets:
        if relationship_config_id is not None:
            target.setdefault("entity_id", relationship_config_id)
            target.setdefault("relationship_config_id", relationship_config_id)
            target.setdefault(
                "class_config_relationship_id",
                relationship_config_id,
            )
        if source_class_config_id is not None:
            target.setdefault("source_class_config_id", source_class_config_id)
            target.setdefault("class_config_id", source_class_config_id)
        if target_class_config_id is not None:
            target.setdefault("target_class_config_id", target_class_config_id)
    signature = _mapping_value(current.get("relationship_signature"))
    for field_name, field_value in (
        ("source_class_config_id", source_class_config_id),
        ("target_class_config_id", target_class_config_id),
    ):
        if field_value is not None:
            signature.setdefault(field_name, field_value)
    if signature:
        current["relationship_signature"] = signature
        payload.setdefault("relationship_signature", signature)
    if payload:
        current["payload"] = payload
    if baseline_object:
        baseline["object"] = baseline_object
    enriched["current"] = current
    enriched["baseline"] = baseline
    return enriched

