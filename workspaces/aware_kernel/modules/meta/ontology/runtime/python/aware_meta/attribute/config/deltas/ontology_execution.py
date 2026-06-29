from __future__ import annotations

from collections.abc import Mapping
from uuid import UUID

from aware_meta.materialization.deltas.ontology_execution.contracts import (
    OntologyExecutionPlanningContext,
    OntologyInvocationIntent,
    OntologyOperationHandlerResult,
    OntologyTypedOperation,
    blocked_handler_result,
)
from aware_meta.materialization.deltas.ontology_execution.receiver_resolution import (
    mapping_value,
    optional_text,
    string_value,
)
from aware_meta.materialization.semantic_function_call_resolution import (
    META_CLASS_CONFIG_CREATE_CLASS_ATTRIBUTE_FUNCTION_REF,
    META_CLASS_CONFIG_CREATE_ENUM_ATTRIBUTE_FUNCTION_REF,
    META_CLASS_CONFIG_CREATE_PRIMITIVE_ATTRIBUTE_FUNCTION_REF,
    META_FUNCTION_CONFIG_ADD_CLASS_ATTRIBUTE_FUNCTION_REF,
    META_FUNCTION_CONFIG_ADD_ENUM_ATTRIBUTE_FUNCTION_REF,
    META_FUNCTION_CONFIG_ADD_PRIMITIVE_ATTRIBUTE_FUNCTION_REF,
)


HANDLER_KEY = "attribute.scalar_function_calls"
ATTRIBUTE_CREATE_INVOCATION_ORDER = 40
ATTRIBUTE_UPDATE_INVOCATION_ORDER = 40
ATTRIBUTE_DELETE_INVOCATION_ORDER = 40
ATTRIBUTE_CONFIG_UPDATE_PRIMITIVE_FUNCTION_REF = (
    "aware_meta_ontology.attribute.attribute_config." "AttributeConfig.update_primitive"
)
ATTRIBUTE_CONFIG_UPDATE_ENUM_FUNCTION_REF = (
    "aware_meta_ontology.attribute.attribute_config.AttributeConfig.update_enum"
)
ATTRIBUTE_CONFIG_UPDATE_CLASS_FUNCTION_REF = (
    "aware_meta_ontology.attribute.attribute_config.AttributeConfig.update_class"
)
CLASS_CONFIG_REMOVE_ATTRIBUTE_CONFIG_FUNCTION_REF = (
    "aware_meta_ontology.class_.class_config.ClassConfig.remove_attribute_config"
)
FUNCTION_CONFIG_REMOVE_ATTRIBUTE_CONFIG_FUNCTION_REF = "aware_meta_ontology.function.function_config.FunctionConfig.remove_attribute_config"


def plan_attribute_operation(
    operation: OntologyTypedOperation,
    context: OntologyExecutionPlanningContext,
) -> OntologyOperationHandlerResult:
    if operation.ontology_subject_kind != "attribute":
        return blocked_handler_result(
            operation=operation,
            handler_key=HANDLER_KEY,
            reason="meta_ocg_ontology_handler_subject_mismatch",
            blockers=(f"unsupported_subject:{operation.ontology_subject_kind}",),
        )
    if operation.operation_family == "update":
        return _plan_attribute_update_operation(operation=operation)
    if operation.operation_family == "delete":
        return _plan_attribute_delete_operation(
            operation=operation,
            context=context,
        )
    if operation.operation_family != "create":
        return blocked_handler_result(
            operation=operation,
            handler_key=HANDLER_KEY,
            reason="meta_ocg_attribute_delta_requires_create_operation",
            blockers=(f"unsupported_operation_family:{operation.operation_family}",),
        )
    return _plan_attribute_create_operation(operation=operation, context=context)


def _plan_attribute_create_operation(
    *,
    operation: OntologyTypedOperation,
    context: OntologyExecutionPlanningContext,
) -> OntologyOperationHandlerResult:
    receiver = _attribute_receiver_resolution(
        operation=operation,
        context=context,
    )
    if receiver["status"] != "attribute_receiver_resolved":
        return blocked_handler_result(
            operation=operation,
            handler_key=HANDLER_KEY,
            reason=string_value(receiver.get("reason")),
            blockers=_tuple_text(receiver.get("blockers")),
        )

    binding = _attribute_create_binding(
        operation=operation,
        receiver=receiver,
    )
    if binding["status"] != "attribute_create_binding_ready":
        return blocked_handler_result(
            operation=operation,
            handler_key=HANDLER_KEY,
            reason=string_value(binding.get("reason")),
            blockers=_tuple_text(binding.get("blockers")),
        )

    return OntologyOperationHandlerResult(
        operation_key=operation.operation_key,
        semantic_key=operation.semantic_key,
        handler_key=HANDLER_KEY,
        status="ontology_operation_handler_ready",
        reason="meta_ocg_attribute_create_function_call_ready",
        invocation_intents=(
            OntologyInvocationIntent(
                intent_key=f"{operation.operation_key}:create_attribute",
                operation_key=operation.operation_key,
                semantic_key=operation.semantic_key,
                invocation_order=ATTRIBUTE_CREATE_INVOCATION_ORDER,
                invocation_mode="instance",
                owner_class_name=string_value(binding.get("owner_class_name")),
                function_name=string_value(binding.get("function_name")),
                function_ref=string_value(binding.get("function_ref")),
                target_object_id=optional_text(receiver.get("receiver_entity_id")),
                receiver_semantic_key=optional_text(receiver.get("owner_semantic_key")),
                result_semantic_key=operation.semantic_key,
                expected_result_object_id=_attribute_object_id(operation=operation),
                kwargs=mapping_value(binding.get("arguments")),
            ),
        ),
    )


def _plan_attribute_update_operation(
    *,
    operation: OntologyTypedOperation,
) -> OntologyOperationHandlerResult:
    attribute_object_id = _attribute_update_object_id(operation=operation)
    if attribute_object_id is None:
        return blocked_handler_result(
            operation=operation,
            handler_key=HANDLER_KEY,
            reason="meta_ocg_attribute_update_requires_attribute_object_id",
            blockers=("missing_attribute_object_id",),
        )
    binding = _attribute_update_binding(operation=operation)
    if binding["status"] != "attribute_update_binding_ready":
        return blocked_handler_result(
            operation=operation,
            handler_key=HANDLER_KEY,
            reason=string_value(binding.get("reason")),
            blockers=_tuple_text(binding.get("blockers")),
        )
    return OntologyOperationHandlerResult(
        operation_key=operation.operation_key,
        semantic_key=operation.semantic_key,
        handler_key=HANDLER_KEY,
        status="ontology_operation_handler_ready",
        reason="meta_ocg_attribute_update_function_call_ready",
        invocation_intents=(
            OntologyInvocationIntent(
                intent_key=f"{operation.operation_key}:update_attribute",
                operation_key=operation.operation_key,
                semantic_key=operation.semantic_key,
                invocation_order=ATTRIBUTE_UPDATE_INVOCATION_ORDER,
                invocation_mode="instance",
                owner_class_name="AttributeConfig",
                function_name=string_value(binding.get("function_name")),
                function_ref=string_value(binding.get("function_ref")),
                target_object_id=attribute_object_id,
                receiver_semantic_key=operation.semantic_key,
                result_semantic_key=operation.semantic_key,
                expected_result_object_id=attribute_object_id,
                kwargs=mapping_value(binding.get("arguments")),
            ),
        ),
    )


def _plan_attribute_delete_operation(
    *,
    operation: OntologyTypedOperation,
    context: OntologyExecutionPlanningContext,
) -> OntologyOperationHandlerResult:
    attribute_object_id = _attribute_update_object_id(operation=operation)
    if attribute_object_id is None:
        return blocked_handler_result(
            operation=operation,
            handler_key=HANDLER_KEY,
            reason="meta_ocg_attribute_delete_requires_attribute_object_id",
            blockers=("missing_attribute_object_id",),
        )
    receiver = _attribute_delete_receiver_resolution(
        operation=operation,
        context=context,
    )
    if receiver["status"] != "attribute_receiver_resolved":
        return blocked_handler_result(
            operation=operation,
            handler_key=HANDLER_KEY,
            reason=string_value(receiver.get("reason")),
            blockers=_tuple_text(receiver.get("blockers")),
        )
    binding = _attribute_delete_binding(
        operation=operation,
        receiver=receiver,
        attribute_object_id=attribute_object_id,
    )
    if binding["status"] != "attribute_delete_binding_ready":
        return blocked_handler_result(
            operation=operation,
            handler_key=HANDLER_KEY,
            reason=string_value(binding.get("reason")),
            blockers=_tuple_text(binding.get("blockers")),
        )

    return OntologyOperationHandlerResult(
        operation_key=operation.operation_key,
        semantic_key=operation.semantic_key,
        handler_key=HANDLER_KEY,
        status="ontology_operation_handler_ready",
        reason="meta_ocg_attribute_delete_function_call_ready",
        invocation_intents=(
            OntologyInvocationIntent(
                intent_key=f"{operation.operation_key}:delete_attribute",
                operation_key=operation.operation_key,
                semantic_key=operation.semantic_key,
                invocation_order=ATTRIBUTE_DELETE_INVOCATION_ORDER,
                invocation_mode="instance",
                owner_class_name=string_value(binding.get("owner_class_name")),
                function_name=string_value(binding.get("function_name")),
                function_ref=string_value(binding.get("function_ref")),
                target_object_id=optional_text(receiver.get("receiver_entity_id")),
                receiver_semantic_key=optional_text(receiver.get("owner_semantic_key")),
                result_semantic_key=operation.semantic_key,
                expected_result_object_id=attribute_object_id,
                kwargs=mapping_value(binding.get("arguments")),
                reason="meta_ocg_attribute_delete_membership_remove_ready",
            ),
        ),
    )


def _attribute_receiver_resolution(
    *,
    operation: OntologyTypedOperation,
    context: OntologyExecutionPlanningContext,
) -> dict[str, object]:
    current = operation.current
    current_payload = mapping_value(current.get("payload"))
    owner_semantic_key = _first_text(
        current.get("owner_semantic_key"),
        current.get("parent_semantic_key"),
        current_payload.get("owner_semantic_key"),
        current_payload.get("parent_semantic_key"),
        _parent_semantic_key_from_attribute_key(operation.semantic_key),
    )
    if owner_semantic_key is None:
        return _blocked_receiver(
            reason="meta_ocg_attribute_create_requires_owner_semantic_key",
            blockers=("missing_attribute_owner_semantic_key",),
            owner_semantic_key=None,
            owner_operation=None,
            owner_kind=None,
            receiver_entity_kind=None,
        )

    owner_operation = context.operation_by_semantic_key.get(owner_semantic_key)
    owner_current = owner_operation.current if owner_operation is not None else {}
    owner_current_payload = mapping_value(owner_current.get("payload"))
    owner_kind = _first_text(
        owner_operation.ontology_subject_kind if owner_operation is not None else None,
        owner_current.get("object_kind"),
        owner_current.get("node_type"),
        owner_current_payload.get("object_kind"),
        owner_current_payload.get("node_type"),
    )
    receiver_entity_kind = _receiver_entity_kind(owner_kind=owner_kind)
    if receiver_entity_kind is None:
        return _blocked_receiver(
            reason="meta_ocg_attribute_create_owner_kind_not_supported",
            blockers=(f"unsupported_attribute_owner_kind:{owner_kind or 'unknown'}",),
            owner_semantic_key=owner_semantic_key,
            owner_operation=owner_operation,
            owner_kind=owner_kind,
            receiver_entity_kind=None,
        )

    receiver_entity_id = _first_uuid_text(
        owner_current.get("entity_id"),
        owner_current_payload.get("entity_id"),
        owner_current.get("object_id"),
        owner_current_payload.get("object_id"),
        current.get("owner_object_id"),
        current_payload.get("owner_object_id"),
    )
    if receiver_entity_id is None:
        return _blocked_receiver(
            reason="meta_ocg_attribute_create_requires_owner_entity_id",
            blockers=(f"missing_owner_entity_id:{owner_semantic_key}",),
            owner_semantic_key=owner_semantic_key,
            owner_operation=owner_operation,
            owner_kind=owner_kind,
            receiver_entity_kind=receiver_entity_kind,
        )

    return {
        "status": "attribute_receiver_resolved",
        "reason": "meta_ocg_attribute_create_owner_receiver_resolved",
        "blockers": (),
        "owner_semantic_key": owner_semantic_key,
        "owner_operation_key": (
            owner_operation.operation_key if owner_operation is not None else None
        ),
        "owner_kind": owner_kind,
        "receiver_entity_kind": receiver_entity_kind,
        "receiver_entity_id": receiver_entity_id,
        "receiver_entity_path": _receiver_entity_path(
            receiver_entity_kind=receiver_entity_kind,
        ),
    }


def _attribute_delete_receiver_resolution(
    *,
    operation: OntologyTypedOperation,
    context: OntologyExecutionPlanningContext,
) -> dict[str, object]:
    current = operation.current
    current_payload = mapping_value(current.get("payload"))
    baseline_object = mapping_value(operation.baseline.get("object"))
    owner_semantic_key = _first_text(
        current.get("owner_semantic_key"),
        current.get("parent_semantic_key"),
        current_payload.get("owner_semantic_key"),
        current_payload.get("parent_semantic_key"),
        baseline_object.get("owner_semantic_key"),
        baseline_object.get("parent_semantic_key"),
        _parent_semantic_key_from_attribute_key(operation.semantic_key),
    )
    if owner_semantic_key is None:
        return _blocked_receiver(
            reason="meta_ocg_attribute_delete_requires_owner_semantic_key",
            blockers=("missing_attribute_owner_semantic_key",),
            owner_semantic_key=None,
            owner_operation=None,
            owner_kind=None,
            receiver_entity_kind=None,
        )

    owner_operation = context.operation_by_semantic_key.get(owner_semantic_key)
    owner_current = owner_operation.current if owner_operation is not None else {}
    owner_current_payload = mapping_value(owner_current.get("payload"))
    owner_baseline = owner_operation.baseline if owner_operation is not None else {}
    owner_baseline_object = mapping_value(owner_baseline.get("object"))
    owner_kind = _first_text(
        owner_operation.ontology_subject_kind if owner_operation is not None else None,
        owner_current.get("object_kind"),
        owner_current.get("node_type"),
        owner_current_payload.get("object_kind"),
        owner_current_payload.get("node_type"),
        owner_baseline.get("object_kind"),
        owner_baseline_object.get("object_kind"),
        owner_baseline_object.get("node_type"),
    )
    receiver_entity_kind = _receiver_entity_kind(owner_kind=owner_kind)
    if receiver_entity_kind is None:
        return _blocked_receiver(
            reason="meta_ocg_attribute_delete_owner_kind_not_supported",
            blockers=(f"unsupported_attribute_owner_kind:{owner_kind or 'unknown'}",),
            owner_semantic_key=owner_semantic_key,
            owner_operation=owner_operation,
            owner_kind=owner_kind,
            receiver_entity_kind=None,
        )

    receiver_entity_id = _first_uuid_text(
        owner_current.get("entity_id"),
        owner_current_payload.get("entity_id"),
        owner_current.get("object_id"),
        owner_current_payload.get("object_id"),
        owner_baseline.get("object_id"),
        owner_baseline_object.get("object_id"),
        owner_baseline_object.get("entity_id"),
        current.get("owner_object_id"),
        current_payload.get("owner_object_id"),
        baseline_object.get("owner_object_id"),
    )
    if receiver_entity_id is None:
        return _blocked_receiver(
            reason="meta_ocg_attribute_delete_requires_owner_entity_id",
            blockers=(f"missing_owner_entity_id:{owner_semantic_key}",),
            owner_semantic_key=owner_semantic_key,
            owner_operation=owner_operation,
            owner_kind=owner_kind,
            receiver_entity_kind=receiver_entity_kind,
        )

    return {
        "status": "attribute_receiver_resolved",
        "reason": "meta_ocg_attribute_delete_owner_receiver_resolved",
        "blockers": (),
        "owner_semantic_key": owner_semantic_key,
        "owner_operation_key": (
            owner_operation.operation_key if owner_operation is not None else None
        ),
        "owner_kind": owner_kind,
        "receiver_entity_kind": receiver_entity_kind,
        "receiver_entity_id": receiver_entity_id,
        "receiver_entity_path": _receiver_entity_path(
            receiver_entity_kind=receiver_entity_kind,
        ),
    }


def _attribute_create_binding(
    *,
    operation: OntologyTypedOperation,
    receiver: Mapping[str, object],
) -> dict[str, object]:
    signature = _attribute_signature(operation=operation)
    descriptor = mapping_value(signature.get("type_descriptor"))
    descriptor_kind = _descriptor_kind(descriptor=descriptor)
    receiver_entity_kind = optional_text(receiver.get("receiver_entity_kind"))
    attribute_name = _first_text(
        signature.get("name"),
        operation.current.get("attribute_name"),
    )
    attribute_object_id = _attribute_object_id(operation=operation)
    if attribute_object_id is None:
        return _blocked_binding(
            reason="meta_ocg_attribute_create_requires_attribute_entity_id",
            blockers=("missing_attribute_entity_id",),
            descriptor_kind=descriptor_kind,
        )
    if attribute_name is None:
        return _blocked_binding(
            reason="meta_ocg_attribute_create_requires_attribute_name",
            blockers=("missing_attribute_name",),
            descriptor_kind=descriptor_kind,
        )

    common_arguments = _attribute_common_arguments(
        operation=operation,
        signature=signature,
        attribute_name=attribute_name,
        include_function_attribute_type=receiver_entity_kind == "function_config",
    )
    if descriptor_kind == "primitive":
        primitive_base_type = _first_text(
            descriptor.get("primitive_base_type"),
            mapping_value(descriptor.get("target")).get("primitive_base_type"),
            "any",
        )
        return _ready_binding(
            receiver_entity_kind=receiver_entity_kind,
            descriptor_kind=descriptor_kind,
            arguments={
                **common_arguments,
                "primitive_base_type": primitive_base_type,
            },
        )
    if descriptor_kind == "enum":
        enum_config_id = _first_uuid_text(
            descriptor.get("enum_config_id"),
            mapping_value(descriptor.get("target")).get("enum_config_id"),
        )
        if enum_config_id is None:
            return _blocked_binding(
                reason="meta_ocg_attribute_create_requires_enum_config_id",
                blockers=("missing_attribute_enum_config_id",),
                descriptor_kind=descriptor_kind,
            )
        return _ready_binding(
            receiver_entity_kind=receiver_entity_kind,
            descriptor_kind=descriptor_kind,
            arguments={**common_arguments, "enum_config_id": enum_config_id},
        )
    if descriptor_kind == "class":
        class_config_id = _first_uuid_text(
            descriptor.get("class_config_id"),
            descriptor.get("type_class_config_id"),
            mapping_value(descriptor.get("target")).get("class_config_id"),
            mapping_value(descriptor.get("target")).get("type_class_config_id"),
        )
        if class_config_id is None:
            return _blocked_binding(
                reason="meta_ocg_attribute_create_requires_type_class_config_id",
                blockers=("missing_attribute_type_class_config_id",),
                descriptor_kind=descriptor_kind,
            )
        return _ready_binding(
            receiver_entity_kind=receiver_entity_kind,
            descriptor_kind=descriptor_kind,
            arguments={
                **common_arguments,
                "type_class_config_id": class_config_id,
            },
        )
    if descriptor_kind == "collection":
        return _blocked_binding(
            reason="meta_ocg_attribute_collection_create_requires_ontology_function",
            blockers=("attribute_collection_ontology_function_missing",),
            descriptor_kind=descriptor_kind,
        )
    return _blocked_binding(
        reason="meta_ocg_attribute_descriptor_kind_not_supported",
        blockers=(f"unsupported_attribute_descriptor_kind:{descriptor_kind}",),
        descriptor_kind=descriptor_kind,
    )


def _attribute_update_binding(
    *,
    operation: OntologyTypedOperation,
) -> dict[str, object]:
    signature = _attribute_signature(operation=operation)
    descriptor = mapping_value(signature.get("type_descriptor"))
    descriptor_kind = _descriptor_kind(descriptor=descriptor)
    common_arguments = _attribute_update_common_arguments(signature=signature)
    if descriptor_kind == "primitive":
        primitive_base_type = _first_text(
            descriptor.get("primitive_base_type"),
            mapping_value(descriptor.get("target")).get("primitive_base_type"),
            "any",
        )
        return _ready_update_binding(
            descriptor_kind=descriptor_kind,
            arguments={
                **common_arguments,
                "primitive_base_type": primitive_base_type,
            },
        )
    if descriptor_kind == "enum":
        enum_config_id = _first_uuid_text(
            descriptor.get("enum_config_id"),
            mapping_value(descriptor.get("target")).get("enum_config_id"),
        )
        if enum_config_id is None:
            return _blocked_binding(
                reason="meta_ocg_attribute_update_requires_enum_config_id",
                blockers=("missing_attribute_enum_config_id",),
                descriptor_kind=descriptor_kind,
            )
        return _ready_update_binding(
            descriptor_kind=descriptor_kind,
            arguments={**common_arguments, "enum_config_id": enum_config_id},
        )
    if descriptor_kind == "class":
        class_config_id = _first_uuid_text(
            descriptor.get("class_config_id"),
            descriptor.get("type_class_config_id"),
            mapping_value(descriptor.get("target")).get("class_config_id"),
            mapping_value(descriptor.get("target")).get("type_class_config_id"),
        )
        if class_config_id is None:
            return _blocked_binding(
                reason="meta_ocg_attribute_update_requires_type_class_config_id",
                blockers=("missing_attribute_type_class_config_id",),
                descriptor_kind=descriptor_kind,
            )
        return _ready_update_binding(
            descriptor_kind=descriptor_kind,
            arguments={
                **common_arguments,
                "type_class_config_id": class_config_id,
            },
        )
    if descriptor_kind == "collection":
        return _blocked_binding(
            reason="meta_ocg_attribute_collection_update_requires_ontology_function",
            blockers=("attribute_collection_update_ontology_function_missing",),
            descriptor_kind=descriptor_kind,
        )
    return _blocked_binding(
        reason="meta_ocg_attribute_update_descriptor_kind_not_supported",
        blockers=(f"unsupported_attribute_descriptor_kind:{descriptor_kind}",),
        descriptor_kind=descriptor_kind,
    )


def _attribute_delete_binding(
    *,
    operation: OntologyTypedOperation,
    receiver: Mapping[str, object],
    attribute_object_id: str,
) -> dict[str, object]:
    receiver_entity_kind = optional_text(receiver.get("receiver_entity_kind"))
    attribute_name = _attribute_delete_name(operation=operation)
    if attribute_name is None:
        return _blocked_binding(
            reason="meta_ocg_attribute_delete_requires_attribute_name",
            blockers=("missing_attribute_name",),
            descriptor_kind="delete",
        )
    if receiver_entity_kind == "class_config":
        return {
            "status": "attribute_delete_binding_ready",
            "reason": "meta_ocg_attribute_delete_function_bound",
            "blockers": (),
            "descriptor_kind": "delete",
            "owner_class_name": "ClassConfig",
            "function_name": "remove_attribute_config",
            "function_ref": CLASS_CONFIG_REMOVE_ATTRIBUTE_CONFIG_FUNCTION_REF,
            "arguments": {
                "name": attribute_name,
                "attribute_config_id": attribute_object_id,
            },
        }
    if receiver_entity_kind == "function_config":
        return {
            "status": "attribute_delete_binding_ready",
            "reason": "meta_ocg_attribute_delete_function_bound",
            "blockers": (),
            "descriptor_kind": "delete",
            "owner_class_name": "FunctionConfig",
            "function_name": "remove_attribute_config",
            "function_ref": FUNCTION_CONFIG_REMOVE_ATTRIBUTE_CONFIG_FUNCTION_REF,
            "arguments": {
                "name": attribute_name,
                "type": _function_attribute_type(operation=operation),
                "attribute_config_id": attribute_object_id,
            },
        }
    return _blocked_binding(
        reason="meta_ocg_attribute_delete_function_not_bound",
        blockers=(
            "missing_attribute_delete_ontology_function:"
            f"{receiver_entity_kind or 'unknown'}",
        ),
        descriptor_kind="delete",
    )


def _attribute_signature(*, operation: OntologyTypedOperation) -> dict[str, object]:
    current_payload = mapping_value(operation.current.get("payload"))
    return mapping_value(
        operation.current.get("attribute_signature")
        or current_payload.get("attribute_signature")
    )


def _attribute_common_arguments(
    *,
    operation: OntologyTypedOperation,
    signature: Mapping[str, object],
    attribute_name: str,
    include_function_attribute_type: bool,
) -> dict[str, object]:
    arguments: dict[str, object] = {
        "name": attribute_name,
        "description": signature.get("description"),
        "default_value": signature.get("default_value"),
        "is_primary": signature.get("is_primary") is True,
        "is_public": signature.get("is_public") is not False,
        "is_required": signature.get("is_required") is True,
        "is_unique": signature.get("is_unique") is True,
        "is_virtual": signature.get("is_virtual") is True,
        "position": _int_value(signature.get("position")),
    }
    if include_function_attribute_type:
        arguments["type"] = _first_text(
            signature.get("function_attribute_type"),
            "input",
        )
        arguments["is_identity_key"] = signature.get("is_identity_key") is True
    return arguments


def _attribute_update_common_arguments(
    *,
    signature: Mapping[str, object],
) -> dict[str, object]:
    return {
        "description": signature.get("description"),
        "default_value": signature.get("default_value"),
        "is_primary": signature.get("is_primary") is True,
        "is_public": signature.get("is_public") is not False,
        "is_required": signature.get("is_required") is True,
        "is_unique": signature.get("is_unique") is True,
        "is_virtual": signature.get("is_virtual") is True,
        "exclude_serialization": signature.get("exclude_serialization") is True,
    }


def _attribute_delete_name(*, operation: OntologyTypedOperation) -> str | None:
    current_payload = mapping_value(operation.current.get("payload"))
    baseline_object = mapping_value(operation.baseline.get("object"))
    baseline_payload = mapping_value(baseline_object.get("payload"))
    return _first_text(
        operation.current.get("attribute_name"),
        current_payload.get("attribute_name"),
        baseline_object.get("attribute_name"),
        baseline_payload.get("attribute_name"),
    )


def _function_attribute_type(*, operation: OntologyTypedOperation) -> str:
    signature = _attribute_signature(operation=operation)
    current_payload = mapping_value(operation.current.get("payload"))
    baseline_object = mapping_value(operation.baseline.get("object"))
    baseline_payload = mapping_value(baseline_object.get("payload"))
    baseline_signature = mapping_value(
        baseline_object.get("attribute_signature")
        or baseline_payload.get("attribute_signature")
    )
    return (
        _first_text(
            signature.get("function_attribute_type"),
            current_payload.get("function_attribute_type"),
            baseline_signature.get("function_attribute_type"),
            baseline_object.get("function_attribute_type"),
            "input",
        )
        or "input"
    )


def _ready_binding(
    *,
    receiver_entity_kind: str | None,
    descriptor_kind: str,
    arguments: Mapping[str, object],
) -> dict[str, object]:
    function_ref = _attribute_function_ref(
        receiver_entity_kind=receiver_entity_kind,
        descriptor_kind=descriptor_kind,
    )
    owner_class_name = _attribute_owner_class_name(
        receiver_entity_kind=receiver_entity_kind,
    )
    function_name = _attribute_function_name(
        receiver_entity_kind=receiver_entity_kind,
        descriptor_kind=descriptor_kind,
    )
    if not function_ref or owner_class_name is None or function_name is None:
        return _blocked_binding(
            reason="meta_ocg_attribute_create_function_not_bound",
            blockers=(
                "missing_attribute_create_ontology_function:"
                f"{receiver_entity_kind or 'unknown'}.{descriptor_kind}",
            ),
            descriptor_kind=descriptor_kind,
        )
    return {
        "status": "attribute_create_binding_ready",
        "reason": "meta_ocg_attribute_create_function_bound",
        "blockers": (),
        "descriptor_kind": descriptor_kind,
        "owner_class_name": owner_class_name,
        "function_name": function_name,
        "function_ref": function_ref,
        "arguments": dict(arguments),
    }


def _ready_update_binding(
    *,
    descriptor_kind: str,
    arguments: Mapping[str, object],
) -> dict[str, object]:
    function_ref = _attribute_update_function_ref(descriptor_kind=descriptor_kind)
    function_name = _attribute_update_function_name(descriptor_kind=descriptor_kind)
    if not function_ref or function_name is None:
        return _blocked_binding(
            reason="meta_ocg_attribute_update_function_not_bound",
            blockers=(
                "missing_attribute_update_ontology_function:"
                f"attribute_config.{descriptor_kind}",
            ),
            descriptor_kind=descriptor_kind,
        )
    return {
        "status": "attribute_update_binding_ready",
        "reason": "meta_ocg_attribute_update_function_bound",
        "blockers": (),
        "descriptor_kind": descriptor_kind,
        "owner_class_name": "AttributeConfig",
        "function_name": function_name,
        "function_ref": function_ref,
        "arguments": dict(arguments),
    }


def _blocked_receiver(
    *,
    reason: str,
    blockers: tuple[str, ...],
    owner_semantic_key: str | None,
    owner_operation: OntologyTypedOperation | None,
    owner_kind: str | None,
    receiver_entity_kind: str | None,
) -> dict[str, object]:
    return {
        "status": "attribute_receiver_blocked",
        "reason": reason,
        "blockers": blockers,
        "owner_semantic_key": owner_semantic_key,
        "owner_operation_key": (
            owner_operation.operation_key if owner_operation is not None else None
        ),
        "owner_kind": owner_kind,
        "receiver_entity_kind": receiver_entity_kind,
        "receiver_entity_id": None,
        "receiver_entity_path": (
            _receiver_entity_path(receiver_entity_kind=receiver_entity_kind)
            if receiver_entity_kind is not None
            else None
        ),
    }


def _blocked_binding(
    *,
    reason: str,
    blockers: tuple[str, ...],
    descriptor_kind: str,
) -> dict[str, object]:
    return {
        "status": "attribute_create_binding_blocked",
        "reason": reason,
        "blockers": blockers,
        "descriptor_kind": descriptor_kind,
        "arguments": {},
    }


def _attribute_function_ref(
    *,
    receiver_entity_kind: str | None,
    descriptor_kind: str,
) -> str:
    if receiver_entity_kind == "class_config":
        return {
            "primitive": META_CLASS_CONFIG_CREATE_PRIMITIVE_ATTRIBUTE_FUNCTION_REF,
            "enum": META_CLASS_CONFIG_CREATE_ENUM_ATTRIBUTE_FUNCTION_REF,
            "class": META_CLASS_CONFIG_CREATE_CLASS_ATTRIBUTE_FUNCTION_REF,
        }.get(descriptor_kind, "")
    if receiver_entity_kind == "function_config":
        return {
            "primitive": META_FUNCTION_CONFIG_ADD_PRIMITIVE_ATTRIBUTE_FUNCTION_REF,
            "enum": META_FUNCTION_CONFIG_ADD_ENUM_ATTRIBUTE_FUNCTION_REF,
            "class": META_FUNCTION_CONFIG_ADD_CLASS_ATTRIBUTE_FUNCTION_REF,
        }.get(descriptor_kind, "")
    return ""


def _attribute_owner_class_name(*, receiver_entity_kind: str | None) -> str | None:
    return {
        "class_config": "ClassConfig",
        "function_config": "FunctionConfig",
    }.get(receiver_entity_kind or "")


def _attribute_function_name(
    *,
    receiver_entity_kind: str | None,
    descriptor_kind: str,
) -> str | None:
    if receiver_entity_kind == "class_config":
        return {
            "primitive": "create_primitive_attribute_config",
            "enum": "create_enum_attribute_config",
            "class": "create_class_attribute_config",
        }.get(descriptor_kind)
    if receiver_entity_kind == "function_config":
        return {
            "primitive": "add_primitive_attribute_config",
            "enum": "add_enum_attribute_config",
            "class": "add_class_attribute_config",
        }.get(descriptor_kind)
    return None


def _attribute_update_function_ref(*, descriptor_kind: str) -> str:
    return {
        "primitive": ATTRIBUTE_CONFIG_UPDATE_PRIMITIVE_FUNCTION_REF,
        "enum": ATTRIBUTE_CONFIG_UPDATE_ENUM_FUNCTION_REF,
        "class": ATTRIBUTE_CONFIG_UPDATE_CLASS_FUNCTION_REF,
    }.get(descriptor_kind, "")


def _attribute_update_function_name(*, descriptor_kind: str) -> str | None:
    return {
        "primitive": "update_primitive",
        "enum": "update_enum",
        "class": "update_class",
    }.get(descriptor_kind)


def _receiver_entity_kind(*, owner_kind: str | None) -> str | None:
    if owner_kind == "class":
        return "class_config"
    if owner_kind == "function":
        return "function_config"
    return None


def _receiver_entity_path(*, receiver_entity_kind: str | None) -> str | None:
    if receiver_entity_kind == "class_config":
        return "object_config_graph_node.class_config"
    if receiver_entity_kind == "function_config":
        return "object_config_graph_node.function_config"
    return None


def _descriptor_kind(*, descriptor: Mapping[str, object]) -> str:
    kind = _first_text(
        descriptor.get("kind"),
        descriptor.get("descriptor_kind"),
    )
    if kind == "class_":
        return "class"
    return kind or "unknown"


def _attribute_object_id(*, operation: OntologyTypedOperation) -> str | None:
    current_payload = mapping_value(operation.current.get("payload"))
    return _first_uuid_text(
        operation.current.get("entity_id"),
        current_payload.get("entity_id"),
        operation.current.get("object_id"),
        current_payload.get("object_id"),
        operation.baseline.get("object_id"),
    )


def _attribute_update_object_id(
    *,
    operation: OntologyTypedOperation,
) -> str | None:
    current_payload = mapping_value(operation.current.get("payload"))
    return _first_uuid_text(
        operation.baseline.get("object_id"),
        operation.current.get("object_id"),
        current_payload.get("object_id"),
        operation.current.get("entity_id"),
        current_payload.get("entity_id"),
        operation.current.get("receiver_object_id"),
        current_payload.get("receiver_object_id"),
        operation.current.get("semantic_apply_receiver_object_id"),
        current_payload.get("semantic_apply_receiver_object_id"),
    )


def _parent_semantic_key_from_attribute_key(value: str | None) -> str | None:
    if value is None or "/attribute:" not in value:
        return None
    return value.rsplit("/attribute:", 1)[0]


def _first_text(*values: object) -> str | None:
    for value in values:
        text = optional_text(value)
        if text is not None:
            return text
    return None


def _first_uuid_text(*values: object) -> str | None:
    for value in values:
        text = optional_text(value)
        if text is None:
            continue
        try:
            return str(UUID(text))
        except ValueError:
            continue
    return None


def _tuple_text(value: object) -> tuple[str, ...]:
    if isinstance(value, (list, tuple)):
        return tuple(
            text
            for item in value
            for text in (optional_text(item),)
            if text is not None
        )
    text = optional_text(value)
    return (text,) if text is not None else ()


def _int_value(value: object) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return value
    text = optional_text(value)
    if text is None:
        return 0
    try:
        return int(text)
    except ValueError:
        return 0


__all__ = [
    "ATTRIBUTE_CONFIG_UPDATE_CLASS_FUNCTION_REF",
    "ATTRIBUTE_CONFIG_UPDATE_ENUM_FUNCTION_REF",
    "ATTRIBUTE_CONFIG_UPDATE_PRIMITIVE_FUNCTION_REF",
    "CLASS_CONFIG_REMOVE_ATTRIBUTE_CONFIG_FUNCTION_REF",
    "FUNCTION_CONFIG_REMOVE_ATTRIBUTE_CONFIG_FUNCTION_REF",
    "plan_attribute_operation",
]
