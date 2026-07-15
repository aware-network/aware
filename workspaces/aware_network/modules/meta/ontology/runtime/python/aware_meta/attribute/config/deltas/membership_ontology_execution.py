from __future__ import annotations

from collections.abc import Mapping

from aware_meta.materialization.deltas.ontology_execution.contracts import (
    OntologyExecutionPlanningContext,
    OntologyInvocationIntent,
    OntologyOperationHandlerResult,
    OntologyTypedOperation,
    blocked_handler_result,
)
from aware_meta.attribute.config.deltas.ontology_execution import (
    CLASS_CONFIG_REMOVE_ATTRIBUTE_CONFIG_FUNCTION_REF,
    FUNCTION_CONFIG_REMOVE_ATTRIBUTE_CONFIG_FUNCTION_REF,
)
from aware_meta.materialization.deltas.ontology_execution.receiver_resolution import (
    mapping_value,
    optional_text,
)
from aware_meta.materialization.semantic_function_call_resolution import (
    META_CLASS_CONFIG_CREATE_CLASS_ATTRIBUTE_FUNCTION_REF,
    META_CLASS_CONFIG_CREATE_ENUM_ATTRIBUTE_FUNCTION_REF,
    META_CLASS_CONFIG_CREATE_PRIMITIVE_ATTRIBUTE_FUNCTION_REF,
    META_FUNCTION_CONFIG_ADD_CLASS_ATTRIBUTE_FUNCTION_REF,
    META_FUNCTION_CONFIG_ADD_ENUM_ATTRIBUTE_FUNCTION_REF,
    META_FUNCTION_CONFIG_ADD_PRIMITIVE_ATTRIBUTE_FUNCTION_REF,
)


HANDLER_KEY = "attribute_membership.edge_function_calls"
CLASS_CONFIG_ATTRIBUTE_CONFIG_UPDATE_CONFIG_FUNCTION_REF = (
    "aware_meta_ontology.class_.class_config_attribute_config."
    "ClassConfigAttributeConfig.update_config"
)
FUNCTION_CONFIG_ATTRIBUTE_CONFIG_UPDATE_CONFIG_FUNCTION_REF = (
    "aware_meta_ontology.function.function_config_attribute_config."
    "FunctionConfigAttributeConfig.update_config"
)
_CLASS_ATTRIBUTE_MEMBERSHIP_IDENTITY_FIELDS = (
    "owner_kind",
    "class_config_id",
    "attribute_config_id",
)
_FUNCTION_ATTRIBUTE_MEMBERSHIP_IDENTITY_FIELDS = (
    "owner_kind",
    "function_config_id",
    "attribute_config_id",
    "name",
    "type",
)


def plan_attribute_membership_operation(
    operation: OntologyTypedOperation,
    context: OntologyExecutionPlanningContext,
) -> OntologyOperationHandlerResult:
    del context
    if operation.ontology_subject_kind != "attribute_membership":
        return blocked_handler_result(
            operation=operation,
            handler_key=HANDLER_KEY,
            reason="meta_ocg_ontology_handler_subject_mismatch",
            blockers=(f"unsupported_subject:{operation.ontology_subject_kind}",),
        )
    if operation.operation_family != "update":
        return blocked_handler_result(
            operation=operation,
            handler_key=HANDLER_KEY,
            reason="meta_ocg_attribute_membership_delta_requires_update_operation",
            blockers=(f"unsupported_operation_family:{operation.operation_family}",),
        )
    return _plan_attribute_membership_update_operation(operation=operation)


def _plan_attribute_membership_update_operation(
    *,
    operation: OntologyTypedOperation,
) -> OntologyOperationHandlerResult:
    owner_kind = _attribute_membership_owner_kind(operation=operation)
    edge_id = _attribute_membership_update_object_id(
        operation=operation,
        owner_kind=owner_kind,
    )
    missing_edge_blockers = (
        ("missing_attribute_membership_update_edge_id",)
        if edge_id is None
        else ()
    )
    replacement_blockers = _attribute_membership_identity_update_blockers(
        operation=operation,
        owner_kind=owner_kind,
    )
    if replacement_blockers:
        return _plan_attribute_membership_replacement_operation(
            operation=operation,
            owner_kind=owner_kind,
            replacement_blockers=replacement_blockers,
        )
    if missing_edge_blockers:
        return blocked_handler_result(
            operation=operation,
            handler_key=HANDLER_KEY,
            reason="meta_ocg_attribute_membership_update_requires_existing_edge",
            blockers=missing_edge_blockers,
        )

    assert edge_id is not None
    owner_class_name = (
        "FunctionConfigAttributeConfig"
        if owner_kind == "function"
        else "ClassConfigAttributeConfig"
    )
    function_ref = (
        FUNCTION_CONFIG_ATTRIBUTE_CONFIG_UPDATE_CONFIG_FUNCTION_REF
        if owner_kind == "function"
        else CLASS_CONFIG_ATTRIBUTE_CONFIG_UPDATE_CONFIG_FUNCTION_REF
    )
    return OntologyOperationHandlerResult(
        operation_key=operation.operation_key,
        semantic_key=operation.semantic_key,
        handler_key=HANDLER_KEY,
        status="ontology_operation_handler_ready",
        reason="meta_ocg_attribute_membership_update_function_call_ready",
        invocation_intents=(
            OntologyInvocationIntent(
                intent_key=(
                    f"{operation.operation_key}:update_attribute_membership"
                ),
                operation_key=operation.operation_key,
                semantic_key=operation.semantic_key,
                invocation_order=0,
                invocation_mode="instance",
                owner_class_name=owner_class_name,
                function_name="update_config",
                function_ref=function_ref,
                target_object_id=edge_id,
                receiver_semantic_key=operation.semantic_key,
                result_semantic_key=operation.semantic_key,
                expected_result_object_id=edge_id,
                kwargs=_attribute_membership_update_arguments(
                    operation=operation,
                    owner_kind=owner_kind,
                ),
                reason="meta_ocg_attribute_membership_update_config_ready",
            ),
        ),
    )


def _plan_attribute_membership_replacement_operation(
    *,
    operation: OntologyTypedOperation,
    owner_kind: str,
    replacement_blockers: tuple[str, ...],
) -> OntologyOperationHandlerResult:
    replacement_plan = _attribute_membership_replacement_plan(
        operation=operation,
        owner_kind=owner_kind,
    )
    if replacement_plan["status"] != "attribute_membership_replacement_ready":
        return blocked_handler_result(
            operation=operation,
            handler_key=HANDLER_KEY,
            reason=_string_value(replacement_plan.get("reason")),
            blockers=(
                *replacement_blockers,
                *_tuple_text(replacement_plan.get("blockers")),
            ),
        )

    return OntologyOperationHandlerResult(
        operation_key=operation.operation_key,
        semantic_key=operation.semantic_key,
        handler_key=HANDLER_KEY,
        status="ontology_operation_handler_ready",
        reason="meta_ocg_attribute_membership_replacement_function_call_ready",
        invocation_intents=(
            OntologyInvocationIntent(
                intent_key=(
                    f"{operation.operation_key}:replace_attribute:remove_old"
                ),
                operation_key=operation.operation_key,
                semantic_key=operation.semantic_key,
                invocation_order=0,
                invocation_mode="instance",
                owner_class_name=_string_value(
                    replacement_plan.get("owner_class_name")
                ),
                function_name="remove_attribute_config",
                function_ref=_string_value(
                    replacement_plan.get("remove_function_ref")
                ),
                target_object_id=optional_text(
                    replacement_plan.get("baseline_owner_object_id")
                ),
                receiver_semantic_key=optional_text(
                    replacement_plan.get("baseline_owner_semantic_key")
                ),
                result_semantic_key=operation.semantic_key,
                expected_result_object_id=optional_text(
                    replacement_plan.get("baseline_attribute_config_id")
                ),
                kwargs=mapping_value(replacement_plan.get("remove_arguments")),
                reason="meta_ocg_attribute_membership_replacement_remove_ready",
            ),
            OntologyInvocationIntent(
                intent_key=(
                    f"{operation.operation_key}:replace_attribute:create_new"
                ),
                operation_key=operation.operation_key,
                semantic_key=operation.semantic_key,
                invocation_order=1,
                invocation_mode="instance",
                owner_class_name=_string_value(
                    replacement_plan.get("owner_class_name")
                ),
                function_name=_string_value(
                    replacement_plan.get("create_function_name")
                ),
                function_ref=_string_value(
                    replacement_plan.get("create_function_ref")
                ),
                target_object_id=optional_text(
                    replacement_plan.get("current_owner_object_id")
                ),
                receiver_semantic_key=optional_text(
                    replacement_plan.get("current_owner_semantic_key")
                ),
                result_semantic_key=operation.semantic_key,
                expected_result_object_id=optional_text(
                    replacement_plan.get("current_attribute_config_id")
                ),
                kwargs=mapping_value(replacement_plan.get("create_arguments")),
                reason="meta_ocg_attribute_membership_replacement_create_ready",
            ),
        ),
    )


def _attribute_membership_replacement_plan(
    *,
    operation: OntologyTypedOperation,
    owner_kind: str,
) -> dict[str, object]:
    baseline_owner_object_id = _attribute_membership_owner_object_id(
        operation=operation,
        owner_kind=owner_kind,
        scope="baseline",
    )
    current_owner_object_id = _attribute_membership_owner_object_id(
        operation=operation,
        owner_kind=owner_kind,
        scope="current",
    )
    baseline_attribute_config_id = _attribute_membership_attribute_config_id(
        operation=operation,
        scope="baseline",
    )
    current_attribute_config_id = _attribute_membership_attribute_config_id(
        operation=operation,
        scope="current",
    )
    baseline_name = _attribute_membership_attribute_name(
        operation=operation,
        scope="baseline",
    )
    current_name = _attribute_membership_attribute_name(
        operation=operation,
        scope="current",
    )
    blockers: list[str] = []
    required_values = {
        "baseline_owner_object_id": baseline_owner_object_id,
        "current_owner_object_id": current_owner_object_id,
        "baseline_attribute_config_id": baseline_attribute_config_id,
        "current_attribute_config_id": current_attribute_config_id,
        "baseline_attribute_name": baseline_name,
        "current_attribute_name": current_name,
    }
    blockers.extend(
        f"missing_attribute_replacement_{field}"
        for field, value in required_values.items()
        if value is None
    )
    create_binding = _attribute_membership_replacement_create_binding(
        operation=operation,
        owner_kind=owner_kind,
        current_name=current_name,
    )
    if create_binding["status"] != "attribute_replacement_create_binding_ready":
        blockers.extend(_tuple_text(create_binding.get("blockers")))

    if blockers:
        return {
            "status": "attribute_membership_replacement_blocked",
            "reason": "meta_ocg_attribute_membership_replacement_blocked",
            "blockers": tuple(dict.fromkeys(blockers)),
        }

    assert baseline_owner_object_id is not None
    assert current_owner_object_id is not None
    assert baseline_attribute_config_id is not None
    assert current_attribute_config_id is not None
    assert baseline_name is not None
    return {
        "status": "attribute_membership_replacement_ready",
        "reason": "meta_ocg_attribute_membership_replacement_ready",
        "blockers": (),
        "owner_class_name": (
            "FunctionConfig" if owner_kind == "function" else "ClassConfig"
        ),
        "remove_function_ref": (
            FUNCTION_CONFIG_REMOVE_ATTRIBUTE_CONFIG_FUNCTION_REF
            if owner_kind == "function"
            else CLASS_CONFIG_REMOVE_ATTRIBUTE_CONFIG_FUNCTION_REF
        ),
        "create_function_name": create_binding.get("function_name"),
        "create_function_ref": create_binding.get("function_ref"),
        "baseline_owner_object_id": baseline_owner_object_id,
        "current_owner_object_id": current_owner_object_id,
        "baseline_owner_semantic_key": _attribute_membership_owner_semantic_key(
            operation=operation,
            scope="baseline",
        ),
        "current_owner_semantic_key": _attribute_membership_owner_semantic_key(
            operation=operation,
            scope="current",
        ),
        "baseline_attribute_config_id": baseline_attribute_config_id,
        "current_attribute_config_id": current_attribute_config_id,
        "remove_arguments": _attribute_membership_replacement_remove_arguments(
            operation=operation,
            owner_kind=owner_kind,
            baseline_name=baseline_name,
            baseline_attribute_config_id=baseline_attribute_config_id,
        ),
        "create_arguments": mapping_value(create_binding.get("arguments")),
    }


def _attribute_membership_replacement_create_binding(
    *,
    operation: OntologyTypedOperation,
    owner_kind: str,
    current_name: str | None,
) -> dict[str, object]:
    signature = _attribute_membership_attribute_signature(
        operation=operation,
        scope="current",
    )
    descriptor = mapping_value(signature.get("type_descriptor"))
    descriptor_kind = _attribute_descriptor_kind(descriptor=descriptor)
    if current_name is None:
        return _blocked_replacement_create_binding(
            reason="meta_ocg_attribute_replacement_create_requires_attribute_name",
            blockers=("missing_attribute_replacement_current_attribute_name",),
            descriptor_kind=descriptor_kind,
        )
    arguments = _attribute_membership_replacement_create_arguments(
        operation=operation,
        owner_kind=owner_kind,
        signature=signature,
        current_name=current_name,
    )
    if descriptor_kind == "primitive":
        primitive_base_type = _first_text(
            descriptor.get("primitive_base_type"),
            mapping_value(descriptor.get("target")).get("primitive_base_type"),
            "any",
        )
        return _ready_replacement_create_binding(
            owner_kind=owner_kind,
            descriptor_kind=descriptor_kind,
            arguments={
                **arguments,
                "primitive_base_type": primitive_base_type,
            },
        )
    if descriptor_kind == "enum":
        enum_config_id = _first_text(
            descriptor.get("enum_config_id"),
            mapping_value(descriptor.get("target")).get("enum_config_id"),
        )
        if enum_config_id is None:
            return _blocked_replacement_create_binding(
                reason="meta_ocg_attribute_replacement_create_requires_enum_config_id",
                blockers=("missing_attribute_replacement_enum_config_id",),
                descriptor_kind=descriptor_kind,
            )
        return _ready_replacement_create_binding(
            owner_kind=owner_kind,
            descriptor_kind=descriptor_kind,
            arguments={**arguments, "enum_config_id": enum_config_id},
        )
    if descriptor_kind == "class":
        type_class_config_id = _first_text(
            descriptor.get("class_config_id"),
            descriptor.get("type_class_config_id"),
            mapping_value(descriptor.get("target")).get("class_config_id"),
            mapping_value(descriptor.get("target")).get("type_class_config_id"),
        )
        if type_class_config_id is None:
            return _blocked_replacement_create_binding(
                reason=(
                    "meta_ocg_attribute_replacement_create_requires_"
                    "type_class_config_id"
                ),
                blockers=("missing_attribute_replacement_type_class_config_id",),
                descriptor_kind=descriptor_kind,
            )
        return _ready_replacement_create_binding(
            owner_kind=owner_kind,
            descriptor_kind=descriptor_kind,
            arguments={**arguments, "type_class_config_id": type_class_config_id},
        )
    if descriptor_kind == "collection":
        return _blocked_replacement_create_binding(
            reason="meta_ocg_attribute_replacement_collection_requires_ontology_function",
            blockers=("attribute_replacement_collection_ontology_function_missing",),
            descriptor_kind=descriptor_kind,
        )
    return _blocked_replacement_create_binding(
        reason="meta_ocg_attribute_replacement_descriptor_kind_not_supported",
        blockers=(f"unsupported_attribute_replacement_descriptor_kind:{descriptor_kind}",),
        descriptor_kind=descriptor_kind,
    )


def _attribute_membership_replacement_create_arguments(
    *,
    operation: OntologyTypedOperation,
    owner_kind: str,
    signature: dict[str, object],
    current_name: str,
) -> dict[str, object]:
    membership_signature = _attribute_membership_signature(operation=operation)
    arguments: dict[str, object] = {
        "name": current_name,
        "description": signature.get("description"),
        "default_value": signature.get("default_value"),
        "is_primary": signature.get("is_primary") is True,
        "is_public": signature.get("is_public") is not False,
        "is_required": signature.get("is_required") is True,
        "is_unique": signature.get("is_unique") is True,
        "is_virtual": signature.get("is_virtual") is True,
        "position": _int_value(
            _first_value(membership_signature.get("position"), signature.get("position"))
        ),
    }
    if owner_kind == "function":
        arguments["type"] = (
            _first_text(
                membership_signature.get("type"),
                signature.get("function_attribute_type"),
                "input",
            )
            or "input"
        )
        arguments["is_identity_key"] = _bool_value(
            _first_value(
                membership_signature.get("is_identity_key"),
                signature.get("is_identity_key"),
                False,
            )
        )
    return arguments


def _attribute_membership_replacement_remove_arguments(
    *,
    operation: OntologyTypedOperation,
    owner_kind: str,
    baseline_name: str,
    baseline_attribute_config_id: str,
) -> dict[str, object]:
    arguments: dict[str, object] = {
        "name": baseline_name,
        "attribute_config_id": baseline_attribute_config_id,
    }
    if owner_kind == "function":
        arguments["type"] = (
            _first_text(
                _attribute_membership_baseline_signature(operation=operation).get(
                    "type"
                ),
                _attribute_membership_attribute_signature(
                    operation=operation,
                    scope="baseline",
                ).get("function_attribute_type"),
                "input",
            )
            or "input"
        )
    return arguments


def _attribute_membership_update_arguments(
    *,
    operation: OntologyTypedOperation,
    owner_kind: str,
) -> dict[str, object]:
    signature = _attribute_membership_signature(operation=operation)
    payload = mapping_value(operation.current.get("payload"))
    arguments: dict[str, object] = {
        "position": _int_value(
            _first_value(
                operation.current.get("position"),
                payload.get("position"),
                signature.get("position"),
                0,
            )
        ),
        "is_identity_key": _bool_value(
            _first_value(
                operation.current.get("is_identity_key"),
                payload.get("is_identity_key"),
                signature.get("is_identity_key"),
                False,
            )
        ),
    }
    if owner_kind == "function":
        arguments["identity_key_origin"] = (
            _first_text(
                operation.current.get("identity_key_origin"),
                payload.get("identity_key_origin"),
                signature.get("identity_key_origin"),
                "standalone",
            )
            or "standalone"
        )
    return arguments


def _attribute_membership_update_object_id(
    *,
    operation: OntologyTypedOperation,
    owner_kind: str,
) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    baseline_object = mapping_value(operation.baseline.get("object"))
    edge_id_field = _attribute_membership_edge_id_field(owner_kind=owner_kind)
    return _first_text(
        operation.current.get("semantic_apply_receiver_object_id"),
        payload.get("semantic_apply_receiver_object_id"),
        operation.current.get("executable_object_id"),
        payload.get("executable_object_id"),
        baseline_object.get("semantic_apply_receiver_object_id"),
        baseline_object.get("executable_object_id"),
        operation.baseline.get("object_id"),
        baseline_object.get("object_id"),
        baseline_object.get(edge_id_field),
        operation.current.get("object_id"),
        operation.current.get(edge_id_field),
        operation.current.get("entity_id"),
        payload.get("object_id"),
        payload.get(edge_id_field),
        payload.get("entity_id"),
    )


def _attribute_membership_identity_update_blockers(
    *,
    operation: OntologyTypedOperation,
    owner_kind: str,
) -> tuple[str, ...]:
    payload = mapping_value(operation.current.get("payload"))
    replacement_fields = _tuple_text(
        operation.current.get("attribute_membership_identity_replacement_fields")
        or payload.get("attribute_membership_identity_replacement_fields")
    )
    if replacement_fields:
        return tuple(
            "attribute_membership_identity_change_requires_replacement:"
            f"{field}"
            for field in replacement_fields
        )

    fields = _attribute_membership_identity_fields(owner_kind=owner_kind)
    baseline_object = mapping_value(operation.baseline.get("object"))
    baseline_signature = _attribute_membership_baseline_signature(
        operation=operation,
    )
    current_signature = _attribute_membership_signature(operation=operation)
    current_payload = mapping_value(operation.current.get("payload"))
    blockers: list[str] = []
    for field in fields:
        baseline_value = _first_text(
            operation.baseline.get(field),
            baseline_object.get(field),
            baseline_signature.get(field),
        )
        current_value = _first_text(
            operation.current.get(field),
            current_payload.get(field),
            current_signature.get(field),
        )
        if (
            baseline_value is not None
            and current_value is not None
            and baseline_value != current_value
        ):
            blockers.append(
                "attribute_membership_identity_change_requires_replacement:"
                f"{field}"
            )
    return tuple(blockers)


def _attribute_membership_identity_fields(
    *,
    owner_kind: str,
) -> tuple[str, ...]:
    if owner_kind == "function":
        return _FUNCTION_ATTRIBUTE_MEMBERSHIP_IDENTITY_FIELDS
    return _CLASS_ATTRIBUTE_MEMBERSHIP_IDENTITY_FIELDS


def _attribute_membership_owner_kind(
    *,
    operation: OntologyTypedOperation,
) -> str:
    payload = mapping_value(operation.current.get("payload"))
    signature = _attribute_membership_signature(operation=operation)
    owner_kind = _first_text(
        operation.current.get("attribute_membership_owner_kind"),
        payload.get("attribute_membership_owner_kind"),
        signature.get("owner_kind"),
    )
    if owner_kind in {"class", "function"}:
        return owner_kind
    if any(
        _first_text(value) is not None
        for value in (
            operation.current.get("function_config_attribute_config_id"),
            payload.get("function_config_attribute_config_id"),
            operation.current.get("function_config_id"),
            payload.get("function_config_id"),
            operation.current.get("function_attribute_type"),
            payload.get("function_attribute_type"),
            signature.get("function_config_id"),
        )
    ):
        return "function"
    return "class"


def _attribute_membership_signature(
    *,
    operation: OntologyTypedOperation,
) -> dict[str, object]:
    payload = mapping_value(operation.current.get("payload"))
    return mapping_value(
        operation.current.get("attribute_membership_signature")
        or payload.get("attribute_membership_signature")
    )


def _attribute_membership_baseline_signature(
    *,
    operation: OntologyTypedOperation,
) -> dict[str, object]:
    baseline_object = mapping_value(operation.baseline.get("object"))
    return mapping_value(
        operation.baseline.get("attribute_membership_signature")
        or baseline_object.get("attribute_membership_signature")
    )


def _attribute_membership_owner_object_id(
    *,
    operation: OntologyTypedOperation,
    owner_kind: str,
    scope: str,
) -> str | None:
    field = "function_config_id" if owner_kind == "function" else "class_config_id"
    signature = (
        _attribute_membership_signature(operation=operation)
        if scope == "current"
        else _attribute_membership_baseline_signature(operation=operation)
    )
    payload = mapping_value(operation.current.get("payload"))
    baseline_object = mapping_value(operation.baseline.get("object"))
    if scope == "current":
        return _first_text(
            operation.current.get(field),
            payload.get(field),
            signature.get(field),
        )
    return _first_text(
        operation.baseline.get(field),
        baseline_object.get(field),
        signature.get(field),
    )


def _attribute_membership_attribute_config_id(
    *,
    operation: OntologyTypedOperation,
    scope: str,
) -> str | None:
    signature = (
        _attribute_membership_signature(operation=operation)
        if scope == "current"
        else _attribute_membership_baseline_signature(operation=operation)
    )
    payload = mapping_value(operation.current.get("payload"))
    baseline_object = mapping_value(operation.baseline.get("object"))
    if scope == "current":
        return _first_text(
            operation.current.get("attribute_config_id"),
            payload.get("attribute_config_id"),
            signature.get("attribute_config_id"),
            operation.current.get("entity_id"),
            payload.get("entity_id"),
        )
    return _first_text(
        operation.baseline.get("attribute_config_id"),
        baseline_object.get("attribute_config_id"),
        signature.get("attribute_config_id"),
        operation.baseline.get("object_id"),
        baseline_object.get("object_id"),
        baseline_object.get("entity_id"),
    )


def _attribute_membership_attribute_name(
    *,
    operation: OntologyTypedOperation,
    scope: str,
) -> str | None:
    membership_signature = (
        _attribute_membership_signature(operation=operation)
        if scope == "current"
        else _attribute_membership_baseline_signature(operation=operation)
    )
    attribute_signature = _attribute_membership_attribute_signature(
        operation=operation,
        scope=scope,
    )
    payload = mapping_value(operation.current.get("payload"))
    baseline_object = mapping_value(operation.baseline.get("object"))
    baseline_payload = mapping_value(baseline_object.get("payload"))
    if scope == "current":
        return _first_text(
            attribute_signature.get("name"),
            operation.current.get("attribute_name"),
            payload.get("attribute_name"),
            membership_signature.get("name"),
            _attribute_name_from_semantic_key(operation.semantic_key),
        )
    return _first_text(
        attribute_signature.get("name"),
        baseline_object.get("attribute_name"),
        baseline_payload.get("attribute_name"),
        membership_signature.get("name"),
        _attribute_name_from_semantic_key(operation.semantic_key),
    )


def _attribute_membership_attribute_signature(
    *,
    operation: OntologyTypedOperation,
    scope: str,
) -> dict[str, object]:
    payload = mapping_value(operation.current.get("payload"))
    baseline_object = mapping_value(operation.baseline.get("object"))
    baseline_payload = mapping_value(baseline_object.get("payload"))
    if scope == "current":
        return mapping_value(
            operation.current.get("attribute_signature")
            or payload.get("attribute_signature")
        )
    return mapping_value(
        operation.baseline.get("attribute_signature")
        or baseline_object.get("attribute_signature")
        or baseline_payload.get("attribute_signature")
    )


def _attribute_membership_owner_semantic_key(
    *,
    operation: OntologyTypedOperation,
    scope: str,
) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    baseline_object = mapping_value(operation.baseline.get("object"))
    if scope == "current":
        return _first_text(
            operation.current.get("owner_semantic_key"),
            operation.current.get("parent_semantic_key"),
            payload.get("owner_semantic_key"),
            payload.get("parent_semantic_key"),
            _owner_semantic_key_from_attribute_membership_key(
                operation.semantic_key
            ),
        )
    return _first_text(
        operation.baseline.get("owner_semantic_key"),
        baseline_object.get("owner_semantic_key"),
        baseline_object.get("parent_semantic_key"),
        _owner_semantic_key_from_attribute_membership_key(operation.semantic_key),
    )


def _attribute_descriptor_kind(*, descriptor: Mapping[str, object]) -> str:
    kind = _first_text(
        descriptor.get("kind"),
        descriptor.get("descriptor_kind"),
    )
    if kind == "class_":
        return "class"
    return kind or "unknown"


def _ready_replacement_create_binding(
    *,
    owner_kind: str,
    descriptor_kind: str,
    arguments: Mapping[str, object],
) -> dict[str, object]:
    function_ref = _replacement_create_function_ref(
        owner_kind=owner_kind,
        descriptor_kind=descriptor_kind,
    )
    function_name = _replacement_create_function_name(
        owner_kind=owner_kind,
        descriptor_kind=descriptor_kind,
    )
    if not function_ref or function_name is None:
        return _blocked_replacement_create_binding(
            reason="meta_ocg_attribute_replacement_create_function_not_bound",
            blockers=(
                "missing_attribute_replacement_create_ontology_function:"
                f"{owner_kind}.{descriptor_kind}",
            ),
            descriptor_kind=descriptor_kind,
        )
    return {
        "status": "attribute_replacement_create_binding_ready",
        "reason": "meta_ocg_attribute_replacement_create_function_bound",
        "blockers": (),
        "descriptor_kind": descriptor_kind,
        "function_name": function_name,
        "function_ref": function_ref,
        "arguments": dict(arguments),
    }


def _blocked_replacement_create_binding(
    *,
    reason: str,
    blockers: tuple[str, ...],
    descriptor_kind: str,
) -> dict[str, object]:
    return {
        "status": "attribute_replacement_create_binding_blocked",
        "reason": reason,
        "blockers": blockers,
        "descriptor_kind": descriptor_kind,
        "arguments": {},
    }


def _replacement_create_function_ref(
    *,
    owner_kind: str,
    descriptor_kind: str,
) -> str:
    if owner_kind == "class":
        return {
            "primitive": META_CLASS_CONFIG_CREATE_PRIMITIVE_ATTRIBUTE_FUNCTION_REF,
            "enum": META_CLASS_CONFIG_CREATE_ENUM_ATTRIBUTE_FUNCTION_REF,
            "class": META_CLASS_CONFIG_CREATE_CLASS_ATTRIBUTE_FUNCTION_REF,
        }.get(descriptor_kind, "")
    if owner_kind == "function":
        return {
            "primitive": META_FUNCTION_CONFIG_ADD_PRIMITIVE_ATTRIBUTE_FUNCTION_REF,
            "enum": META_FUNCTION_CONFIG_ADD_ENUM_ATTRIBUTE_FUNCTION_REF,
            "class": META_FUNCTION_CONFIG_ADD_CLASS_ATTRIBUTE_FUNCTION_REF,
        }.get(descriptor_kind, "")
    return ""


def _replacement_create_function_name(
    *,
    owner_kind: str,
    descriptor_kind: str,
) -> str | None:
    if owner_kind == "class":
        return {
            "primitive": "create_primitive_attribute_config",
            "enum": "create_enum_attribute_config",
            "class": "create_class_attribute_config",
        }.get(descriptor_kind)
    if owner_kind == "function":
        return {
            "primitive": "add_primitive_attribute_config",
            "enum": "add_enum_attribute_config",
            "class": "add_class_attribute_config",
        }.get(descriptor_kind)
    return None


def _attribute_membership_edge_id_field(*, owner_kind: str) -> str:
    if owner_kind == "function":
        return "function_config_attribute_config_id"
    return "class_config_attribute_config_id"


def _owner_semantic_key_from_attribute_membership_key(value: str | None) -> str | None:
    if value is None:
        return None
    attribute_key = value.split("/membership:", 1)[0]
    if "/attribute:" not in attribute_key:
        return None
    return attribute_key.rsplit("/attribute:", 1)[0]


def _attribute_name_from_semantic_key(value: str | None) -> str | None:
    if value is None:
        return None
    attribute_key = value.split("/membership:", 1)[0]
    if "/attribute:" not in attribute_key:
        return None
    token = attribute_key.rsplit("/attribute:", 1)[1]
    return _first_text(token.rsplit(":", 1)[-1])


def _first_text(*values: object) -> str | None:
    for value in values:
        text = optional_text(value)
        if text is not None:
            return text
    return None


def _first_value(*values: object) -> object | None:
    for value in values:
        if value is not None:
            return value
    return None


def _tuple_text(value: object) -> tuple[str, ...]:
    if isinstance(value, (list, tuple)):
        return tuple(
            text
            for item in value
            for text in (_first_text(item),)
            if text is not None
        )
    text = _first_text(value)
    return (text,) if text is not None else ()


def _bool_value(value: object) -> bool:
    if isinstance(value, bool):
        return value
    text = optional_text(value)
    if text is None:
        return False
    return text.casefold() in {"1", "true", "yes", "y", "on"}


def _int_value(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    text = optional_text(value)
    if text is None:
        return 0
    return int(text)


def _string_value(value: object) -> str:
    text = optional_text(value)
    return text or ""


__all__ = [
    "CLASS_CONFIG_ATTRIBUTE_CONFIG_UPDATE_CONFIG_FUNCTION_REF",
    "FUNCTION_CONFIG_ATTRIBUTE_CONFIG_UPDATE_CONFIG_FUNCTION_REF",
    "plan_attribute_membership_operation",
]
