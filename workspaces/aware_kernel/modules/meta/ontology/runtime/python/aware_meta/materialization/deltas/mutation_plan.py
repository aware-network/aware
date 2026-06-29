from __future__ import annotations

from collections.abc import Mapping

from aware_meta.materialization.semantic_function_call_resolution import (
    META_CLASS_CONFIG_CREATE_CLASS_ATTRIBUTE_FUNCTION_REF,
    META_CLASS_CONFIG_CREATE_ENUM_ATTRIBUTE_FUNCTION_REF,
    META_CLASS_CONFIG_CREATE_PRIMITIVE_ATTRIBUTE_FUNCTION_REF,
    META_FUNCTION_CONFIG_ADD_CLASS_ATTRIBUTE_FUNCTION_REF,
    META_FUNCTION_CONFIG_ADD_ENUM_ATTRIBUTE_FUNCTION_REF,
    META_FUNCTION_CONFIG_ADD_PRIMITIVE_ATTRIBUTE_FUNCTION_REF,
    META_OCG_BUILD_FUNCTION_REF,
    META_OCG_CREATE_NODE_FUNCTION_REF,
    META_OCG_PACKAGE_BUILD_FUNCTION_REF,
)
from aware_meta.materialization.deltas.contracts import (
    META_PROVIDER_DELTA_MUTATION_STEP_CONTRACT_VERSION,
)
from aware_meta.materialization.deltas.baseline import (
    _int_object_value,
    _int_payload_value,
)


_MUTATION_STEP_CONTRACT_VERSION = META_PROVIDER_DELTA_MUTATION_STEP_CONTRACT_VERSION
META_PROVIDER_DELTA_CLASS_CONFIG_CREATE_COLLECTION_ATTRIBUTE_FUNCTION_REF = (
    "aware_meta.provider_delta.class_config.create_collection_attribute_config"
)
META_PROVIDER_DELTA_FUNCTION_CONFIG_ADD_COLLECTION_ATTRIBUTE_FUNCTION_REF = (
    "aware_meta.provider_delta.function_config.add_collection_attribute_config"
)
META_PROVIDER_DELTA_FUNCTION_CONFIG_CREATE_FUNCTION_IMPL_FUNCTION_REF = (
    "aware_meta_ontology.function.function_config.FunctionConfig.create_function_impl"
)


def _mutation_step_from_typed_operation(
    *,
    typed_operation: Mapping[str, object],
    force_blocked: bool,
    typed_operation_by_semantic_key: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    operation_family = _string_value(typed_operation.get("operation_family"))
    subject_kind = _string_value(typed_operation.get("ontology_subject_kind"))
    if force_blocked or typed_operation.get("blocked") is True:
        return _mutation_step_blocked_payload(
            typed_operation=typed_operation,
            reason=(
                _optional_text(typed_operation.get("blocked_reason"))
                or "meta_ocg_provider_delta_mutation_requires_ready_typed_operation"
            ),
            blockers=(
                _optional_text(typed_operation.get("blocked_reason"))
                or "meta_ocg_provider_delta_mutation_requires_ready_typed_operation",
            ),
        )
    if operation_family not in {"create", "update"}:
        return _mutation_step_blocked_payload(
            typed_operation=typed_operation,
            reason="meta_ocg_provider_delta_mutation_operation_not_supported",
            blockers=(f"unsupported_operation_family:{operation_family}",),
        )
    if subject_kind == "object_config_graph_package":
        return _mutation_step_ready_payload(
            typed_operation=typed_operation,
            function_ref=META_OCG_PACKAGE_BUILD_FUNCTION_REF,
            receiver_semantic_key=None,
            receiver_source="root",
            dependencies=(),
            fallback_arguments=_typed_operation_ocg_arguments(
                typed_operation=typed_operation,
            ),
        )
    if subject_kind == "object_config_graph":
        return _mutation_step_ready_payload(
            typed_operation=typed_operation,
            function_ref=META_OCG_BUILD_FUNCTION_REF,
            receiver_semantic_key=None,
            receiver_source="root",
            dependencies=(),
            fallback_arguments=_typed_operation_ocg_arguments(
                typed_operation=typed_operation,
            ),
        )
    if subject_kind in {"class", "enum", "relationship", "function"}:
        receiver_semantic_key = _typed_operation_receiver_semantic_key(
            typed_operation=typed_operation,
        )
        dependencies = (
            (receiver_semantic_key,) if receiver_semantic_key is not None else ()
        )
        return _mutation_step_ready_payload(
            typed_operation=typed_operation,
            function_ref=META_OCG_CREATE_NODE_FUNCTION_REF,
            receiver_semantic_key=receiver_semantic_key,
            receiver_source="semantic_key",
            dependencies=dependencies,
            fallback_arguments=_node_mutation_arguments(
                typed_operation=typed_operation,
            ),
        )
    if subject_kind == "attribute":
        return _attribute_mutation_step_from_typed_operation(
            typed_operation=typed_operation,
            typed_operation_by_semantic_key=typed_operation_by_semantic_key,
        )
    if subject_kind == "function_impl":
        return _function_impl_mutation_step_from_typed_operation(
            typed_operation=typed_operation,
            typed_operation_by_semantic_key=typed_operation_by_semantic_key,
        )
    return _mutation_step_blocked_payload(
        typed_operation=typed_operation,
        reason="meta_ocg_provider_delta_mutation_subject_kind_not_supported",
        blockers=(f"unsupported_ontology_subject_kind:{subject_kind}",),
    )


def _function_impl_mutation_step_from_typed_operation(
    *,
    typed_operation: Mapping[str, object],
    typed_operation_by_semantic_key: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    current = _mapping_value(typed_operation.get("current"))
    receiver_semantic_key = _optional_text(
        current.get("function_semantic_key")
    ) or _typed_operation_receiver_semantic_key(typed_operation=typed_operation)
    candidate_arguments = _typed_operation_ocg_arguments(
        typed_operation=typed_operation,
    )
    if receiver_semantic_key is None:
        return _mutation_step_blocked_payload(
            typed_operation=typed_operation,
            reason="meta_ocg_function_impl_mutation_requires_function_semantic_key",
            blockers=("missing_function_impl_function_semantic_key",),
            receiver_semantic_key=None,
            dependencies=(),
            candidate_arguments=candidate_arguments,
        )
    owner_operation = typed_operation_by_semantic_key.get(receiver_semantic_key)
    dependencies = _receiver_dependencies(
        receiver_semantic_key=receiver_semantic_key,
        receiver_operation=owner_operation,
    )
    if owner_operation is None:
        return _mutation_step_blocked_payload(
            typed_operation=typed_operation,
            reason="meta_ocg_function_impl_mutation_requires_function_typed_operation",
            blockers=(f"missing_function_typed_operation:{receiver_semantic_key}",),
            receiver_semantic_key=receiver_semantic_key,
            dependencies=dependencies,
            candidate_arguments=candidate_arguments,
        )
    receiver = _function_impl_receiver_resolution(
        function_semantic_key=receiver_semantic_key,
        function_operation=owner_operation,
    )
    if receiver["status"] != "function_impl_receiver_resolved":
        return _mutation_step_blocked_payload(
            typed_operation=typed_operation,
            reason=_string_value(receiver.get("reason")),
            blockers=_tuple_text(receiver.get("blockers")),
            receiver_semantic_key=receiver_semantic_key,
            dependencies=dependencies,
            candidate_arguments=candidate_arguments,
            extra_payload={"receiver_resolution": receiver},
        )
    return _mutation_step_base_payload(
        typed_operation=typed_operation,
        status="mutation_step_ready",
        reason="meta_ocg_function_impl_mutation_step_ready",
        function_ref=META_PROVIDER_DELTA_FUNCTION_CONFIG_CREATE_FUNCTION_IMPL_FUNCTION_REF,
        receiver_semantic_key=receiver_semantic_key,
        receiver_object_id=_optional_text(receiver.get("receiver_entity_id")),
        receiver_source="semantic_function_contained_entity",
        arguments={
            "key": (
                _optional_text(candidate_arguments.get("function_impl_key"))
                or "default"
            ),
            "impl_kind": (
                _optional_text(candidate_arguments.get("function_impl_kind"))
                or "instruction_body"
            ),
            "function_impl_signature": _mapping_value(
                candidate_arguments.get("function_impl_signature")
            ),
        },
        argument_refs={},
        dependencies=dependencies,
        blockers=(),
        candidate_arguments=None,
        function_call_plan=None,
        extra_payload={
            "receiver_entity_kind": _optional_text(
                receiver.get("receiver_entity_kind")
            ),
            "receiver_entity_id": _optional_text(receiver.get("receiver_entity_id")),
            "receiver_entity_path": _optional_text(
                receiver.get("receiver_entity_path")
            ),
            "receiver_resolution": receiver,
            "function_impl_key": _optional_text(
                candidate_arguments.get("function_impl_key")
            ),
            "function_impl_kind": _optional_text(
                candidate_arguments.get("function_impl_kind")
            ),
            "function_impl_signature": _mapping_value(
                candidate_arguments.get("function_impl_signature")
            ),
        },
    )


def _function_impl_receiver_resolution(
    *,
    function_semantic_key: str,
    function_operation: Mapping[str, object],
) -> dict[str, object]:
    owner_current = _mapping_value(function_operation.get("current"))
    owner_kind = (
        _optional_text(function_operation.get("ontology_subject_kind"))
        or _optional_text(owner_current.get("object_kind"))
        or _optional_text(owner_current.get("node_type"))
    )
    if owner_kind != "function":
        return {
            "status": "function_impl_receiver_blocked",
            "reason": "meta_ocg_function_impl_mutation_owner_kind_not_supported",
            "blockers": (f"unsupported_function_impl_owner_kind:{owner_kind}",),
            "function_semantic_key": function_semantic_key,
            "owner_operation_key": _optional_text(
                function_operation.get("operation_key")
            ),
            "owner_kind": owner_kind,
            "receiver_entity_kind": None,
            "receiver_entity_id": None,
            "receiver_entity_path": None,
        }
    receiver_entity_id = _optional_text(owner_current.get("entity_id"))
    if receiver_entity_id is None:
        return {
            "status": "function_impl_receiver_blocked",
            "reason": "meta_ocg_function_impl_mutation_requires_function_entity_id",
            "blockers": (f"missing_function_entity_id:{function_semantic_key}",),
            "function_semantic_key": function_semantic_key,
            "owner_operation_key": _optional_text(
                function_operation.get("operation_key")
            ),
            "owner_kind": owner_kind,
            "receiver_entity_kind": "function_config",
            "receiver_entity_id": None,
            "receiver_entity_path": "object_config_graph_node.function_config",
        }
    return {
        "status": "function_impl_receiver_resolved",
        "reason": "meta_ocg_function_impl_mutation_receiver_resolved",
        "blockers": (),
        "function_semantic_key": function_semantic_key,
        "owner_operation_key": _optional_text(function_operation.get("operation_key")),
        "owner_kind": owner_kind,
        "receiver_entity_kind": "function_config",
        "receiver_entity_id": receiver_entity_id,
        "receiver_entity_path": "object_config_graph_node.function_config",
    }


def _attribute_mutation_step_from_typed_operation(
    *,
    typed_operation: Mapping[str, object],
    typed_operation_by_semantic_key: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    owner_semantic_key = _typed_operation_receiver_semantic_key(
        typed_operation=typed_operation,
    )
    candidate_arguments = _typed_operation_ocg_arguments(
        typed_operation=typed_operation,
    )
    if owner_semantic_key is None:
        return _attribute_mutation_blocked_payload(
            typed_operation=typed_operation,
            reason="meta_ocg_attribute_mutation_requires_owner_semantic_key",
            blockers=("missing_attribute_owner_semantic_key",),
            receiver_semantic_key=None,
            dependencies=(),
            candidate_arguments=candidate_arguments,
        )
    owner_operation = typed_operation_by_semantic_key.get(owner_semantic_key)
    dependencies = _receiver_dependencies(
        receiver_semantic_key=owner_semantic_key,
        receiver_operation=owner_operation,
    )
    if owner_operation is None:
        return _attribute_mutation_blocked_payload(
            typed_operation=typed_operation,
            reason="meta_ocg_attribute_mutation_requires_owner_typed_operation",
            blockers=(f"missing_owner_typed_operation:{owner_semantic_key}",),
            receiver_semantic_key=owner_semantic_key,
            dependencies=dependencies,
            candidate_arguments=candidate_arguments,
        )
    receiver = _attribute_receiver_resolution(
        owner_semantic_key=owner_semantic_key,
        owner_operation=owner_operation,
    )
    if receiver["status"] != "attribute_receiver_resolved":
        return _attribute_mutation_blocked_payload(
            typed_operation=typed_operation,
            reason=_string_value(receiver["reason"]),
            blockers=_tuple_text(receiver.get("blockers")),
            receiver_semantic_key=owner_semantic_key,
            dependencies=dependencies,
            candidate_arguments=candidate_arguments,
            receiver=receiver,
        )
    method_binding = _attribute_method_binding(
        typed_operation=typed_operation,
        receiver=receiver,
    )
    if method_binding["status"] != "attribute_method_bound":
        return _attribute_mutation_blocked_payload(
            typed_operation=typed_operation,
            reason=_string_value(method_binding["reason"]),
            blockers=_tuple_text(method_binding.get("blockers")),
            receiver_semantic_key=owner_semantic_key,
            dependencies=dependencies,
            candidate_arguments=candidate_arguments,
            receiver=receiver,
            method_binding=method_binding,
        )
    return _mutation_step_base_payload(
        typed_operation=typed_operation,
        status="mutation_step_ready",
        reason="meta_ocg_attribute_mutation_step_ready",
        function_ref=_string_value(method_binding["function_ref"]),
        receiver_semantic_key=owner_semantic_key,
        receiver_object_id=_optional_text(receiver.get("receiver_entity_id")),
        receiver_source="semantic_node_contained_entity",
        arguments=_mapping_value(method_binding.get("arguments")),
        argument_refs={},
        dependencies=dependencies,
        blockers=(),
        candidate_arguments=None,
        function_call_plan=None,
        extra_payload={
            "receiver_entity_kind": _optional_text(
                receiver.get("receiver_entity_kind")
            ),
            "receiver_entity_id": _optional_text(receiver.get("receiver_entity_id")),
            "receiver_entity_path": _optional_text(
                receiver.get("receiver_entity_path")
            ),
            "receiver_resolution": dict(receiver),
            "method_binding": dict(method_binding),
            "attribute_descriptor_kind": _optional_text(
                method_binding.get("attribute_descriptor_kind")
            ),
            "attribute_descriptor_resolution": _mapping_value(
                method_binding.get("attribute_descriptor_resolution")
            ),
        },
    )


def _receiver_dependencies(
    *,
    receiver_semantic_key: str | None,
    receiver_operation: Mapping[str, object] | None,
) -> tuple[str, ...]:
    if receiver_semantic_key is None:
        return ()
    if receiver_operation is not None:
        operation_family = _optional_text(receiver_operation.get("operation_family"))
        if operation_family == "anchor":
            return ()
    return (receiver_semantic_key,)


def _attribute_receiver_resolution(
    *,
    owner_semantic_key: str,
    owner_operation: Mapping[str, object],
) -> dict[str, object]:
    owner_current = _mapping_value(owner_operation.get("current"))
    owner_kind = _optional_text(owner_operation.get("ontology_subject_kind"))
    if owner_kind is None:
        owner_kind = _optional_text(owner_current.get("object_kind"))
    if owner_kind is None:
        owner_kind = _optional_text(owner_current.get("node_type"))
    receiver_entity_id = _optional_text(owner_current.get("entity_id"))
    if owner_kind == "class":
        receiver_entity_kind = "class_config"
        receiver_entity_path = "object_config_graph_node.class_config"
    elif owner_kind == "function":
        receiver_entity_kind = "function_config"
        receiver_entity_path = "object_config_graph_node.function_config"
    else:
        return {
            "status": "attribute_receiver_blocked",
            "reason": "meta_ocg_attribute_mutation_owner_kind_not_supported",
            "blockers": (f"unsupported_attribute_owner_kind:{owner_kind}",),
            "owner_semantic_key": owner_semantic_key,
            "owner_operation_key": _optional_text(owner_operation.get("operation_key")),
            "owner_kind": owner_kind,
            "receiver_entity_kind": None,
            "receiver_entity_id": None,
            "receiver_entity_path": None,
        }
    if receiver_entity_id is None:
        return {
            "status": "attribute_receiver_blocked",
            "reason": "meta_ocg_attribute_mutation_requires_owner_entity_id",
            "blockers": (f"missing_owner_entity_id:{owner_semantic_key}",),
            "owner_semantic_key": owner_semantic_key,
            "owner_operation_key": _optional_text(owner_operation.get("operation_key")),
            "owner_kind": owner_kind,
            "receiver_entity_kind": receiver_entity_kind,
            "receiver_entity_id": None,
            "receiver_entity_path": receiver_entity_path,
        }
    return {
        "status": "attribute_receiver_resolved",
        "reason": "meta_ocg_attribute_mutation_owner_receiver_resolved",
        "blockers": (),
        "owner_semantic_key": owner_semantic_key,
        "owner_operation_key": _optional_text(owner_operation.get("operation_key")),
        "owner_kind": owner_kind,
        "receiver_entity_kind": receiver_entity_kind,
        "receiver_entity_id": receiver_entity_id,
        "receiver_entity_path": receiver_entity_path,
    }


def _attribute_method_binding(
    *,
    typed_operation: Mapping[str, object],
    receiver: Mapping[str, object],
) -> dict[str, object]:
    current = _mapping_value(typed_operation.get("current"))
    signature = _mapping_value(current.get("attribute_signature"))
    descriptor = _mapping_value(signature.get("type_descriptor"))
    descriptor_resolution = _attribute_descriptor_resolution(descriptor=descriptor)
    descriptor_kind = _string_value(descriptor_resolution.get("method_descriptor_kind"))
    source_descriptor_kind = _string_value(descriptor_resolution.get("descriptor_kind"))
    if descriptor_resolution["status"] != "attribute_descriptor_resolved":
        return _attribute_method_blocked_payload(
            typed_operation=typed_operation,
            descriptor_kind=source_descriptor_kind or descriptor_kind or "unknown",
            reason=_string_value(descriptor_resolution["reason"]),
            blockers=_tuple_text(descriptor_resolution.get("blockers")),
            descriptor_resolution=descriptor_resolution,
        )
    receiver_entity_kind = _optional_text(receiver.get("receiver_entity_kind"))
    if descriptor_kind == "primitive":
        primitive_base_type = (
            _optional_text(descriptor_resolution.get("primitive_base_type")) or "any"
        )
        function_ref = _attribute_function_ref(
            receiver_entity_kind=receiver_entity_kind,
            descriptor_kind=descriptor_kind,
        )
        return _attribute_method_bound_payload(
            typed_operation=typed_operation,
            receiver=receiver,
            descriptor_kind=descriptor_kind,
            function_ref=function_ref,
            descriptor_resolution=descriptor_resolution,
            arguments={
                **_attribute_common_arguments(
                    typed_operation=typed_operation,
                    signature=signature,
                    include_function_attribute_type=(
                        receiver_entity_kind == "function_config"
                    ),
                ),
                "primitive_base_type": primitive_base_type,
            },
        )
    if descriptor_kind == "enum":
        enum_config_id = _optional_text(descriptor_resolution.get("enum_config_id"))
        if enum_config_id is None:
            return _attribute_method_blocked_payload(
                typed_operation=typed_operation,
                descriptor_kind=descriptor_kind,
                reason="meta_ocg_attribute_mutation_requires_enum_config_id",
                blockers=("missing_attribute_enum_config_id",),
                descriptor_resolution=descriptor_resolution,
            )
        return _attribute_method_bound_payload(
            typed_operation=typed_operation,
            receiver=receiver,
            descriptor_kind=descriptor_kind,
            function_ref=_attribute_function_ref(
                receiver_entity_kind=receiver_entity_kind,
                descriptor_kind=descriptor_kind,
            ),
            descriptor_resolution=descriptor_resolution,
            arguments={
                **_attribute_common_arguments(
                    typed_operation=typed_operation,
                    signature=signature,
                    include_function_attribute_type=(
                        receiver_entity_kind == "function_config"
                    ),
                ),
                "enum_config_id": enum_config_id,
            },
        )
    if descriptor_kind == "class":
        type_class_config_id = _optional_text(
            descriptor_resolution.get("class_config_id")
        )
        if type_class_config_id is None:
            return _attribute_method_blocked_payload(
                typed_operation=typed_operation,
                descriptor_kind=descriptor_kind,
                reason="meta_ocg_attribute_mutation_requires_type_class_config_id",
                blockers=("missing_attribute_type_class_config_id",),
                descriptor_resolution=descriptor_resolution,
            )
        return _attribute_method_bound_payload(
            typed_operation=typed_operation,
            receiver=receiver,
            descriptor_kind=descriptor_kind,
            function_ref=_attribute_function_ref(
                receiver_entity_kind=receiver_entity_kind,
                descriptor_kind=descriptor_kind,
            ),
            descriptor_resolution=descriptor_resolution,
            arguments={
                **_attribute_common_arguments(
                    typed_operation=typed_operation,
                    signature=signature,
                    include_function_attribute_type=(
                        receiver_entity_kind == "function_config"
                    ),
                ),
                "type_class_config_id": type_class_config_id,
            },
        )
    if descriptor_kind == "collection":
        collection_arguments = _attribute_collection_arguments(
            typed_operation=typed_operation,
            signature=signature,
            descriptor_resolution=descriptor_resolution,
            include_function_attribute_type=(receiver_entity_kind == "function_config"),
        )
        if collection_arguments is None:
            return _attribute_method_blocked_payload(
                typed_operation=typed_operation,
                descriptor_kind=descriptor_kind,
                reason="meta_ocg_attribute_collection_descriptor_requires_element_target",
                blockers=("missing_collection_attribute_element_target",),
                descriptor_resolution=descriptor_resolution,
            )
        return _attribute_method_bound_payload(
            typed_operation=typed_operation,
            receiver=receiver,
            descriptor_kind=descriptor_kind,
            function_ref=_attribute_function_ref(
                receiver_entity_kind=receiver_entity_kind,
                descriptor_kind=descriptor_kind,
            ),
            descriptor_resolution=descriptor_resolution,
            arguments=collection_arguments,
        )
    return _attribute_method_blocked_payload(
        typed_operation=typed_operation,
        descriptor_kind=descriptor_kind,
        reason="meta_ocg_attribute_descriptor_kind_not_supported_by_current_mutation_methods",
        blockers=(f"unsupported_attribute_descriptor_kind:{descriptor_kind}",),
        descriptor_resolution=descriptor_resolution,
    )


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
            "collection": (
                META_PROVIDER_DELTA_CLASS_CONFIG_CREATE_COLLECTION_ATTRIBUTE_FUNCTION_REF
            ),
        }[descriptor_kind]
    if receiver_entity_kind == "function_config":
        return {
            "primitive": META_FUNCTION_CONFIG_ADD_PRIMITIVE_ATTRIBUTE_FUNCTION_REF,
            "enum": META_FUNCTION_CONFIG_ADD_ENUM_ATTRIBUTE_FUNCTION_REF,
            "class": META_FUNCTION_CONFIG_ADD_CLASS_ATTRIBUTE_FUNCTION_REF,
            "collection": (
                META_PROVIDER_DELTA_FUNCTION_CONFIG_ADD_COLLECTION_ATTRIBUTE_FUNCTION_REF
            ),
        }[descriptor_kind]
    return ""


def _attribute_method_bound_payload(
    *,
    typed_operation: Mapping[str, object],
    receiver: Mapping[str, object],
    descriptor_kind: str,
    function_ref: str,
    descriptor_resolution: Mapping[str, object],
    arguments: Mapping[str, object],
) -> dict[str, object]:
    return {
        "status": "attribute_method_bound",
        "reason": "meta_ocg_attribute_mutation_method_bound",
        "blockers": (),
        "binding_key": _attribute_method_binding_key(
            receiver_entity_kind=_optional_text(receiver.get("receiver_entity_kind")),
            descriptor_kind=descriptor_kind,
        ),
        "function_ref": function_ref,
        "attribute_descriptor_kind": descriptor_kind,
        "attribute_semantic_key": _optional_text(typed_operation.get("semantic_key")),
        "attribute_descriptor_resolution": dict(descriptor_resolution),
        "arguments": dict(arguments),
    }


def _attribute_method_blocked_payload(
    *,
    typed_operation: Mapping[str, object],
    descriptor_kind: str,
    reason: str,
    blockers: tuple[str, ...],
    descriptor_resolution: Mapping[str, object] | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "status": "attribute_method_blocked",
        "reason": reason,
        "blockers": blockers,
        "binding_key": None,
        "function_ref": None,
        "attribute_descriptor_kind": descriptor_kind,
        "attribute_semantic_key": _optional_text(typed_operation.get("semantic_key")),
        "arguments": {},
    }
    if descriptor_resolution is not None:
        payload["attribute_descriptor_resolution"] = dict(descriptor_resolution)
    return payload


def _attribute_common_arguments(
    *,
    typed_operation: Mapping[str, object],
    signature: Mapping[str, object],
    include_function_attribute_type: bool,
) -> dict[str, object]:
    current = _mapping_value(typed_operation.get("current"))
    arguments: dict[str, object] = {
        "name": (
            _optional_text(signature.get("name"))
            or _optional_text(current.get("attribute_name"))
        ),
        "description": signature.get("description"),
        "default_value": signature.get("default_value"),
        "is_primary": signature.get("is_primary") is True,
        "is_public": signature.get("is_public") is not False,
        "is_required": signature.get("is_required") is True,
        "is_unique": signature.get("is_unique") is True,
        "is_virtual": signature.get("is_virtual") is True,
        "position": _int_object_value(signature.get("position")),
    }
    if include_function_attribute_type:
        arguments["type"] = (
            _optional_text(signature.get("function_attribute_type")) or "input"
        )
        arguments["is_identity_key"] = signature.get("is_identity_key") is True
    return arguments


def _attribute_collection_arguments(
    *,
    typed_operation: Mapping[str, object],
    signature: Mapping[str, object],
    descriptor_resolution: Mapping[str, object],
    include_function_attribute_type: bool,
) -> dict[str, object] | None:
    element_descriptor_kind = _optional_text(
        descriptor_resolution.get("element_descriptor_kind")
    )
    collection_kind = _optional_text(descriptor_resolution.get("collection_kind"))
    if collection_kind is None or element_descriptor_kind is None:
        return None
    arguments = {
        **_attribute_common_arguments(
            typed_operation=typed_operation,
            signature=signature,
            include_function_attribute_type=include_function_attribute_type,
        ),
        "collection_kind": collection_kind,
        "element_descriptor_kind": element_descriptor_kind,
        "descriptor_graph": dict(
            _mapping_value(descriptor_resolution.get("descriptor_graph"))
        ),
        "descriptor_leaf_candidates": tuple(
            _tuple_evidence(descriptor_resolution.get("descriptor_leaf_candidates"))
        ),
        "execution_method": "provider_delta_function_call_collection_attribute",
        "execution_wired": False,
    }
    if element_descriptor_kind == "primitive":
        primitive_base_type = (
            _optional_text(descriptor_resolution.get("element_primitive_base_type"))
            or "any"
        )
        arguments["element_primitive_base_type"] = primitive_base_type
        primitive_config_id = _optional_text(
            descriptor_resolution.get("element_primitive_config_id")
        )
        if primitive_config_id is not None:
            arguments["element_primitive_config_id"] = primitive_config_id
        return arguments
    if element_descriptor_kind == "enum":
        enum_config_id = _optional_text(
            descriptor_resolution.get("element_enum_config_id")
        )
        if enum_config_id is None:
            return None
        arguments["element_enum_config_id"] = enum_config_id
        return arguments
    if element_descriptor_kind == "class":
        class_config_id = _optional_text(
            descriptor_resolution.get("element_class_config_id")
        )
        if class_config_id is None:
            return None
        arguments["element_type_class_config_id"] = class_config_id
        return arguments
    return None


def _attribute_descriptor_resolution(
    *,
    descriptor: Mapping[str, object],
) -> dict[str, object]:
    if not descriptor:
        return _attribute_descriptor_blocked_resolution(
            descriptor=descriptor,
            descriptor_kind="unknown",
            reason="meta_ocg_attribute_mutation_requires_type_descriptor",
            blockers=("missing_attribute_type_descriptor",),
            candidates=(),
        )
    descriptor_kind = _attribute_descriptor_kind(descriptor=descriptor)
    if descriptor_kind in {"primitive", "enum", "class"}:
        candidate = _attribute_descriptor_leaf_candidate(
            descriptor=descriptor,
            descriptor_path=(descriptor_kind,),
        )
        return _attribute_descriptor_resolved_payload(
            descriptor=descriptor,
            candidate=candidate,
            descriptor_kind=descriptor_kind,
            is_optional=False,
            resolution_source="direct_descriptor",
        )
    if descriptor_kind == "union":
        candidates = _attribute_descriptor_leaf_candidates(
            descriptor=descriptor,
            descriptor_path=("union",),
        )
        null_candidate_count = len(
            tuple(candidate for candidate in candidates if candidate["is_null"])
        )
        non_null_candidates = tuple(
            candidate for candidate in candidates if not candidate["is_null"]
        )
        if len(non_null_candidates) == 1:
            candidate = non_null_candidates[0]
            return _attribute_descriptor_resolved_payload(
                descriptor=descriptor,
                candidate=candidate,
                descriptor_kind=descriptor_kind,
                is_optional=null_candidate_count > 0,
                resolution_source="union_single_non_null_descriptor",
            )
        return _attribute_descriptor_blocked_resolution(
            descriptor=descriptor,
            descriptor_kind=descriptor_kind,
            reason="meta_ocg_attribute_union_descriptor_requires_single_non_null_target",
            blockers=(
                "union_descriptor_requires_single_non_null_target",
                f"union_non_null_target_count:{len(non_null_candidates)}",
            ),
            candidates=non_null_candidates,
        )
    if descriptor_kind == "collection":
        candidates = tuple(
            candidate
            for candidate in _attribute_descriptor_leaf_candidates(
                descriptor=descriptor,
                descriptor_path=("collection",),
            )
            if not candidate["is_null"]
        )
        if len(candidates) == 1:
            return _attribute_descriptor_resolved_payload(
                descriptor=descriptor,
                candidate=candidates[0],
                descriptor_kind=descriptor_kind,
                is_optional=False,
                resolution_source="collection_single_element_descriptor",
            )
        return _attribute_descriptor_collection_blocked_resolution(
            descriptor=descriptor,
            descriptor_kind=descriptor_kind,
            candidates=candidates,
        )
    return _attribute_descriptor_blocked_resolution(
        descriptor=descriptor,
        descriptor_kind=descriptor_kind,
        reason="meta_ocg_attribute_descriptor_kind_not_supported_by_current_mutation_methods",
        blockers=(f"unsupported_attribute_descriptor_kind:{descriptor_kind}",),
        candidates=_attribute_descriptor_leaf_candidates(
            descriptor=descriptor,
            descriptor_path=(descriptor_kind,),
        ),
    )


def _attribute_descriptor_resolved_payload(
    *,
    descriptor: Mapping[str, object],
    candidate: Mapping[str, object],
    descriptor_kind: str,
    is_optional: bool,
    resolution_source: str,
) -> dict[str, object]:
    return {
        "status": "attribute_descriptor_resolved",
        "reason": "meta_ocg_attribute_descriptor_resolved",
        "blockers": (),
        "descriptor_kind": descriptor_kind,
        "descriptor_id": _optional_text(descriptor.get("descriptor_id")),
        "method_descriptor_kind": _optional_text(
            candidate.get("method_descriptor_kind")
        ),
        "element_descriptor_kind": _optional_text(
            candidate.get("element_descriptor_kind")
        ),
        "resolved_descriptor_kind": _optional_text(candidate.get("descriptor_kind")),
        "resolved_descriptor_id": _optional_text(candidate.get("descriptor_id")),
        "resolution_source": resolution_source,
        "descriptor_path": _tuple_text(candidate.get("descriptor_path")),
        "is_optional": is_optional,
        "is_collection": candidate.get("is_collection") is True,
        "collection_kind": _optional_text(candidate.get("collection_kind")),
        "class_config_id": _optional_text(candidate.get("class_config_id")),
        "enum_config_id": _optional_text(candidate.get("enum_config_id")),
        "primitive_config_id": _optional_text(candidate.get("primitive_config_id")),
        "primitive_base_type": _optional_text(candidate.get("primitive_base_type")),
        "primitive_signature": _optional_text(candidate.get("primitive_signature")),
        "element_class_config_id": _optional_text(
            candidate.get("element_class_config_id")
        )
        or _optional_text(candidate.get("class_config_id")),
        "element_enum_config_id": _optional_text(
            candidate.get("element_enum_config_id")
        )
        or _optional_text(candidate.get("enum_config_id")),
        "element_primitive_config_id": _optional_text(
            candidate.get("element_primitive_config_id")
        )
        or _optional_text(candidate.get("primitive_config_id")),
        "element_primitive_base_type": _optional_text(
            candidate.get("element_primitive_base_type")
        )
        or _optional_text(candidate.get("primitive_base_type")),
        "element_primitive_signature": _optional_text(
            candidate.get("element_primitive_signature")
        )
        or _optional_text(candidate.get("primitive_signature")),
        "target": _mapping_value(candidate.get("target")),
        "descriptor_graph": dict(descriptor),
        "resolved_descriptor": _mapping_value(candidate.get("descriptor")),
        "descriptor_leaf_candidates": (
            _attribute_descriptor_candidate_payload(candidate),
        ),
    }


def _attribute_descriptor_collection_blocked_resolution(
    *,
    descriptor: Mapping[str, object],
    descriptor_kind: str,
    candidates: tuple[Mapping[str, object], ...],
) -> dict[str, object]:
    return _attribute_descriptor_blocked_resolution(
        descriptor=descriptor,
        descriptor_kind=descriptor_kind,
        reason=(
            "meta_ocg_attribute_collection_descriptor_requires_single_element_target"
        ),
        blockers=(
            "collection_attribute_descriptor_requires_single_element_target",
            f"collection_element_target_count:{len(candidates)}",
        ),
        candidates=candidates,
    )


def _attribute_descriptor_blocked_resolution(
    *,
    descriptor: Mapping[str, object],
    descriptor_kind: str,
    reason: str,
    blockers: tuple[str, ...],
    candidates: tuple[Mapping[str, object], ...],
) -> dict[str, object]:
    return {
        "status": "attribute_descriptor_blocked",
        "reason": reason,
        "blockers": blockers,
        "descriptor_kind": descriptor_kind,
        "descriptor_id": _optional_text(descriptor.get("descriptor_id")),
        "method_descriptor_kind": None,
        "resolved_descriptor_kind": None,
        "resolved_descriptor_id": None,
        "resolution_source": "descriptor_graph",
        "descriptor_path": (),
        "is_optional": False,
        "is_collection": descriptor_kind == "collection",
        "collection_kind": _optional_text(descriptor.get("collection_kind")),
        "class_config_id": None,
        "enum_config_id": None,
        "primitive_config_id": None,
        "primitive_base_type": None,
        "primitive_signature": None,
        "target": _mapping_value(descriptor.get("target")),
        "descriptor_graph": dict(descriptor),
        "descriptor_leaf_candidates": tuple(
            _attribute_descriptor_candidate_payload(candidate)
            for candidate in candidates
        ),
    }


def _attribute_descriptor_leaf_candidates(
    *,
    descriptor: Mapping[str, object],
    descriptor_path: tuple[str, ...],
) -> tuple[dict[str, object], ...]:
    descriptor_kind = _attribute_descriptor_kind(descriptor=descriptor)
    if descriptor_kind in {"primitive", "enum", "class"}:
        return (
            _attribute_descriptor_leaf_candidate(
                descriptor=descriptor,
                descriptor_path=descriptor_path,
            ),
        )
    child_links = tuple(
        _mapping_value(link)
        for link in _tuple_evidence(descriptor.get("child_links"))
        if isinstance(link, Mapping)
    )
    candidates: list[dict[str, object]] = []
    for link in child_links:
        child_descriptor = _mapping_value(link.get("child_descriptor"))
        if not child_descriptor:
            continue
        role = _optional_text(link.get("role")) or "child"
        child_path = (
            *descriptor_path,
            f"{role}:{_int_payload_value(link, 'position')}",
        )
        for candidate in _attribute_descriptor_leaf_candidates(
            descriptor=child_descriptor,
            descriptor_path=child_path,
        ):
            if descriptor_kind == "collection":
                updated = dict(candidate)
                updated["is_collection"] = True
                updated["collection_kind"] = _optional_text(
                    descriptor.get("collection_kind")
                )
                updated["method_descriptor_kind"] = "collection"
                updated["element_descriptor_kind"] = _optional_text(
                    candidate.get("descriptor_kind")
                )
                updated["element_class_config_id"] = _optional_text(
                    candidate.get("class_config_id")
                )
                updated["element_enum_config_id"] = _optional_text(
                    candidate.get("enum_config_id")
                )
                updated["element_primitive_config_id"] = _optional_text(
                    candidate.get("primitive_config_id")
                )
                updated["element_primitive_base_type"] = _optional_text(
                    candidate.get("primitive_base_type")
                )
                updated["element_primitive_signature"] = _optional_text(
                    candidate.get("primitive_signature")
                )
                updated["container_descriptor_kind"] = descriptor_kind
                updated["container_descriptor_id"] = _optional_text(
                    descriptor.get("descriptor_id")
                )
                candidates.append(updated)
            else:
                candidates.append(candidate)
    return tuple(candidates)


def _attribute_descriptor_leaf_candidate(
    *,
    descriptor: Mapping[str, object],
    descriptor_path: tuple[str, ...],
) -> dict[str, object]:
    descriptor_kind = _attribute_descriptor_kind(descriptor=descriptor)
    target = _mapping_value(descriptor.get("target"))
    primitive_base_type = _optional_text(
        descriptor.get("primitive_base_type")
    ) or _optional_text(target.get("primitive_base_type"))
    primitive_signature = _optional_text(
        descriptor.get("primitive_signature")
    ) or _optional_text(target.get("primitive_signature"))
    return {
        "descriptor_kind": descriptor_kind,
        "method_descriptor_kind": descriptor_kind,
        "descriptor_id": _optional_text(descriptor.get("descriptor_id")),
        "descriptor_path": descriptor_path,
        "descriptor": dict(descriptor),
        "target": target,
        "is_collection": (
            _optional_text(descriptor.get("collection_kind")) not in {None, "single"}
        ),
        "collection_kind": _optional_text(descriptor.get("collection_kind")),
        "is_null": _attribute_descriptor_leaf_is_null(
            descriptor_kind=descriptor_kind,
            primitive_base_type=primitive_base_type,
            primitive_signature=primitive_signature,
        ),
        "class_config_id": (
            _optional_text(descriptor.get("class_config_id"))
            or _optional_text(target.get("class_config_id"))
        ),
        "enum_config_id": (
            _optional_text(descriptor.get("enum_config_id"))
            or _optional_text(target.get("enum_config_id"))
        ),
        "primitive_config_id": (
            _optional_text(descriptor.get("primitive_config_id"))
            or _optional_text(target.get("primitive_config_id"))
        ),
        "primitive_base_type": primitive_base_type,
        "primitive_signature": primitive_signature,
    }


def _attribute_descriptor_leaf_is_null(
    *,
    descriptor_kind: str,
    primitive_base_type: str | None,
    primitive_signature: str | None,
) -> bool:
    if descriptor_kind != "primitive":
        return False
    return (primitive_base_type or primitive_signature or "").lower() == "null"


def _attribute_descriptor_candidate_payload(
    candidate: Mapping[str, object],
) -> dict[str, object]:
    return {
        "descriptor_kind": _optional_text(candidate.get("descriptor_kind")),
        "method_descriptor_kind": _optional_text(
            candidate.get("method_descriptor_kind")
        ),
        "element_descriptor_kind": _optional_text(
            candidate.get("element_descriptor_kind")
        ),
        "descriptor_id": _optional_text(candidate.get("descriptor_id")),
        "descriptor_path": _tuple_text(candidate.get("descriptor_path")),
        "is_collection": candidate.get("is_collection") is True,
        "collection_kind": _optional_text(candidate.get("collection_kind")),
        "is_null": candidate.get("is_null") is True,
        "class_config_id": _optional_text(candidate.get("class_config_id")),
        "enum_config_id": _optional_text(candidate.get("enum_config_id")),
        "primitive_config_id": _optional_text(candidate.get("primitive_config_id")),
        "primitive_base_type": _optional_text(candidate.get("primitive_base_type")),
        "primitive_signature": _optional_text(candidate.get("primitive_signature")),
        "element_class_config_id": _optional_text(
            candidate.get("element_class_config_id")
        ),
        "element_enum_config_id": _optional_text(
            candidate.get("element_enum_config_id")
        ),
        "element_primitive_config_id": _optional_text(
            candidate.get("element_primitive_config_id")
        ),
        "element_primitive_base_type": _optional_text(
            candidate.get("element_primitive_base_type")
        ),
        "element_primitive_signature": _optional_text(
            candidate.get("element_primitive_signature")
        ),
        "target": _mapping_value(candidate.get("target")),
    }


def _attribute_descriptor_kind(*, descriptor: Mapping[str, object]) -> str:
    kind = _optional_text(descriptor.get("kind"))
    if kind is None:
        return "unknown"
    if kind == "class_":
        return "class"
    return kind


def _attribute_method_binding_key(
    *,
    receiver_entity_kind: str | None,
    descriptor_kind: str,
) -> str | None:
    if receiver_entity_kind == "class_config":
        if descriptor_kind == "collection":
            return "aware_meta.provider_delta.class_config.create_collection_attribute_config"
        return f"aware_meta.class_config.create_{descriptor_kind}_attribute_config"
    if receiver_entity_kind == "function_config":
        if descriptor_kind == "collection":
            return "aware_meta.provider_delta.function_config.add_collection_attribute_config"
        return f"aware_meta.function_config.add_{descriptor_kind}_attribute_config"
    return None


def _mutation_step_ready_payload(
    *,
    typed_operation: Mapping[str, object],
    function_ref: str,
    receiver_semantic_key: str | None,
    receiver_source: str,
    dependencies: tuple[str, ...],
    fallback_arguments: Mapping[str, object],
) -> dict[str, object]:
    function_call_plan = _mapping_value(typed_operation.get("function_call_plan"))
    planned_function_ref = _optional_text(function_call_plan.get("function_ref"))
    arguments = _mapping_value(function_call_plan.get("arguments"))
    if not arguments:
        arguments = dict(fallback_arguments)
    argument_refs = _mapping_value(function_call_plan.get("argument_refs"))
    receiver_object_id = _optional_text(function_call_plan.get("receiver_object_id"))
    if planned_function_ref is not None:
        function_ref = planned_function_ref
    return _mutation_step_base_payload(
        typed_operation=typed_operation,
        status="mutation_step_ready",
        reason="meta_ocg_provider_delta_mutation_step_ready",
        function_ref=function_ref,
        receiver_semantic_key=(
            _optional_text(function_call_plan.get("receiver_semantic_key"))
            or receiver_semantic_key
        ),
        receiver_object_id=receiver_object_id,
        receiver_source=(
            _optional_text(function_call_plan.get("receiver_source")) or receiver_source
        ),
        arguments=arguments,
        argument_refs=argument_refs,
        dependencies=(
            _tuple_text(function_call_plan.get("dependencies")) or dependencies
        ),
        blockers=(),
        candidate_arguments=None,
        function_call_plan=function_call_plan if function_call_plan else None,
        extra_payload=None,
    )


def _mutation_step_blocked_payload(
    *,
    typed_operation: Mapping[str, object],
    reason: str,
    blockers: tuple[str, ...],
    receiver_semantic_key: str | None = None,
    dependencies: tuple[str, ...] = (),
    candidate_arguments: Mapping[str, object] | None = None,
    extra_payload: Mapping[str, object] | None = None,
) -> dict[str, object]:
    return _mutation_step_base_payload(
        typed_operation=typed_operation,
        status="mutation_step_blocked",
        reason=reason,
        function_ref=None,
        receiver_semantic_key=receiver_semantic_key
        or _typed_operation_receiver_semantic_key(typed_operation=typed_operation),
        receiver_object_id=None,
        receiver_source="blocked",
        arguments={},
        argument_refs={},
        dependencies=dependencies,
        blockers=blockers,
        candidate_arguments=(
            dict(candidate_arguments) if candidate_arguments is not None else None
        ),
        function_call_plan=None,
        extra_payload=extra_payload,
    )


def _attribute_mutation_blocked_payload(
    *,
    typed_operation: Mapping[str, object],
    reason: str,
    blockers: tuple[str, ...],
    receiver_semantic_key: str | None,
    dependencies: tuple[str, ...],
    candidate_arguments: Mapping[str, object],
    receiver: Mapping[str, object] | None = None,
    method_binding: Mapping[str, object] | None = None,
) -> dict[str, object]:
    extra_payload: dict[str, object] = {}
    if receiver is not None:
        extra_payload.update(
            {
                "receiver_entity_kind": _optional_text(
                    receiver.get("receiver_entity_kind")
                ),
                "receiver_entity_id": _optional_text(
                    receiver.get("receiver_entity_id")
                ),
                "receiver_entity_path": _optional_text(
                    receiver.get("receiver_entity_path")
                ),
                "receiver_resolution": dict(receiver),
            }
        )
    if method_binding is not None:
        extra_payload["method_binding"] = dict(method_binding)
        extra_payload["attribute_descriptor_kind"] = _optional_text(
            method_binding.get("attribute_descriptor_kind")
        )
        extra_payload["attribute_descriptor_resolution"] = _mapping_value(
            method_binding.get("attribute_descriptor_resolution")
        )
    return _mutation_step_blocked_payload(
        typed_operation=typed_operation,
        reason=reason,
        blockers=blockers,
        receiver_semantic_key=receiver_semantic_key,
        dependencies=dependencies,
        candidate_arguments=candidate_arguments,
        extra_payload=extra_payload,
    )


def _mutation_step_base_payload(
    *,
    typed_operation: Mapping[str, object],
    status: str,
    reason: str,
    function_ref: str | None,
    receiver_semantic_key: str | None,
    receiver_object_id: str | None,
    receiver_source: str,
    arguments: Mapping[str, object],
    argument_refs: Mapping[str, object],
    dependencies: tuple[str, ...],
    blockers: tuple[str, ...],
    candidate_arguments: Mapping[str, object] | None,
    function_call_plan: Mapping[str, object] | None,
    extra_payload: Mapping[str, object] | None,
) -> dict[str, object]:
    semantic_key = _optional_text(typed_operation.get("semantic_key"))
    operation_family = _string_value(typed_operation.get("operation_family"))
    subject_kind = _string_value(typed_operation.get("ontology_subject_kind"))
    provider_operation_type = _string_value(
        typed_operation.get("provider_operation_type")
    )
    payload: dict[str, object] = {
        "step_kind": "meta_ocg_provider_delta_mutation_step",
        "contract_version": _MUTATION_STEP_CONTRACT_VERSION,
        "status": status,
        "reason": reason,
        "step_key": f"meta_ocg_mutation:{operation_family}:{subject_kind}:{semantic_key}",
        "source_typed_operation_key": _optional_text(
            typed_operation.get("operation_key")
        ),
        "source_entry_key": _optional_text(typed_operation.get("source_entry_key")),
        "source_delta_key": _optional_text(typed_operation.get("source_delta_key")),
        "source_refs": _tuple_text(typed_operation.get("source_refs")),
        "semantic_key": semantic_key,
        "operation_family": operation_family,
        "provider_operation_type": provider_operation_type,
        "semantic_subject_type": _optional_text(
            typed_operation.get("semantic_subject_type")
        ),
        "ontology_subject_kind": subject_kind,
        "function_ref": function_ref,
        "receiver_semantic_key": receiver_semantic_key,
        "receiver_object_id": receiver_object_id,
        "receiver_source": receiver_source,
        "arguments": dict(arguments),
        "argument_refs": dict(argument_refs),
        "dependencies": dependencies,
        "baseline": _mapping_value(typed_operation.get("baseline")),
        "current": _mapping_value(typed_operation.get("current")),
        "blockers": blockers,
        "would_execute": False,
        "did_execute": False,
        "would_persist": False,
        "did_persist": False,
        "execution_wired": False,
        "production_execution_wired": False,
    }
    if candidate_arguments is not None:
        payload["candidate_arguments"] = dict(candidate_arguments)
    if function_call_plan is not None:
        payload["function_call_plan"] = dict(function_call_plan)
    if extra_payload is not None:
        payload.update(dict(extra_payload))
    return payload


def _typed_operation_ocg_arguments(
    *,
    typed_operation: Mapping[str, object],
) -> dict[str, object]:
    ocg_operation = _mapping_value(typed_operation.get("ocg_operation"))
    return _mapping_value(ocg_operation.get("arguments"))


def _typed_operation_receiver_semantic_key(
    *,
    typed_operation: Mapping[str, object],
) -> str | None:
    ocg_operation = _mapping_value(typed_operation.get("ocg_operation"))
    receiver_semantic_key = _optional_text(ocg_operation.get("receiver_semantic_key"))
    if receiver_semantic_key is not None:
        return receiver_semantic_key
    current = _mapping_value(typed_operation.get("current"))
    return _optional_text(current.get("graph_semantic_key"))


def _node_mutation_arguments(
    *,
    typed_operation: Mapping[str, object],
) -> dict[str, object]:
    current = _mapping_value(typed_operation.get("current"))
    ocg_arguments = _typed_operation_ocg_arguments(typed_operation=typed_operation)
    return {
        "type": current.get("node_type") or ocg_arguments.get("node_type"),
        "node_key": current.get("node_key") or ocg_arguments.get("node_key"),
    }


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _tuple_evidence(value: object) -> tuple[object, ...]:
    if isinstance(value, tuple):
        return value
    if isinstance(value, list):
        return tuple(value)
    return ()


def _mapping_value(value: object) -> dict[str, object]:
    if not isinstance(value, Mapping):
        return {}
    return {str(key): item for key, item in value.items()}


def _string_value(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _tuple_text(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(
        text for text in (_optional_text(item) for item in value) if text is not None
    )


__all__ = [
    "META_PROVIDER_DELTA_CLASS_CONFIG_CREATE_COLLECTION_ATTRIBUTE_FUNCTION_REF",
    "META_PROVIDER_DELTA_FUNCTION_CONFIG_ADD_COLLECTION_ATTRIBUTE_FUNCTION_REF",
    "_mutation_step_from_typed_operation",
]
