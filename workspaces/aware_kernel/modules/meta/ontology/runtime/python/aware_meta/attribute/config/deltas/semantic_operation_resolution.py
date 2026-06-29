from __future__ import annotations

from collections.abc import Mapping

from aware_meta.semantic_operation_resolution import (
    META_ATTRIBUTE_CREATE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
    META_ATTRIBUTE_DEFAULT_VALUE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
    META_ATTRIBUTE_DELETE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
    META_ATTRIBUTE_TYPE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
    META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_CREATE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_DEFAULT_VALUE_UPDATE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_DELETE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_IDENTITY_RENAME_OPERATION,
    META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_MEMBERSHIP_UPDATE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_TYPE_UPDATE_OPERATION,
    _PRIMITIVE_TYPE_NAMES,
    MetaSemanticOperationResolution,
    _attribute_name_from_attribute_semantic_key,
    _blocked_resolution,
    _class_fqn_from_package_context,
    _class_name_from_attribute_semantic_key,
    _first_text,
    _mapping_value,
    _optional_text,
    _semantic_key,
    _stable_attribute_config_id_for_create,
    _string_value,
    _tuple_values,
)


def resolve_attribute_config_semantic_operation(
    *,
    operation: Mapping[str, object],
    operation_group: tuple[Mapping[str, object], ...],
    current_objects: Mapping[str, str],
    current_object_identities: Mapping[str, Mapping[str, object]],
) -> MetaSemanticOperationResolution:
    del operation_group
    operation_type = _string_value(operation.get("semantic_operation_type"))
    if operation_type == META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_TYPE_UPDATE_OPERATION:
        return _resolve_attribute_type_update(
            operation=operation,
            current_objects=current_objects,
        )
    if (
        operation_type
        == META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_DEFAULT_VALUE_UPDATE_OPERATION
    ):
        return _resolve_attribute_default_value_update(
            operation=operation,
            current_objects=current_objects,
        )
    if (
        operation_type
        == META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_MEMBERSHIP_UPDATE_OPERATION
    ):
        return _resolve_attribute_membership_update(
            operation=operation,
            current_objects=current_objects,
            current_object_identities=current_object_identities,
        )
    if operation_type == META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_CREATE_OPERATION:
        return _resolve_attribute_create(
            operation=operation,
            current_objects=current_objects,
        )
    if operation_type == META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_DELETE_OPERATION:
        return _resolve_attribute_delete(
            operation=operation,
            current_objects=current_objects,
        )
    if operation_type == META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_IDENTITY_RENAME_OPERATION:
        return _resolve_attribute_identity_rename(operation=operation)
    return _blocked_resolution(
        operation=operation,
        reason="meta_ocg_attribute_operation_type_not_supported",
        blockers=(f"unsupported_operation_type:{operation_type or 'unknown'}",),
    )


def _resolve_attribute_type_update(
    *,
    operation: Mapping[str, object],
    current_objects: Mapping[str, str],
) -> MetaSemanticOperationResolution:
    if _string_value(operation.get("operation_family")) != "update":
        return _blocked_resolution(
            operation=operation,
            reason="meta_ocg_attribute_type_update_requires_update_family",
            blockers=(
                "unsupported_operation_family:"
                f"{_string_value(operation.get('operation_family')) or 'unknown'}",
            ),
        )
    if _string_value(operation.get("semantic_subject_type")) != (
        "ClassConfigAttributeConfig"
    ):
        return _blocked_resolution(
            operation=operation,
            reason="meta_ocg_attribute_type_update_subject_not_supported",
            blockers=(
                "unsupported_semantic_subject_type:"
                f"{_string_value(operation.get('semantic_subject_type')) or 'unknown'}",
            ),
        )
    if _optional_text(operation.get("field_path")) not in {None, "type"}:
        return _blocked_resolution(
            operation=operation,
            reason="meta_ocg_attribute_type_update_field_not_supported",
            blockers=(
                "unsupported_field_path:"
                f"{_string_value(operation.get('field_path')) or 'unknown'}",
            ),
        )

    descriptor = _after_type_descriptor(operation=operation)
    descriptor_kind = _descriptor_kind(descriptor=descriptor)
    if descriptor_kind == "primitive":
        primitive_base_type = _primitive_base_type(descriptor=descriptor)
        if primitive_base_type is None:
            return _blocked_resolution(
                operation=operation,
                reason="meta_ocg_attribute_type_update_requires_primitive_base_type",
                blockers=("missing_primitive_base_type",),
            )
        return _primitive_attribute_update_resolution(
            operation=operation,
            primitive_base_type=primitive_base_type,
            current_objects=current_objects,
        )
    if descriptor_kind in {"class", "enum", "collection"}:
        return _blocked_resolution(
            operation=operation,
            reason=(
                "meta_ocg_attribute_type_update_requires_target_ref_for_"
                f"{descriptor_kind}"
            ),
            blockers=(f"missing_{descriptor_kind}_target_ref",),
            metadata={"descriptor_kind": descriptor_kind},
        )
    return _blocked_resolution(
        operation=operation,
        reason="meta_ocg_attribute_type_update_descriptor_not_supported",
        blockers=(f"unsupported_descriptor_kind:{descriptor_kind or 'unknown'}",),
        metadata={"descriptor_kind": descriptor_kind or "unknown"},
    )


def _resolve_attribute_default_value_update(
    *,
    operation: Mapping[str, object],
    current_objects: Mapping[str, str],
) -> MetaSemanticOperationResolution:
    if _string_value(operation.get("operation_family")) != "update":
        return _blocked_resolution(
            operation=operation,
            reason="meta_ocg_attribute_default_value_update_requires_update_family",
            blockers=(
                "unsupported_operation_family:"
                f"{_string_value(operation.get('operation_family')) or 'unknown'}",
            ),
        )
    if _string_value(operation.get("semantic_subject_type")) != (
        "ClassConfigAttributeConfig"
    ):
        return _blocked_resolution(
            operation=operation,
            reason="meta_ocg_attribute_default_value_update_subject_not_supported",
            blockers=(
                "unsupported_semantic_subject_type:"
                f"{_string_value(operation.get('semantic_subject_type')) or 'unknown'}",
            ),
        )
    if _optional_text(operation.get("field_path")) not in {None, "default_value"}:
        return _blocked_resolution(
            operation=operation,
            reason="meta_ocg_attribute_default_value_update_field_not_supported",
            blockers=(
                "unsupported_field_path:"
                f"{_string_value(operation.get('field_path')) or 'unknown'}",
            ),
        )
    after_payload = _mapping_value(operation.get("after_payload"))
    if "default_value" not in after_payload:
        return _blocked_resolution(
            operation=operation,
            reason="meta_ocg_attribute_default_value_update_requires_after_value",
            blockers=("missing_after_default_value",),
        )
    return _attribute_default_value_update_resolution(
        operation=operation,
        current_objects=current_objects,
    )


def _resolve_attribute_membership_update(
    *,
    operation: Mapping[str, object],
    current_objects: Mapping[str, str],
    current_object_identities: Mapping[str, Mapping[str, object]],
) -> MetaSemanticOperationResolution:
    if _string_value(operation.get("operation_family")) != "update":
        return _blocked_resolution(
            operation=operation,
            reason="meta_ocg_attribute_membership_update_requires_update_family",
            blockers=(
                "unsupported_operation_family:"
                f"{_string_value(operation.get('operation_family')) or 'unknown'}",
            ),
        )
    if _string_value(operation.get("semantic_subject_type")) not in {
        "ClassConfigAttributeConfig",
        "aware_meta.ClassConfigAttributeConfig",
    }:
        return _blocked_resolution(
            operation=operation,
            reason="meta_ocg_attribute_membership_update_subject_not_supported",
            blockers=(
                "unsupported_semantic_subject_type:"
                f"{_string_value(operation.get('semantic_subject_type')) or 'unknown'}",
            ),
        )
    if _optional_text(operation.get("field_path")) not in {
        None,
        "is_identity_key",
    }:
        return _blocked_resolution(
            operation=operation,
            reason="meta_ocg_attribute_membership_update_field_not_supported",
            blockers=(
                "unsupported_field_path:"
                f"{_string_value(operation.get('field_path')) or 'unknown'}",
            ),
        )

    semantic_key = _semantic_key(operation)
    attribute_semantic_key = _attribute_semantic_key_from_membership_key(
        semantic_key,
    )
    before_payload = _mapping_value(operation.get("before_payload"))
    after_payload = _mapping_value(operation.get("after_payload"))
    attribute_identity = _attribute_identity_for_membership_update(
        operation=operation,
        semantic_key=semantic_key,
        attribute_semantic_key=attribute_semantic_key,
        current_object_identities=current_object_identities,
    )
    class_name = _first_text(
        after_payload.get("class_name"),
        before_payload.get("class_name"),
        _class_name_from_attribute_semantic_key(attribute_semantic_key),
    )
    attribute_name = _first_text(
        after_payload.get("attribute_name"),
        before_payload.get("attribute_name"),
        after_payload.get("name"),
        before_payload.get("name"),
        _attribute_name_from_attribute_semantic_key(attribute_semantic_key),
    )
    owner_semantic_key = _first_text(
        after_payload.get("owner_semantic_key"),
        before_payload.get("owner_semantic_key"),
        attribute_identity.get("owner_semantic_key"),
        f"meta.class:{class_name}" if class_name is not None else None,
    )
    edge_semantic_key = _attribute_membership_edge_semantic_key(
        class_name=class_name,
        attribute_name=attribute_name,
    )
    class_config_id = _first_text(
        after_payload.get("class_config_id"),
        before_payload.get("class_config_id"),
        attribute_identity.get("class_config_id"),
        current_objects.get(owner_semantic_key) if owner_semantic_key else None,
    )
    attribute_config_id = _first_text(
        after_payload.get("attribute_config_id"),
        before_payload.get("attribute_config_id"),
        attribute_identity.get("attribute_config_id"),
        attribute_identity.get("entity_id"),
        attribute_identity.get("object_id"),
        current_objects.get(attribute_semantic_key),
    )
    edge_id = _first_text(
        after_payload.get("class_config_attribute_config_id"),
        before_payload.get("class_config_attribute_config_id"),
        attribute_identity.get("class_config_attribute_config_id"),
    )
    execution_receiver_object_id = _first_text(
        attribute_identity.get("semantic_apply_receiver_object_id"),
        attribute_identity.get("executable_object_id"),
        edge_id,
    )
    baseline_signature = _attribute_membership_signature_for_payload(
        payload=before_payload,
        identity=attribute_identity,
        class_config_id=class_config_id,
        attribute_config_id=attribute_config_id,
        default_identity_key=False,
    )
    current_signature = _attribute_membership_signature_for_payload(
        payload=after_payload,
        identity=attribute_identity,
        class_config_id=class_config_id,
        attribute_config_id=attribute_config_id,
        default_identity_key=False,
    )
    enriched_operation = _attribute_membership_update_operation_with_identity(
        operation=operation,
        semantic_key=semantic_key,
        attribute_semantic_key=attribute_semantic_key,
        class_config_id=class_config_id,
        attribute_config_id=attribute_config_id,
        edge_id=edge_id,
        executable_object_id=execution_receiver_object_id,
        baseline_signature=baseline_signature,
        current_signature=current_signature,
    )
    provider_delta_typed_operation_metadata = (
        _provider_delta_typed_operation_metadata_for_attribute_membership_update(
            operation=enriched_operation,
        )
    )
    blockers = tuple(
        blocker
        for blocker, value in (
            ("missing_class_name", class_name),
            ("missing_attribute_name", attribute_name),
            ("missing_owner_semantic_key", owner_semantic_key),
            ("missing_class_config_id", class_config_id),
            ("missing_attribute_config_id", attribute_config_id),
            ("missing_class_config_attribute_config_id", edge_id),
        )
        if value is None
    )
    metadata: dict[str, object] = {
        "source": "aware_meta.semantic_operation_resolution",
        "semantic_apply_boundary": "provider_delta_ontology_operation_executor",
        "provider_delta_handler_key": "attribute_membership.edge_function_calls",
        "provider_operation_type": "meta_ocg.attribute_membership.update",
        "execution_ready": not blockers,
        "execution_preconditions": ("provider_delta_ontology_operation_executor",),
        "preview_only": True,
        "receiver_semantic_key": edge_semantic_key or semantic_key,
        "receiver_object_id": execution_receiver_object_id,
        "result_semantic_key": semantic_key,
        "result_object_id": edge_id,
        "semantic_source_object_id": edge_id,
        **provider_delta_typed_operation_metadata,
    }
    if (
        execution_receiver_object_id is not None
        and edge_id is not None
        and execution_receiver_object_id != edge_id
    ):
        metadata["semantic_apply_receiver_object_id"] = execution_receiver_object_id
    return _blocked_resolution(
        operation=enriched_operation,
        reason=(
            "meta_ocg_attribute_membership_update_requires_provider_delta_"
            "ontology_operation_executor"
        ),
        blockers=(
            *blockers,
            "semantic_plan_single_function_call_preview_not_supported",
            "provider_delta_attribute_membership_update_operation_executor_required",
        ),
        metadata=metadata,
    )


def _resolve_attribute_create(
    *,
    operation: Mapping[str, object],
    current_objects: Mapping[str, str],
) -> MetaSemanticOperationResolution:
    operation_family = _string_value(operation.get("operation_family"))
    if operation_family not in {"create", "upsert"}:
        return _blocked_resolution(
            operation=operation,
            reason="meta_ocg_attribute_create_requires_create_family",
            blockers=(
                "unsupported_operation_family:" f"{operation_family or 'unknown'}",
            ),
        )
    subject_type = _string_value(operation.get("semantic_subject_type"))
    if subject_type not in {"AttributeConfig", "aware_meta.AttributeConfig"}:
        return _blocked_resolution(
            operation=operation,
            reason="meta_ocg_attribute_create_subject_not_supported",
            blockers=(
                "unsupported_semantic_subject_type:" f"{subject_type or 'unknown'}",
            ),
        )
    after_payload = _mapping_value(operation.get("after_payload"))
    semantic_key = _semantic_key(operation)
    class_name = _first_text(
        after_payload.get("class_name"),
        _class_name_from_attribute_semantic_key(semantic_key),
    )
    attribute_name = _first_text(
        after_payload.get("attribute_name"),
        after_payload.get("name"),
        _attribute_name_from_attribute_semantic_key(semantic_key),
    )
    raw_class_fqn = _first_text(
        after_payload.get("class_fqn"),
        after_payload.get("owner_key"),
        after_payload.get("node_key"),
        class_name,
    )
    class_fqn = _class_fqn_from_package_context(
        class_name=class_name,
        raw_class_fqn=raw_class_fqn,
        operation=operation,
    )
    owner_semantic_key = _first_text(
        after_payload.get("owner_semantic_key"),
        after_payload.get("parent_semantic_key"),
        f"meta.class:{class_name}" if class_name is not None else None,
    )
    owner_object_id = (
        current_objects.get(owner_semantic_key) if owner_semantic_key is not None else None
    )
    attribute_config_id = _first_text(
        after_payload.get("attribute_config_id"),
        after_payload.get("entity_id"),
        _stable_attribute_config_id_for_create(
            owner_key=class_fqn,
            attribute_name=attribute_name,
        ),
    )
    blockers = tuple(
        blocker
        for blocker, value in (
            ("missing_class_name", class_name),
            ("missing_class_fqn", class_fqn),
            ("missing_attribute_name", attribute_name),
            ("missing_owner_semantic_key", owner_semantic_key),
            ("missing_owner_object_id", owner_object_id),
            ("missing_attribute_config_id", attribute_config_id),
        )
        if value is None
    )
    provider_delta_typed_operation_metadata = (
        _provider_delta_typed_operation_metadata_for_attribute_structural(
            operation=operation,
            operation_kind="create",
            owner_semantic_key=owner_semantic_key,
            owner_object_id=owner_object_id,
            owner_key=class_fqn,
            class_name=class_name,
            attribute_name=attribute_name,
            attribute_config_id=attribute_config_id,
        )
    )
    metadata: dict[str, object] = {
        "source": "aware_meta.semantic_operation_resolution",
        "semantic_apply_boundary": "provider_delta_ontology_operation_executor",
        "provider_delta_handler_key": "attribute.scalar_function_calls",
        "provider_operation_type": "meta_ocg.attribute.create",
        "requires_baseline_object_identity": False,
        "requires_owner_semantic_object_identity": True,
        "execution_ready": not blockers,
        "execution_preconditions": ("provider_delta_ontology_operation_executor",),
        "preview_only": True,
        "receiver_semantic_key": owner_semantic_key,
        "receiver_object_id": owner_object_id,
        "result_semantic_key": semantic_key,
        "result_object_id": attribute_config_id,
        **provider_delta_typed_operation_metadata,
    }
    if class_name is not None:
        metadata["class_name"] = class_name
    if class_fqn is not None:
        metadata["class_fqn"] = class_fqn
    if attribute_name is not None:
        metadata["attribute_name"] = attribute_name
    return _blocked_resolution(
        operation=operation,
        reason=(
            "meta_ocg_attribute_create_requires_provider_delta_"
            "ontology_operation_executor"
        ),
        blockers=(
            *blockers,
            "semantic_plan_single_function_call_preview_not_supported",
            "provider_delta_attribute_create_operation_executor_required",
        ),
        metadata=metadata,
    )


def _resolve_attribute_delete(
    *,
    operation: Mapping[str, object],
    current_objects: Mapping[str, str],
) -> MetaSemanticOperationResolution:
    operation_family = _string_value(operation.get("operation_family"))
    if operation_family != "delete":
        return _blocked_resolution(
            operation=operation,
            reason="meta_ocg_attribute_delete_requires_delete_family",
            blockers=(
                "unsupported_operation_family:" f"{operation_family or 'unknown'}",
            ),
        )
    subject_type = _string_value(operation.get("semantic_subject_type"))
    if subject_type not in {"AttributeConfig", "aware_meta.AttributeConfig"}:
        return _blocked_resolution(
            operation=operation,
            reason="meta_ocg_attribute_delete_subject_not_supported",
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
        _class_name_from_attribute_semantic_key(semantic_key),
    )
    attribute_name = _first_text(
        before_payload.get("attribute_name"),
        before_payload.get("name"),
        after_payload.get("attribute_name"),
        after_payload.get("name"),
        _attribute_name_from_attribute_semantic_key(semantic_key),
    )
    raw_class_fqn = _first_text(
        before_payload.get("class_fqn"),
        before_payload.get("owner_key"),
        before_payload.get("node_key"),
        after_payload.get("class_fqn"),
        after_payload.get("owner_key"),
        after_payload.get("node_key"),
        class_name,
    )
    class_fqn = _class_fqn_from_package_context(
        class_name=class_name,
        raw_class_fqn=raw_class_fqn,
        operation=operation,
    )
    owner_semantic_key = _first_text(
        before_payload.get("owner_semantic_key"),
        before_payload.get("parent_semantic_key"),
        after_payload.get("owner_semantic_key"),
        after_payload.get("parent_semantic_key"),
        f"meta.class:{class_name}" if class_name is not None else None,
    )
    owner_object_id = (
        current_objects.get(owner_semantic_key) if owner_semantic_key is not None else None
    )
    attribute_config_id = _first_text(
        current_objects.get(semantic_key),
        before_payload.get("attribute_config_id"),
        before_payload.get("entity_id"),
        after_payload.get("attribute_config_id"),
        after_payload.get("entity_id"),
        _stable_attribute_config_id_for_create(
            owner_key=class_fqn,
            attribute_name=attribute_name,
        ),
    )
    blockers = tuple(
        blocker
        for blocker, value in (
            ("missing_class_name", class_name),
            ("missing_class_fqn", class_fqn),
            ("missing_attribute_name", attribute_name),
            ("missing_owner_semantic_key", owner_semantic_key),
            ("missing_owner_object_id", owner_object_id),
            ("missing_attribute_config_id", attribute_config_id),
        )
        if value is None
    )
    provider_delta_typed_operation_metadata = (
        _provider_delta_typed_operation_metadata_for_attribute_structural(
            operation=operation,
            operation_kind="delete",
            owner_semantic_key=owner_semantic_key,
            owner_object_id=owner_object_id,
            owner_key=class_fqn,
            class_name=class_name,
            attribute_name=attribute_name,
            attribute_config_id=attribute_config_id,
        )
    )
    metadata: dict[str, object] = {
        "source": "aware_meta.semantic_operation_resolution",
        "semantic_apply_boundary": "provider_delta_ontology_operation_executor",
        "provider_delta_handler_key": "attribute.scalar_function_calls",
        "provider_operation_type": "meta_ocg.attribute.delete",
        "requires_baseline_object_identity": True,
        "requires_owner_semantic_object_identity": True,
        "execution_ready": not blockers,
        "execution_preconditions": ("provider_delta_ontology_operation_executor",),
        "preview_only": True,
        "receiver_semantic_key": owner_semantic_key,
        "receiver_object_id": owner_object_id,
        "result_semantic_key": semantic_key,
        "result_object_id": attribute_config_id,
        **provider_delta_typed_operation_metadata,
    }
    if class_name is not None:
        metadata["class_name"] = class_name
    if class_fqn is not None:
        metadata["class_fqn"] = class_fqn
    if attribute_name is not None:
        metadata["attribute_name"] = attribute_name
    return _blocked_resolution(
        operation=operation,
        reason=(
            "meta_ocg_attribute_delete_requires_provider_delta_"
            "ontology_operation_executor"
        ),
        blockers=(
            *blockers,
            "semantic_plan_single_function_call_preview_not_supported",
            "provider_delta_attribute_delete_operation_executor_required",
        ),
        metadata=metadata,
    )


def _attribute_default_value_update_resolution(
    *,
    operation: Mapping[str, object],
    current_objects: Mapping[str, str],
) -> MetaSemanticOperationResolution:
    semantic_key = _semantic_key(operation)
    receiver_object_id = current_objects.get(semantic_key)
    provider_delta_typed_operation_metadata = (
        _provider_delta_typed_operation_metadata_for_attribute_default_value_update(
            operation=operation,
        )
    )
    metadata: dict[str, object] = {
        "source": "aware_meta.semantic_operation_resolution",
        "semantic_apply_boundary": "provider_delta_ontology_operation_executor",
        "provider_delta_handler_key": "attribute.scalar_function_calls",
        "provider_operation_type": "meta_ocg.attribute.update",
        "requires_baseline_object_identity": True,
        "execution_ready": receiver_object_id is not None,
        "execution_preconditions": ("provider_delta_ontology_operation_executor",),
        "preview_only": True,
        **provider_delta_typed_operation_metadata,
    }
    if receiver_object_id is not None:
        metadata["receiver_object_id"] = receiver_object_id
    return _blocked_resolution(
        operation=operation,
        reason=(
            "meta_ocg_attribute_default_value_update_requires_provider_delta_"
            "ontology_operation_executor"
        ),
        blockers=(
            "semantic_plan_single_function_call_preview_not_supported",
            "provider_delta_attribute_update_operation_executor_required",
        ),
        metadata=metadata,
    )


def _resolve_attribute_identity_rename(
    *,
    operation: Mapping[str, object],
) -> MetaSemanticOperationResolution:
    operation_family = _string_value(operation.get("operation_family"))
    if operation_family != "rename":
        return _blocked_resolution(
            operation=operation,
            reason="meta_ocg_attribute_identity_rename_requires_rename_family",
            blockers=(
                "unsupported_operation_family:" f"{operation_family or 'unknown'}",
            ),
        )
    subject_type = _string_value(operation.get("semantic_subject_type"))
    if subject_type not in {"AttributeConfig", "aware_meta.AttributeConfig"}:
        return _blocked_resolution(
            operation=operation,
            reason="meta_ocg_attribute_identity_rename_subject_not_supported",
            blockers=(
                "unsupported_semantic_subject_type:" f"{subject_type or 'unknown'}",
            ),
        )
    field_path = _optional_text(operation.get("field_path"))
    if field_path not in {None, "name"}:
        return _blocked_resolution(
            operation=operation,
            reason="meta_ocg_attribute_identity_rename_field_not_supported",
            blockers=(f"unsupported_field_path:{field_path or 'unknown'}",),
        )

    before_payload = _mapping_value(operation.get("before_payload"))
    after_payload = _mapping_value(operation.get("after_payload"))
    before_class_name = _first_text(
        before_payload.get("class_name"),
        after_payload.get("class_name"),
    )
    after_class_name = _first_text(
        after_payload.get("class_name"),
        before_class_name,
    )
    before_attribute_name = _first_text(
        before_payload.get("attribute_name"),
        before_payload.get("name"),
    )
    after_attribute_name = _first_text(
        after_payload.get("attribute_name"),
        after_payload.get("name"),
    )
    before_semantic_key = _attribute_semantic_key_for_parts(
        class_name=before_class_name,
        attribute_name=before_attribute_name,
    )
    after_semantic_key = _attribute_semantic_key_for_parts(
        class_name=after_class_name,
        attribute_name=after_attribute_name,
    )
    blockers = tuple(
        blocker
        for blocker, value in (
            ("missing_before_attribute_identity", before_semantic_key),
            ("missing_after_attribute_identity", after_semantic_key),
        )
        if value is None
    )
    return _blocked_resolution(
        operation=operation,
        reason="meta_ocg_attribute_identity_rename_requires_explicit_replacement_policy",
        blockers=(
            *blockers,
            "attribute_identity_rename_is_not_mutable_update",
            "attribute_identity_replacement_requires_explicit_delete_create_or_migration",
            "provider_delta_attribute_identity_rename_execution_not_supported",
        ),
        metadata={
            "source": "aware_meta.semantic_operation_resolution",
            "semantic_apply_boundary": "provider_delta_ontology_operation_executor",
            "provider_operation_type": "meta_ocg.attribute.identity.rename",
            "replacement_policy": "explicit_fallback_required",
            "fallback_required": True,
            "fallback_reason": (
                "meta_attribute_identity_rename_requires_explicit_replacement_policy"
            ),
            "execution_ready": False,
            "preview_only": True,
            "before_semantic_key": before_semantic_key,
            "after_semantic_key": after_semantic_key,
            "before_attribute_name": before_attribute_name,
            "after_attribute_name": after_attribute_name,
            "before_class_name": before_class_name,
            "after_class_name": after_class_name,
            "allowed_replacement_operations": (
                META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_DELETE_OPERATION,
                META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_CREATE_OPERATION,
            ),
        },
    )


def _primitive_attribute_update_resolution(
    *,
    operation: Mapping[str, object],
    primitive_base_type: str,
    current_objects: Mapping[str, str],
) -> MetaSemanticOperationResolution:
    semantic_key = _semantic_key(operation)
    receiver_object_id = current_objects.get(semantic_key)
    provider_delta_typed_operation_metadata = (
        _provider_delta_typed_operation_metadata_for_attribute_type_update(
            operation=operation,
        )
    )
    metadata: dict[str, object] = {
        "source": "aware_meta.semantic_operation_resolution",
        "semantic_apply_boundary": "provider_delta_ontology_operation_executor",
        "provider_delta_handler_key": "attribute.scalar_function_calls",
        "provider_operation_type": "meta_ocg.attribute.update",
        "requires_baseline_object_identity": True,
        "execution_ready": receiver_object_id is not None,
        "execution_preconditions": ("provider_delta_ontology_operation_executor",),
        "preview_only": True,
        "descriptor_kind": "primitive",
        "primitive_base_type": primitive_base_type,
        **provider_delta_typed_operation_metadata,
    }
    if receiver_object_id is not None:
        metadata["receiver_object_id"] = receiver_object_id
    return _blocked_resolution(
        operation=operation,
        reason=(
            "meta_ocg_attribute_type_update_requires_provider_delta_"
            "ontology_operation_executor"
        ),
        blockers=(
            "semantic_plan_single_function_call_preview_not_supported",
            "provider_delta_attribute_update_operation_executor_required",
        ),
        metadata=metadata,
    )


def _provider_delta_typed_operation_metadata_for_attribute_type_update(
    *,
    operation: Mapping[str, object],
) -> dict[str, object]:
    from aware_meta.materialization.deltas.source_projection import (  # noqa: WPS433,E501
        typed_operation_plan_from_semantic_source_meaning,
    )

    typed_operation_plan = typed_operation_plan_from_semantic_source_meaning(
        semantic_status={},
        typed_operations=(operation,),
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
            "attribute_type_provider_delta_operation_ready"
            if ready
            else "attribute_type_provider_delta_operation_blocked"
        ),
        "provider_delta_typed_operation_plan": typed_operation_plan,
    }
    if typed_operation is not None:
        metadata["provider_delta_typed_operation"] = dict(typed_operation)
    if not ready:
        metadata["provider_delta_typed_operation_blockers"] = (
            "attribute_type_provider_delta_typed_operation_unavailable",
        )
    metadata.update(
        _attribute_type_generated_materialization_intent_metadata(
            typed_operation_plan=typed_operation_plan,
            typed_operation=typed_operation,
            ready=ready,
        )
    )
    return metadata


def _provider_delta_typed_operation_metadata_for_attribute_default_value_update(
    *,
    operation: Mapping[str, object],
) -> dict[str, object]:
    from aware_meta.materialization.deltas.source_projection import (  # noqa: WPS433,E501
        typed_operation_plan_from_semantic_source_meaning,
    )

    typed_operation_plan = typed_operation_plan_from_semantic_source_meaning(
        semantic_status={},
        typed_operations=(operation,),
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
            "attribute_default_value_provider_delta_operation_ready"
            if ready
            else "attribute_default_value_provider_delta_operation_blocked"
        ),
        "provider_delta_typed_operation_plan": typed_operation_plan,
    }
    if typed_operation is not None:
        metadata["provider_delta_typed_operation"] = dict(typed_operation)
    if not ready:
        metadata["provider_delta_typed_operation_blockers"] = (
            "attribute_default_value_provider_delta_typed_operation_unavailable",
        )
    metadata.update(
        _attribute_default_value_generated_materialization_intent_metadata(
            typed_operation_plan=typed_operation_plan,
            typed_operation=typed_operation,
            ready=ready,
        )
    )
    return metadata


def _provider_delta_typed_operation_metadata_for_attribute_membership_update(
    *,
    operation: Mapping[str, object],
) -> dict[str, object]:
    from aware_meta.materialization.deltas.source_projection import (  # noqa: WPS433,E501
        typed_operation_plan_from_semantic_source_meaning,
    )

    typed_operation_plan = typed_operation_plan_from_semantic_source_meaning(
        semantic_status={},
        typed_operations=(operation,),
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
            "attribute_membership_provider_delta_operation_ready"
            if ready
            else "attribute_membership_provider_delta_operation_blocked"
        ),
        "provider_delta_typed_operation_plan": typed_operation_plan,
    }
    if typed_operation is not None:
        metadata["provider_delta_typed_operation"] = dict(typed_operation)
    if not ready:
        metadata["provider_delta_typed_operation_blockers"] = (
            "attribute_membership_provider_delta_typed_operation_unavailable",
        )
    return metadata


def _attribute_membership_update_operation_with_identity(
    *,
    operation: Mapping[str, object],
    semantic_key: str,
    attribute_semantic_key: str,
    class_config_id: str | None,
    attribute_config_id: str | None,
    edge_id: str | None,
    executable_object_id: str | None,
    baseline_signature: Mapping[str, object],
    current_signature: Mapping[str, object],
) -> Mapping[str, object]:
    enriched = dict(operation)
    before_payload = dict(_mapping_value(operation.get("before_payload")))
    after_payload = dict(_mapping_value(operation.get("after_payload")))
    for payload, signature in (
        (before_payload, baseline_signature),
        (after_payload, current_signature),
    ):
        payload.setdefault("attribute_semantic_key", attribute_semantic_key)
        payload.setdefault("attribute_membership_semantic_key", semantic_key)
        payload.setdefault("attribute_membership_owner_kind", "class")
        payload.setdefault("attribute_membership_signature", dict(signature))
        if class_config_id is not None:
            payload.setdefault("class_config_id", class_config_id)
        if attribute_config_id is not None:
            payload.setdefault("attribute_config_id", attribute_config_id)
        if edge_id is not None:
            payload.setdefault("class_config_attribute_config_id", edge_id)
            payload.setdefault("entity_id", edge_id)
        if (
            executable_object_id is not None
            and edge_id is not None
            and executable_object_id != edge_id
        ):
            payload.setdefault(
                "semantic_apply_receiver_object_id",
                executable_object_id,
            )
            payload.setdefault("executable_object_id", executable_object_id)
    if (
        executable_object_id is not None
        and edge_id is not None
        and executable_object_id != edge_id
    ):
        enriched["semantic_apply_receiver_object_id"] = executable_object_id
        enriched["executable_object_id"] = executable_object_id
    enriched["before_payload"] = before_payload
    enriched["after_payload"] = after_payload
    return enriched


def _attribute_identity_for_membership_update(
    *,
    operation: Mapping[str, object],
    semantic_key: str,
    attribute_semantic_key: str,
    current_object_identities: Mapping[str, Mapping[str, object]],
) -> Mapping[str, object]:
    direct_identity = (
        current_object_identities.get(semantic_key)
    )
    if direct_identity is not None:
        return direct_identity
    class_name = _first_text(
        _mapping_value(operation.get("after_payload")).get("class_name"),
        _mapping_value(operation.get("before_payload")).get("class_name"),
        _class_name_from_attribute_semantic_key(attribute_semantic_key),
    )
    attribute_name = _first_text(
        _mapping_value(operation.get("after_payload")).get("attribute_name"),
        _mapping_value(operation.get("before_payload")).get("attribute_name"),
        _attribute_name_from_attribute_semantic_key(attribute_semantic_key),
    )
    if class_name is not None and attribute_name is not None:
        edge_identity = current_object_identities.get(
            f"meta.class_attribute_edge:{class_name}.{attribute_name}"
        )
        if edge_identity is not None:
            return edge_identity
    attribute_identity = current_object_identities.get(attribute_semantic_key)
    if attribute_identity is not None:
        return attribute_identity
    matches = tuple(
        identity
        for identity_key, identity in current_object_identities.items()
        if _attribute_identity_matches_membership_update(
            identity_key=identity_key,
            identity=identity,
            class_name=class_name,
            attribute_name=attribute_name,
        )
    )
    if len(matches) == 1:
        return matches[0]
    edge_matches = tuple(
        identity
        for identity in matches
        if _first_text(identity.get("object_kind")) == "class_attribute_edge"
    )
    if len(edge_matches) == 1:
        return edge_matches[0]
    return {}


def _attribute_identity_matches_membership_update(
    *,
    identity_key: str,
    identity: Mapping[str, object],
    class_name: str | None,
    attribute_name: str | None,
) -> bool:
    if attribute_name is None:
        return False
    identity_attribute_name = _first_text(
        identity.get("attribute_name"),
        identity.get("name"),
        _attribute_name_from_attribute_semantic_key(identity_key),
    )
    if identity_attribute_name != attribute_name:
        return False
    if class_name is None:
        return True
    identity_class_name = _first_text(
        identity.get("class_name"),
        _class_name_from_attribute_semantic_key(identity_key),
    )
    if identity_class_name == class_name:
        return True
    owner_semantic_key = _first_text(
        identity.get("owner_semantic_key"),
        identity.get("parent_semantic_key"),
    )
    return owner_semantic_key == f"meta.class:{class_name}"


def _attribute_membership_signature_for_payload(
    *,
    payload: Mapping[str, object],
    identity: Mapping[str, object],
    class_config_id: str | None,
    attribute_config_id: str | None,
    default_identity_key: bool,
) -> dict[str, object]:
    signature = dict(
        _mapping_value(identity.get("attribute_membership_signature"))
    )
    signature.update(_mapping_value(payload.get("attribute_membership_signature")))
    signature.setdefault("owner_kind", "class")
    if class_config_id is not None:
        signature.setdefault("class_config_id", class_config_id)
    if attribute_config_id is not None:
        signature.setdefault("attribute_config_id", attribute_config_id)
    if "position" not in signature:
        signature["position"] = 0
    identity_key_value = payload.get("is_identity_key")
    if isinstance(identity_key_value, bool):
        signature["is_identity_key"] = identity_key_value
    else:
        signature.setdefault("is_identity_key", default_identity_key)
    return signature


def _attribute_semantic_key_from_membership_key(value: str) -> str:
    return value.split("/membership:", maxsplit=1)[0]


def _attribute_semantic_key_for_parts(
    *,
    class_name: str | None,
    attribute_name: str | None,
) -> str | None:
    if class_name is None or attribute_name is None:
        return None
    return f"meta.attribute:{class_name}.{attribute_name}"


def _attribute_membership_edge_semantic_key(
    *,
    class_name: str | None,
    attribute_name: str | None,
) -> str | None:
    if class_name is None or attribute_name is None:
        return None
    return f"meta.class_attribute_edge:{class_name}.{attribute_name}"


def _provider_delta_typed_operation_metadata_for_attribute_structural(
    *,
    operation: Mapping[str, object],
    operation_kind: str,
    owner_semantic_key: str | None,
    owner_object_id: str | None,
    owner_key: str | None,
    class_name: str | None,
    attribute_name: str | None,
    attribute_config_id: str | None,
) -> dict[str, object]:
    from aware_meta.materialization.deltas.source_projection import (  # noqa: WPS433,E501
        typed_operation_plan_from_semantic_source_meaning,
    )

    typed_operation_plan = typed_operation_plan_from_semantic_source_meaning(
        semantic_status={},
        typed_operations=(operation,),
    )
    if (
        owner_semantic_key is not None
        and owner_object_id is not None
        and owner_key is not None
        and attribute_name is not None
        and attribute_config_id is not None
    ):
        typed_operation_plan = _attribute_structural_typed_operation_plan_with_identity(
            typed_operation_plan=typed_operation_plan,
            owner_semantic_key=owner_semantic_key,
            owner_object_id=owner_object_id,
            owner_key=owner_key,
            class_name=class_name,
            attribute_name=attribute_name,
            attribute_config_id=attribute_config_id,
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
        _attribute_structural_generated_materialization_intent_metadata(
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
            f"attribute_{operation_kind}_provider_delta_operation_ready"
            if ready
            else f"attribute_{operation_kind}_provider_delta_operation_blocked"
        ),
        "provider_delta_typed_operation_plan": typed_operation_plan,
        **generated_materialization_metadata,
    }
    if typed_operation is not None:
        metadata["provider_delta_typed_operation"] = dict(typed_operation)
    if not ready:
        metadata["provider_delta_typed_operation_blockers"] = (
            f"attribute_{operation_kind}_provider_delta_typed_operation_unavailable",
        )
    return metadata


def _attribute_structural_generated_materialization_intent_metadata(
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
            f"attribute_{operation_kind}_generated_materialization_"
            "typed_plan_unavailable",
        )
    )
    status = (
        "generated_materialization_intent_ready"
        if ready
        else "generated_materialization_intent_blocked"
    )
    reason = (
        f"attribute_{operation_kind}_generated_materialization_intent_ready"
        if ready
        else f"attribute_{operation_kind}_generated_materialization_intent_blocked"
    )
    contract_version = (
        META_ATTRIBUTE_CREATE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION
        if operation_kind == "create"
        else META_ATTRIBUTE_DELETE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION
    )
    intent: dict[str, object] = {
        "intent_kind": (
            f"meta_attribute_{operation_kind}_generated_materialization_intent"
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
                "renderer_key": "python.orm.attribute.field",
                "policy_key": f"aware_meta.python_orm.attribute.{operation_kind}",
                "materialization_target": "python_orm_attribute_field",
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


def _attribute_structural_typed_operation_plan_with_identity(
    *,
    typed_operation_plan: Mapping[str, object],
    owner_semantic_key: str,
    owner_object_id: str,
    owner_key: str,
    class_name: str | None,
    attribute_name: str,
    attribute_config_id: str,
) -> dict[str, object]:
    enriched_plan = dict(typed_operation_plan)
    enriched_plan["typed_operations"] = tuple(
        (
            _attribute_structural_typed_operation_with_identity(
                typed_operation=item,
                owner_semantic_key=owner_semantic_key,
                owner_object_id=owner_object_id,
                owner_key=owner_key,
                class_name=class_name,
                attribute_name=attribute_name,
                attribute_config_id=attribute_config_id,
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
            "operation_key": f"meta_ocg.class.anchor:{owner_semantic_key}",
            "operation_family": "anchor",
            "provider_operation_type": "meta_ocg.class.anchor",
            "semantic_key": owner_semantic_key,
            "ontology_subject_kind": "class",
            "baseline": {
                "object_id": owner_object_id,
                "entity_id": owner_object_id,
            },
            "current": {
                "entity_id": owner_object_id,
                "object_id": owner_object_id,
                "object_kind": "class",
                "node_type": "class",
                "class_config_id": owner_object_id,
                "class_fqn": owner_key,
                "class_name": class_name,
                "entity_name": class_name,
                "payload": {
                    "entity_id": owner_object_id,
                    "object_id": owner_object_id,
                    "object_kind": "class",
                    "node_type": "class",
                    "class_config_id": owner_object_id,
                    "class_fqn": owner_key,
                    "class_name": class_name,
                    "entity_name": class_name,
                },
            },
            "source_refs": (),
        },
    )
    return enriched_plan


def _attribute_structural_typed_operation_with_identity(
    *,
    typed_operation: Mapping[str, object],
    owner_semantic_key: str,
    owner_object_id: str,
    owner_key: str,
    class_name: str | None,
    attribute_name: str,
    attribute_config_id: str,
) -> dict[str, object]:
    enriched = dict(typed_operation)
    current = _mapping_value(enriched.get("current"))
    current_payload = _mapping_value(current.get("payload"))
    baseline = _mapping_value(enriched.get("baseline"))
    baseline_object = _mapping_value(baseline.get("object"))
    baseline_payload = _mapping_value(baseline_object.get("payload"))
    for target in (current, current_payload, baseline_object, baseline_payload):
        target.setdefault("owner_semantic_key", owner_semantic_key)
        target.setdefault("parent_semantic_key", owner_semantic_key)
        target.setdefault("owner_object_id", owner_object_id)
        target.setdefault("owner_key", owner_key)
        target.setdefault("class_fqn", owner_key)
        if class_name is not None:
            target.setdefault("class_name", class_name)
        target.setdefault("attribute_name", attribute_name)
        target.setdefault("entity_id", attribute_config_id)
        target.setdefault("attribute_config_id", attribute_config_id)
    if current_payload:
        current["payload"] = current_payload
    if baseline_payload:
        baseline_object["payload"] = baseline_payload
    if baseline_object:
        baseline["object"] = baseline_object
    enriched["current"] = current
    enriched["baseline"] = baseline
    return enriched


def _attribute_type_generated_materialization_intent_metadata(
    *,
    typed_operation_plan: Mapping[str, object],
    typed_operation: Mapping[str, object] | None,
    ready: bool,
) -> dict[str, object]:
    blockers: tuple[str, ...] = (
        ()
        if ready
        else ("attribute_type_generated_materialization_typed_plan_unavailable",)
    )
    status = (
        "generated_materialization_intent_ready"
        if ready
        else "generated_materialization_intent_blocked"
    )
    reason = (
        "attribute_type_generated_materialization_intent_ready"
        if ready
        else "attribute_type_generated_materialization_intent_blocked"
    )
    intent: dict[str, object] = {
        "intent_kind": "meta_attribute_type_generated_materialization_intent",
        "contract_version": (
            META_ATTRIBUTE_TYPE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION
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


def _attribute_default_value_generated_materialization_intent_metadata(
    *,
    typed_operation_plan: Mapping[str, object],
    typed_operation: Mapping[str, object] | None,
    ready: bool,
) -> dict[str, object]:
    blockers: tuple[str, ...] = (
        ()
        if ready
        else (
            "attribute_default_value_generated_materialization_typed_plan_unavailable",
        )
    )
    status = (
        "generated_materialization_intent_ready"
        if ready
        else "generated_materialization_intent_blocked"
    )
    reason = (
        "attribute_default_value_generated_materialization_intent_ready"
        if ready
        else "attribute_default_value_generated_materialization_intent_blocked"
    )
    intent: dict[str, object] = {
        "intent_kind": "meta_attribute_default_value_generated_materialization_intent",
        "contract_version": (
            META_ATTRIBUTE_DEFAULT_VALUE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION
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


def _after_type_descriptor(
    *,
    operation: Mapping[str, object],
) -> Mapping[str, object]:
    after_payload = _mapping_value(operation.get("after_payload"))
    if isinstance(after_payload.get("type_descriptor"), Mapping):
        return _mapping_value(after_payload.get("type_descriptor"))
    if isinstance(after_payload.get("descriptor"), Mapping):
        return _mapping_value(after_payload.get("descriptor"))
    type_value = _optional_text(after_payload.get("type"))
    if type_value is not None:
        if type_value in _PRIMITIVE_TYPE_NAMES:
            return {
                "descriptor_kind": "primitive",
                "primitive_base_type": type_value,
            }
        return {
            "descriptor_kind": "class",
            "class_name": type_value,
        }
    descriptor_kind = _optional_text(after_payload.get("descriptor_kind"))
    if descriptor_kind is not None:
        return after_payload
    return {}


def _descriptor_kind(*, descriptor: Mapping[str, object]) -> str | None:
    kind = _optional_text(descriptor.get("descriptor_kind"))
    if kind is not None:
        return kind
    if _optional_text(descriptor.get("primitive_base_type")) is not None:
        return "primitive"
    if _optional_text(descriptor.get("enum_config_id")) is not None:
        return "enum"
    if _optional_text(descriptor.get("class_config_id")) is not None:
        return "class"
    return None


def _primitive_base_type(*, descriptor: Mapping[str, object]) -> str | None:
    return _first_text(
        descriptor.get("primitive_base_type"),
        _mapping_value(descriptor.get("target")).get("primitive_base_type"),
        descriptor.get("type"),
    )
