from __future__ import annotations

from collections.abc import Mapping

from aware_meta.materialization.deltas.generated_materialization_dispatch import (
    generated_materialization_intent_target_metadata,
)
from aware_meta.materialization.deltas.contracts import (
    META_PROVIDER_DELTA_TYPED_OPERATION_PLAN_CONTRACT_VERSION,
)
from aware_meta.semantic_operation_resolution import (
    CLASS_CONFIG_CREATE_FUNCTION_CONFIG_FUNCTION_REF,
    META_FUNCTION_CREATE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
    META_FUNCTION_DELETE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
    META_OBJECT_CONFIG_GRAPH_FUNCTION_CREATE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_FUNCTION_DELETE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_FUNCTION_SIGNATURE_UPDATE_OPERATION,
    MetaSemanticOperationFunctionCallPlan,
    MetaSemanticOperationResolution,
    _provider_delta_typed_operation_metadata_for_signature_update as _root_provider_delta_typed_operation_metadata_for_signature_update,
    _blocked_resolution,
    _class_fqn_from_package_context,
    _class_name_from_semantic_key,
    _first_text,
    _function_name_from_semantic_key,
    _int_value,
    _mapping_value,
    _operation_key,
    _optional_text,
    _semantic_key,
    _semantic_operation_type,
    _stable_function_config_id_for_create,
    _string_value,
    _tuple_values,
)

_FUNCTION_SIGNATURE_UPDATE_FIELD_PATHS = frozenset(
    (
        "signature",
        "owner_key",
        "name",
        "kind",
        "description",
        "verb",
        "is_async",
        "inputs",
        "outputs",
        "class_config_id",
        "function_config_id",
        "is_public",
        "is_constructor",
        "position",
    )
)


def resolve_function_config_semantic_operation(
    *,
    operation: Mapping[str, object],
    operation_group: tuple[Mapping[str, object], ...],
    current_objects: Mapping[str, str],
    current_object_identities: Mapping[str, Mapping[str, object]],
) -> MetaSemanticOperationResolution:
    operation_type = _string_value(operation.get("semantic_operation_type"))
    if operation_type == META_OBJECT_CONFIG_GRAPH_FUNCTION_CREATE_OPERATION:
        return _resolve_function_create(
            operation=operation,
            current_objects=current_objects,
            current_object_identities=current_object_identities,
        )
    if operation_type == META_OBJECT_CONFIG_GRAPH_FUNCTION_DELETE_OPERATION:
        return _resolve_function_delete(
            operation=operation,
            current_objects=current_objects,
            current_object_identities=current_object_identities,
        )
    if operation_type == META_OBJECT_CONFIG_GRAPH_FUNCTION_SIGNATURE_UPDATE_OPERATION:
        return _resolve_function_signature_update(
            operation=operation,
            operation_group=operation_group,
            current_objects=current_objects,
            current_object_identities=current_object_identities,
        )
    return _blocked_resolution(
        operation=operation,
        reason="meta_ocg_function_operation_type_not_supported",
        blockers=(f"unsupported_operation_type:{operation_type or 'unknown'}",),
    )


def _resolve_function_create(
    *,
    operation: Mapping[str, object],
    current_objects: Mapping[str, str],
    current_object_identities: Mapping[str, Mapping[str, object]],
) -> MetaSemanticOperationResolution:
    if _string_value(operation.get("operation_family")) not in {"create", "upsert"}:
        return _blocked_resolution(
            operation=operation,
            reason="meta_ocg_function_create_requires_create_family",
            blockers=(
                "unsupported_operation_family:"
                f"{_string_value(operation.get('operation_family')) or 'unknown'}",
            ),
        )
    if _string_value(operation.get("semantic_subject_type")) not in {
        "FunctionConfig",
        "aware_meta.FunctionConfig",
    }:
        return _blocked_resolution(
            operation=operation,
            reason="meta_ocg_function_create_subject_not_supported",
            blockers=(
                "unsupported_semantic_subject_type:"
                f"{_string_value(operation.get('semantic_subject_type')) or 'unknown'}",
            ),
        )
    after_payload = _mapping_value(operation.get("after_payload"))
    function_name = _first_text(
        after_payload.get("function_name"),
        after_payload.get("name"),
        _function_name_from_semantic_key(_semantic_key(operation)),
    )
    class_name = _first_text(
        after_payload.get("class_name"),
        _class_name_from_semantic_key(_semantic_key(operation)),
    )
    if function_name is None or class_name is None:
        return _blocked_resolution(
            operation=operation,
            reason="meta_ocg_function_create_requires_class_and_function_name",
            blockers=tuple(
                blocker
                for blocker, value in (
                    ("missing_class_name", class_name),
                    ("missing_function_name", function_name),
                )
                if value is None
            ),
        )
    receiver_semantic_key = f"meta.class:{class_name}"
    receiver_object_id = current_objects.get(receiver_semantic_key)
    provider_delta_owner_object_id = _first_text(
        after_payload.get("class_config_id"),
        after_payload.get("owner_object_id"),
        receiver_object_id,
    )
    if provider_delta_owner_object_id is not None:
        return _resolve_function_create_via_provider_delta(
            operation=operation,
            after_payload=after_payload,
            class_name=class_name,
            function_name=function_name,
            class_config_id=provider_delta_owner_object_id,
            receiver_semantic_key=receiver_semantic_key,
            current_object_identities=current_object_identities,
        )
    execution_preconditions = (
        () if receiver_object_id is not None else ("baseline_object_identity",)
    )
    metadata = {
        "source": "aware_meta.semantic_operation_resolution",
        "semantic_apply_boundary": "ontology_function_call",
        "requires_baseline_object_identity": True,
        "execution_ready": receiver_object_id is not None,
        "execution_preconditions": execution_preconditions,
        "preview_only": True,
    }
    if receiver_object_id is not None:
        metadata["receiver_object_id"] = receiver_object_id
    plan = MetaSemanticOperationFunctionCallPlan(
        operation_key=_operation_key(operation),
        semantic_operation_type=_semantic_operation_type(operation),
        semantic_key=_semantic_key(operation),
        function_ref=CLASS_CONFIG_CREATE_FUNCTION_CONFIG_FUNCTION_REF,
        binding_key="aware_meta.object_config_graph.function.create",
        event_key=_optional_text(operation.get("event_key")),
        receiver_semantic_key=receiver_semantic_key,
        receiver_object_id=receiver_object_id,
        arguments={
            "name": function_name,
            "description": _first_text(
                after_payload.get("function_description"),
                after_payload.get("description"),
            ),
            "verb": _optional_text(after_payload.get("verb")),
            "is_async": after_payload.get("is_async") is True,
            "kind": _first_text(after_payload.get("kind")) or "instance",
            "is_public": after_payload.get("is_public") is not False,
            "is_constructor": after_payload.get("is_constructor") is True,
            "position": _int_value(after_payload.get("position")) or 0,
        },
        result_semantic_key=_semantic_key(operation),
        metadata=metadata,
    )
    return MetaSemanticOperationResolution(
        operation_key=_operation_key(operation),
        semantic_operation_type=_semantic_operation_type(operation),
        semantic_key=_semantic_key(operation),
        status="function_call_plan_ready",
        reason="meta_ocg_function_create_function_call_plan_ready",
        function_call_plan=plan,
        metadata={"execution_preconditions": execution_preconditions},
    )


def _resolve_function_create_via_provider_delta(
    *,
    operation: Mapping[str, object],
    after_payload: Mapping[str, object],
    class_name: str,
    function_name: str,
    class_config_id: str,
    receiver_semantic_key: str,
    current_object_identities: Mapping[str, Mapping[str, object]],
) -> MetaSemanticOperationResolution:
    owner_key = _class_fqn_from_package_context(
        class_name=class_name,
        raw_class_fqn=_first_text(
            after_payload.get("owner_key"),
            after_payload.get("class_fqn"),
            class_name,
        ),
        operation=operation,
    )
    kind = _first_text(after_payload.get("kind"), "instance")
    function_config_id = _first_text(
        after_payload.get("function_config_id"),
        after_payload.get("entity_id"),
        after_payload.get("object_id"),
        _stable_function_config_id_for_create(
            owner_key=owner_key,
            function_name=function_name,
            kind=kind,
        ),
    )
    blockers = tuple(
        blocker
        for blocker, value in (
            ("missing_owner_key", owner_key),
            ("missing_class_config_id", class_config_id),
            ("missing_function_config_id", function_config_id),
        )
        if value is None
    )
    provider_delta_typed_operation_metadata = (
        _provider_delta_typed_operation_metadata_for_function_create(
            operation=operation,
            owner_semantic_key=receiver_semantic_key,
            class_config_id=class_config_id,
            function_config_id=function_config_id,
            function_name=function_name,
            owner_key=owner_key,
            owner_generated_materialization=(
                _owner_class_generated_materialization_for_function_create(
                    current_object_identities=current_object_identities,
                    receiver_semantic_key=receiver_semantic_key,
                    class_name=class_name,
                    owner_key=owner_key,
                )
            ),
        )
    )
    metadata: dict[str, object] = {
        "source": "aware_meta.semantic_operation_resolution",
        "semantic_apply_boundary": "provider_delta_ontology_operation_executor",
        "provider_delta_handler_key": "function.scalar_function_calls",
        "provider_operation_type": "meta_ocg.function.create",
        "requires_baseline_object_identity": False,
        "requires_owner_class_config_id": True,
        "execution_ready": not blockers,
        "execution_preconditions": ("provider_delta_ontology_operation_executor",),
        "preview_only": True,
        "receiver_semantic_key": receiver_semantic_key,
        "receiver_object_id": class_config_id,
        "result_semantic_key": _semantic_key(operation),
        "result_object_id": function_config_id,
        **provider_delta_typed_operation_metadata,
    }
    if owner_key is not None:
        metadata["owner_key"] = owner_key
    return _blocked_resolution(
        operation=operation,
        reason=(
            "meta_ocg_function_create_requires_provider_delta_"
            "ontology_operation_executor"
        ),
        blockers=(
            *blockers,
            "semantic_plan_single_function_call_preview_not_supported",
            "provider_delta_function_create_operation_executor_required",
        ),
        metadata=metadata,
    )


def _provider_delta_typed_operation_metadata_for_function_create(
    *,
    operation: Mapping[str, object],
    owner_semantic_key: str,
    class_config_id: str,
    function_config_id: str | None,
    function_name: str,
    owner_key: str | None,
    owner_generated_materialization: Mapping[str, object] | None = None,
) -> dict[str, object]:
    if function_config_id is None or owner_key is None:
        typed_operation_plan = _function_create_typed_operation_plan(
            typed_operations=(),
            reason="function_create_provider_delta_operation_blocked",
        )
    else:
        from aware_meta.function.config.deltas.typed_operations import (  # noqa: WPS433,E501
            function_config_create_typed_operation,
        )

        after_payload = _mapping_value(operation.get("after_payload"))
        generated_materialization = (
            _mapping_value(operation.get("generated_materialization"))
            or _mapping_value(after_payload.get("generated_materialization"))
            or _mapping_value(owner_generated_materialization)
            or None
        )
        function_signature = _mapping_value(after_payload.get("function_signature"))
        typed_operation = function_config_create_typed_operation(
            semantic_key=_semantic_key(operation),
            owner_semantic_key=owner_semantic_key,
            class_config_id=class_config_id,
            function_config_id=function_config_id,
            function_name=function_name,
            owner_key=owner_key,
            source_refs=tuple(
                str(item)
                for item in _tuple_values(operation.get("source_refs"))
                if _optional_text(item) is not None
            ),
            description=_first_text(
                after_payload.get("function_description"),
                after_payload.get("description"),
            ),
            verb=_optional_text(after_payload.get("verb")),
            is_async=after_payload.get("is_async") is True,
            kind=_first_text(after_payload.get("kind")) or "instance",
            inputs=_function_signature_child_payloads(
                function_signature=function_signature,
                child_key="inputs",
            ),
            outputs=_function_signature_child_payloads(
                function_signature=function_signature,
                child_key="outputs",
            ),
            is_public=after_payload.get("is_public") is not False,
            is_constructor=after_payload.get("is_constructor") is True,
            position=_int_value(after_payload.get("position")) or 0,
            generated_materialization=generated_materialization,
        ).evidence_payload()
        typed_operation_plan = _function_create_typed_operation_plan(
            typed_operations=(typed_operation,),
            reason="function_create_provider_delta_operation_ready",
        )
    typed_operations = tuple(_tuple_values(typed_operation_plan.get("typed_operations")))
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
            "function_create_provider_delta_operation_ready"
            if ready
            else "function_create_provider_delta_operation_blocked"
        ),
        "provider_delta_typed_operation_plan": typed_operation_plan,
        **_function_create_generated_materialization_intent_metadata(
            typed_operation_plan=typed_operation_plan,
            typed_operation=typed_operation,
            ready=ready,
        ),
    }
    if typed_operation is not None:
        metadata["provider_delta_typed_operation"] = dict(typed_operation)
    if not ready:
        metadata["provider_delta_typed_operation_blockers"] = (
            "function_create_provider_delta_typed_operation_unavailable",
        )
    return metadata


def _owner_class_generated_materialization_for_function_create(
    *,
    current_object_identities: Mapping[str, Mapping[str, object]],
    receiver_semantic_key: str,
    class_name: str,
    owner_key: str | None,
) -> Mapping[str, object] | None:
    owner_identity = _owner_class_identity_for_function_create(
        current_object_identities=current_object_identities,
        receiver_semantic_key=receiver_semantic_key,
        class_name=class_name,
        owner_key=owner_key,
    )
    if owner_identity is None:
        return None
    generated_materialization = _mapping_value(
        owner_identity.get("generated_materialization"),
    )
    if generated_materialization:
        return generated_materialization
    payload = _mapping_value(owner_identity.get("payload"))
    generated_materialization = _mapping_value(
        payload.get("generated_materialization"),
    )
    return generated_materialization or None


def _owner_class_identity_for_function_create(
    *,
    current_object_identities: Mapping[str, Mapping[str, object]],
    receiver_semantic_key: str,
    class_name: str,
    owner_key: str | None,
) -> Mapping[str, object] | None:
    direct = current_object_identities.get(receiver_semantic_key)
    if direct is not None:
        return direct
    for semantic_key, identity in current_object_identities.items():
        if _function_create_identity_matches_owner_class(
            semantic_key=semantic_key,
            identity=identity,
            receiver_semantic_key=receiver_semantic_key,
            class_name=class_name,
            owner_key=owner_key,
        ):
            return identity
    return None


def _function_create_identity_matches_owner_class(
    *,
    semantic_key: str,
    identity: Mapping[str, object],
    receiver_semantic_key: str,
    class_name: str,
    owner_key: str | None,
) -> bool:
    if semantic_key == receiver_semantic_key:
        return True
    semantic_identity_key = _optional_text(identity.get("semantic_key"))
    if semantic_identity_key == receiver_semantic_key:
        return True
    identity_class_names = {
        item
        for item in (
            _optional_text(identity.get("class_name")),
            _optional_text(identity.get("name")),
            _optional_text(identity.get("entity_name")),
            _terminal_name(_optional_text(identity.get("class_fqn"))),
            _terminal_name(_optional_text(identity.get("node_key"))),
        )
        if item is not None
    }
    if class_name not in identity_class_names:
        return False
    if owner_key is None:
        return True
    identity_owner_keys = {
        item
        for item in (
            _optional_text(identity.get("class_fqn")),
            _optional_text(identity.get("node_key")),
            _optional_text(identity.get("owner_key")),
        )
        if item is not None
    }
    return owner_key in identity_owner_keys or semantic_key.endswith(
        f"/node:{owner_key}",
    )


def _terminal_name(value: str | None) -> str | None:
    if value is None:
        return None
    return value.rsplit(".", maxsplit=1)[-1]


def _function_create_typed_operation_plan(
    *,
    typed_operations: tuple[Mapping[str, object], ...],
    reason: str,
) -> dict[str, object]:
    ready = bool(typed_operations)
    return {
        "plan_kind": "meta_ocg_provider_delta_typed_operation_plan",
        "contract_version": META_PROVIDER_DELTA_TYPED_OPERATION_PLAN_CONTRACT_VERSION,
        "status": (
            "typed_operation_plan_ready" if ready else "typed_operation_plan_blocked"
        ),
        "reason": reason,
        "source": "aware_meta.function.config.semantic_operation_resolution",
        "provider_key": "aware_meta",
        "typed_operation_count": len(typed_operations),
        "semantic_object_anchor_count": 0,
        "blocked_operation_count": 0 if ready else 1,
        "typed_operations": typed_operations,
        "semantic_object_anchors": (),
        "blocked_operations": (),
        "semantic_change_projection_ready": ready,
        "available": ready,
        "blocked": not ready,
        "would_execute": False,
        "did_execute": False,
        "would_persist": False,
        "did_persist": False,
        "execution_wired": False,
        "production_execution_wired": False,
    }


def _function_create_generated_materialization_intent_metadata(
    *,
    typed_operation_plan: Mapping[str, object],
    typed_operation: Mapping[str, object] | None,
    ready: bool,
) -> dict[str, object]:
    blockers: tuple[str, ...] = (
        ("function_create_generated_materialization_typed_plan_unavailable",)
        if not ready
        else ()
    )
    status = (
        "generated_materialization_intent_ready"
        if ready
        else "generated_materialization_intent_blocked"
    )
    reason = (
        "function_create_generated_materialization_intent_ready"
        if ready
        else "function_create_generated_materialization_intent_blocked"
    )
    intent: dict[str, object] = {
        "intent_kind": "meta_function_create_generated_materialization_intent",
        "contract_version": (
            META_FUNCTION_CREATE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION
        ),
        "status": status,
        "reason": reason,
        "generated_materialization_provider_key": "aware_meta",
        "blockers": blockers,
        "provider_delta_typed_operation_plan": dict(typed_operation_plan),
    }
    if ready:
        intent.update(
            generated_materialization_intent_target_metadata(
                policy_key="aware_meta.generated_materialization.function.create",
                materialization_target="function",
            )
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
        if ready:
            metadata["provider_delta_generated_materialization_typed_operation"] = (
                typed_operation_payload
            )
    return metadata


def _function_signature_child_payloads(
    *,
    function_signature: Mapping[str, object],
    child_key: str,
) -> tuple[Mapping[str, object], ...]:
    return tuple(
        _function_signature_contract_payload(_mapping_value(item))
        for item in _tuple_values(function_signature.get(child_key))
        if isinstance(item, Mapping)
    )


def _function_signature_contract_payload(
    payload: Mapping[str, object],
) -> dict[str, object]:
    return dict(payload)


def _resolve_function_delete(
    *,
    operation: Mapping[str, object],
    current_objects: Mapping[str, str],
    current_object_identities: Mapping[str, Mapping[str, object]],
) -> MetaSemanticOperationResolution:
    operation_family = _string_value(operation.get("operation_family"))
    if operation_family != "delete":
        return _blocked_resolution(
            operation=operation,
            reason="meta_ocg_function_delete_requires_delete_family",
            blockers=(
                "unsupported_operation_family:" f"{operation_family or 'unknown'}",
            ),
        )
    subject_type = _string_value(operation.get("semantic_subject_type"))
    if subject_type not in {"FunctionConfig", "aware_meta.FunctionConfig"}:
        return _blocked_resolution(
            operation=operation,
            reason="meta_ocg_function_delete_subject_not_supported",
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
        _class_name_from_semantic_key(semantic_key),
    )
    function_name = _first_text(
        before_payload.get("function_name"),
        before_payload.get("name"),
        after_payload.get("function_name"),
        after_payload.get("name"),
        _function_name_from_semantic_key(semantic_key),
    )
    raw_owner_key = _first_text(
        before_payload.get("owner_key"),
        before_payload.get("class_fqn"),
        after_payload.get("owner_key"),
        after_payload.get("class_fqn"),
        class_name,
    )
    owner_key = _class_fqn_from_package_context(
        class_name=class_name,
        raw_class_fqn=raw_owner_key,
        operation=operation,
    )
    owner_semantic_key = f"meta.class:{class_name}" if class_name is not None else None
    function_identity = current_object_identities.get(semantic_key)
    function_receiver_object_id = current_objects.get(semantic_key)
    function_generated_materialization = (
        _mapping_value(function_identity.get("generated_materialization"))
        if function_identity is not None
        else {}
    )
    class_config_id = _first_text(
        (
            current_objects.get(owner_semantic_key)
            if owner_semantic_key is not None
            else None
        ),
        before_payload.get("class_config_id"),
        before_payload.get("owner_object_id"),
        after_payload.get("class_config_id"),
        after_payload.get("owner_object_id"),
    )
    kind = _first_text(
        before_payload.get("kind"),
        after_payload.get("kind"),
        "instance",
    )
    function_config_id = _first_text(
        operation.get("semantic_source_object_id"),
        before_payload.get("semantic_source_object_id"),
        after_payload.get("semantic_source_object_id"),
        (
            None
            if function_identity is None
            else function_identity.get("semantic_source_object_id")
        ),
        (
            None
            if function_identity is None
            else function_identity.get("source_object_id")
        ),
        before_payload.get("function_config_id"),
        before_payload.get("entity_id"),
        before_payload.get("object_id"),
        after_payload.get("function_config_id"),
        after_payload.get("entity_id"),
        after_payload.get("object_id"),
        current_objects.get(semantic_key),
        _stable_function_config_id_for_create(
            owner_key=owner_key,
            function_name=function_name,
            kind=kind,
        ),
    )
    blockers = tuple(
        blocker
        for blocker, value in (
            ("missing_class_name", class_name),
            ("missing_owner_key", owner_key),
            ("missing_owner_semantic_key", owner_semantic_key),
            ("missing_class_config_id", class_config_id),
            ("missing_function_name", function_name),
            ("missing_function_config_id", function_config_id),
        )
        if value is None
    )
    provider_delta_typed_operation_metadata = (
        _provider_delta_typed_operation_metadata_for_function_delete(
            operation=operation,
            owner_semantic_key=owner_semantic_key,
            class_config_id=class_config_id,
            function_config_id=function_config_id,
            function_receiver_object_id=function_receiver_object_id,
            function_generated_materialization=function_generated_materialization,
            owner_key=owner_key,
            function_name=function_name,
            kind=kind,
        )
    )
    metadata: dict[str, object] = {
        "source": "aware_meta.semantic_operation_resolution",
        "semantic_apply_boundary": "provider_delta_ontology_operation_executor",
        "provider_delta_handler_key": "function.object_config_graph_function_calls",
        "provider_operation_type": "meta_ocg.function.delete",
        "requires_baseline_object_identity": True,
        "requires_owner_semantic_object_identity": True,
        "execution_ready": not blockers,
        "execution_preconditions": ("provider_delta_ontology_operation_executor",),
        "preview_only": True,
        "receiver_semantic_key": owner_semantic_key,
        "receiver_object_id": class_config_id,
        "result_semantic_key": semantic_key,
        "result_object_id": function_config_id,
        **provider_delta_typed_operation_metadata,
    }
    if class_name is not None:
        metadata["class_name"] = class_name
    if owner_key is not None:
        metadata["owner_key"] = owner_key
    if function_name is not None:
        metadata["function_name"] = function_name
    if (
        function_receiver_object_id is not None
        and function_config_id is not None
        and function_receiver_object_id != function_config_id
    ):
        metadata["semantic_apply_receiver_object_id"] = function_receiver_object_id
        metadata["semantic_source_object_id"] = function_config_id
    return _blocked_resolution(
        operation=operation,
        reason=(
            "meta_ocg_function_delete_requires_provider_delta_"
            "ontology_operation_executor"
        ),
        blockers=(
            *blockers,
            "semantic_plan_single_function_call_preview_not_supported",
            "provider_delta_function_delete_operation_executor_required",
        ),
        metadata=metadata,
    )


def _provider_delta_typed_operation_metadata_for_function_delete(
    *,
    operation: Mapping[str, object],
    owner_semantic_key: str | None,
    class_config_id: str | None,
    function_config_id: str | None,
    function_receiver_object_id: str | None,
    function_generated_materialization: Mapping[str, object],
    owner_key: str | None,
    function_name: str | None,
    kind: str | None,
) -> dict[str, object]:
    from aware_meta.materialization.deltas.source_projection import (  # noqa: WPS433,E501
        typed_operation_plan_from_semantic_source_meaning,
    )

    enriched_operation = _function_delete_operation_with_identity(
        operation=operation,
        owner_semantic_key=owner_semantic_key,
        class_config_id=class_config_id,
        function_config_id=function_config_id,
        function_receiver_object_id=function_receiver_object_id,
        function_generated_materialization=function_generated_materialization,
        owner_key=owner_key,
        function_name=function_name,
        kind=kind,
    )
    typed_operation_plan = typed_operation_plan_from_semantic_source_meaning(
        semantic_status={},
        typed_operations=(enriched_operation,),
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
            "function_delete_provider_delta_operation_ready"
            if ready
            else "function_delete_provider_delta_operation_blocked"
        ),
        "provider_delta_typed_operation_plan": typed_operation_plan,
    }
    if typed_operation is not None:
        metadata["provider_delta_typed_operation"] = dict(typed_operation)
    if not ready:
        metadata["provider_delta_typed_operation_blockers"] = (
            "function_delete_provider_delta_typed_operation_unavailable",
        )
    metadata.update(
        _function_delete_generated_materialization_intent_metadata(
            typed_operation_plan=typed_operation_plan,
            typed_operation=typed_operation,
            ready=ready,
        )
    )
    return metadata


def _function_delete_operation_with_identity(
    *,
    operation: Mapping[str, object],
    owner_semantic_key: str | None,
    class_config_id: str | None,
    function_config_id: str | None,
    function_receiver_object_id: str | None,
    function_generated_materialization: Mapping[str, object],
    owner_key: str | None,
    function_name: str | None,
    kind: str | None,
) -> dict[str, object]:
    enriched = dict(operation)
    before_payload = _mapping_value(enriched.get("before_payload"))
    for target in (enriched, before_payload):
        if owner_semantic_key is not None:
            target["owner_semantic_key"] = owner_semantic_key
            target["parent_semantic_key"] = owner_semantic_key
            target["class_semantic_key"] = owner_semantic_key
        if class_config_id is not None:
            target["class_config_id"] = class_config_id
        if function_config_id is not None:
            target["semantic_source_object_id"] = function_config_id
            target["function_config_id"] = function_config_id
            target["entity_id"] = function_config_id
            target["object_id"] = function_config_id
        if (
            function_receiver_object_id is not None
            and function_receiver_object_id != function_config_id
        ):
            target["semantic_apply_receiver_object_id"] = function_receiver_object_id
            target["executable_object_id"] = function_receiver_object_id
        if function_generated_materialization:
            target["generated_materialization"] = dict(
                function_generated_materialization
            )
        if owner_key is not None:
            target["owner_key"] = owner_key
            target["class_fqn"] = owner_key
        if function_name is not None:
            target["function_name"] = function_name
            target["name"] = function_name
            target["entity_name"] = function_name
        if kind is not None:
            target["kind"] = kind
    if before_payload:
        enriched["before_payload"] = before_payload
    return enriched


def _function_delete_generated_materialization_intent_metadata(
    *,
    typed_operation_plan: Mapping[str, object],
    typed_operation: Mapping[str, object] | None,
    ready: bool,
) -> dict[str, object]:
    blockers: tuple[str, ...] = (
        ()
        if ready
        else ("function_delete_generated_materialization_typed_plan_unavailable",)
    )
    status = (
        "generated_materialization_intent_ready"
        if ready
        else "generated_materialization_intent_blocked"
    )
    reason = (
        "function_delete_generated_materialization_intent_ready"
        if ready
        else "function_delete_generated_materialization_intent_blocked"
    )
    intent: dict[str, object] = {
        "intent_kind": "meta_function_delete_generated_materialization_intent",
        "contract_version": (
            META_FUNCTION_DELETE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION
        ),
        "status": status,
        "reason": reason,
        "generated_materialization_provider_key": "aware_meta",
        "blockers": blockers,
        "provider_delta_typed_operation_plan": dict(typed_operation_plan),
    }
    if ready:
        intent.update(
            generated_materialization_intent_target_metadata(
                policy_key="aware_meta.generated_materialization.function.delete",
                materialization_target="function",
            )
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


def _resolve_function_signature_update(
    *,
    operation: Mapping[str, object],
    operation_group: tuple[Mapping[str, object], ...],
    current_objects: Mapping[str, str],
    current_object_identities: Mapping[str, Mapping[str, object]],
) -> MetaSemanticOperationResolution:
    if _string_value(operation.get("operation_family")) not in {"update", "upsert"}:
        return _blocked_resolution(
            operation=operation,
            reason="meta_ocg_function_signature_update_requires_update_family",
            blockers=(
                "unsupported_operation_family:"
                f"{_string_value(operation.get('operation_family')) or 'unknown'}",
            ),
        )
    if _string_value(operation.get("semantic_subject_type")) not in {
        "FunctionConfig",
        "aware_meta.FunctionConfig",
    }:
        return _blocked_resolution(
            operation=operation,
            reason="meta_ocg_function_signature_update_subject_not_supported",
            blockers=(
                "unsupported_semantic_subject_type:"
                f"{_string_value(operation.get('semantic_subject_type')) or 'unknown'}",
            ),
        )
    field_path = _optional_text(operation.get("field_path"))
    if (
        field_path is not None
        and field_path not in _FUNCTION_SIGNATURE_UPDATE_FIELD_PATHS
    ):
        return _blocked_resolution(
            operation=operation,
            reason="meta_ocg_function_signature_update_field_not_supported",
            blockers=("unsupported_field_path:" f"{field_path or 'unknown'}",),
        )

    after_payload = _mapping_value(operation.get("after_payload"))
    semantic_key = _semantic_key(operation)
    if _operation_group_has_function_create(
        operation_group=operation_group,
        semantic_key=semantic_key,
    ):
        return MetaSemanticOperationResolution(
            operation_key=_operation_key(operation),
            semantic_operation_type=_semantic_operation_type(operation),
            semantic_key=semantic_key,
            status="unsupported_operation",
            reason="meta_ocg_function_signature_update_folded_into_create",
            metadata={
                "source": "aware_meta.semantic_operation_resolution",
                "semantic_apply_boundary": "not_applicable",
                "folded_into_operation_type": (
                    META_OBJECT_CONFIG_GRAPH_FUNCTION_CREATE_OPERATION
                ),
                "execution_ready": False,
                "preview_only": True,
            },
        )
    function_name = _first_text(
        after_payload.get("function_name"),
        _function_name_from_semantic_key(semantic_key),
    )
    class_name = _first_text(
        after_payload.get("class_name"),
        _class_name_from_semantic_key(semantic_key),
    )
    receiver_semantic_key = (
        f"meta.function:{class_name}.{function_name}"
        if class_name is not None and function_name is not None
        else semantic_key
    )
    owner_semantic_key = _first_text(
        after_payload.get("owner_semantic_key"),
        after_payload.get("parent_semantic_key"),
        f"meta.class:{class_name}" if class_name is not None else None,
    )
    blockers = tuple(
        blocker
        for blocker, value in (
            ("missing_class_name", class_name),
            ("missing_function_name", function_name),
        )
        if value is None
    )
    before_payload = _mapping_value(operation.get("before_payload"))
    function_receiver_object_id = current_objects.get(receiver_semantic_key)
    function_identity = _function_identity_for_signature_update(
        operation=operation,
        semantic_key=semantic_key,
        receiver_semantic_key=receiver_semantic_key,
        current_object_identities=current_object_identities,
        class_name=class_name,
        function_name=function_name,
    )
    if owner_semantic_key is None:
        owner_semantic_key = _first_text(
            function_identity.get("owner_semantic_key"),
            function_identity.get("parent_semantic_key"),
        )
    is_membership_update = field_path in {
        "class_config_id",
        "function_config_id",
        "is_public",
        "is_constructor",
        "position",
    }
    execution_receiver_semantic_key = (
        owner_semantic_key if is_membership_update else receiver_semantic_key
    )
    current_execution_receiver_object_id = (
        current_objects.get(execution_receiver_semantic_key)
        if execution_receiver_semantic_key is not None
        else None
    )
    execution_receiver_object_id = (
        _first_text(
            current_execution_receiver_object_id,
            function_identity.get("class_config_id"),
        )
        if is_membership_update
        else function_receiver_object_id
    )
    result_semantic_key = (
        _first_text(
            after_payload.get("function_membership_semantic_key"),
            function_identity.get("function_membership_semantic_key"),
            f"{semantic_key}/membership:class_config",
        )
        if is_membership_update
        else semantic_key
    )
    result_object_id = (
        _first_text(
            function_identity.get("class_config_function_config_id"),
            after_payload.get("class_config_function_config_id"),
            before_payload.get("class_config_function_config_id"),
        )
        if is_membership_update
        else function_receiver_object_id
    )
    function_config_id = _first_text(
        after_payload.get("function_config_id"),
        before_payload.get("function_config_id"),
        operation.get("semantic_source_object_id"),
        function_identity.get("function_config_id"),
        function_identity.get("entity_id"),
        function_identity.get("object_id"),
        function_receiver_object_id,
    )
    enriched_operation = _function_signature_update_operation_with_baseline_identity(
        operation=operation,
        function_identity=function_identity,
        function_config_id=function_config_id,
    )
    provider_delta_typed_operation_metadata = (
        provider_delta_typed_operation_metadata_for_signature_update(
            operation=enriched_operation,
            function_config_id=function_config_id,
        )
    )
    typed_operation = _mapping_value(
        provider_delta_typed_operation_metadata.get("provider_delta_typed_operation")
    )
    provider_operation_type = (
        _string_value(typed_operation.get("provider_operation_type"))
        or "meta_ocg.function.update"
    )
    metadata: dict[str, object] = {
        "source": "aware_meta.semantic_operation_resolution",
        "semantic_apply_boundary": "provider_delta_ontology_operation_executor",
        "provider_delta_handler_key": (
            "function_membership.class_config_function_config_calls"
            if is_membership_update
            else "function_config.update_config"
        ),
        "provider_operation_type": provider_operation_type,
        "execution_ready": not blockers and execution_receiver_object_id is not None,
        "execution_preconditions": ("provider_delta_ontology_operation_executor",),
        "preview_only": True,
        "receiver_semantic_key": execution_receiver_semantic_key,
        "receiver_object_id": execution_receiver_object_id,
        "result_semantic_key": result_semantic_key,
        "result_object_id": result_object_id,
        **provider_delta_typed_operation_metadata,
    }
    if class_name is not None:
        metadata["class_name"] = class_name
    if function_name is not None:
        metadata["function_name"] = function_name
    if (
        function_config_id is not None
        and execution_receiver_object_id is not None
        and function_config_id != execution_receiver_object_id
    ):
        metadata["semantic_source_object_id"] = function_config_id
        metadata["semantic_apply_receiver_object_id"] = execution_receiver_object_id
    return _blocked_resolution(
        operation=enriched_operation,
        reason=(
            "meta_ocg_function_signature_update_requires_provider_delta_"
            "ontology_operation_executor"
        ),
        blockers=(
            *blockers,
            "semantic_plan_single_function_call_preview_not_supported",
            "provider_delta_function_update_operation_executor_required",
        ),
        metadata=metadata,
    )


def _operation_group_has_function_create(
    *,
    operation_group: tuple[Mapping[str, object], ...],
    semantic_key: str,
) -> bool:
    for candidate in operation_group:
        if _semantic_key(candidate) != semantic_key:
            continue
        if (
            _semantic_operation_type(candidate)
            == META_OBJECT_CONFIG_GRAPH_FUNCTION_CREATE_OPERATION
        ):
            return True
    return False


def _function_identity_for_signature_update(
    *,
    operation: Mapping[str, object],
    semantic_key: str,
    receiver_semantic_key: str,
    current_object_identities: Mapping[str, Mapping[str, object]],
    class_name: str | None,
    function_name: str | None,
) -> Mapping[str, object]:
    direct_identity = current_object_identities.get(
        receiver_semantic_key
    ) or current_object_identities.get(semantic_key)
    if direct_identity is not None:
        return direct_identity
    matches = tuple(
        identity
        for identity_key, identity in current_object_identities.items()
        if _function_identity_matches_signature_update(
            identity_key=identity_key,
            identity=identity,
            operation=operation,
            class_name=class_name,
            function_name=function_name,
        )
    )
    if len(matches) == 1:
        return matches[0]
    return {}


def _function_identity_matches_signature_update(
    *,
    identity_key: str,
    identity: Mapping[str, object],
    operation: Mapping[str, object],
    class_name: str | None,
    function_name: str | None,
) -> bool:
    if function_name is None:
        return False
    identity_function_name = _first_text(
        identity.get("function_name"),
        identity.get("name"),
        _function_name_from_semantic_key(identity_key),
    )
    if identity_function_name != function_name:
        return False
    if class_name is None:
        return True
    owner_semantic_key = f"meta.class:{class_name}"
    identity_owner_semantic_key = _first_text(
        identity.get("owner_semantic_key"),
        identity.get("parent_semantic_key"),
        identity.get("class_semantic_key"),
    )
    if identity_owner_semantic_key == owner_semantic_key:
        return True
    raw_class_fqn = _first_text(
        identity.get("class_fqn"),
        identity.get("owner_key"),
        _mapping_value(operation.get("after_payload")).get("class_fqn"),
        _mapping_value(operation.get("before_payload")).get("class_fqn"),
    )
    expected_class_fqn = _class_fqn_from_package_context(
        class_name=class_name,
        raw_class_fqn=raw_class_fqn,
        operation=operation,
    )
    identity_class_name = _first_text(
        identity.get("class_name"),
        _last_dotted_token(identity.get("class_fqn")),
        _last_dotted_token(identity.get("owner_key")),
    )
    if identity_class_name == class_name:
        return True
    if expected_class_fqn is None:
        return False
    return identity_key.endswith(f"/node:{expected_class_fqn}/function:{function_name}")


def _last_dotted_token(value: object) -> str | None:
    text = _optional_text(value)
    if text is None:
        return None
    return text.rsplit(".", maxsplit=1)[-1] or None


def _function_signature_update_operation_with_baseline_identity(
    *,
    operation: Mapping[str, object],
    function_identity: Mapping[str, object],
    function_config_id: str | None,
) -> Mapping[str, object]:
    if not function_identity and function_config_id is None:
        return operation
    enriched = dict(operation)
    before_payload = _mapping_value(enriched.get("before_payload"))
    after_payload = _mapping_value(enriched.get("after_payload"))
    enriched_before = dict(before_payload)
    enriched_after = dict(after_payload)
    for payload in (enriched_before, enriched_after):
        for field_name in (
            "class_config_id",
            "class_config_function_config_id",
            "function_membership_semantic_key",
            "function_membership_signature",
            "function_signature",
        ):
            if field_name not in payload and field_name in function_identity:
                payload[field_name] = function_identity[field_name]
        if "function_config_id" not in payload:
            payload["function_config_id"] = (
                function_config_id
                or function_identity.get("function_config_id")
                or function_identity.get("entity_id")
                or function_identity.get("object_id")
            )
    enriched["before_payload"] = enriched_before
    enriched["after_payload"] = enriched_after
    return enriched


def provider_delta_typed_operation_metadata_for_signature_update(
    *,
    operation: Mapping[str, object],
    function_config_id: str | None = None,
) -> dict[str, object]:
    return _root_provider_delta_typed_operation_metadata_for_signature_update(
        operation=operation,
        function_config_id=function_config_id,
    )


__all__ = [
    "provider_delta_typed_operation_metadata_for_signature_update",
    "resolve_function_config_semantic_operation",
]
