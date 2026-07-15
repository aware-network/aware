from __future__ import annotations

from collections.abc import Mapping

from aware_meta.graph.package.deltas.typed_operations import (
    object_config_graph_package_attach_graph_typed_operation,
    object_config_graph_package_create_typed_operation,
)
from aware_meta.materialization.deltas.contracts import (
    META_PROVIDER_DELTA_TYPED_OPERATION_PLAN_CONTRACT_VERSION,
)
from aware_meta.semantic_operation_resolution import (
    META_OBJECT_CONFIG_GRAPH_PACKAGE_ATTACH_GRAPH_OPERATION,
    META_OBJECT_CONFIG_GRAPH_PACKAGE_CREATE_OPERATION,
    MetaSemanticOperationResolution,
    _blocked_resolution,
    _first_text,
    _mapping_value,
    _optional_text,
    _semantic_key,
    _string_value,
    _tuple_values,
)


def resolve_object_config_graph_package_semantic_operation(
    *,
    operation: Mapping[str, object],
    operation_group: tuple[Mapping[str, object], ...],
    current_objects: Mapping[str, str],
    current_object_identities: Mapping[str, Mapping[str, object]],
) -> MetaSemanticOperationResolution:
    del operation_group, current_object_identities
    operation_type = _string_value(operation.get("semantic_operation_type"))
    if operation_type == META_OBJECT_CONFIG_GRAPH_PACKAGE_CREATE_OPERATION:
        return _resolve_package_create(operation=operation)
    if operation_type == META_OBJECT_CONFIG_GRAPH_PACKAGE_ATTACH_GRAPH_OPERATION:
        return _resolve_package_attach_graph(
            operation=operation,
            current_objects=current_objects,
        )
    return _blocked_resolution(
        operation=operation,
        reason="meta_ocg_package_operation_type_not_supported",
        blockers=(f"unsupported_operation_type:{operation_type or 'unknown'}",),
    )


def _resolve_package_create(
    *,
    operation: Mapping[str, object],
) -> MetaSemanticOperationResolution:
    operation_family = _string_value(operation.get("operation_family"))
    if operation_family not in {"create", "upsert"}:
        return _blocked_resolution(
            operation=operation,
            reason="meta_ocg_package_create_requires_create_family",
            blockers=(
                "unsupported_operation_family:" f"{operation_family or 'unknown'}",
            ),
        )
    subject_type = _string_value(operation.get("semantic_subject_type"))
    if subject_type not in {
        "ObjectConfigGraphPackage",
        "aware_meta.ObjectConfigGraphPackage",
    }:
        return _blocked_resolution(
            operation=operation,
            reason="meta_ocg_package_create_subject_not_supported",
            blockers=(
                "unsupported_semantic_subject_type:" f"{subject_type or 'unknown'}",
            ),
        )

    after_payload = _mapping_value(operation.get("after_payload"))
    package_name = _first_text(
        after_payload.get("package_name"),
        operation.get("package_name"),
    )
    fqn_prefix = _first_text(
        after_payload.get("fqn_prefix"),
        operation.get("fqn_prefix"),
        operation.get("source_fqn_prefix"),
    )
    package_id = _first_text(
        after_payload.get("object_config_graph_package_id"),
        after_payload.get("package_id"),
        after_payload.get("entity_id"),
        after_payload.get("object_id"),
        _stable_package_id(package_name=package_name, fqn_prefix=fqn_prefix),
    )
    blockers = tuple(
        blocker
        for blocker, value in (
            ("missing_package_name", package_name),
            ("missing_fqn_prefix", fqn_prefix),
            ("missing_object_config_graph_package_id", package_id),
        )
        if value is None
    )
    typed_operation_plan = _package_create_typed_operation_plan(
        operation=operation,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        package_id=package_id,
    )
    typed_operation = _first_typed_operation(typed_operation_plan)
    metadata: dict[str, object] = {
        "source": "aware_meta.graph.package.semantic_operation_resolution",
        "semantic_apply_boundary": "provider_delta_ontology_operation_executor",
        "provider_delta_handler_key": "object_config_graph_package.function_calls",
        "provider_operation_type": "meta_ocg.object_config_graph_package.create",
        "requires_baseline_object_identity": False,
        "execution_ready": not blockers and typed_operation is not None,
        "execution_preconditions": ("provider_delta_ontology_operation_executor",),
        "preview_only": True,
        "receiver_semantic_key": None,
        "receiver_object_id": None,
        "result_semantic_key": _semantic_key(operation),
        "result_object_id": package_id,
        **_provider_delta_metadata(
            typed_operation_plan=typed_operation_plan,
            typed_operation=typed_operation,
            ready=not blockers and typed_operation is not None,
            ready_reason="package_create_provider_delta_operation_ready",
            blocked_reason="package_create_provider_delta_operation_blocked",
        ),
    }
    if package_name is not None:
        metadata["package_name"] = package_name
    if fqn_prefix is not None:
        metadata["fqn_prefix"] = fqn_prefix
    return _blocked_resolution(
        operation=operation,
        reason=(
            "meta_ocg_package_create_requires_provider_delta_"
            "ontology_operation_executor"
        ),
        blockers=(
            *blockers,
            "semantic_plan_single_function_call_preview_not_supported",
            "provider_delta_package_create_operation_executor_required",
        ),
        metadata=metadata,
    )


def _resolve_package_attach_graph(
    *,
    operation: Mapping[str, object],
    current_objects: Mapping[str, str],
) -> MetaSemanticOperationResolution:
    operation_family = _string_value(operation.get("operation_family"))
    if operation_family not in {"update", "upsert"}:
        return _blocked_resolution(
            operation=operation,
            reason="meta_ocg_package_attach_graph_requires_update_family",
            blockers=(
                "unsupported_operation_family:" f"{operation_family or 'unknown'}",
            ),
        )
    subject_type = _string_value(operation.get("semantic_subject_type"))
    if subject_type not in {
        "ObjectConfigGraphPackage",
        "aware_meta.ObjectConfigGraphPackage",
    }:
        return _blocked_resolution(
            operation=operation,
            reason="meta_ocg_package_attach_graph_subject_not_supported",
            blockers=(
                "unsupported_semantic_subject_type:" f"{subject_type or 'unknown'}",
            ),
        )

    after_payload = _mapping_value(operation.get("after_payload"))
    before_payload = _mapping_value(operation.get("before_payload"))
    semantic_key = _semantic_key(operation)
    package_name = _first_text(
        after_payload.get("package_name"),
        before_payload.get("package_name"),
        operation.get("package_name"),
    )
    fqn_prefix = _first_text(
        after_payload.get("fqn_prefix"),
        before_payload.get("fqn_prefix"),
        operation.get("fqn_prefix"),
        operation.get("source_fqn_prefix"),
    )
    package_id = _first_text(
        current_objects.get(semantic_key),
        after_payload.get("object_config_graph_package_id"),
        after_payload.get("package_id"),
        after_payload.get("entity_id"),
        after_payload.get("object_id"),
        before_payload.get("object_config_graph_package_id"),
        before_payload.get("package_id"),
        before_payload.get("entity_id"),
        before_payload.get("object_id"),
        _stable_package_id(package_name=package_name, fqn_prefix=fqn_prefix),
    )
    graph_semantic_key = _first_text(
        after_payload.get("graph_semantic_key"),
        before_payload.get("graph_semantic_key"),
        operation.get("graph_semantic_key"),
    )
    graph_id = _first_text(
        after_payload.get("object_config_graph_id"),
        after_payload.get("graph_object_id"),
        after_payload.get("graph_id"),
        before_payload.get("object_config_graph_id"),
        before_payload.get("graph_object_id"),
        before_payload.get("graph_id"),
        current_objects.get(graph_semantic_key or ""),
    )
    blockers = tuple(
        blocker
        for blocker, value in (
            ("missing_package_name", package_name),
            ("missing_object_config_graph_package_id", package_id),
            ("missing_object_config_graph_id", graph_id),
        )
        if value is None
    )
    typed_operation_plan = _package_attach_graph_typed_operation_plan(
        operation=operation,
        package_name=package_name,
        package_id=package_id,
        graph_id=graph_id,
    )
    typed_operation = _first_typed_operation(typed_operation_plan)
    metadata: dict[str, object] = {
        "source": "aware_meta.graph.package.semantic_operation_resolution",
        "semantic_apply_boundary": "provider_delta_ontology_operation_executor",
        "provider_delta_handler_key": "object_config_graph_package.function_calls",
        "provider_operation_type": "meta_ocg.object_config_graph_package.update",
        "requires_baseline_object_identity": True,
        "execution_ready": not blockers and typed_operation is not None,
        "execution_preconditions": ("provider_delta_ontology_operation_executor",),
        "preview_only": True,
        "receiver_semantic_key": semantic_key,
        "receiver_object_id": package_id,
        "result_semantic_key": semantic_key,
        "result_object_id": package_id,
        **_provider_delta_metadata(
            typed_operation_plan=typed_operation_plan,
            typed_operation=typed_operation,
            ready=not blockers and typed_operation is not None,
            ready_reason="package_attach_graph_provider_delta_operation_ready",
            blocked_reason="package_attach_graph_provider_delta_operation_blocked",
        ),
    }
    if package_name is not None:
        metadata["package_name"] = package_name
    if fqn_prefix is not None:
        metadata["fqn_prefix"] = fqn_prefix
    if graph_semantic_key is not None:
        metadata["graph_semantic_key"] = graph_semantic_key
    if graph_id is not None:
        metadata["object_config_graph_id"] = graph_id
    return _blocked_resolution(
        operation=operation,
        reason=(
            "meta_ocg_package_attach_graph_requires_provider_delta_"
            "ontology_operation_executor"
        ),
        blockers=(
            *blockers,
            "semantic_plan_single_function_call_preview_not_supported",
            "provider_delta_package_attach_graph_operation_executor_required",
        ),
        metadata=metadata,
    )


def _package_create_typed_operation_plan(
    *,
    operation: Mapping[str, object],
    package_name: str | None,
    fqn_prefix: str | None,
    package_id: str | None,
) -> dict[str, object]:
    if package_name is None or fqn_prefix is None or package_id is None:
        return _typed_operation_plan(
            reason="package_create_typed_operation_requires_identity",
            typed_operations=(),
        )
    after_payload = _mapping_value(operation.get("after_payload"))
    typed_operation = object_config_graph_package_create_typed_operation(
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        package_id=package_id,
        semantic_key=_semantic_key(operation),
        source_refs=_source_refs(operation),
        title=_first_text(after_payload.get("title")),
        description=_first_text(after_payload.get("description")),
    ).evidence_payload()
    current = _mapping_value(typed_operation.get("current"))
    payload = _mapping_value(current.get("payload"))
    for key in (
        "source_code_package_id",
        "object_config_graph_id",
        "object_config_graph_object_instance_graph_commit_id",
        "function_impl_ownership",
        "function_impl_parity_policy",
        "implementation_policy_source",
    ):
        value = _first_text(after_payload.get(key))
        if value is not None:
            current[key] = value
            payload[key] = value
    current["payload"] = payload
    typed_operation["current"] = current
    return _typed_operation_plan(
        reason="package_create_typed_operation_ready",
        typed_operations=(typed_operation,),
    )


def _package_attach_graph_typed_operation_plan(
    *,
    operation: Mapping[str, object],
    package_name: str | None,
    package_id: str | None,
    graph_id: str | None,
) -> dict[str, object]:
    if package_name is None or package_id is None or graph_id is None:
        return _typed_operation_plan(
            reason="package_attach_graph_typed_operation_requires_identity",
            typed_operations=(),
        )
    after_payload = _mapping_value(operation.get("after_payload"))
    typed_operation = object_config_graph_package_attach_graph_typed_operation(
        package_name=package_name,
        package_id=package_id,
        object_config_graph_id=graph_id,
        semantic_key=_semantic_key(operation),
        source_refs=_source_refs(operation),
        title=_first_text(after_payload.get("title")),
        description=_first_text(after_payload.get("description")),
    ).evidence_payload()
    current = _mapping_value(typed_operation.get("current"))
    payload = _mapping_value(current.get("payload"))
    commit_id = _first_text(
        after_payload.get("object_config_graph_object_instance_graph_commit_id")
    )
    if commit_id is not None:
        current["object_config_graph_object_instance_graph_commit_id"] = commit_id
        payload["object_config_graph_object_instance_graph_commit_id"] = commit_id
    current["payload"] = payload
    typed_operation["current"] = current
    return _typed_operation_plan(
        reason="package_attach_graph_typed_operation_ready",
        typed_operations=(typed_operation,),
    )


def _typed_operation_plan(
    *,
    reason: str,
    typed_operations: tuple[Mapping[str, object], ...],
) -> dict[str, object]:
    ready = bool(typed_operations)
    return {
        "plan_kind": "meta_ocg_provider_delta_typed_operation_plan",
        "contract_version": META_PROVIDER_DELTA_TYPED_OPERATION_PLAN_CONTRACT_VERSION,
        "status": (
            "typed_operation_plan_ready" if ready else "typed_operation_plan_blocked"
        ),
        "reason": reason,
        "source": "aware_meta.graph.package.semantic_operation_resolution",
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


def _provider_delta_metadata(
    *,
    typed_operation_plan: Mapping[str, object],
    typed_operation: Mapping[str, object] | None,
    ready: bool,
    ready_reason: str,
    blocked_reason: str,
) -> dict[str, object]:
    metadata: dict[str, object] = {
        "provider_delta_typed_operation_status": (
            "provider_delta_typed_operation_ready"
            if ready
            else "provider_delta_typed_operation_blocked"
        ),
        "provider_delta_typed_operation_reason": (
            ready_reason if ready else blocked_reason
        ),
        "provider_delta_typed_operation_plan": dict(typed_operation_plan),
    }
    if typed_operation is not None:
        metadata["provider_delta_typed_operation"] = dict(typed_operation)
    if not ready:
        metadata["provider_delta_typed_operation_blockers"] = (
            "package_provider_delta_typed_operation_unavailable",
        )
    return metadata


def _first_typed_operation(
    typed_operation_plan: Mapping[str, object],
) -> Mapping[str, object] | None:
    return next(
        (
            item
            for item in _tuple_values(typed_operation_plan.get("typed_operations"))
            if isinstance(item, Mapping)
        ),
        None,
    )


def _stable_package_id(
    *,
    package_name: str | None,
    fqn_prefix: str | None,
) -> str | None:
    if package_name is None or fqn_prefix is None:
        return None
    from aware_meta_ontology.stable_ids import (  # noqa: WPS433
        stable_object_config_graph_package_id,
    )

    return str(
        stable_object_config_graph_package_id(
            package_name=package_name,
            fqn_prefix=fqn_prefix,
        )
    )


def _source_refs(operation: Mapping[str, object]) -> tuple[str, ...]:
    return tuple(
        source_ref
        for item in _tuple_values(operation.get("source_refs"))
        if (source_ref := _optional_text(item)) is not None
    )


__all__ = [
    "resolve_object_config_graph_package_semantic_operation",
]
