from __future__ import annotations

from collections.abc import Mapping

from aware_meta.graph.config.deltas.typed_operations import (
    object_config_graph_identity_create_typed_operation,
    object_config_graph_create_typed_operation,
)
from aware_meta.materialization.deltas.contracts import (
    META_PROVIDER_DELTA_TYPED_OPERATION_PLAN_CONTRACT_VERSION,
)
from aware_meta.semantic_operation_resolution import (
    META_OBJECT_CONFIG_GRAPH_CREATE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_IDENTITY_CREATE_OPERATION,
    MetaSemanticOperationResolution,
    _blocked_resolution,
    _first_text,
    _fqn_prefix_from_package_name,
    _fqn_prefix_from_package_root,
    _mapping_value,
    _optional_text,
    _semantic_key,
    _string_value,
    _tuple_values,
)


def resolve_object_config_graph_semantic_operation(
    *,
    operation: Mapping[str, object],
    operation_group: tuple[Mapping[str, object], ...],
    current_objects: Mapping[str, str],
    current_object_identities: Mapping[str, Mapping[str, object]],
) -> MetaSemanticOperationResolution:
    del operation_group, current_objects, current_object_identities
    operation_type = _string_value(operation.get("semantic_operation_type"))
    if operation_type == META_OBJECT_CONFIG_GRAPH_IDENTITY_CREATE_OPERATION:
        return _resolve_graph_identity_create(operation=operation)
    if operation_type == META_OBJECT_CONFIG_GRAPH_CREATE_OPERATION:
        return _resolve_graph_create(operation=operation)
    return _blocked_resolution(
        operation=operation,
        reason="meta_ocg_graph_operation_type_not_supported",
        blockers=(f"unsupported_operation_type:{operation_type or 'unknown'}",),
    )


def _resolve_graph_identity_create(
    *,
    operation: Mapping[str, object],
) -> MetaSemanticOperationResolution:
    operation_family = _string_value(operation.get("operation_family"))
    if operation_family not in {"create", "upsert"}:
        return _blocked_resolution(
            operation=operation,
            reason="meta_ocg_graph_identity_create_requires_create_family",
            blockers=(
                "unsupported_operation_family:" f"{operation_family or 'unknown'}",
            ),
        )
    subject_type = _string_value(operation.get("semantic_subject_type"))
    if subject_type not in {
        "ObjectConfigGraphIdentity",
        "aware_meta.ObjectConfigGraphIdentity",
    }:
        return _blocked_resolution(
            operation=operation,
            reason="meta_ocg_graph_identity_create_subject_not_supported",
            blockers=(
                "unsupported_semantic_subject_type:" f"{subject_type or 'unknown'}",
            ),
        )

    after_payload = _mapping_value(operation.get("after_payload"))
    fqn_prefix = _first_text(
        after_payload.get("fqn_prefix"),
        operation.get("fqn_prefix"),
        operation.get("source_fqn_prefix"),
        _fqn_prefix_from_package_root(operation.get("package_root")),
        _fqn_prefix_from_package_name(operation.get("package_name")),
    )
    language = _first_text(
        after_payload.get("language"),
        operation.get("language"),
        "aware",
    )
    key = _first_text(
        after_payload.get("key"),
        operation.get("key"),
        _graph_identity_key(fqn_prefix=fqn_prefix, language=language),
    )
    identity_id = _first_text(
        after_payload.get("object_config_graph_identity_id"),
        after_payload.get("entity_id"),
        after_payload.get("object_id"),
        _stable_graph_identity_id_from_key(key=key),
    )
    blockers = tuple(
        blocker
        for blocker, value in (
            ("missing_object_config_graph_identity_key", key),
            ("missing_object_config_graph_identity_id", identity_id),
        )
        if value is None
    )
    typed_operation_plan = _graph_identity_create_typed_operation_plan(
        operation=operation,
        identity_id=identity_id,
        key=key,
    )
    typed_operation = _first_typed_operation(typed_operation_plan)
    metadata: dict[str, object] = {
        "source": "aware_meta.graph.config.semantic_operation_resolution",
        "semantic_apply_boundary": "provider_delta_ontology_operation_executor",
        "provider_delta_handler_key": "object_config_graph_identity.function_calls",
        "provider_operation_type": "meta_ocg.object_config_graph_identity.create",
        "requires_baseline_object_identity": False,
        "execution_ready": not blockers and typed_operation is not None,
        "execution_preconditions": ("provider_delta_ontology_operation_executor",),
        "preview_only": True,
        "receiver_semantic_key": None,
        "receiver_object_id": None,
        "result_semantic_key": _semantic_key(operation),
        "result_object_id": identity_id,
        **_provider_delta_metadata(
            typed_operation_plan=typed_operation_plan,
            typed_operation=typed_operation,
            ready=not blockers and typed_operation is not None,
            ready_reason="graph_identity_create_provider_delta_operation_ready",
            blocked_reason="graph_identity_create_provider_delta_operation_blocked",
            blocked_token="graph_identity_provider_delta_typed_operation_unavailable",
        ),
    }
    if key is not None:
        metadata["object_config_graph_identity_key"] = key
    if fqn_prefix is not None:
        metadata["fqn_prefix"] = fqn_prefix
    if language is not None:
        metadata["language"] = language
    return _blocked_resolution(
        operation=operation,
        reason=(
            "meta_ocg_graph_identity_create_requires_provider_delta_"
            "ontology_operation_executor"
        ),
        blockers=(
            *blockers,
            "semantic_plan_single_function_call_preview_not_supported",
            "provider_delta_graph_identity_create_operation_executor_required",
        ),
        metadata=metadata,
    )


def _resolve_graph_create(
    *,
    operation: Mapping[str, object],
) -> MetaSemanticOperationResolution:
    operation_family = _string_value(operation.get("operation_family"))
    if operation_family not in {"create", "upsert"}:
        return _blocked_resolution(
            operation=operation,
            reason="meta_ocg_graph_create_requires_create_family",
            blockers=(
                "unsupported_operation_family:" f"{operation_family or 'unknown'}",
            ),
        )
    subject_type = _string_value(operation.get("semantic_subject_type"))
    if subject_type not in {
        "ObjectConfigGraph",
        "aware_meta.ObjectConfigGraph",
    }:
        return _blocked_resolution(
            operation=operation,
            reason="meta_ocg_graph_create_subject_not_supported",
            blockers=(
                "unsupported_semantic_subject_type:" f"{subject_type or 'unknown'}",
            ),
        )

    after_payload = _mapping_value(operation.get("after_payload"))
    fqn_prefix = _first_text(
        after_payload.get("fqn_prefix"),
        operation.get("fqn_prefix"),
        operation.get("source_fqn_prefix"),
        _fqn_prefix_from_package_root(operation.get("package_root")),
        _fqn_prefix_from_package_name(operation.get("package_name")),
    )
    language = _first_text(
        after_payload.get("language"),
        operation.get("language"),
        "aware",
    )
    graph_id = _first_text(
        after_payload.get("object_config_graph_id"),
        after_payload.get("graph_id"),
        after_payload.get("entity_id"),
        after_payload.get("object_id"),
        _stable_graph_id(fqn_prefix=fqn_prefix, language=language),
    )
    name = _first_text(
        after_payload.get("name"),
        after_payload.get("graph_name"),
        fqn_prefix,
    )
    graph_hash = _first_text(
        after_payload.get("hash"),
        after_payload.get("graph_hash"),
        "semantic-operation-intent",
    )
    blockers = tuple(
        blocker
        for blocker, value in (
            ("missing_fqn_prefix", fqn_prefix),
            ("missing_language", language),
            ("missing_object_config_graph_id", graph_id),
            ("missing_name", name),
            ("missing_hash", graph_hash),
        )
        if value is None
    )
    typed_operation_plan = _graph_create_typed_operation_plan(
        operation=operation,
        graph_id=graph_id,
        name=name,
        graph_hash=graph_hash,
        fqn_prefix=fqn_prefix,
        language=language,
    )
    typed_operation = _first_typed_operation(typed_operation_plan)
    metadata: dict[str, object] = {
        "source": "aware_meta.graph.config.semantic_operation_resolution",
        "semantic_apply_boundary": "provider_delta_ontology_operation_executor",
        "provider_delta_handler_key": "object_config_graph.function_calls",
        "provider_operation_type": "meta_ocg.object_config_graph.create",
        "requires_baseline_object_identity": False,
        "execution_ready": not blockers and typed_operation is not None,
        "execution_preconditions": ("provider_delta_ontology_operation_executor",),
        "preview_only": True,
        "receiver_semantic_key": None,
        "receiver_object_id": None,
        "result_semantic_key": _semantic_key(operation),
        "result_object_id": graph_id,
        **_provider_delta_metadata(
            typed_operation_plan=typed_operation_plan,
            typed_operation=typed_operation,
            ready=not blockers and typed_operation is not None,
            ready_reason="graph_create_provider_delta_operation_ready",
            blocked_reason="graph_create_provider_delta_operation_blocked",
            blocked_token="graph_provider_delta_typed_operation_unavailable",
        ),
    }
    if fqn_prefix is not None:
        metadata["fqn_prefix"] = fqn_prefix
    if language is not None:
        metadata["language"] = language
    if name is not None:
        metadata["graph_name"] = name
    return _blocked_resolution(
        operation=operation,
        reason=(
            "meta_ocg_graph_create_requires_provider_delta_"
            "ontology_operation_executor"
        ),
        blockers=(
            *blockers,
            "semantic_plan_single_function_call_preview_not_supported",
            "provider_delta_graph_create_operation_executor_required",
        ),
        metadata=metadata,
    )


def _graph_create_typed_operation_plan(
    *,
    operation: Mapping[str, object],
    graph_id: str | None,
    name: str | None,
    graph_hash: str | None,
    fqn_prefix: str | None,
    language: str | None,
) -> dict[str, object]:
    if (
        graph_id is None
        or name is None
        or graph_hash is None
        or fqn_prefix is None
        or language is None
    ):
        return _typed_operation_plan(
            reason="graph_create_typed_operation_requires_identity",
            typed_operations=(),
        )
    after_payload = _mapping_value(operation.get("after_payload"))
    typed_operation = object_config_graph_create_typed_operation(
        fqn_prefix=fqn_prefix,
        semantic_key=_semantic_key(operation),
        object_config_graph_id=graph_id,
        name=name,
        source_refs=_source_refs(operation),
        graph_hash=graph_hash,
        layout_hash=_first_text(after_payload.get("layout_hash")),
        language=language,
        description=_first_text(after_payload.get("description")),
    ).evidence_payload()
    current = _mapping_value(typed_operation.get("current"))
    payload = _mapping_value(current.get("payload"))
    identity_id = _first_text(
        after_payload.get("object_config_graph_identity_id"),
        _stable_graph_identity_id(fqn_prefix=fqn_prefix, language=language),
    )
    if identity_id is not None:
        current["object_config_graph_identity_id"] = identity_id
        payload["object_config_graph_identity_id"] = identity_id
    current["payload"] = payload
    typed_operation["current"] = current
    return _typed_operation_plan(
        reason="graph_create_typed_operation_ready",
        typed_operations=(typed_operation,),
    )


def _graph_identity_create_typed_operation_plan(
    *,
    operation: Mapping[str, object],
    identity_id: str | None,
    key: str | None,
) -> dict[str, object]:
    if identity_id is None or key is None:
        return _typed_operation_plan(
            reason="graph_identity_create_typed_operation_requires_identity",
            typed_operations=(),
        )
    after_payload = _mapping_value(operation.get("after_payload"))
    typed_operation = object_config_graph_identity_create_typed_operation(
        semantic_key=_semantic_key(operation),
        object_config_graph_identity_id=identity_id,
        key=key,
        source_refs=_source_refs(operation),
        label=_first_text(after_payload.get("label")),
    ).evidence_payload()
    return _typed_operation_plan(
        reason="graph_identity_create_typed_operation_ready",
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
        "source": "aware_meta.graph.config.semantic_operation_resolution",
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
    blocked_token: str,
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
        metadata["provider_delta_typed_operation_blockers"] = (blocked_token,)
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


def _stable_graph_id(
    *,
    fqn_prefix: str | None,
    language: str | None,
) -> str | None:
    if fqn_prefix is None or language is None:
        return None
    from aware_meta.graph.config.stable_ids import (  # noqa: WPS433
        stable_object_config_graph_id,
    )

    return str(
        stable_object_config_graph_id(
            fqn_prefix=fqn_prefix,
            language=language,
        )
    )


def _stable_graph_identity_id(
    *,
    fqn_prefix: str,
    language: str,
) -> str:
    from aware_meta.graph.config.stable_ids import (  # noqa: WPS433
        stable_object_config_graph_identity_id,
    )

    return str(
        stable_object_config_graph_identity_id(
            key=f"{fqn_prefix}:{language}",
        )
    )


def _stable_graph_identity_id_from_key(*, key: str | None) -> str | None:
    if key is None:
        return None
    from aware_meta.graph.config.stable_ids import (  # noqa: WPS433
        stable_object_config_graph_identity_id,
    )

    return str(stable_object_config_graph_identity_id(key=key))


def _graph_identity_key(
    *,
    fqn_prefix: str | None,
    language: str | None,
) -> str | None:
    if fqn_prefix is None or language is None:
        return None
    return f"{fqn_prefix}:{language}"


def _source_refs(operation: Mapping[str, object]) -> tuple[str, ...]:
    return tuple(
        source_ref
        for item in _tuple_values(operation.get("source_refs"))
        if (source_ref := _optional_text(item)) is not None
    )


__all__ = [
    "resolve_object_config_graph_semantic_operation",
]
