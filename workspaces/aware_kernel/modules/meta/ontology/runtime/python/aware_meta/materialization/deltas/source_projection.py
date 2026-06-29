from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from hashlib import sha256
from pathlib import Path
from typing import Any, cast

from aware_meta.materialization.deltas.code_dto import (
    CodeGrammarAnchorBinding,
    CodeGrammarAnchorRenderSource,
    CodeSectionDeltaEntry,
    CodeSectionDeltaSet,
    CodeSourceProjectionActionBinding,
    CodeSourceProjectionEventRef,
    CodeSourceProjectionRequest,
    CodeSourceProjectionResult,
    CodeSourceProjectionSkippedEvent,
    ResolveCodeGrammarAnchorRenderDeltaRequest,
)
from aware_meta.materialization.deltas.coercion import (
    mapping_value,
    optional_text,
    tuple_text,
)
from aware_meta.materialization.deltas.change_evidence_contracts import (
    MetaProviderDeltaSemanticChangeReport,
    MetaProviderDeltaSemanticWorldChange,
)
from aware_meta.materialization.deltas.change_evidence import (
    _provider_delta_semantic_change_report,
)
from aware_meta.enum.config.deltas.operation_normalization import (
    coalesced_enum_aggregate_delete_source_operations,
)
from aware_meta.class_.config.deltas.operation_normalization import (
    coalesced_class_aggregate_delete_source_operations,
    coalesced_class_create_update_source_operations,
)
from aware_meta.class_.config.deltas.typed_operations import (
    class_config_create_typed_operation,
    class_config_delete_typed_operation,
)
from aware_meta.attribute.config.deltas.typed_operations import (
    attribute_config_create_typed_operation,
)
from aware_meta.function.config.deltas.typed_operations import (
    function_config_delete_typed_operation,
)
from aware_meta.materialization.deltas.feature_contracts import (
    MetaProviderDeltaSourceProjectionContext,
    MetaProviderDeltaSourceProjectionFeatureResult,
)
from aware_meta.materialization.deltas.feature_registry import (
    source_projection_feature_results_from_typed_operation,
)
from aware_meta.materialization.deltas.typed_operation_contracts import (
    MetaProviderDeltaTypedOperationPlan,
)
from aware_types import JsonObject


META_SOURCE_PROJECTION_PROVIDER_KEY = "aware_meta"
META_SOURCE_PROJECTION_PRODUCT_INTENT = "meta_ocg_source_projection"
META_SOURCE_PROJECTION_POLICY_PREFIX = "aware_meta.ocg.source_projection"
META_PROVIDER_DELTA_SOURCE_PROJECTION_CONTRACT_VERSION = (
    "aware.meta.ocg.provider-delta-source-projection.v1"
)
META_SEMANTIC_APPLY_SOURCE_PROJECTION_EVIDENCE_CONTRACT_VERSION = (
    "aware.meta.semantic-apply-source-projection-evidence.v1"
)
META_OBJECT_CONFIG_GRAPH_CLASS_DESCRIPTION_UPDATE_OPERATION = (
    "aware_meta.object_config_graph.class.description.update"
)
META_OBJECT_CONFIG_GRAPH_CLASS_CREATE_OPERATION = (
    "aware_meta.object_config_graph.class.create"
)
META_OBJECT_CONFIG_GRAPH_CLASS_DELETE_OPERATION = (
    "aware_meta.object_config_graph.class.delete"
)
META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_CREATE_OPERATION = (
    "aware_meta.object_config_graph.attribute.create"
)
META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_DELETE_OPERATION = (
    "aware_meta.object_config_graph.attribute.delete"
)
META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_IDENTITY_RENAME_OPERATION = (
    "aware_meta.object_config_graph.attribute.identity.rename"
)
META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_MEMBERSHIP_UPDATE_OPERATION = (
    "aware_meta.object_config_graph.attribute.membership.update"
)
META_OBJECT_CONFIG_GRAPH_CLASS_IDENTITY_RENAME_OPERATION = (
    "aware_meta.object_config_graph.class.identity.rename"
)
META_OBJECT_CONFIG_GRAPH_ENUM_DESCRIPTION_UPDATE_OPERATION = (
    "aware_meta.object_config_graph.enum.description.update"
)
META_OBJECT_CONFIG_GRAPH_ENUM_CREATE_OPERATION = (
    "aware_meta.object_config_graph.enum.create"
)
META_OBJECT_CONFIG_GRAPH_ENUM_DELETE_OPERATION = (
    "aware_meta.object_config_graph.enum.delete"
)
META_OBJECT_CONFIG_GRAPH_ENUM_IDENTITY_RENAME_OPERATION = (
    "aware_meta.object_config_graph.enum.identity.rename"
)
META_OBJECT_CONFIG_GRAPH_ENUM_OPTION_CREATE_OPERATION = (
    "aware_meta.object_config_graph.enum_option.create"
)
META_OBJECT_CONFIG_GRAPH_ENUM_OPTION_POSITION_UPDATE_OPERATION = (
    "aware_meta.object_config_graph.enum_option.position.update"
)
META_OBJECT_CONFIG_GRAPH_ENUM_OPTION_DELETE_OPERATION = (
    "aware_meta.object_config_graph.enum_option.delete"
)
META_OBJECT_CONFIG_GRAPH_FUNCTION_CREATE_OPERATION = (
    "aware_meta.object_config_graph.function.create"
)
META_OBJECT_CONFIG_GRAPH_FUNCTION_DELETE_OPERATION = (
    "aware_meta.object_config_graph.function.delete"
)
META_OBJECT_CONFIG_GRAPH_FUNCTION_SIGNATURE_UPDATE_OPERATION = (
    "aware_meta.object_config_graph.function.signature.update"
)
META_OBJECT_CONFIG_GRAPH_RELATIONSHIP_LOAD_POLICY_UPDATE_OPERATION = (
    "aware_meta.object_config_graph.relationship.load_policy.update"
)
META_OBJECT_CONFIG_GRAPH_RELATIONSHIP_CREATE_OPERATION = (
    "aware_meta.object_config_graph.relationship.create"
)
META_OBJECT_CONFIG_GRAPH_RELATIONSHIP_DELETE_OPERATION = (
    "aware_meta.object_config_graph.relationship.delete"
)


def provider_delta_source_projection_stage(
    *,
    package_payload: Mapping[str, object],
    manifest_path: Path,
    current_delta_fingerprint: str,
    provider_delta_semantic_change_report: Mapping[str, object],
    provider_delta_typed_operation_plan: Mapping[str, object],
    code_package_delta: object | None = None,
) -> dict[str, object]:
    """Build Meta provider-local source-projection evidence for Workspace/Code."""

    report = MetaProviderDeltaSemanticChangeReport.from_payload(
        provider_delta_semantic_change_report
    )
    typed_plan = MetaProviderDeltaTypedOperationPlan.from_payload(
        provider_delta_typed_operation_plan
    )
    if not report.ready:
        return _provider_delta_source_projection_blocked_stage(
            reason="meta_source_projection_semantic_change_report_not_ready",
            current_delta_fingerprint=current_delta_fingerprint,
            report=report,
            typed_plan=typed_plan,
        )
    if typed_plan.status != "typed_operation_plan_ready":
        return _provider_delta_source_projection_blocked_stage(
            reason="meta_source_projection_typed_operation_plan_not_ready",
            current_delta_fingerprint=current_delta_fingerprint,
            report=report,
            typed_plan=typed_plan,
        )

    projection = code_source_projection_request_from_meta_change_report(
        report,
        package_name=_source_projection_package_name(
            package_payload=package_payload,
            code_package_delta=code_package_delta,
        ),
        package_root=_source_projection_package_root(
            manifest_path=manifest_path,
            code_package_delta=code_package_delta,
        ),
        sources_root=_source_projection_sources_root(
            code_package_delta=code_package_delta,
        ),
        target_language=_source_projection_target_language(
            code_package_delta=code_package_delta,
        ),
        source_refs=_source_projection_delta_source_refs(
            code_package_delta=code_package_delta,
        ),
        require_ready=False,
    )
    feature_results = source_projection_feature_results_from_meta_typed_operations(
        provider_delta_typed_operation_plan,
        package_name=projection.package_name,
        package_root=projection.package_root,
        sources_root=projection.sources_root,
        target_language=projection.target_language,
        require_ready=False,
    )
    result = code_source_projection_result_from_meta_feature_results(
        report,
        projection=projection,
        feature_results=feature_results,
        diagnostics=_source_projection_feature_diagnostics(feature_results),
        require_ready=False,
        require_projected=False,
    )
    grammar_anchor_render_delta_request = (
        code_grammar_anchor_render_delta_request_from_meta_feature_results(
            projection=projection,
            feature_results=feature_results,
        )
    )
    projected_entry_count = sum(len(item.entries) for item in feature_results)
    grammar_anchor_binding_count = sum(
        len(item.grammar_anchor_bindings) for item in feature_results
    )
    grammar_anchor_source_count = sum(
        len(item.grammar_anchor_sources) for item in feature_results
    )
    grammar_anchor_replacement_count = sum(
        len(item.grammar_anchor_replacements) for item in feature_results
    )
    blocked_count = sum(1 for item in feature_results if item.blocked)
    skipped_count = sum(
        1 for item in feature_results if item.status == "source_projection_skipped"
    )
    status, reason = _provider_delta_source_projection_status_and_reason(
        projected_entry_count=projected_entry_count,
        grammar_anchor_replacement_count=grammar_anchor_replacement_count,
        blocked_count=blocked_count,
        skipped_count=skipped_count,
        feature_result_count=len(feature_results),
    )
    return {
        "stage_kind": "meta_ocg_provider_delta_source_projection",
        "contract_version": META_PROVIDER_DELTA_SOURCE_PROJECTION_CONTRACT_VERSION,
        "status": status,
        "reason": reason,
        "available": True,
        "ready": status == "source_projection_ready",
        "blocked": status == "source_projection_blocked",
        "projected": result.projected,
        "provider_key": META_SOURCE_PROJECTION_PROVIDER_KEY,
        "current_delta_fingerprint": current_delta_fingerprint,
        "change_count": len(projection.events),
        "action_count": len(projection.action_bindings),
        "feature_result_count": len(feature_results),
        "projected_entry_count": projected_entry_count,
        "grammar_anchor_binding_count": grammar_anchor_binding_count,
        "grammar_anchor_source_count": grammar_anchor_source_count,
        "grammar_anchor_replacement_count": grammar_anchor_replacement_count,
        "blocked_feature_result_count": blocked_count,
        "skipped_feature_result_count": skipped_count,
        "skipped_change_count": len(result.skipped_events),
        "diagnostics": tuple(result.diagnostics),
        "projection": projection.model_dump(mode="json"),
        "result": result.model_dump(mode="json"),
        "grammar_anchor_render_delta_request": (
            grammar_anchor_render_delta_request.model_dump(mode="json")
            if grammar_anchor_render_delta_request is not None
            else None
        ),
        "feature_results": tuple(item.evidence_payload() for item in feature_results),
    }


def provider_delta_result_from_semantic_apply_source_projection_evidence(
    *,
    semantic_status: Mapping[str, object],
    semantic_apply: Mapping[str, object],
    package_name: str,
    package_root: str,
    sources_root: str | None = None,
    target_language: str = "aware",
    source_refs: Sequence[str] = (),
    source_text_by_ref: Mapping[str, str] | None = None,
    source_session_context: Mapping[str, object] | None = None,
    commit_ids: Sequence[str] = (),
    head_commit_ids: Sequence[str] = (),
    current_delta_fingerprint: str | None = None,
    baseline_semantic_object_index: (
        Mapping[str, Mapping[str, object]] | None
    ) = None,
    metadata: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Build provider_delta source_projection evidence from semantic_apply output."""

    typed_operations = tuple(
        _semantic_source_typed_operations(semantic_status=semantic_status)
    )
    if baseline_semantic_object_index:
        typed_operations = _semantic_source_operations_with_baseline_index(
            operations=typed_operations,
            baseline_semantic_object_index=baseline_semantic_object_index,
        )
    resolved_source_refs = _semantic_apply_source_refs(
        semantic_status=semantic_status,
        source_refs=source_refs,
        source_text_by_ref=source_text_by_ref,
        typed_operations=typed_operations,
    )
    typed_plan = typed_operation_plan_from_semantic_source_meaning(
        semantic_status=semantic_status,
        default_source_refs=resolved_source_refs,
        typed_operations=typed_operations,
    )
    report = _provider_delta_semantic_change_report(
        semantic_dirty_diff={
            "status": "semantic_dirty_diff_ready",
            "reason": "semantic_apply_source_projection_evidence",
            "dirty_entry_count": len(typed_operations),
        },
        provider_delta_typed_operation_plan=typed_plan,
    )
    source_delta_fingerprint = (
        current_delta_fingerprint
        or optional_text((source_session_context or {}).get("source_delta_fingerprint"))
        or _semantic_status_delta_fingerprint(semantic_status=semantic_status)
        or _source_text_fingerprint(source_text_by_ref or {})
    )
    stage = provider_delta_source_projection_stage(
        package_payload={"package_name": package_name},
        manifest_path=Path(package_root) / "aware.toml",
        current_delta_fingerprint=source_delta_fingerprint,
        provider_delta_semantic_change_report=report,
        provider_delta_typed_operation_plan=typed_plan,
        code_package_delta={
            "package_name": package_name,
            "package_root": package_root,
            "sources_root": sources_root,
            "paths": tuple(
                {
                    "relative_path": source_ref,
                    "language": target_language,
                }
                for source_ref in resolved_source_refs
            ),
        },
    )
    stage = _semantic_apply_source_projection_stage_with_context(
        stage=stage,
        semantic_apply=semantic_apply,
        source_text_by_ref=source_text_by_ref or {},
        source_session_context=source_session_context,
        commit_ids=commit_ids,
        head_commit_ids=head_commit_ids,
        metadata=metadata,
    )
    return {
        "semantic_contract": {
            "provider_key": META_SOURCE_PROJECTION_PROVIDER_KEY,
            "semantic_owner": "aware_meta.provider",
        },
        "package": {"package_name": package_name},
        "current_delta_fingerprint": source_delta_fingerprint,
        "semantic_source_session_context": dict(source_session_context or {}),
        "metadata": {
            "contract_version": (
                META_SEMANTIC_APPLY_SOURCE_PROJECTION_EVIDENCE_CONTRACT_VERSION
            ),
            "source": "aware_meta.semantic_apply.source_projection_evidence",
            "semantic_apply_status": semantic_apply.get("status"),
            "semantic_apply_commit_ids": tuple(commit_ids),
            "semantic_apply_head_commit_ids": tuple(head_commit_ids),
            "caller_metadata": (
                {str(key): value for key, value in metadata.items()} if metadata else {}
            ),
        },
        "details": {
            "provider_delta_source_projection": stage,
        },
    }


def _semantic_source_operations_with_baseline_index(
    *,
    operations: Sequence[Mapping[str, object]],
    baseline_semantic_object_index: Mapping[str, Mapping[str, object]],
) -> tuple[Mapping[str, object], ...]:
    return tuple(
        _semantic_source_operation_with_baseline_index(
            operation=operation,
            baseline_semantic_object_index=baseline_semantic_object_index,
        )
        for operation in operations
    )


def _semantic_source_operation_with_baseline_index(
    *,
    operation: Mapping[str, object],
    baseline_semantic_object_index: Mapping[str, Mapping[str, object]],
) -> Mapping[str, object]:
    if (
        optional_text(operation.get("semantic_operation_type"))
        != META_OBJECT_CONFIG_GRAPH_FUNCTION_SIGNATURE_UPDATE_OPERATION
    ):
        return operation
    identity = _function_baseline_identity_for_semantic_source_operation(
        operation=operation,
        baseline_semantic_object_index=baseline_semantic_object_index,
    )
    if not identity:
        return operation
    enriched = dict(operation)
    before_payload = dict(mapping_value(enriched.get("before_payload")))
    after_payload = dict(mapping_value(enriched.get("after_payload")))
    for payload in (before_payload, after_payload):
        _enrich_function_payload_with_baseline_identity(
            payload=payload,
            identity=identity,
        )
    enriched["before_payload"] = before_payload
    enriched["after_payload"] = after_payload
    semantic_source_object_id = _first_text(
        identity.get("semantic_source_object_id"),
        identity.get("function_config_id"),
        identity.get("entity_id"),
        identity.get("object_id"),
    )
    if semantic_source_object_id is not None:
        enriched.setdefault("semantic_source_object_id", semantic_source_object_id)
    semantic_apply_receiver_object_id = _first_text(
        identity.get("semantic_apply_receiver_object_id"),
        identity.get("executable_object_id"),
    )
    if semantic_apply_receiver_object_id is not None:
        enriched.setdefault(
            "semantic_apply_receiver_object_id",
            semantic_apply_receiver_object_id,
        )
    return enriched


def _function_baseline_identity_for_semantic_source_operation(
    *,
    operation: Mapping[str, object],
    baseline_semantic_object_index: Mapping[str, Mapping[str, object]],
) -> Mapping[str, object]:
    semantic_key = optional_text(operation.get("semantic_key")) or ""
    direct_identity = baseline_semantic_object_index.get(semantic_key)
    if direct_identity is not None:
        return direct_identity
    after_payload = mapping_value(operation.get("after_payload"))
    before_payload = mapping_value(operation.get("before_payload"))
    function_name = _first_text(
        after_payload.get("function_name"),
        before_payload.get("function_name"),
        _function_name_from_semantic_key(semantic_key),
    )
    class_name = _first_text(
        after_payload.get("class_name"),
        before_payload.get("class_name"),
        _function_class_from_semantic_key(semantic_key),
    )
    matches = tuple(
        identity
        for identity_key, identity in baseline_semantic_object_index.items()
        if _function_baseline_identity_matches(
            identity_key=identity_key,
            identity=identity,
            class_name=class_name,
            function_name=function_name,
        )
    )
    if len(matches) == 1:
        return matches[0]
    return {}


def _function_baseline_identity_matches(
    *,
    identity_key: str,
    identity: Mapping[str, object],
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
    if _first_text(identity.get("class_name")) == class_name:
        return True
    owner_semantic_key = f"meta.class:{class_name}"
    identity_owner_semantic_key = _first_text(
        identity.get("owner_semantic_key"),
        identity.get("parent_semantic_key"),
        identity.get("class_semantic_key"),
    )
    if identity_owner_semantic_key == owner_semantic_key:
        return True
    identity_class_name = _first_text(
        _last_dotted_token(identity.get("class_fqn")),
        _last_dotted_token(identity.get("owner_key")),
        _function_class_from_semantic_key(identity_key),
    )
    return identity_class_name == class_name


def _enrich_function_payload_with_baseline_identity(
    *,
    payload: dict[str, object],
    identity: Mapping[str, object],
) -> None:
    for field_name in (
        "class_config_id",
        "class_config_function_config_id",
        "function_config_id",
        "function_membership_semantic_key",
        "owner_semantic_key",
        "parent_semantic_key",
        "class_semantic_key",
        "class_fqn",
        "owner_key",
    ):
        if field_name not in payload and field_name in identity:
            payload[field_name] = identity[field_name]
    identity_membership_signature = mapping_value(
        identity.get("function_membership_signature")
    )
    payload_membership_signature = mapping_value(
        payload.get("function_membership_signature")
    )
    if identity_membership_signature or payload_membership_signature:
        payload["function_membership_signature"] = {
            **identity_membership_signature,
            **payload_membership_signature,
        }


def _last_dotted_token(value: object) -> str | None:
    text = optional_text(value)
    if text is None:
        return None
    return text.rsplit(".", maxsplit=1)[-1] or None


def typed_operation_plan_from_semantic_source_meaning(
    *,
    semantic_status: Mapping[str, object],
    default_source_refs: Sequence[str] = (),
    typed_operations: Sequence[Mapping[str, object]] | None = None,
) -> dict[str, object]:
    operations: list[dict[str, object]] = []
    blocked_operations: list[dict[str, object]] = []
    semantic_source_operations = _coalesced_semantic_source_operations(
        typed_operations
        if typed_operations is not None
        else _semantic_source_typed_operations(semantic_status=semantic_status)
    )
    for operation in semantic_source_operations:
        for provider_operation in _provider_operations_from_semantic_source_operation(
            operation
        ):
            if _semantic_source_operation_requires_explicit_fallback(
                provider_operation
            ):
                blocked_operations.append(
                    _blocked_semantic_source_operation(
                        provider_operation,
                        reason=_semantic_source_operation_explicit_fallback_reason(
                            provider_operation
                        ),
                    )
                )
                continue
            operations.append(
                _meta_typed_operation_from_semantic_source_operation(
                    provider_operation,
                    default_source_refs=default_source_refs,
                )
            )
    status = (
        "typed_operation_plan_blocked"
        if blocked_operations
        else (
            "typed_operation_plan_ready"
            if operations
            else "typed_operation_plan_blocked"
        )
    )
    reason = (
        "semantic_apply_source_projection_blocked_operations"
        if blocked_operations
        else (
            "semantic_apply_source_projection_from_semantic_source_meaning"
            if operations
            else "semantic_apply_source_projection_no_typed_operations"
        )
    )
    return {
        "status": status,
        "reason": reason,
        "typed_operations": [] if blocked_operations else operations,
        "semantic_object_anchors": [],
        "blocked_operations": blocked_operations,
    }


def _coalesced_semantic_source_operations(
    operations: Sequence[Mapping[str, object]],
) -> tuple[Mapping[str, object], ...]:
    return coalesced_class_aggregate_delete_source_operations(
        operations=coalesced_class_create_update_source_operations(
            operations=coalesced_enum_aggregate_delete_source_operations(
                operations=tuple(operations),
            ),
        ),
    )


def _provider_operations_from_semantic_source_operation(
    operation: Mapping[str, object],
) -> tuple[Mapping[str, object], ...]:
    if _is_class_identity_rename_operation(operation):
        composed_operations = _composed_class_identity_rename_operations(operation)
        if composed_operations is None:
            return (operation,)
        return composed_operations
    if _is_attribute_identity_rename_operation(operation):
        composed_operations = _composed_attribute_identity_rename_operations(operation)
        if composed_operations is None:
            return (operation,)
        return composed_operations
    if not _is_enum_identity_rename_operation(operation):
        return (operation,)
    composed_operations = _composed_enum_identity_rename_operations(operation)
    if composed_operations is None:
        return (operation,)
    return composed_operations


def _composed_class_identity_rename_operations(
    operation: Mapping[str, object],
) -> tuple[Mapping[str, object], Mapping[str, object]] | None:
    if _class_identity_rename_composition_blockers(operation):
        return None
    before_payload = mapping_value(operation.get("before_payload"))
    after_payload = mapping_value(operation.get("after_payload"))
    graph_semantic_key = _class_identity_rename_graph_semantic_key(
        operation=operation,
        before_payload=before_payload,
        after_payload=after_payload,
    )
    old_name = _class_identity_rename_before_name(before_payload=before_payload)
    new_name = _class_identity_rename_after_name(after_payload=after_payload)
    assert graph_semantic_key is not None
    assert old_name is not None
    assert new_name is not None
    old_semantic_key = _class_identity_rename_before_semantic_key(
        operation=operation,
        before_payload=before_payload,
        old_name=old_name,
    )
    new_semantic_key = _class_identity_rename_after_semantic_key(
        operation=operation,
        after_payload=after_payload,
        new_name=new_name,
    )
    assert old_semantic_key is not None
    assert new_semantic_key is not None
    source_refs = tuple_text(operation.get("source_refs"))
    delete_before_payload = dict(before_payload)
    delete_before_payload.setdefault("name", old_name)
    delete_before_payload.setdefault("class_name", old_name)
    delete_before_payload.setdefault("graph_semantic_key", graph_semantic_key)
    create_after_payload = dict(after_payload)
    create_after_payload.setdefault("name", new_name)
    create_after_payload.setdefault("class_name", new_name)
    create_after_payload.setdefault("graph_semantic_key", graph_semantic_key)
    return (
        {
            **dict(operation),
            "operation_key": _class_identity_rename_composed_operation_key(
                operation=operation,
                suffix="delete_old",
            ),
            "operation_family": "delete",
            "semantic_operation_type": META_OBJECT_CONFIG_GRAPH_CLASS_DELETE_OPERATION,
            "semantic_key": old_semantic_key,
            "event_key": _class_identity_rename_composed_event_key(
                operation=operation,
                suffix="delete_old",
            ),
            "source_refs": source_refs,
            "before_payload": delete_before_payload,
            "after_payload": None,
            "graph_semantic_key": graph_semantic_key,
            "composition": {
                "composition_kind": "class_identity_rename_delete_create",
                "composition_part": "delete_old",
                "source_operation_key": optional_text(operation.get("operation_key")),
                "rename_semantic_key": optional_text(operation.get("semantic_key")),
                "old_semantic_key": old_semantic_key,
                "new_semantic_key": new_semantic_key,
            },
        },
        {
            **dict(operation),
            "operation_key": _class_identity_rename_composed_operation_key(
                operation=operation,
                suffix="create_new",
            ),
            "operation_family": "create",
            "semantic_operation_type": META_OBJECT_CONFIG_GRAPH_CLASS_CREATE_OPERATION,
            "semantic_key": new_semantic_key,
            "event_key": _class_identity_rename_composed_event_key(
                operation=operation,
                suffix="create_new",
            ),
            "source_refs": source_refs,
            "before_payload": None,
            "after_payload": create_after_payload,
            "graph_semantic_key": graph_semantic_key,
            "composition": {
                "composition_kind": "class_identity_rename_delete_create",
                "composition_part": "create_new",
                "source_operation_key": optional_text(operation.get("operation_key")),
                "rename_semantic_key": optional_text(operation.get("semantic_key")),
                "old_semantic_key": old_semantic_key,
                "new_semantic_key": new_semantic_key,
            },
        },
    )


def _class_identity_rename_composition_blockers(
    operation: Mapping[str, object],
) -> tuple[str, ...]:
    before_payload = mapping_value(operation.get("before_payload"))
    after_payload = mapping_value(operation.get("after_payload"))
    graph_semantic_key = _class_identity_rename_graph_semantic_key(
        operation=operation,
        before_payload=before_payload,
        after_payload=after_payload,
    )
    blockers: list[str] = []
    for field_name, value in (
        (
            "before_name",
            _class_identity_rename_before_name(before_payload=before_payload),
        ),
        ("after_name", _class_identity_rename_after_name(after_payload=after_payload)),
        ("graph_semantic_key", graph_semantic_key),
        (
            "before_object_config_graph_node_id",
            _first_text(
                before_payload.get("object_config_graph_node_id"),
                before_payload.get("node_id"),
            ),
        ),
    ):
        if value is None:
            blockers.append(f"class_identity_rename_missing_{field_name}")
    return tuple(blockers)


def _class_identity_rename_graph_semantic_key(
    *,
    operation: Mapping[str, object],
    before_payload: Mapping[str, object],
    after_payload: Mapping[str, object],
) -> str | None:
    return _first_text(
        before_payload.get("graph_semantic_key"),
        after_payload.get("graph_semantic_key"),
        operation.get("graph_semantic_key"),
        _graph_semantic_key_from_class_semantic_key(
            optional_text(operation.get("semantic_key")) or ""
        ),
    )


def _class_identity_rename_before_name(
    *,
    before_payload: Mapping[str, object],
) -> str | None:
    return _first_text(before_payload.get("class_name"), before_payload.get("name"))


def _class_identity_rename_after_name(
    *,
    after_payload: Mapping[str, object],
) -> str | None:
    return _first_text(after_payload.get("class_name"), after_payload.get("name"))


def _class_identity_rename_before_semantic_key(
    *,
    operation: Mapping[str, object],
    before_payload: Mapping[str, object],
    old_name: str,
) -> str | None:
    return _first_text(
        before_payload.get("semantic_key"),
        mapping_value(operation.get("metadata")).get("before_semantic_key"),
        f"meta.class:{old_name}",
    )


def _class_identity_rename_after_semantic_key(
    *,
    operation: Mapping[str, object],
    after_payload: Mapping[str, object],
    new_name: str,
) -> str | None:
    return _first_text(
        after_payload.get("semantic_key"),
        mapping_value(operation.get("metadata")).get("after_semantic_key"),
        operation.get("semantic_key"),
        f"meta.class:{new_name}",
    )


def _class_identity_rename_composed_operation_key(
    *,
    operation: Mapping[str, object],
    suffix: str,
) -> str:
    operation_key = optional_text(operation.get("operation_key"))
    if operation_key is not None:
        return f"{operation_key}:{suffix}"
    return f"aware_meta.object_config_graph.class.identity.rename:{suffix}"


def _class_identity_rename_composed_event_key(
    *,
    operation: Mapping[str, object],
    suffix: str,
) -> str | None:
    event_key = optional_text(operation.get("event_key"))
    if event_key is None:
        return None
    return f"{event_key}:{suffix}"


def _composed_attribute_identity_rename_operations(
    operation: Mapping[str, object],
) -> tuple[Mapping[str, object], Mapping[str, object]] | None:
    if _attribute_identity_rename_composition_blockers(operation):
        return None
    before_payload = mapping_value(operation.get("before_payload"))
    after_payload = mapping_value(operation.get("after_payload"))
    old_class_name = _attribute_identity_rename_before_class_name(
        before_payload=before_payload,
        after_payload=after_payload,
    )
    new_class_name = _attribute_identity_rename_after_class_name(
        before_payload=before_payload,
        after_payload=after_payload,
    )
    old_attribute_name = _attribute_identity_rename_before_attribute_name(
        before_payload=before_payload,
    )
    new_attribute_name = _attribute_identity_rename_after_attribute_name(
        after_payload=after_payload,
    )
    assert old_class_name is not None
    assert new_class_name is not None
    assert old_attribute_name is not None
    assert new_attribute_name is not None
    old_semantic_key = _attribute_identity_rename_before_semantic_key(
        operation=operation,
        before_payload=before_payload,
        old_class_name=old_class_name,
        old_attribute_name=old_attribute_name,
    )
    new_semantic_key = _attribute_identity_rename_after_semantic_key(
        operation=operation,
        after_payload=after_payload,
        new_class_name=new_class_name,
        new_attribute_name=new_attribute_name,
    )
    assert old_semantic_key is not None
    assert new_semantic_key is not None
    source_refs = tuple_text(operation.get("source_refs"))
    delete_before_payload = dict(before_payload)
    delete_before_payload.setdefault("class_name", old_class_name)
    delete_before_payload.setdefault("attribute_name", old_attribute_name)
    delete_before_payload.setdefault("name", old_attribute_name)
    create_after_payload = {**dict(before_payload), **dict(after_payload)}
    create_after_payload.setdefault("class_name", new_class_name)
    create_after_payload["attribute_name"] = new_attribute_name
    create_after_payload["name"] = new_attribute_name
    create_after_payload.pop("attribute_config_id", None)
    create_after_payload.pop("entity_id", None)
    return (
        {
            **dict(operation),
            "operation_key": _attribute_identity_rename_composed_operation_key(
                operation=operation,
                suffix="delete_old",
            ),
            "operation_family": "delete",
            "semantic_operation_type": (
                META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_DELETE_OPERATION
            ),
            "semantic_key": old_semantic_key,
            "event_key": _attribute_identity_rename_composed_event_key(
                operation=operation,
                suffix="delete_old",
            ),
            "source_refs": source_refs,
            "before_payload": delete_before_payload,
            "after_payload": None,
            "composition": {
                "composition_kind": "attribute_identity_rename_delete_create",
                "composition_part": "delete_old",
                "source_operation_key": optional_text(operation.get("operation_key")),
                "rename_semantic_key": optional_text(operation.get("semantic_key")),
                "old_semantic_key": old_semantic_key,
                "new_semantic_key": new_semantic_key,
            },
        },
        {
            **dict(operation),
            "operation_key": _attribute_identity_rename_composed_operation_key(
                operation=operation,
                suffix="create_new",
            ),
            "operation_family": "create",
            "semantic_operation_type": (
                META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_CREATE_OPERATION
            ),
            "semantic_key": new_semantic_key,
            "event_key": _attribute_identity_rename_composed_event_key(
                operation=operation,
                suffix="create_new",
            ),
            "source_refs": source_refs,
            "before_payload": None,
            "after_payload": create_after_payload,
            "composition": {
                "composition_kind": "attribute_identity_rename_delete_create",
                "composition_part": "create_new",
                "source_operation_key": optional_text(operation.get("operation_key")),
                "rename_semantic_key": optional_text(operation.get("semantic_key")),
                "old_semantic_key": old_semantic_key,
                "new_semantic_key": new_semantic_key,
            },
        },
    )


def _attribute_identity_rename_composition_blockers(
    operation: Mapping[str, object],
) -> tuple[str, ...]:
    before_payload = mapping_value(operation.get("before_payload"))
    after_payload = mapping_value(operation.get("after_payload"))
    blockers: list[str] = []
    for field_name, value in (
        (
            "before_class_name",
            _attribute_identity_rename_before_class_name(
                before_payload=before_payload,
                after_payload=after_payload,
            ),
        ),
        (
            "after_class_name",
            _attribute_identity_rename_after_class_name(
                before_payload=before_payload,
                after_payload=after_payload,
            ),
        ),
        (
            "before_attribute_name",
            _attribute_identity_rename_before_attribute_name(
                before_payload=before_payload,
            ),
        ),
        (
            "after_attribute_name",
            _attribute_identity_rename_after_attribute_name(
                after_payload=after_payload,
            ),
        ),
        (
            "before_attribute_config_id",
            _first_text(
                before_payload.get("attribute_config_id"),
                before_payload.get("entity_id"),
            ),
        ),
    ):
        if value is None:
            blockers.append(f"attribute_identity_rename_missing_{field_name}")
    return tuple(blockers)


def _attribute_identity_rename_before_class_name(
    *,
    before_payload: Mapping[str, object],
    after_payload: Mapping[str, object],
) -> str | None:
    return _first_text(before_payload.get("class_name"), after_payload.get("class_name"))


def _attribute_identity_rename_after_class_name(
    *,
    before_payload: Mapping[str, object],
    after_payload: Mapping[str, object],
) -> str | None:
    return _first_text(after_payload.get("class_name"), before_payload.get("class_name"))


def _attribute_identity_rename_before_attribute_name(
    *,
    before_payload: Mapping[str, object],
) -> str | None:
    return _first_text(
        before_payload.get("attribute_name"),
        before_payload.get("name"),
    )


def _attribute_identity_rename_after_attribute_name(
    *,
    after_payload: Mapping[str, object],
) -> str | None:
    return _first_text(after_payload.get("attribute_name"), after_payload.get("name"))


def _attribute_identity_rename_before_semantic_key(
    *,
    operation: Mapping[str, object],
    before_payload: Mapping[str, object],
    old_class_name: str,
    old_attribute_name: str,
) -> str | None:
    return _first_text(
        before_payload.get("semantic_key"),
        mapping_value(operation.get("metadata")).get("before_semantic_key"),
        f"meta.attribute:{old_class_name}.{old_attribute_name}",
    )


def _attribute_identity_rename_after_semantic_key(
    *,
    operation: Mapping[str, object],
    after_payload: Mapping[str, object],
    new_class_name: str,
    new_attribute_name: str,
) -> str | None:
    return _first_text(
        after_payload.get("semantic_key"),
        mapping_value(operation.get("metadata")).get("after_semantic_key"),
        operation.get("semantic_key"),
        f"meta.attribute:{new_class_name}.{new_attribute_name}",
    )


def _attribute_identity_rename_composed_operation_key(
    *,
    operation: Mapping[str, object],
    suffix: str,
) -> str:
    operation_key = optional_text(operation.get("operation_key"))
    if operation_key is not None:
        return f"{operation_key}:{suffix}"
    return f"aware_meta.object_config_graph.attribute.identity.rename:{suffix}"


def _attribute_identity_rename_composed_event_key(
    *,
    operation: Mapping[str, object],
    suffix: str,
) -> str | None:
    event_key = optional_text(operation.get("event_key"))
    if event_key is None:
        return None
    return f"{event_key}:{suffix}"


def _composed_enum_identity_rename_operations(
    operation: Mapping[str, object],
) -> tuple[Mapping[str, object], Mapping[str, object]] | None:
    if _enum_identity_rename_composition_blockers(operation):
        return None
    before_payload = mapping_value(operation.get("before_payload"))
    after_payload = mapping_value(operation.get("after_payload"))
    graph_semantic_key = _enum_identity_rename_graph_semantic_key(
        operation=operation,
        before_payload=before_payload,
        after_payload=after_payload,
    )
    old_name = _enum_identity_rename_before_name(before_payload=before_payload)
    new_name = _enum_identity_rename_after_name(after_payload=after_payload)
    assert graph_semantic_key is not None
    assert old_name is not None
    assert new_name is not None
    old_semantic_key = _enum_identity_rename_before_semantic_key(
        operation=operation,
        before_payload=before_payload,
        old_name=old_name,
    )
    new_semantic_key = _enum_identity_rename_after_semantic_key(
        operation=operation,
        after_payload=after_payload,
        new_name=new_name,
    )
    assert old_semantic_key is not None
    assert new_semantic_key is not None
    source_refs = tuple_text(operation.get("source_refs"))
    delete_before_payload = dict(before_payload)
    delete_before_payload.setdefault("name", old_name)
    delete_before_payload.setdefault("enum_name", old_name)
    delete_before_payload.setdefault("graph_semantic_key", graph_semantic_key)
    create_after_payload = dict(after_payload)
    create_after_payload.setdefault("name", new_name)
    create_after_payload.setdefault("enum_name", new_name)
    create_after_payload.setdefault("graph_semantic_key", graph_semantic_key)
    return (
        {
            **dict(operation),
            "operation_key": _enum_identity_rename_composed_operation_key(
                operation=operation,
                suffix="delete_old",
            ),
            "operation_family": "delete",
            "semantic_operation_type": META_OBJECT_CONFIG_GRAPH_ENUM_DELETE_OPERATION,
            "semantic_key": old_semantic_key,
            "event_key": _enum_identity_rename_composed_event_key(
                operation=operation,
                suffix="delete_old",
            ),
            "source_refs": source_refs,
            "before_payload": delete_before_payload,
            "after_payload": None,
            "graph_semantic_key": graph_semantic_key,
            "composition": {
                "composition_kind": "enum_identity_rename_delete_create",
                "composition_part": "delete_old",
                "source_operation_key": optional_text(operation.get("operation_key")),
                "rename_semantic_key": optional_text(operation.get("semantic_key")),
                "old_semantic_key": old_semantic_key,
                "new_semantic_key": new_semantic_key,
            },
        },
        {
            **dict(operation),
            "operation_key": _enum_identity_rename_composed_operation_key(
                operation=operation,
                suffix="create_new",
            ),
            "operation_family": "create",
            "semantic_operation_type": META_OBJECT_CONFIG_GRAPH_ENUM_CREATE_OPERATION,
            "semantic_key": new_semantic_key,
            "event_key": _enum_identity_rename_composed_event_key(
                operation=operation,
                suffix="create_new",
            ),
            "source_refs": source_refs,
            "before_payload": None,
            "after_payload": create_after_payload,
            "graph_semantic_key": graph_semantic_key,
            "composition": {
                "composition_kind": "enum_identity_rename_delete_create",
                "composition_part": "create_new",
                "source_operation_key": optional_text(operation.get("operation_key")),
                "rename_semantic_key": optional_text(operation.get("semantic_key")),
                "old_semantic_key": old_semantic_key,
                "new_semantic_key": new_semantic_key,
            },
        },
    )


def _enum_identity_rename_composition_blockers(
    operation: Mapping[str, object],
) -> tuple[str, ...]:
    before_payload = mapping_value(operation.get("before_payload"))
    after_payload = mapping_value(operation.get("after_payload"))
    graph_semantic_key = _enum_identity_rename_graph_semantic_key(
        operation=operation,
        before_payload=before_payload,
        after_payload=after_payload,
    )
    blockers: list[str] = []
    for field_name, value in (
        (
            "before_name",
            _enum_identity_rename_before_name(before_payload=before_payload),
        ),
        ("after_name", _enum_identity_rename_after_name(after_payload=after_payload)),
        ("graph_semantic_key", graph_semantic_key),
        (
            "before_object_config_graph_node_id",
            _first_text(
                before_payload.get("object_config_graph_node_id"),
                before_payload.get("node_id"),
            ),
        ),
    ):
        if value is None:
            blockers.append(f"enum_identity_rename_missing_{field_name}")
    return tuple(blockers)


def _enum_identity_rename_graph_semantic_key(
    *,
    operation: Mapping[str, object],
    before_payload: Mapping[str, object],
    after_payload: Mapping[str, object],
) -> str | None:
    return _first_text(
        before_payload.get("graph_semantic_key"),
        after_payload.get("graph_semantic_key"),
        operation.get("graph_semantic_key"),
        _graph_semantic_key_from_enum_semantic_key(
            optional_text(operation.get("semantic_key")) or ""
        ),
    )


def _enum_identity_rename_before_name(
    *,
    before_payload: Mapping[str, object],
) -> str | None:
    return _first_text(before_payload.get("enum_name"), before_payload.get("name"))


def _enum_identity_rename_after_name(
    *,
    after_payload: Mapping[str, object],
) -> str | None:
    return _first_text(after_payload.get("enum_name"), after_payload.get("name"))


def _enum_identity_rename_before_semantic_key(
    *,
    operation: Mapping[str, object],
    before_payload: Mapping[str, object],
    old_name: str,
) -> str | None:
    return _first_text(
        before_payload.get("semantic_key"),
        mapping_value(operation.get("metadata")).get("before_semantic_key"),
        f"meta.enum:{old_name}",
    )


def _enum_identity_rename_after_semantic_key(
    *,
    operation: Mapping[str, object],
    after_payload: Mapping[str, object],
    new_name: str,
) -> str | None:
    return _first_text(
        after_payload.get("semantic_key"),
        mapping_value(operation.get("metadata")).get("after_semantic_key"),
        operation.get("semantic_key"),
        f"meta.enum:{new_name}",
    )


def _enum_identity_rename_composed_operation_key(
    *,
    operation: Mapping[str, object],
    suffix: str,
) -> str:
    operation_key = optional_text(operation.get("operation_key"))
    if operation_key is not None:
        return f"{operation_key}:{suffix}"
    return f"aware_meta.object_config_graph.enum.identity.rename:{suffix}"


def _enum_identity_rename_composed_event_key(
    *,
    operation: Mapping[str, object],
    suffix: str,
) -> str | None:
    event_key = optional_text(operation.get("event_key"))
    if event_key is None:
        return None
    return f"{event_key}:{suffix}"


def _semantic_source_operation_requires_explicit_fallback(
    operation: Mapping[str, object],
) -> bool:
    return (
        _is_class_identity_rename_operation(operation)
        or _is_class_identity_scalar_update_operation(operation)
        or _is_attribute_identity_rename_operation(operation)
        or _is_attribute_identity_scalar_update_operation(operation)
        or _is_enum_identity_rename_operation(operation)
        or _is_enum_identity_scalar_update_operation(operation)
    )


def _semantic_source_operation_explicit_fallback_reason(
    operation: Mapping[str, object],
) -> str:
    if _is_class_identity_rename_operation(
        operation
    ) or _is_class_identity_scalar_update_operation(operation):
        return "meta_class_identity_rename_requires_explicit_policy"
    if _is_attribute_identity_rename_operation(
        operation
    ) or _is_attribute_identity_scalar_update_operation(operation):
        return "meta_attribute_identity_rename_requires_explicit_policy"
    if _is_enum_identity_rename_operation(
        operation
    ) or _is_enum_identity_scalar_update_operation(operation):
        return "meta_enum_identity_rename_requires_explicit_policy"
    return "meta_enum_option_reorder_delete_requires_explicit_fallback"


def _is_class_identity_rename_operation(
    operation: Mapping[str, object],
) -> bool:
    semantic_operation_type = optional_text(operation.get("semantic_operation_type"))
    operation_family = optional_text(operation.get("operation_family"))
    semantic_subject_type = optional_text(operation.get("semantic_subject_type"))
    field_path = optional_text(operation.get("field_path"))
    return semantic_operation_type == (
        META_OBJECT_CONFIG_GRAPH_CLASS_IDENTITY_RENAME_OPERATION
    ) or (
        semantic_subject_type == "aware_meta.ClassConfig"
        and operation_family == "rename"
        and field_path in {None, "name", "identity"}
    )


def _is_class_identity_scalar_update_operation(
    operation: Mapping[str, object],
) -> bool:
    semantic_subject_type = optional_text(operation.get("semantic_subject_type"))
    operation_family = optional_text(operation.get("operation_family"))
    field_path = optional_text(operation.get("field_path"))
    return (
        semantic_subject_type == "aware_meta.ClassConfig"
        and operation_family == "update"
        and field_path in {"name", "identity"}
    )


def _is_attribute_identity_rename_operation(
    operation: Mapping[str, object],
) -> bool:
    semantic_operation_type = optional_text(operation.get("semantic_operation_type"))
    operation_family = optional_text(operation.get("operation_family"))
    semantic_subject_type = optional_text(operation.get("semantic_subject_type"))
    field_path = optional_text(operation.get("field_path"))
    return semantic_operation_type == (
        META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_IDENTITY_RENAME_OPERATION
    ) or (
        semantic_subject_type == "aware_meta.AttributeConfig"
        and operation_family == "rename"
        and field_path in {None, "name", "identity"}
    )


def _is_attribute_identity_scalar_update_operation(
    operation: Mapping[str, object],
) -> bool:
    semantic_subject_type = optional_text(operation.get("semantic_subject_type"))
    operation_family = optional_text(operation.get("operation_family"))
    field_path = optional_text(operation.get("field_path"))
    return (
        semantic_subject_type == "aware_meta.AttributeConfig"
        and operation_family == "update"
        and field_path in {"name", "identity"}
    )


def _is_enum_identity_rename_operation(
    operation: Mapping[str, object],
) -> bool:
    semantic_operation_type = optional_text(operation.get("semantic_operation_type"))
    operation_family = optional_text(operation.get("operation_family"))
    semantic_subject_type = optional_text(operation.get("semantic_subject_type"))
    field_path = optional_text(operation.get("field_path"))
    return semantic_operation_type == (
        META_OBJECT_CONFIG_GRAPH_ENUM_IDENTITY_RENAME_OPERATION
    ) or (
        semantic_subject_type == "aware_meta.EnumConfig"
        and operation_family == "rename"
        and field_path in {None, "name", "identity"}
    )


def _is_enum_identity_scalar_update_operation(
    operation: Mapping[str, object],
) -> bool:
    semantic_subject_type = optional_text(operation.get("semantic_subject_type"))
    operation_family = optional_text(operation.get("operation_family"))
    field_path = optional_text(operation.get("field_path"))
    return (
        semantic_subject_type == "aware_meta.EnumConfig"
        and operation_family == "update"
        and field_path in {"name", "identity"}
    )


def _blocked_semantic_source_operation(
    operation: Mapping[str, object],
    *,
    reason: str,
) -> dict[str, object]:
    if (
        reason == "meta_class_identity_rename_requires_explicit_policy"
        and _is_class_identity_rename_operation(operation)
    ):
        rename_blockers = _class_identity_rename_composition_blockers(operation)
        if rename_blockers:
            blockers = (*rename_blockers, "explicit_fallback_required")
        else:
            blockers = (
                "class_identity_rename_requires_delete_create_policy",
                "class_identity_must_not_use_scalar_update",
                "explicit_fallback_required",
            )
    elif (
        reason == "meta_class_identity_rename_requires_explicit_policy"
        and _is_class_identity_scalar_update_operation(operation)
    ):
        blockers = (
            "class_identity_must_not_use_scalar_update",
            "explicit_fallback_required",
        )
    elif (
        reason == "meta_attribute_identity_rename_requires_explicit_policy"
        and _is_attribute_identity_rename_operation(operation)
    ):
        rename_blockers = _attribute_identity_rename_composition_blockers(operation)
        if rename_blockers:
            blockers = (*rename_blockers, "explicit_fallback_required")
        else:
            blockers = (
                "attribute_identity_rename_requires_delete_create_policy",
                "attribute_identity_must_not_use_scalar_update",
                "explicit_fallback_required",
            )
    elif (
        reason == "meta_attribute_identity_rename_requires_explicit_policy"
        and _is_attribute_identity_scalar_update_operation(operation)
    ):
        blockers = (
            "attribute_identity_must_not_use_scalar_update",
            "explicit_fallback_required",
        )
    elif (
        reason == "meta_enum_identity_rename_requires_explicit_policy"
        and _is_enum_identity_rename_operation(operation)
    ):
        rename_blockers = _enum_identity_rename_composition_blockers(operation)
        if rename_blockers:
            blockers = (*rename_blockers, "explicit_fallback_required")
        else:
            blockers = (
                "enum_identity_rename_requires_delete_create_policy",
                "enum_identity_must_not_use_scalar_update",
                "explicit_fallback_required",
            )
    elif (
        reason == "meta_enum_identity_rename_requires_explicit_policy"
        and _is_enum_identity_scalar_update_operation(operation)
    ):
        blockers = (
            "enum_identity_must_not_use_scalar_update",
            "explicit_fallback_required",
        )
    else:
        blockers = (
            "enum_option_reorder_delete_renderer_policy_missing",
            "explicit_fallback_required",
        )
    return {
        "operation_key": optional_text(operation.get("operation_key")),
        "semantic_operation_type": optional_text(
            operation.get("semantic_operation_type")
        ),
        "semantic_key": optional_text(operation.get("semantic_key")),
        "operation_family": optional_text(operation.get("operation_family")),
        "reason": reason,
        "blockers": blockers,
        "semantic_source_operation": dict(operation),
    }


def _semantic_source_typed_operations(
    *,
    semantic_status: Mapping[str, object],
) -> tuple[Mapping[str, object], ...]:
    packages = tuple(
        mapping_value(package)
        for package in _object_sequence(semantic_status.get("packages"))
    )
    operations: list[Mapping[str, object]] = []
    for package in packages or (semantic_status,):
        package_context = _semantic_source_package_context(package)
        source_meaning = mapping_value(package.get("semantic_source_meaning"))
        operations.extend(
            _semantic_source_operation_with_package_context(
                operation=mapping_value(operation),
                package_context=package_context,
            )
            for operation in _object_sequence(source_meaning.get("typed_operations"))
        )
        if operations:
            continue
        change_preview = mapping_value(package.get("change_preview"))
        operations.extend(
            _semantic_source_operation_with_package_context(
                operation=mapping_value(operation),
                package_context=package_context,
            )
            for operation in _object_sequence(change_preview.get("typed_operations"))
        )
    return tuple(operation for operation in operations if operation)


def _semantic_source_package_context(
    package: Mapping[str, object],
) -> dict[str, object]:
    metadata = mapping_value(package.get("semantic_package_metadata"))
    fqn_prefix = _first_text(
        package.get("fqn_prefix"),
        package.get("source_fqn_prefix"),
        metadata.get("fqn_prefix"),
        _fqn_prefix_from_package_root(package.get("package_root")),
        _fqn_prefix_from_package_name(package.get("package_name")),
    )
    graph_semantic_key = _first_text(
        package.get("graph_semantic_key"),
        metadata.get("graph_semantic_key"),
        f"ocg:{fqn_prefix}" if fqn_prefix is not None else None,
    )
    return {
        "package_name": optional_text(package.get("package_name")),
        "package_root": optional_text(package.get("package_root")),
        "manifest_relative_path": optional_text(package.get("manifest_relative_path")),
        "fqn_prefix": fqn_prefix,
        "graph_semantic_key": graph_semantic_key,
    }


def _semantic_source_operation_with_package_context(
    *,
    operation: Mapping[str, object],
    package_context: Mapping[str, object],
) -> Mapping[str, object]:
    if not package_context:
        return operation
    semantic_operation_type = optional_text(operation.get("semantic_operation_type"))
    graph_semantic_key = optional_text(package_context.get("graph_semantic_key"))
    fqn_prefix = optional_text(package_context.get("fqn_prefix"))
    if (
        semantic_operation_type
        not in {
            META_OBJECT_CONFIG_GRAPH_CLASS_CREATE_OPERATION,
            META_OBJECT_CONFIG_GRAPH_CLASS_DELETE_OPERATION,
            META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_CREATE_OPERATION,
            META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_DELETE_OPERATION,
            META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_IDENTITY_RENAME_OPERATION,
            META_OBJECT_CONFIG_GRAPH_CLASS_IDENTITY_RENAME_OPERATION,
            META_OBJECT_CONFIG_GRAPH_ENUM_CREATE_OPERATION,
            META_OBJECT_CONFIG_GRAPH_ENUM_IDENTITY_RENAME_OPERATION,
            META_OBJECT_CONFIG_GRAPH_ENUM_DELETE_OPERATION,
        }
        or graph_semantic_key is None
    ):
        return operation
    after_payload = mapping_value(operation.get("after_payload"))
    enriched_after_payload = dict(after_payload)
    enriched_after_payload.setdefault("graph_semantic_key", graph_semantic_key)
    enriched_operation: dict[str, object] = dict(operation)
    enriched_operation["after_payload"] = enriched_after_payload
    enriched_operation["graph_semantic_key"] = graph_semantic_key
    if semantic_operation_type in {
        META_OBJECT_CONFIG_GRAPH_CLASS_IDENTITY_RENAME_OPERATION,
        META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_IDENTITY_RENAME_OPERATION,
        META_OBJECT_CONFIG_GRAPH_ENUM_IDENTITY_RENAME_OPERATION,
    }:
        before_payload = mapping_value(operation.get("before_payload"))
        enriched_before_payload = dict(before_payload)
        enriched_before_payload.setdefault("graph_semantic_key", graph_semantic_key)
        enriched_operation["before_payload"] = enriched_before_payload
    if fqn_prefix is not None:
        enriched_operation["fqn_prefix"] = fqn_prefix
    for key in ("package_name", "package_root", "manifest_relative_path"):
        value = optional_text(package_context.get(key))
        if value is not None:
            enriched_operation[key] = value
    return enriched_operation


def _meta_typed_operation_from_semantic_source_operation(
    operation: Mapping[str, object],
    *,
    default_source_refs: Sequence[str],
) -> dict[str, object]:
    semantic_key = optional_text(operation.get("semantic_key")) or ""
    semantic_operation_type = optional_text(operation.get("semantic_operation_type"))
    if semantic_operation_type == META_OBJECT_CONFIG_GRAPH_FUNCTION_CREATE_OPERATION:
        return _meta_function_create_typed_operation_from_semantic_source_operation(
            operation,
            default_source_refs=default_source_refs,
            semantic_key=semantic_key,
        )
    if semantic_operation_type == META_OBJECT_CONFIG_GRAPH_FUNCTION_DELETE_OPERATION:
        return _meta_function_delete_typed_operation_from_semantic_source_operation(
            operation,
            default_source_refs=default_source_refs,
            semantic_key=semantic_key,
        )
    if semantic_operation_type == META_OBJECT_CONFIG_GRAPH_CLASS_CREATE_OPERATION:
        return _meta_class_create_typed_operation_from_semantic_source_operation(
            operation,
            default_source_refs=default_source_refs,
            semantic_key=semantic_key,
        )
    if semantic_operation_type == META_OBJECT_CONFIG_GRAPH_CLASS_DELETE_OPERATION:
        return _meta_class_delete_typed_operation_from_semantic_source_operation(
            operation,
            default_source_refs=default_source_refs,
            semantic_key=semantic_key,
        )
    if semantic_operation_type == META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_CREATE_OPERATION:
        return _meta_attribute_create_typed_operation_from_semantic_source_operation(
            operation,
            default_source_refs=default_source_refs,
            semantic_key=semantic_key,
        )
    if semantic_operation_type == META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_DELETE_OPERATION:
        return _meta_attribute_delete_typed_operation_from_semantic_source_operation(
            operation,
            default_source_refs=default_source_refs,
            semantic_key=semantic_key,
        )
    if (
        semantic_operation_type
        == META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_MEMBERSHIP_UPDATE_OPERATION
    ):
        return _meta_attribute_membership_update_typed_operation_from_semantic_source_operation(
            operation,
            default_source_refs=default_source_refs,
            semantic_key=semantic_key,
        )
    if (
        semantic_operation_type
        == META_OBJECT_CONFIG_GRAPH_FUNCTION_SIGNATURE_UPDATE_OPERATION
    ):
        return _meta_function_update_typed_operation_from_semantic_source_operation(
            operation,
            default_source_refs=default_source_refs,
            semantic_key=semantic_key,
        )
    if (
        semantic_operation_type
        == META_OBJECT_CONFIG_GRAPH_CLASS_DESCRIPTION_UPDATE_OPERATION
    ):
        return _meta_class_update_typed_operation_from_semantic_source_operation(
            operation,
            default_source_refs=default_source_refs,
            semantic_key=semantic_key,
        )
    if (
        semantic_operation_type
        == META_OBJECT_CONFIG_GRAPH_ENUM_DESCRIPTION_UPDATE_OPERATION
    ):
        return _meta_enum_update_typed_operation_from_semantic_source_operation(
            operation,
            default_source_refs=default_source_refs,
            semantic_key=semantic_key,
        )
    if semantic_operation_type == META_OBJECT_CONFIG_GRAPH_ENUM_CREATE_OPERATION:
        return _meta_enum_create_typed_operation_from_semantic_source_operation(
            operation,
            default_source_refs=default_source_refs,
            semantic_key=semantic_key,
        )
    if semantic_operation_type == META_OBJECT_CONFIG_GRAPH_ENUM_DELETE_OPERATION:
        return _meta_enum_delete_typed_operation_from_semantic_source_operation(
            operation,
            default_source_refs=default_source_refs,
            semantic_key=semantic_key,
        )
    if semantic_operation_type == META_OBJECT_CONFIG_GRAPH_ENUM_OPTION_CREATE_OPERATION:
        return _meta_enum_option_create_typed_operation_from_semantic_source_operation(
            operation,
            default_source_refs=default_source_refs,
            semantic_key=semantic_key,
        )
    if (
        semantic_operation_type
        == META_OBJECT_CONFIG_GRAPH_ENUM_OPTION_POSITION_UPDATE_OPERATION
    ):
        return _meta_enum_option_update_typed_operation_from_semantic_source_operation(
            operation,
            default_source_refs=default_source_refs,
            semantic_key=semantic_key,
        )
    if semantic_operation_type == META_OBJECT_CONFIG_GRAPH_ENUM_OPTION_DELETE_OPERATION:
        return _meta_enum_option_delete_typed_operation_from_semantic_source_operation(
            operation,
            default_source_refs=default_source_refs,
            semantic_key=semantic_key,
        )
    if (
        semantic_operation_type
        == META_OBJECT_CONFIG_GRAPH_RELATIONSHIP_LOAD_POLICY_UPDATE_OPERATION
    ):
        return _meta_relationship_update_typed_operation_from_semantic_source_operation(
            operation,
            default_source_refs=default_source_refs,
            semantic_key=semantic_key,
        )
    if semantic_operation_type in {
        META_OBJECT_CONFIG_GRAPH_RELATIONSHIP_CREATE_OPERATION,
        META_OBJECT_CONFIG_GRAPH_RELATIONSHIP_DELETE_OPERATION,
    }:
        return _meta_relationship_update_typed_operation_from_semantic_source_operation(
            operation,
            default_source_refs=default_source_refs,
            semantic_key=semantic_key,
        )
    class_name, attribute_name = _class_attribute_from_semantic_key(semantic_key)
    field_path = optional_text(operation.get("field_path")) or "type"
    before_payload = mapping_value(operation.get("before_payload"))
    after_payload = mapping_value(operation.get("after_payload"))
    source_refs = tuple_text(operation.get("source_refs")) or tuple(default_source_refs)
    owner_key = _owner_key_from_semantic_key(semantic_key) or class_name
    operation_family = optional_text(operation.get("operation_family")) or "update"
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": (
            optional_text(operation.get("operation_key"))
            or f"semantic_apply.{class_name}.{attribute_name}.{field_path}.update"
        ),
        "operation_family": operation_family,
        "provider_operation_type": "meta_ocg.attribute.update",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.AttributeConfig",
        "ontology_subject_kind": "attribute",
        "source_refs": list(source_refs),
        "baseline": {
            "object": _semantic_apply_attribute_payload(
                attribute_name=attribute_name,
                owner_key=owner_key,
                field_path=field_path,
                payload=before_payload,
            )
        },
        "current": _semantic_apply_attribute_payload(
            attribute_name=attribute_name,
            owner_key=owner_key,
            field_path=field_path,
            payload=after_payload,
        ),
        "source_semantic_change": {
            "event_ref": operation.get("event_key"),
            "semantic_key": semantic_key,
            "source": "aware_meta.semantic_apply.source_projection_evidence",
            "semantic_source_operation": dict(operation),
        },
    }


def _meta_attribute_membership_update_typed_operation_from_semantic_source_operation(
    operation: Mapping[str, object],
    *,
    default_source_refs: Sequence[str],
    semantic_key: str,
) -> dict[str, object]:
    before_payload = mapping_value(operation.get("before_payload"))
    after_payload = mapping_value(operation.get("after_payload"))
    source_refs = tuple_text(operation.get("source_refs")) or tuple(default_source_refs)
    class_name, attribute_name = _class_attribute_from_semantic_key(
        _attribute_semantic_key_from_membership_key(semantic_key)
    )
    current_signature = _attribute_membership_signature_payload(
        payload=after_payload,
        class_name=class_name,
        attribute_name=attribute_name,
    )
    baseline_signature = _attribute_membership_signature_payload(
        payload=before_payload,
        class_name=class_name,
        attribute_name=attribute_name,
    )
    edge_id = optional_text(
        after_payload.get("class_config_attribute_config_id")
        or before_payload.get("class_config_attribute_config_id")
        or after_payload.get("entity_id")
        or before_payload.get("entity_id")
    )
    attribute_config_id = optional_text(
        after_payload.get("attribute_config_id")
        or before_payload.get("attribute_config_id")
    )
    class_config_id = optional_text(
        after_payload.get("class_config_id") or before_payload.get("class_config_id")
    )
    executable_object_id = (
        optional_text(operation.get("semantic_apply_receiver_object_id"))
        or optional_text(operation.get("executable_object_id"))
        or optional_text(after_payload.get("semantic_apply_receiver_object_id"))
        or optional_text(after_payload.get("executable_object_id"))
        or optional_text(before_payload.get("semantic_apply_receiver_object_id"))
        or optional_text(before_payload.get("executable_object_id"))
    )
    baseline_object = {
        "class_config_attribute_config_id": edge_id,
        "class_config_id": class_config_id,
        "attribute_config_id": attribute_config_id,
        "attribute_membership_signature": baseline_signature,
    }
    current = {
        "semantic_key": semantic_key,
        "object_kind": "attribute_membership",
        "class_config_attribute_config_id": edge_id,
        "class_config_id": class_config_id,
        "attribute_config_id": attribute_config_id,
        "attribute_membership_owner_kind": "class",
        "attribute_membership_signature": current_signature,
        "attribute_membership_changed_fields": (
            _changed_signature_fields(
                baseline_signature=baseline_signature,
                current_signature=current_signature,
            )
        ),
        "attribute_membership_mutable_update_fields": (
            "is_identity_key",
        ),
        "attribute_membership_identity_replacement_fields": (),
        "attribute_membership_replacement_required": False,
        "payload": dict(after_payload),
    }
    if (
        executable_object_id is not None
        and edge_id is not None
        and executable_object_id != edge_id
    ):
        baseline_object["semantic_apply_receiver_object_id"] = executable_object_id
        baseline_object["executable_object_id"] = executable_object_id
        current["semantic_apply_receiver_object_id"] = executable_object_id
        current["executable_object_id"] = executable_object_id
        payload = mapping_value(current.get("payload"))
        payload["semantic_apply_receiver_object_id"] = executable_object_id
        payload["executable_object_id"] = executable_object_id
        current["payload"] = payload
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": (
            optional_text(operation.get("operation_key"))
            or f"semantic_apply.{class_name}.{attribute_name}.membership.update"
        ),
        "operation_family": optional_text(operation.get("operation_family"))
        or "update",
        "provider_operation_type": "meta_ocg.attribute_membership.update",
        "semantic_key": semantic_key,
        "semantic_subject_type": (
            optional_text(operation.get("semantic_subject_type"))
            or "aware_meta.ClassConfigAttributeConfig"
        ),
        "ontology_subject_kind": "attribute_membership",
        "source_refs": list(source_refs),
        "baseline": {
            "object_id": edge_id,
            "object_kind": "attribute_membership",
            "object": baseline_object,
        },
        "current": current,
        "source_semantic_change": {
            "event_ref": operation.get("event_key"),
            "semantic_key": semantic_key,
            "source": "aware_meta.semantic_apply.source_projection_evidence",
            "semantic_source_operation": dict(operation),
        },
    }


def _meta_relationship_update_typed_operation_from_semantic_source_operation(
    operation: Mapping[str, object],
    *,
    default_source_refs: Sequence[str],
    semantic_key: str,
) -> dict[str, object]:
    before_payload = mapping_value(operation.get("before_payload"))
    after_payload = mapping_value(operation.get("after_payload"))
    class_name = (
        optional_text(after_payload.get("class_name"))
        or optional_text(before_payload.get("class_name"))
        or _relationship_class_from_semantic_key(semantic_key)
        or "UnknownClass"
    )
    relationship_key = (
        optional_text(after_payload.get("relationship_key"))
        or optional_text(after_payload.get("attribute_name"))
        or optional_text(before_payload.get("relationship_key"))
        or optional_text(before_payload.get("attribute_name"))
        or _relationship_key_from_semantic_key(semantic_key)
        or "unknown_relationship"
    )
    source_class_fqn = (
        optional_text(after_payload.get("class_fqn"))
        or optional_text(before_payload.get("class_fqn"))
        or _class_fqn_from_class_name(class_name)
    )
    target_class_fqn = optional_text(
        after_payload.get("target_class_fqn")
    ) or optional_text(before_payload.get("target_class_fqn"))
    relationship_type = (
        optional_text(after_payload.get("relationship_type"))
        or optional_text(before_payload.get("relationship_type"))
        or _relationship_type_from_semantic_key(semantic_key)
    )
    source_refs = tuple_text(operation.get("source_refs")) or tuple(default_source_refs)
    operation_family = optional_text(operation.get("operation_family")) or "update"
    baseline_signature = _semantic_apply_relationship_signature_payload(
        payload=before_payload,
        source_class_fqn=source_class_fqn,
        target_class_fqn=target_class_fqn,
        relationship_key=relationship_key,
        relationship_type=relationship_type,
    )
    current_signature = _semantic_apply_relationship_signature_payload(
        payload=after_payload,
        source_class_fqn=source_class_fqn,
        target_class_fqn=target_class_fqn,
        relationship_key=relationship_key,
        relationship_type=relationship_type,
    )
    current: dict[str, object] = {
        "semantic_key": semantic_key,
        "object_kind": "relationship",
        "owner_semantic_key": f"meta.class:{class_name}",
        "parent_semantic_key": f"meta.class:{class_name}",
        "source_class_semantic_key": f"meta.class:{class_name}",
        "source_class_fqn": source_class_fqn,
        "target_class_fqn": target_class_fqn,
        "relationship_key": relationship_key,
        "relationship_type": relationship_type,
        "relationship_signature": current_signature,
    }
    current.update(_relationship_loading_strategy_fields(payload=after_payload))
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": (
            optional_text(operation.get("operation_key"))
            or f"semantic_apply.{class_name}.{relationship_key}.{operation_family}"
        ),
        "operation_family": operation_family,
        "provider_operation_type": f"meta_ocg.relationship.{operation_family}",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.ClassConfigRelationship",
        "ontology_subject_kind": "relationship",
        "source_refs": list(source_refs),
        "baseline": {
            "object": {
                "relationship_key": relationship_key,
                "source_class_fqn": source_class_fqn,
                "target_class_fqn": target_class_fqn,
                "relationship_type": relationship_type,
                "relationship_signature": baseline_signature,
            }
        },
        "current": {**current, "payload": current},
        "source_semantic_change": {
            "event_ref": operation.get("event_key"),
            "semantic_key": semantic_key,
            "source": "aware_meta.semantic_apply.source_projection_evidence",
            "semantic_source_operation": dict(operation),
        },
    }


def _meta_class_create_typed_operation_from_semantic_source_operation(
    operation: Mapping[str, object],
    *,
    default_source_refs: Sequence[str],
    semantic_key: str,
) -> dict[str, object]:
    after_payload = mapping_value(operation.get("after_payload"))
    class_name = (
        optional_text(after_payload.get("class_name"))
        or optional_text(after_payload.get("name"))
        or _class_name_from_class_semantic_key(semantic_key)
        or "UnknownClass"
    )
    source_refs = tuple_text(operation.get("source_refs")) or tuple(default_source_refs)
    raw_class_fqn = (
        optional_text(after_payload.get("class_fqn"))
        or optional_text(after_payload.get("node_key"))
        or _class_fqn_from_class_semantic_key(semantic_key)
        or class_name
    )
    class_fqn = _class_fqn_from_package_context(
        class_name=class_name,
        raw_class_fqn=raw_class_fqn,
        operation=operation,
        source_refs=source_refs,
    )
    graph_semantic_key = (
        optional_text(after_payload.get("graph_semantic_key"))
        or optional_text(operation.get("graph_semantic_key"))
        or _graph_semantic_key_from_class_semantic_key(semantic_key)
    )
    object_config_graph_node_id = optional_text(
        after_payload.get("object_config_graph_node_id")
    ) or optional_text(after_payload.get("node_id"))
    class_config_id = optional_text(
        after_payload.get("class_config_id")
    ) or optional_text(after_payload.get("entity_id"))
    operation_payload = class_config_create_typed_operation(
        semantic_key=semantic_key,
        graph_semantic_key=graph_semantic_key or "",
        object_config_graph_node_id=object_config_graph_node_id or "",
        class_config_id=class_config_id or "",
        node_key=class_fqn,
        class_fqn=class_fqn,
        class_name=class_name,
        source_refs=source_refs,
        description=(
            optional_text(after_payload.get("description"))
            or optional_text(after_payload.get("class_description"))
        ),
    ).evidence_payload()
    current = mapping_value(operation_payload.get("current"))
    payload = mapping_value(current.get("payload"))
    if object_config_graph_node_id is not None:
        current["object_config_graph_node_id"] = object_config_graph_node_id
        payload["object_config_graph_node_id"] = object_config_graph_node_id
    if class_config_id is not None:
        current["class_config_id"] = class_config_id
        payload["class_config_id"] = class_config_id
    if payload:
        current["payload"] = payload
    operation_payload["current"] = current
    operation_payload["operation_key"] = (
        optional_text(operation.get("operation_key"))
        or operation_payload["operation_key"]
    )
    operation_payload["source_semantic_change"] = {
        "event_ref": operation.get("event_key"),
        "semantic_key": semantic_key,
        "source": "aware_meta.semantic_apply.source_projection_evidence",
        "semantic_source_operation": dict(operation),
    }
    return operation_payload


def _meta_class_delete_typed_operation_from_semantic_source_operation(
    operation: Mapping[str, object],
    *,
    default_source_refs: Sequence[str],
    semantic_key: str,
) -> dict[str, object]:
    before_payload = mapping_value(operation.get("before_payload"))
    after_payload = mapping_value(operation.get("after_payload"))
    class_name = (
        optional_text(before_payload.get("class_name"))
        or optional_text(before_payload.get("name"))
        or optional_text(after_payload.get("class_name"))
        or optional_text(after_payload.get("name"))
        or _class_name_from_class_semantic_key(semantic_key)
        or "UnknownClass"
    )
    source_refs = tuple_text(operation.get("source_refs")) or tuple(default_source_refs)
    raw_class_fqn = (
        optional_text(before_payload.get("class_fqn"))
        or optional_text(before_payload.get("node_key"))
        or optional_text(after_payload.get("class_fqn"))
        or optional_text(after_payload.get("node_key"))
        or _class_fqn_from_class_semantic_key(semantic_key)
        or class_name
    )
    class_fqn = _class_fqn_from_package_context(
        class_name=class_name,
        raw_class_fqn=raw_class_fqn,
        operation=operation,
        source_refs=source_refs,
    )
    graph_semantic_key = (
        optional_text(before_payload.get("graph_semantic_key"))
        or optional_text(after_payload.get("graph_semantic_key"))
        or optional_text(operation.get("graph_semantic_key"))
        or _graph_semantic_key_from_class_semantic_key(semantic_key)
    )
    object_config_graph_node_id = (
        optional_text(before_payload.get("object_config_graph_node_id"))
        or optional_text(before_payload.get("node_id"))
        or optional_text(after_payload.get("object_config_graph_node_id"))
        or optional_text(after_payload.get("node_id"))
    )
    class_config_id = (
        optional_text(before_payload.get("class_config_id"))
        or optional_text(before_payload.get("entity_id"))
        or optional_text(after_payload.get("class_config_id"))
        or optional_text(after_payload.get("entity_id"))
    )
    operation_payload = class_config_delete_typed_operation(
        semantic_key=semantic_key,
        graph_semantic_key=graph_semantic_key or "",
        object_config_graph_node_id=object_config_graph_node_id or "",
        class_config_id=class_config_id,
        node_key=class_fqn,
        class_fqn=class_fqn,
        class_name=class_name,
        source_refs=source_refs,
        description=(
            optional_text(before_payload.get("description"))
            or optional_text(before_payload.get("class_description"))
            or optional_text(after_payload.get("description"))
            or optional_text(after_payload.get("class_description"))
        ),
    ).evidence_payload()
    baseline = mapping_value(operation_payload.get("baseline"))
    baseline_object = mapping_value(baseline.get("object"))
    current = mapping_value(operation_payload.get("current"))
    payload = mapping_value(current.get("payload"))
    for target in (baseline_object, current, payload):
        if object_config_graph_node_id is not None:
            target["object_config_graph_node_id"] = object_config_graph_node_id
            target["node_id"] = object_config_graph_node_id
        if class_config_id is not None:
            target["class_config_id"] = class_config_id
            target["entity_id"] = class_config_id
    if baseline_object:
        baseline["object"] = baseline_object
    if payload:
        current["payload"] = payload
    operation_payload["baseline"] = baseline
    operation_payload["current"] = current
    operation_payload["operation_key"] = (
        optional_text(operation.get("operation_key"))
        or operation_payload["operation_key"]
    )
    operation_payload["source_semantic_change"] = {
        "event_ref": operation.get("event_key"),
        "semantic_key": semantic_key,
        "source": "aware_meta.semantic_apply.source_projection_evidence",
        "semantic_source_operation": dict(operation),
    }
    return operation_payload


def _meta_attribute_create_typed_operation_from_semantic_source_operation(
    operation: Mapping[str, object],
    *,
    default_source_refs: Sequence[str],
    semantic_key: str,
) -> dict[str, object]:
    after_payload = mapping_value(operation.get("after_payload"))
    class_name = (
        optional_text(after_payload.get("class_name"))
        or _attribute_class_from_semantic_key(semantic_key)
        or "UnknownClass"
    )
    attribute_name = (
        optional_text(after_payload.get("attribute_name"))
        or optional_text(after_payload.get("name"))
        or _attribute_name_from_semantic_key(semantic_key)
        or "unknown_attribute"
    )
    source_refs = tuple_text(operation.get("source_refs")) or tuple(default_source_refs)
    raw_class_fqn = (
        optional_text(after_payload.get("class_fqn"))
        or optional_text(after_payload.get("owner_key"))
        or class_name
    )
    class_fqn = _class_fqn_from_package_context(
        class_name=class_name,
        raw_class_fqn=raw_class_fqn,
        operation=operation,
        source_refs=source_refs,
    )
    attribute_config_id = (
        optional_text(after_payload.get("attribute_config_id"))
        or optional_text(after_payload.get("entity_id"))
        or _stable_attribute_config_id(
            owner_key=class_fqn, attribute_name=attribute_name
        )
        or ""
    )
    primitive_base_type, _is_required = _primitive_type_descriptor_from_text(
        optional_text(after_payload.get("type"))
    )
    operation_payload = attribute_config_create_typed_operation(
        semantic_key=semantic_key,
        attribute_config_id=attribute_config_id,
        owner_semantic_key=(
            optional_text(after_payload.get("owner_semantic_key"))
            or f"meta.class:{class_name}"
        ),
        attribute_name=attribute_name,
        source_refs=source_refs,
        primitive_base_type=primitive_base_type,
        description=optional_text(after_payload.get("description")),
    ).evidence_payload()
    current = mapping_value(operation_payload.get("current"))
    signature = mapping_value(current.get("attribute_signature"))
    signature.update(
        {
            "owner_key": class_fqn,
            "class_name": class_name,
            "type": optional_text(after_payload.get("type")) or "String",
        }
    )
    if after_payload.get("default_value") is not None:
        signature["default_value"] = after_payload["default_value"]
    current.update(
        {
            "owner_key": class_fqn,
            "class_fqn": class_fqn,
            "class_name": class_name,
            "attribute_config_id": attribute_config_id,
            "entity_id": attribute_config_id,
            "attribute_signature": signature,
            "generated_materialization": {
                "python_orm": {
                    "relative_path": _python_orm_relative_path_from_source_refs(
                        source_refs=source_refs,
                        package_name=optional_text(operation.get("package_name")),
                    ),
                },
            },
        }
    )
    operation_payload["current"] = current
    operation_payload["operation_key"] = (
        optional_text(operation.get("operation_key"))
        or operation_payload["operation_key"]
    )
    operation_payload["source_semantic_change"] = {
        "event_ref": operation.get("event_key"),
        "semantic_key": semantic_key,
        "source": "aware_meta.semantic_apply.source_projection_evidence",
        "semantic_source_operation": dict(operation),
    }
    return operation_payload


def _meta_attribute_delete_typed_operation_from_semantic_source_operation(
    operation: Mapping[str, object],
    *,
    default_source_refs: Sequence[str],
    semantic_key: str,
) -> dict[str, object]:
    before_payload = mapping_value(operation.get("before_payload"))
    after_payload = mapping_value(operation.get("after_payload"))
    class_name = (
        optional_text(before_payload.get("class_name"))
        or optional_text(after_payload.get("class_name"))
        or _attribute_class_from_semantic_key(semantic_key)
        or "UnknownClass"
    )
    attribute_name = (
        optional_text(before_payload.get("attribute_name"))
        or optional_text(before_payload.get("name"))
        or optional_text(after_payload.get("attribute_name"))
        or optional_text(after_payload.get("name"))
        or _attribute_name_from_semantic_key(semantic_key)
        or "unknown_attribute"
    )
    source_refs = tuple_text(operation.get("source_refs")) or tuple(default_source_refs)
    raw_class_fqn = (
        optional_text(before_payload.get("class_fqn"))
        or optional_text(before_payload.get("owner_key"))
        or optional_text(after_payload.get("class_fqn"))
        or optional_text(after_payload.get("owner_key"))
        or class_name
    )
    class_fqn = _class_fqn_from_package_context(
        class_name=class_name,
        raw_class_fqn=raw_class_fqn,
        operation=operation,
        source_refs=source_refs,
    )
    attribute_config_id = (
        optional_text(before_payload.get("attribute_config_id"))
        or optional_text(before_payload.get("entity_id"))
        or optional_text(after_payload.get("attribute_config_id"))
        or optional_text(after_payload.get("entity_id"))
        or _stable_attribute_config_id(
            owner_key=class_fqn, attribute_name=attribute_name
        )
        or ""
    )
    type_text = (
        optional_text(before_payload.get("type"))
        or optional_text(after_payload.get("type"))
        or "String"
    )
    primitive_base_type, is_required = _primitive_type_descriptor_from_text(type_text)
    attribute_signature = {
        "name": attribute_name,
        "owner_key": class_fqn,
        "class_name": class_name,
        "is_required": is_required,
        "is_public": True,
        "type": type_text,
        "type_descriptor": {
            "kind": "primitive",
            "primitive_base_type": primitive_base_type,
        },
    }
    baseline_object = {
        "object_kind": "attribute",
        "object_id": attribute_config_id,
        "entity_id": attribute_config_id,
        "owner_semantic_key": (
            optional_text(before_payload.get("owner_semantic_key"))
            or optional_text(after_payload.get("owner_semantic_key"))
            or f"meta.class:{class_name}"
        ),
        "owner_key": class_fqn,
        "class_fqn": class_fqn,
        "class_name": class_name,
        "attribute_name": attribute_name,
        "attribute_config_id": attribute_config_id,
        "attribute_signature": attribute_signature,
        "generated_materialization": {
            "python_orm": {
                "relative_path": _python_orm_relative_path_from_source_refs(
                    source_refs=source_refs,
                    package_name=optional_text(operation.get("package_name")),
                ),
            },
        },
    }
    current = {
        "semantic_key": semantic_key,
        "object_kind": "attribute",
        "owner_semantic_key": baseline_object["owner_semantic_key"],
        "owner_key": class_fqn,
        "class_fqn": class_fqn,
        "class_name": class_name,
        "attribute_name": attribute_name,
        "attribute_config_id": attribute_config_id,
        "entity_id": attribute_config_id,
        "attribute_signature": attribute_signature,
        "generated_materialization": baseline_object["generated_materialization"],
    }
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": (
            optional_text(operation.get("operation_key"))
            or f"semantic_apply.{class_name}.{attribute_name}.delete"
        ),
        "operation_family": "delete",
        "provider_operation_type": "meta_ocg.attribute.delete",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.AttributeConfig",
        "ontology_subject_kind": "attribute",
        "source_refs": list(source_refs),
        "baseline": {"object_id": attribute_config_id, "object": baseline_object},
        "current": {**current, "payload": current},
        "source_semantic_change": {
            "event_ref": operation.get("event_key"),
            "semantic_key": semantic_key,
            "source": "aware_meta.semantic_apply.source_projection_evidence",
            "semantic_source_operation": dict(operation),
        },
    }


def _meta_class_update_typed_operation_from_semantic_source_operation(
    operation: Mapping[str, object],
    *,
    default_source_refs: Sequence[str],
    semantic_key: str,
) -> dict[str, object]:
    before_payload = mapping_value(operation.get("before_payload"))
    after_payload = mapping_value(operation.get("after_payload"))
    class_name = (
        optional_text(after_payload.get("class_name"))
        or optional_text(before_payload.get("class_name"))
        or _class_name_from_class_semantic_key(semantic_key)
        or "UnknownClass"
    )
    owner_key = (
        optional_text(after_payload.get("class_fqn"))
        or optional_text(before_payload.get("class_fqn"))
        or _class_fqn_from_class_name(class_name)
    )
    baseline_description = optional_text(
        before_payload.get("description")
    ) or optional_text(before_payload.get("class_description"))
    current_description = optional_text(
        after_payload.get("description")
    ) or optional_text(after_payload.get("class_description"))
    source_refs = tuple_text(operation.get("source_refs")) or tuple(default_source_refs)
    operation_family = optional_text(operation.get("operation_family")) or "update"
    baseline_object = {
        "class_name": class_name,
        "name": class_name,
        "entity_name": class_name,
        "class_fqn": owner_key,
        "description": baseline_description,
    }
    current = {
        "semantic_key": semantic_key,
        "object_kind": "class",
        "class_name": class_name,
        "name": class_name,
        "entity_name": class_name,
        "class_fqn": owner_key,
        "description": current_description,
        "class_signature": {
            "class_name": class_name,
            "name": class_name,
            "class_fqn": owner_key,
            "description": current_description,
        },
    }
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": (
            optional_text(operation.get("operation_key"))
            or f"semantic_apply.{class_name}.description.update"
        ),
        "operation_family": operation_family,
        "provider_operation_type": "meta_ocg.class.update",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.ClassConfig",
        "ontology_subject_kind": "class",
        "source_refs": list(source_refs),
        "baseline": {"object": baseline_object},
        "current": {**current, "payload": current},
        "source_semantic_change": {
            "event_ref": operation.get("event_key"),
            "semantic_key": semantic_key,
            "source": "aware_meta.semantic_apply.source_projection_evidence",
            "semantic_source_operation": dict(operation),
        },
    }


def _meta_enum_update_typed_operation_from_semantic_source_operation(
    operation: Mapping[str, object],
    *,
    default_source_refs: Sequence[str],
    semantic_key: str,
) -> dict[str, object]:
    before_payload = mapping_value(operation.get("before_payload"))
    after_payload = mapping_value(operation.get("after_payload"))
    enum_name = (
        optional_text(after_payload.get("enum_name"))
        or optional_text(before_payload.get("enum_name"))
        or _enum_name_from_enum_semantic_key(semantic_key)
        or "UnknownEnum"
    )
    enum_fqn = (
        optional_text(after_payload.get("enum_fqn"))
        or optional_text(before_payload.get("enum_fqn"))
        or _enum_fqn_from_enum_semantic_key(semantic_key)
        or enum_name
    )
    baseline_description = optional_text(
        before_payload.get("description")
    ) or optional_text(before_payload.get("enum_description"))
    current_description = optional_text(
        after_payload.get("description")
    ) or optional_text(after_payload.get("enum_description"))
    source_refs = tuple_text(operation.get("source_refs")) or tuple(default_source_refs)
    operation_family = optional_text(operation.get("operation_family")) or "update"
    baseline_object = {
        "enum_fqn": enum_fqn,
        "name": enum_name,
        "entity_name": enum_name,
        "description": baseline_description,
    }
    current = {
        "semantic_key": semantic_key,
        "object_kind": "enum",
        "enum_fqn": enum_fqn,
        "name": enum_name,
        "entity_name": enum_name,
        "description": current_description,
    }
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": (
            optional_text(operation.get("operation_key"))
            or f"semantic_apply.{enum_name}.description.update"
        ),
        "operation_family": operation_family,
        "provider_operation_type": "meta_ocg.enum.update",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.EnumConfig",
        "ontology_subject_kind": "enum",
        "source_refs": list(source_refs),
        "baseline": {"object": baseline_object},
        "current": {**current, "payload": current},
        "source_semantic_change": {
            "event_ref": operation.get("event_key"),
            "semantic_key": semantic_key,
            "source": "aware_meta.semantic_apply.source_projection_evidence",
            "semantic_source_operation": dict(operation),
        },
    }


def _meta_enum_create_typed_operation_from_semantic_source_operation(
    operation: Mapping[str, object],
    *,
    default_source_refs: Sequence[str],
    semantic_key: str,
) -> dict[str, object]:
    after_payload = mapping_value(operation.get("after_payload"))
    enum_name = (
        optional_text(after_payload.get("enum_name"))
        or optional_text(after_payload.get("name"))
        or _enum_name_from_enum_semantic_key(semantic_key)
        or "UnknownEnum"
    )
    source_refs = tuple_text(operation.get("source_refs")) or tuple(default_source_refs)
    raw_enum_fqn = (
        optional_text(after_payload.get("enum_fqn"))
        or optional_text(after_payload.get("node_key"))
        or _enum_fqn_from_enum_semantic_key(semantic_key)
        or enum_name
    )
    enum_fqn = _enum_fqn_from_package_context(
        enum_name=enum_name,
        raw_enum_fqn=raw_enum_fqn,
        operation=operation,
        source_refs=source_refs,
    )
    graph_semantic_key = (
        optional_text(after_payload.get("graph_semantic_key"))
        or optional_text(operation.get("graph_semantic_key"))
        or _graph_semantic_key_from_enum_semantic_key(semantic_key)
    )
    current = {
        "semantic_key": semantic_key,
        "object_kind": "enum",
        "graph_semantic_key": graph_semantic_key,
        "object_config_graph_node_id": optional_text(
            after_payload.get("object_config_graph_node_id")
        )
        or optional_text(after_payload.get("node_id")),
        "enum_config_id": optional_text(after_payload.get("enum_config_id"))
        or optional_text(after_payload.get("entity_id")),
        "node_key": enum_fqn,
        "node_type": "enum",
        "enum_fqn": enum_fqn,
        "name": enum_name,
        "entity_name": enum_name,
        "description": (
            optional_text(after_payload.get("description"))
            or optional_text(after_payload.get("enum_description"))
        ),
        "values": tuple_text(after_payload.get("values")),
    }
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": (
            optional_text(operation.get("operation_key"))
            or f"semantic_apply.{enum_name}.create"
        ),
        "operation_family": "create",
        "provider_operation_type": "meta_ocg.enum.create",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.ObjectConfigGraphNode",
        "ontology_subject_kind": "enum",
        "source_refs": list(source_refs),
        "baseline": {"object": {}},
        "current": {**current, "payload": current},
        "source_semantic_change": {
            "event_ref": operation.get("event_key"),
            "semantic_key": semantic_key,
            "source": "aware_meta.semantic_apply.source_projection_evidence",
            "semantic_source_operation": dict(operation),
        },
    }


def _meta_enum_delete_typed_operation_from_semantic_source_operation(
    operation: Mapping[str, object],
    *,
    default_source_refs: Sequence[str],
    semantic_key: str,
) -> dict[str, object]:
    before_payload = mapping_value(operation.get("before_payload"))
    after_payload = mapping_value(operation.get("after_payload"))
    enum_name = (
        optional_text(before_payload.get("enum_name"))
        or optional_text(before_payload.get("name"))
        or optional_text(after_payload.get("enum_name"))
        or optional_text(after_payload.get("name"))
        or _enum_name_from_enum_semantic_key(semantic_key)
        or "UnknownEnum"
    )
    source_refs = tuple_text(operation.get("source_refs")) or tuple(default_source_refs)
    raw_enum_fqn = (
        optional_text(before_payload.get("enum_fqn"))
        or optional_text(before_payload.get("node_key"))
        or optional_text(after_payload.get("enum_fqn"))
        or optional_text(after_payload.get("node_key"))
        or _enum_fqn_from_enum_semantic_key(semantic_key)
        or enum_name
    )
    enum_fqn = _enum_fqn_from_package_context(
        enum_name=enum_name,
        raw_enum_fqn=raw_enum_fqn,
        operation=operation,
        source_refs=source_refs,
    )
    graph_semantic_key = (
        optional_text(before_payload.get("graph_semantic_key"))
        or optional_text(after_payload.get("graph_semantic_key"))
        or optional_text(operation.get("graph_semantic_key"))
        or _graph_semantic_key_from_enum_semantic_key(semantic_key)
    )
    baseline_object = {
        "semantic_key": semantic_key,
        "object_kind": "enum",
        "graph_semantic_key": graph_semantic_key,
        "object_config_graph_node_id": (
            optional_text(before_payload.get("object_config_graph_node_id"))
            or optional_text(before_payload.get("node_id"))
        ),
        "node_id": (
            optional_text(before_payload.get("node_id"))
            or optional_text(before_payload.get("object_config_graph_node_id"))
        ),
        "enum_config_id": (
            optional_text(before_payload.get("enum_config_id"))
            or optional_text(before_payload.get("entity_id"))
        ),
        "entity_id": (
            optional_text(before_payload.get("entity_id"))
            or optional_text(before_payload.get("enum_config_id"))
        ),
        "node_key": enum_fqn,
        "node_type": "enum",
        "enum_fqn": enum_fqn,
        "name": enum_name,
        "entity_name": enum_name,
        "description": (
            optional_text(before_payload.get("description"))
            or optional_text(before_payload.get("enum_description"))
        ),
    }
    current = dict(baseline_object)
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": (
            optional_text(operation.get("operation_key"))
            or f"semantic_apply.{enum_name}.delete"
        ),
        "operation_family": "delete",
        "provider_operation_type": "meta_ocg.enum.delete",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.ObjectConfigGraph",
        "ontology_subject_kind": "enum",
        "source_refs": list(source_refs),
        "baseline": {"object": {**baseline_object, "payload": baseline_object}},
        "current": {**current, "payload": current},
        "source_semantic_change": {
            "event_ref": operation.get("event_key"),
            "semantic_key": semantic_key,
            "source": "aware_meta.semantic_apply.source_projection_evidence",
            "semantic_source_operation": dict(operation),
        },
    }


def _meta_enum_option_create_typed_operation_from_semantic_source_operation(
    operation: Mapping[str, object],
    *,
    default_source_refs: Sequence[str],
    semantic_key: str,
) -> dict[str, object]:
    after_payload = mapping_value(operation.get("after_payload"))
    enum_semantic_key = (
        optional_text(after_payload.get("enum_semantic_key"))
        or optional_text(after_payload.get("parent_semantic_key"))
        or _enum_semantic_key_from_option_semantic_key(semantic_key)
        or "meta.enum:UnknownEnum"
    )
    enum_name = (
        optional_text(after_payload.get("enum_name"))
        or _enum_name_from_enum_semantic_key(enum_semantic_key)
        or "UnknownEnum"
    )
    enum_fqn = (
        optional_text(after_payload.get("enum_fqn"))
        or _enum_fqn_from_enum_semantic_key(enum_semantic_key)
        or enum_name
    )
    option_value = (
        optional_text(after_payload.get("value"))
        or optional_text(after_payload.get("enum_option_value"))
        or _enum_option_value_from_semantic_key(semantic_key)
        or "unknown_option"
    )
    position = _int_value(after_payload.get("position"))
    if position is None:
        position = 0
    source_refs = tuple_text(operation.get("source_refs")) or tuple(default_source_refs)
    current = {
        "semantic_key": semantic_key,
        "object_kind": "enum_option",
        "enum_semantic_key": enum_semantic_key,
        "parent_semantic_key": enum_semantic_key,
        "enum_fqn": enum_fqn,
        "enum_name": enum_name,
        "value": option_value,
        "entity_name": option_value,
        "label": optional_text(after_payload.get("label")),
        "description": optional_text(after_payload.get("description")),
        "position": position,
    }
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": (
            optional_text(operation.get("operation_key"))
            or f"semantic_apply.{enum_name}.{option_value}.create"
        ),
        "operation_family": "create",
        "provider_operation_type": "meta_ocg.enum_option.create",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.EnumOption",
        "ontology_subject_kind": "enum_option",
        "source_refs": list(source_refs),
        "baseline": {"object": {}},
        "current": {**current, "payload": current},
        "source_semantic_change": {
            "event_ref": operation.get("event_key"),
            "semantic_key": semantic_key,
            "source": "aware_meta.semantic_apply.source_projection_evidence",
            "semantic_source_operation": dict(operation),
        },
    }


def _meta_enum_option_update_typed_operation_from_semantic_source_operation(
    operation: Mapping[str, object],
    *,
    default_source_refs: Sequence[str],
    semantic_key: str,
) -> dict[str, object]:
    before_payload = mapping_value(operation.get("before_payload"))
    after_payload = mapping_value(operation.get("after_payload"))
    identity = _enum_option_semantic_source_identity(
        operation=operation,
        semantic_key=semantic_key,
        before_payload=before_payload,
        after_payload=after_payload,
    )
    position = _int_value(after_payload.get("position"))
    source_refs = tuple_text(operation.get("source_refs")) or tuple(default_source_refs)
    baseline_object = {
        **identity,
        "label": optional_text(before_payload.get("label")),
        "description": optional_text(before_payload.get("description")),
        "position": _int_value(before_payload.get("position")),
    }
    current = {
        **identity,
        "label": optional_text(after_payload.get("label")),
        "description": optional_text(after_payload.get("description")),
        "position": 0 if position is None else position,
    }
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": (
            optional_text(operation.get("operation_key"))
            or (
                f"semantic_apply.{identity['enum_name']}."
                f"{identity['value']}.position.update"
            )
        ),
        "operation_family": "update",
        "provider_operation_type": "meta_ocg.enum_option.update",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.EnumOption",
        "ontology_subject_kind": "enum_option",
        "source_refs": list(source_refs),
        "baseline": {"object": {**baseline_object, "payload": baseline_object}},
        "current": {**current, "payload": current},
        "source_semantic_change": {
            "event_ref": operation.get("event_key"),
            "semantic_key": semantic_key,
            "source": "aware_meta.semantic_apply.source_projection_evidence",
            "semantic_source_operation": dict(operation),
        },
    }


def _meta_enum_option_delete_typed_operation_from_semantic_source_operation(
    operation: Mapping[str, object],
    *,
    default_source_refs: Sequence[str],
    semantic_key: str,
) -> dict[str, object]:
    before_payload = mapping_value(operation.get("before_payload"))
    after_payload = mapping_value(operation.get("after_payload"))
    identity = _enum_option_semantic_source_identity(
        operation=operation,
        semantic_key=semantic_key,
        before_payload=before_payload,
        after_payload=after_payload,
    )
    source_refs = tuple_text(operation.get("source_refs")) or tuple(default_source_refs)
    baseline_object = {
        **identity,
        "label": optional_text(before_payload.get("label")),
        "description": optional_text(before_payload.get("description")),
        "position": _int_value(before_payload.get("position")),
    }
    current = dict(baseline_object)
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": (
            optional_text(operation.get("operation_key"))
            or f"semantic_apply.{identity['enum_name']}.{identity['value']}.delete"
        ),
        "operation_family": "delete",
        "provider_operation_type": "meta_ocg.enum_option.delete",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.EnumOption",
        "ontology_subject_kind": "enum_option",
        "source_refs": list(source_refs),
        "baseline": {"object": {**baseline_object, "payload": baseline_object}},
        "current": {**current, "payload": current},
        "source_semantic_change": {
            "event_ref": operation.get("event_key"),
            "semantic_key": semantic_key,
            "source": "aware_meta.semantic_apply.source_projection_evidence",
            "semantic_source_operation": dict(operation),
        },
    }


def _enum_option_semantic_source_identity(
    *,
    operation: Mapping[str, object],
    semantic_key: str,
    before_payload: Mapping[str, object],
    after_payload: Mapping[str, object],
) -> dict[str, object]:
    enum_semantic_key = (
        optional_text(after_payload.get("enum_semantic_key"))
        or optional_text(after_payload.get("parent_semantic_key"))
        or optional_text(before_payload.get("enum_semantic_key"))
        or optional_text(before_payload.get("parent_semantic_key"))
        or _enum_semantic_key_from_option_semantic_key(semantic_key)
        or "meta.enum:UnknownEnum"
    )
    enum_name = (
        optional_text(after_payload.get("enum_name"))
        or optional_text(before_payload.get("enum_name"))
        or _enum_name_from_enum_semantic_key(enum_semantic_key)
        or "UnknownEnum"
    )
    enum_fqn = (
        optional_text(after_payload.get("enum_fqn"))
        or optional_text(before_payload.get("enum_fqn"))
        or _enum_fqn_from_enum_semantic_key(enum_semantic_key)
        or enum_name
    )
    option_value = (
        optional_text(after_payload.get("value"))
        or optional_text(after_payload.get("enum_option_value"))
        or optional_text(before_payload.get("value"))
        or optional_text(before_payload.get("enum_option_value"))
        or _enum_option_value_from_semantic_key(semantic_key)
        or "unknown_option"
    )
    enum_config_id = _first_text(
        operation.get("enum_config_id"),
        operation.get("receiver_object_id"),
        operation.get("semantic_apply_receiver_object_id"),
        after_payload.get("enum_config_id"),
        after_payload.get("receiver_object_id"),
        before_payload.get("enum_config_id"),
        before_payload.get("receiver_object_id"),
    )
    enum_option_id = _first_text(
        operation.get("enum_option_id"),
        operation.get("entity_id"),
        operation.get("result_object_id"),
        after_payload.get("enum_option_id"),
        after_payload.get("entity_id"),
        before_payload.get("enum_option_id"),
        before_payload.get("entity_id"),
    )
    identity: dict[str, object] = {
        "semantic_key": semantic_key,
        "object_kind": "enum_option",
        "enum_semantic_key": enum_semantic_key,
        "parent_semantic_key": enum_semantic_key,
        "enum_fqn": enum_fqn,
        "enum_name": enum_name,
        "value": option_value,
        "entity_name": option_value,
    }
    if enum_config_id is not None:
        identity["enum_config_id"] = enum_config_id
    if enum_option_id is not None:
        identity["enum_option_id"] = enum_option_id
        identity["entity_id"] = enum_option_id
    return identity


def _meta_function_update_typed_operation_from_semantic_source_operation(
    operation: Mapping[str, object],
    *,
    default_source_refs: Sequence[str],
    semantic_key: str,
) -> dict[str, object]:
    before_payload = mapping_value(operation.get("before_payload"))
    after_payload = mapping_value(operation.get("after_payload"))
    class_name = (
        optional_text(after_payload.get("class_name"))
        or optional_text(before_payload.get("class_name"))
        or _function_class_from_semantic_key(semantic_key)
        or "UnknownClass"
    )
    function_name = (
        optional_text(after_payload.get("function_name"))
        or optional_text(after_payload.get("name"))
        or optional_text(before_payload.get("function_name"))
        or optional_text(before_payload.get("name"))
        or _function_name_from_semantic_key(semantic_key)
        or "unknown_function"
    )
    owner_key = (
        optional_text(after_payload.get("class_fqn"))
        or optional_text(before_payload.get("class_fqn"))
        or _owner_key_from_semantic_key(semantic_key)
        or class_name
    )
    source_refs = tuple_text(operation.get("source_refs")) or tuple(default_source_refs)
    operation_family = optional_text(operation.get("operation_family")) or "update"
    field_path = optional_text(operation.get("field_path"))
    if field_path in {"class_config_id", "function_config_id", "is_public", "is_constructor", "position"}:
        return _meta_function_membership_update_typed_operation_from_semantic_source_operation(
            operation,
            default_source_refs=default_source_refs,
            semantic_key=semantic_key,
            class_name=class_name,
            function_name=function_name,
            source_refs=source_refs,
            operation_family=operation_family,
        )
    baseline_signature = _semantic_apply_function_signature_payload(
        payload=before_payload,
        owner_key=owner_key,
        function_name=function_name,
    )
    current_signature = _semantic_apply_function_signature_payload(
        payload=after_payload,
        owner_key=owner_key,
        function_name=function_name,
    )
    current = {
        "semantic_key": semantic_key,
        "object_kind": "function",
        "owner_semantic_key": f"meta.class:{class_name}",
        "function_name": function_name,
        "owner_key": owner_key,
        "kind": current_signature["kind"],
        "description": current_signature["description"],
        "verb": current_signature["verb"],
        "is_async": current_signature["is_async"],
        "function_signature": current_signature,
    }
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": (
            optional_text(operation.get("operation_key"))
            or f"semantic_apply.{class_name}.{function_name}.signature.update"
        ),
        "operation_family": operation_family,
        "provider_operation_type": "meta_ocg.function.update",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.FunctionConfig",
        "ontology_subject_kind": "function",
        "source_refs": list(source_refs),
        "baseline": {
            "object": {
                "function_name": function_name,
                "owner_semantic_key": f"meta.class:{class_name}",
                "function_signature": baseline_signature,
            }
        },
        "current": {**current, "payload": current},
        "source_semantic_change": {
            "event_ref": operation.get("event_key"),
            "semantic_key": semantic_key,
            "source": "aware_meta.semantic_apply.source_projection_evidence",
            "semantic_source_operation": dict(operation),
        },
    }


def _meta_function_membership_update_typed_operation_from_semantic_source_operation(
    operation: Mapping[str, object],
    *,
    default_source_refs: Sequence[str],
    semantic_key: str,
    class_name: str,
    function_name: str,
    source_refs: Sequence[str],
    operation_family: str,
) -> dict[str, object]:
    del default_source_refs
    before_payload = mapping_value(operation.get("before_payload"))
    after_payload = mapping_value(operation.get("after_payload"))
    class_config_id = _first_text(
        after_payload.get("class_config_id"),
        before_payload.get("class_config_id"),
    )
    function_config_id = _first_text(
        after_payload.get("function_config_id"),
        before_payload.get("function_config_id"),
        operation.get("semantic_source_object_id"),
    )
    edge_id = _first_text(
        before_payload.get("class_config_function_config_id"),
        after_payload.get("class_config_function_config_id"),
    )
    membership_semantic_key = _first_text(
        after_payload.get("function_membership_semantic_key"),
        before_payload.get("function_membership_semantic_key"),
        f"{semantic_key}/membership:class_config",
    )
    baseline_signature = _semantic_apply_function_membership_signature_payload(
        payload=before_payload,
        class_config_id=class_config_id,
        function_config_id=function_config_id,
    )
    current_signature = _semantic_apply_function_membership_signature_payload(
        payload=after_payload,
        class_config_id=class_config_id,
        function_config_id=function_config_id,
    )
    baseline_object = {
        "object_id": edge_id,
        "object_kind": "function_membership",
        "class_config_function_config_id": edge_id,
        "class_config_id": class_config_id,
        "function_config_id": function_config_id,
        "function_semantic_key": semantic_key,
        "function_name": function_name,
        "function_membership_semantic_key": membership_semantic_key,
        "function_membership_signature": baseline_signature,
    }
    current = {
        "semantic_key": membership_semantic_key,
        "object_kind": "function_membership",
        "class_config_function_config_id": edge_id,
        "class_config_id": class_config_id,
        "function_config_id": function_config_id,
        "function_semantic_key": semantic_key,
        "function_name": function_name,
        "function_membership_semantic_key": membership_semantic_key,
        "function_membership_signature": current_signature,
    }
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": (
            optional_text(operation.get("operation_key"))
            or f"semantic_apply.{class_name}.{function_name}.membership.update"
        ),
        "operation_family": operation_family,
        "provider_operation_type": "meta_ocg.function_membership.update",
        "semantic_key": membership_semantic_key,
        "semantic_subject_type": "aware_meta.ClassConfigFunctionConfig",
        "ontology_subject_kind": "function_membership",
        "source_refs": list(source_refs),
        "baseline": {
            "object_id": edge_id,
            "object_kind": "function_membership",
            "object": baseline_object,
        },
        "current": {**current, "payload": current},
        "source_semantic_change": {
            "event_ref": operation.get("event_key"),
            "semantic_key": semantic_key,
            "source": "aware_meta.semantic_apply.source_projection_evidence",
            "semantic_source_operation": dict(operation),
        },
    }


def _meta_function_delete_typed_operation_from_semantic_source_operation(
    operation: Mapping[str, object],
    *,
    default_source_refs: Sequence[str],
    semantic_key: str,
) -> dict[str, object]:
    before_payload = mapping_value(operation.get("before_payload"))
    after_payload = mapping_value(operation.get("after_payload"))
    class_name = (
        optional_text(before_payload.get("class_name"))
        or optional_text(after_payload.get("class_name"))
        or _function_class_from_semantic_key(semantic_key)
        or "UnknownClass"
    )
    function_name = (
        optional_text(before_payload.get("function_name"))
        or optional_text(before_payload.get("name"))
        or optional_text(after_payload.get("function_name"))
        or optional_text(after_payload.get("name"))
        or _function_name_from_semantic_key(semantic_key)
        or "unknown_function"
    )
    owner_key = (
        optional_text(before_payload.get("owner_key"))
        or optional_text(before_payload.get("class_fqn"))
        or optional_text(after_payload.get("owner_key"))
        or optional_text(after_payload.get("class_fqn"))
        or _owner_key_from_semantic_key(semantic_key)
        or class_name
    )
    source_refs = tuple_text(operation.get("source_refs")) or tuple(default_source_refs)
    class_config_id = (
        optional_text(operation.get("class_config_id"))
        or optional_text(before_payload.get("class_config_id"))
        or optional_text(before_payload.get("owner_object_id"))
        or optional_text(after_payload.get("class_config_id"))
        or optional_text(after_payload.get("owner_object_id"))
    )
    semantic_source_object_id = (
        optional_text(operation.get("semantic_source_object_id"))
        or optional_text(before_payload.get("semantic_source_object_id"))
        or optional_text(after_payload.get("semantic_source_object_id"))
    )
    executable_object_id = (
        optional_text(operation.get("semantic_apply_receiver_object_id"))
        or optional_text(operation.get("executable_object_id"))
        or optional_text(before_payload.get("semantic_apply_receiver_object_id"))
        or optional_text(before_payload.get("executable_object_id"))
        or optional_text(after_payload.get("semantic_apply_receiver_object_id"))
        or optional_text(after_payload.get("executable_object_id"))
    )
    generated_materialization = (
        mapping_value(operation.get("generated_materialization"))
        or mapping_value(before_payload.get("generated_materialization"))
        or mapping_value(after_payload.get("generated_materialization"))
    )
    function_config_id = (
        semantic_source_object_id
        or optional_text(operation.get("function_config_id"))
        or optional_text(before_payload.get("function_config_id"))
        or optional_text(before_payload.get("entity_id"))
        or optional_text(before_payload.get("object_id"))
        or optional_text(after_payload.get("function_config_id"))
        or optional_text(after_payload.get("entity_id"))
        or optional_text(after_payload.get("object_id"))
    )
    kind = (
        optional_text(before_payload.get("kind"))
        or optional_text(after_payload.get("kind"))
        or "instance"
    )
    operation_payload = function_config_delete_typed_operation(
        semantic_key=semantic_key,
        owner_semantic_key=f"meta.class:{class_name}",
        class_config_id=class_config_id or "",
        function_config_id=function_config_id or "",
        function_name=function_name,
        owner_key=owner_key,
        kind=kind,
        source_refs=source_refs,
        semantic_source_object_id=semantic_source_object_id,
    ).evidence_payload()
    baseline = mapping_value(operation_payload.get("baseline"))
    baseline_object = mapping_value(baseline.get("object"))
    current = mapping_value(operation_payload.get("current"))
    payload = mapping_value(current.get("payload"))
    for target in (baseline_object, current, payload):
        target["owner_semantic_key"] = f"meta.class:{class_name}"
        target["parent_semantic_key"] = f"meta.class:{class_name}"
        target["class_semantic_key"] = f"meta.class:{class_name}"
        target["owner_key"] = owner_key
        target["function_name"] = function_name
        target["name"] = function_name
        target["kind"] = kind
        if class_config_id is not None:
            target["class_config_id"] = class_config_id
        if function_config_id is not None:
            target["semantic_source_object_id"] = function_config_id
            target["function_config_id"] = function_config_id
            target["entity_id"] = function_config_id
            target["object_id"] = function_config_id
        if (
            executable_object_id is not None
            and executable_object_id != function_config_id
        ):
            target["semantic_apply_receiver_object_id"] = executable_object_id
            target["executable_object_id"] = executable_object_id
        if generated_materialization:
            target["generated_materialization"] = dict(generated_materialization)
    if baseline_object:
        baseline["object"] = baseline_object
    if payload:
        current["payload"] = payload
    operation_payload["baseline"] = baseline
    operation_payload["current"] = current
    operation_payload["operation_key"] = (
        optional_text(operation.get("operation_key"))
        or operation_payload["operation_key"]
    )
    operation_payload["source_semantic_change"] = {
        "event_ref": operation.get("event_key"),
        "semantic_key": semantic_key,
        "source": "aware_meta.semantic_apply.source_projection_evidence",
        "semantic_source_operation": dict(operation),
    }
    return operation_payload


def _meta_function_create_typed_operation_from_semantic_source_operation(
    operation: Mapping[str, object],
    *,
    default_source_refs: Sequence[str],
    semantic_key: str,
) -> dict[str, object]:
    after_payload = mapping_value(operation.get("after_payload"))
    class_name = (
        optional_text(after_payload.get("class_name"))
        or _function_class_from_semantic_key(semantic_key)
        or "UnknownClass"
    )
    function_name = (
        optional_text(after_payload.get("function_name"))
        or optional_text(after_payload.get("name"))
        or _function_name_from_semantic_key(semantic_key)
        or "unknown_function"
    )
    owner_key = optional_text(after_payload.get("class_fqn")) or class_name
    description = optional_text(
        after_payload.get("function_description")
    ) or optional_text(after_payload.get("description"))
    source_refs = tuple_text(operation.get("source_refs")) or tuple(default_source_refs)
    function_signature = {
        "owner_key": owner_key,
        "name": function_name,
        "kind": optional_text(after_payload.get("kind")) or "instance",
        "description": description,
        "verb": optional_text(after_payload.get("verb")),
        "is_async": after_payload.get("is_async") is True,
    }
    current = {
        "semantic_key": semantic_key,
        "object_kind": "function",
        "owner_semantic_key": f"meta.class:{class_name}",
        "class_config_id": optional_text(after_payload.get("class_config_id")),
        "entity_id": optional_text(after_payload.get("function_config_id")),
        "function_config_id": optional_text(after_payload.get("function_config_id")),
        "entity_name": function_name,
        "function_name": function_name,
        "owner_key": owner_key,
        "kind": function_signature["kind"],
        "description": description,
        "verb": function_signature["verb"],
        "is_async": function_signature["is_async"],
        "is_public": after_payload.get("is_public") is not False,
        "is_constructor": after_payload.get("is_constructor") is True,
        "position": _int_value(after_payload.get("position")) or 0,
        "function_signature": function_signature,
    }
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": (
            optional_text(operation.get("operation_key"))
            or f"semantic_apply.{class_name}.{function_name}.create"
        ),
        "operation_family": "create",
        "provider_operation_type": "meta_ocg.function.create",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.FunctionConfig",
        "ontology_subject_kind": "function",
        "source_refs": list(source_refs),
        "baseline": {},
        "current": {**current, "payload": current},
        "source_semantic_change": {
            "event_ref": operation.get("event_key"),
            "semantic_key": semantic_key,
            "source": "aware_meta.semantic_apply.source_projection_evidence",
            "semantic_source_operation": dict(operation),
        },
    }


def _semantic_apply_relationship_signature_payload(
    *,
    payload: Mapping[str, object],
    source_class_fqn: str,
    target_class_fqn: str | None,
    relationship_key: str,
    relationship_type: str | None,
) -> dict[str, object]:
    signature_payload = mapping_value(payload.get("relationship_signature"))
    signature: dict[str, object] = {
        "source_class_fqn": (
            optional_text(signature_payload.get("source_class_fqn")) or source_class_fqn
        ),
        "target_class_fqn": (
            optional_text(signature_payload.get("target_class_fqn")) or target_class_fqn
        ),
        "relationship_key": (
            optional_text(signature_payload.get("relationship_key")) or relationship_key
        ),
        "relationship_type": (
            optional_text(signature_payload.get("relationship_type"))
            or relationship_type
        ),
    }
    signature.update(_relationship_loading_strategy_fields(payload=payload))
    return signature


def _relationship_loading_strategy_fields(
    *,
    payload: Mapping[str, object],
) -> dict[str, object]:
    fields: dict[str, object] = {}
    forward_loading_strategy = optional_text(payload.get("forward_loading_strategy"))
    reverse_loading_strategy = optional_text(payload.get("reverse_loading_strategy"))
    for direction, strategy in _load_policy_arg_pairs(
        optional_text(payload.get("load_policy_args"))
        or optional_text(payload.get("ann_args"))
    ):
        if direction == "forward":
            forward_loading_strategy = strategy
        elif direction == "reverse":
            reverse_loading_strategy = strategy
    if forward_loading_strategy is not None:
        fields["forward_loading_strategy"] = forward_loading_strategy
    if reverse_loading_strategy is not None:
        fields["reverse_loading_strategy"] = reverse_loading_strategy
    return fields


def _load_policy_arg_pairs(value: str | None) -> tuple[tuple[str, str], ...]:
    if value is None:
        return ()
    tokens = tuple(part for part in value.split() if part)
    pairs: list[tuple[str, str]] = []
    index = 0
    while index + 1 < len(tokens):
        direction = tokens[index].strip().lower()
        strategy = tokens[index + 1].strip().lower()
        if direction in {"forward", "reverse"} and strategy:
            pairs.append((direction, strategy))
            index += 2
            continue
        index += 1
    return tuple(pairs)


def _semantic_apply_function_signature_payload(
    *,
    payload: Mapping[str, object],
    owner_key: str,
    function_name: str,
) -> dict[str, object]:
    signature_payload = mapping_value(payload.get("function_signature"))
    signature_text = optional_text(payload.get("signature")) or optional_text(
        payload.get("signature_text")
    )
    parsed_signature = _parse_aware_function_signature_text(signature_text)
    function_signature: dict[str, object] = {
        "owner_key": optional_text(signature_payload.get("owner_key")) or owner_key,
        "name": (
            optional_text(signature_payload.get("name"))
            or optional_text(payload.get("function_name"))
            or optional_text(payload.get("name"))
            or function_name
        ),
        "kind": (
            optional_text(signature_payload.get("kind"))
            or optional_text(payload.get("kind"))
            or "instance"
        ),
        "description": (
            optional_text(signature_payload.get("description"))
            or optional_text(payload.get("function_description"))
            or optional_text(payload.get("description"))
        ),
        "verb": (
            optional_text(signature_payload.get("verb"))
            or optional_text(payload.get("verb"))
        ),
        "is_async": _bool_value(
            signature_payload.get("is_async")
            if "is_async" in signature_payload
            else payload.get("is_async")
        ),
    }
    if signature_text is not None:
        function_signature["signature_text"] = signature_text
    if parsed_signature is not None:
        function_signature.update(parsed_signature)
    elif signature_payload:
        inputs = tuple(
            mapping_value(item)
            for item in _object_sequence(signature_payload.get("inputs"))
        )
        outputs = tuple(
            mapping_value(item)
            for item in _object_sequence(signature_payload.get("outputs"))
        )
        if "inputs" in signature_payload:
            function_signature["inputs"] = inputs
        if "outputs" in signature_payload:
            function_signature["outputs"] = outputs
    return function_signature


def _semantic_apply_function_membership_signature_payload(
    *,
    payload: Mapping[str, object],
    class_config_id: str | None,
    function_config_id: str | None,
) -> dict[str, object]:
    signature_payload = mapping_value(payload.get("function_membership_signature"))
    is_public = True
    if "is_public" in signature_payload:
        is_public = _bool_value(signature_payload.get("is_public"))
    elif "is_public" in payload:
        is_public = _bool_value(payload.get("is_public"))
    is_constructor = False
    if "is_constructor" in signature_payload:
        is_constructor = _bool_value(signature_payload.get("is_constructor"))
    elif "is_constructor" in payload:
        is_constructor = _bool_value(payload.get("is_constructor"))
    position = _int_value(
        signature_payload.get("position")
        if "position" in signature_payload
        else payload.get("position")
    )
    return {
        "class_config_id": (
            optional_text(signature_payload.get("class_config_id"))
            or class_config_id
        ),
        "function_config_id": (
            optional_text(signature_payload.get("function_config_id"))
            or function_config_id
        ),
        "is_public": is_public,
        "is_constructor": is_constructor,
        "position": position if position is not None else 0,
    }


def _parse_aware_function_signature_text(
    value: str | None,
) -> dict[str, object] | None:
    if value is None:
        return None
    raw_value = value.strip()
    if not raw_value.startswith("(") or "->" not in raw_value:
        return None
    inputs_text, return_text = raw_value.split("->", maxsplit=1)
    inputs_text = inputs_text.strip()
    return_text = return_text.strip()
    if not inputs_text.startswith("(") or not inputs_text.endswith(")"):
        return None
    input_items = _parse_aware_signature_input_items(inputs_text[1:-1].strip())
    if input_items is None:
        return None
    output_items = _parse_aware_signature_output_items(return_text)
    if output_items is None:
        return None
    return {
        "inputs": input_items,
        "outputs": output_items,
    }


def _parse_aware_signature_input_items(
    value: str,
) -> tuple[dict[str, object], ...] | None:
    if not value:
        return ()
    items: list[dict[str, object]] = []
    for index, raw_item in enumerate(_split_aware_signature_items(value)):
        item = _parse_aware_signature_named_type(
            raw_item,
            position=index,
            attribute_type="input",
        )
        if item is None:
            return None
        items.append(item)
    return tuple(items)


def _parse_aware_signature_output_items(
    value: str,
) -> tuple[dict[str, object], ...] | None:
    if value.startswith("(") and value.endswith(")"):
        items: list[dict[str, object]] = []
        for index, raw_item in enumerate(_split_aware_signature_items(value[1:-1])):
            item = _parse_aware_signature_named_type(
                raw_item,
                position=index,
                attribute_type="output",
            )
            if item is None:
                return None
            items.append(item)
        return tuple(items)
    descriptor, is_required = _aware_type_descriptor_from_text(value)
    return (
        {
            "name": "result",
            "type": "output",
            "position": 0,
            "is_required": is_required,
            "type_descriptor": descriptor,
        },
    )


def _parse_aware_signature_named_type(
    value: str,
    *,
    position: int,
    attribute_type: str,
) -> dict[str, object] | None:
    item = value.split("=", maxsplit=1)[0].strip()
    if item.endswith(" key"):
        item = item.removesuffix(" key").strip()
    parts = item.split(None, maxsplit=1)
    if len(parts) != 2:
        return None
    descriptor, is_required = _aware_type_descriptor_from_text(parts[1])
    return {
        "name": parts[0],
        "type": attribute_type,
        "position": position,
        "is_required": is_required,
        "type_descriptor": descriptor,
    }


def _split_aware_signature_items(value: str) -> tuple[str, ...]:
    items: list[str] = []
    start = 0
    depth = 0
    for index, char in enumerate(value):
        if char in "([{<":
            depth += 1
        elif char in ")]}>":
            depth = max(depth - 1, 0)
        elif char == "," and depth == 0:
            item = value[start:index].strip()
            if item:
                items.append(item)
            start = index + 1
    last_item = value[start:].strip()
    if last_item:
        items.append(last_item)
    return tuple(items)


def _aware_type_descriptor_from_text(
    value: str,
) -> tuple[dict[str, object], bool]:
    raw_value = value.strip()
    is_required = not raw_value.endswith("?")
    type_text = raw_value.removesuffix("?").strip()
    primitive_base_type = _primitive_base_type(type_text)
    if primitive_base_type in {
        "boolean",
        "date",
        "datetime",
        "decimal",
        "float",
        "integer",
        "json",
        "number",
        "string",
        "text",
        "uuid",
    }:
        return (
            {
                "kind": "primitive",
                "primitive_base_type": primitive_base_type,
            },
            is_required,
        )
    return (
        {
            "kind": "class",
            "class_fqn": type_text,
        },
        is_required,
    )


def _bool_value(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes"}
    return False


def _semantic_apply_attribute_payload(
    *,
    attribute_name: str,
    owner_key: str,
    field_path: str,
    payload: Mapping[str, object],
) -> dict[str, object]:
    type_text = optional_text(payload.get("type"))
    primitive_base_type, is_required = _primitive_type_descriptor_from_text(type_text)
    signature: dict[str, object] = {
        "name": attribute_name,
        "owner_key": owner_key,
        "is_required": is_required,
        "type_descriptor": {
            "kind": "primitive",
            "primitive_base_type": primitive_base_type,
        },
    }
    if field_path == "default_value" and "default_value" in payload:
        signature["default_value"] = payload["default_value"]
    return {
        "attribute_name": attribute_name,
        "owner_key": owner_key,
        "attribute_signature": signature,
    }


def _primitive_type_descriptor_from_text(
    value: str | None,
) -> tuple[str, bool]:
    raw_value = (value or "string").strip()
    is_required = not raw_value.endswith("?")
    return _primitive_base_type(raw_value.removesuffix("?")), is_required


def _primitive_base_type(value: str) -> str:
    key = value.strip().rsplit(".", maxsplit=1)[-1].lower()
    if key in {"int", "integer"}:
        return "integer"
    if key in {"str", "string"}:
        return "string"
    if key in {"bool", "boolean"}:
        return "boolean"
    return key


def _class_attribute_from_semantic_key(semantic_key: str) -> tuple[str, str]:
    if semantic_key.startswith("meta.attribute:"):
        raw = semantic_key.split(":", maxsplit=1)[-1]
        raw = raw.split("/membership:", maxsplit=1)[0]
        if "." in raw:
            class_name, attribute_name = raw.rsplit(".", maxsplit=1)
            return class_name, attribute_name
    marker = "/attribute:"
    if marker in semantic_key:
        owner, attribute_name = semantic_key.rsplit(marker, maxsplit=1)
        return (
            owner.rsplit(".", maxsplit=1)[-1],
            attribute_name.rsplit(
                "/",
                maxsplit=1,
            )[0],
        )
    return "unknown", "unknown"


def _attribute_semantic_key_from_membership_key(semantic_key: str) -> str:
    return semantic_key.split("/membership:", maxsplit=1)[0]


def _attribute_membership_signature_payload(
    *,
    payload: Mapping[str, object],
    class_name: str,
    attribute_name: str,
) -> dict[str, object]:
    signature = mapping_value(payload.get("attribute_membership_signature"))
    is_identity_key = payload.get("is_identity_key")
    if "is_identity_key" not in signature and isinstance(is_identity_key, bool):
        signature["is_identity_key"] = is_identity_key
    signature.setdefault("owner_kind", "class")
    for field_name in (
        "class_config_id",
        "attribute_config_id",
        "position",
    ):
        if field_name not in signature and field_name in payload:
            signature[field_name] = payload[field_name]
    signature.setdefault("class_name", class_name)
    signature.setdefault("attribute_name", attribute_name)
    return signature


def _changed_signature_fields(
    *,
    baseline_signature: Mapping[str, object],
    current_signature: Mapping[str, object],
) -> tuple[str, ...]:
    return tuple(
        field_name
        for field_name in ("position", "is_identity_key")
        if (
            field_name in baseline_signature
            and field_name in current_signature
            and baseline_signature[field_name] != current_signature[field_name]
        )
    )


def _attribute_class_from_semantic_key(semantic_key: str) -> str | None:
    class_name, _attribute_name = _class_attribute_from_semantic_key(semantic_key)
    return None if class_name == "unknown" else class_name


def _attribute_name_from_semantic_key(semantic_key: str) -> str | None:
    _class_name, attribute_name = _class_attribute_from_semantic_key(semantic_key)
    return None if attribute_name == "unknown" else attribute_name


def _relationship_class_from_semantic_key(semantic_key: str) -> str | None:
    if semantic_key.startswith("meta.relationship:"):
        raw = semantic_key.split(":", maxsplit=1)[-1]
        if "." in raw:
            return raw.rsplit(".", maxsplit=1)[0]
    marker = "/relationship:"
    if marker in semantic_key:
        owner = semantic_key.rsplit(marker, maxsplit=1)[0]
        return owner.rsplit(".", maxsplit=1)[-1]
    return None


def _relationship_key_from_semantic_key(semantic_key: str) -> str | None:
    if semantic_key.startswith("meta.relationship:"):
        raw = semantic_key.split(":", maxsplit=1)[-1]
        if "." in raw:
            return raw.rsplit(".", maxsplit=1)[-1]
    marker = "/relationship:"
    if marker in semantic_key:
        return semantic_key.rsplit(marker, maxsplit=1)[-1].split(
            "/",
            maxsplit=1,
        )[0]
    return None


def _relationship_type_from_semantic_key(semantic_key: str) -> str | None:
    _, separator, node_key = semantic_key.partition("/node:")
    if not separator:
        return None
    parts = node_key.split(":")
    if len(parts) < 3:
        return None
    return optional_text(parts[2])


def _owner_key_from_semantic_key(semantic_key: str) -> str | None:
    node_marker = "/node:"
    attribute_marker = "/attribute:"
    if node_marker not in semantic_key or attribute_marker not in semantic_key:
        return None
    return semantic_key.split(node_marker, maxsplit=1)[-1].split(
        attribute_marker,
        maxsplit=1,
    )[0]


def _function_class_from_semantic_key(semantic_key: str) -> str | None:
    if semantic_key.startswith("meta.function:"):
        raw = semantic_key.split(":", maxsplit=1)[-1]
        if "." in raw:
            return raw.rsplit(".", maxsplit=1)[0]
    marker = "/function:"
    if marker in semantic_key:
        owner, _function_name = semantic_key.rsplit(marker, maxsplit=1)
        return owner.rsplit(".", maxsplit=1)[-1]
    return None


def _function_name_from_semantic_key(semantic_key: str) -> str | None:
    if semantic_key.startswith("meta.function:"):
        raw = semantic_key.split(":", maxsplit=1)[-1]
        if "." in raw:
            return raw.rsplit(".", maxsplit=1)[-1]
    marker = "/function:"
    if marker in semantic_key:
        return semantic_key.rsplit(marker, maxsplit=1)[-1].split(
            "/",
            maxsplit=1,
        )[0]
    return None


def _class_name_from_class_semantic_key(semantic_key: str) -> str | None:
    if semantic_key.startswith("meta.class:"):
        raw = semantic_key.split(":", maxsplit=1)[-1]
        return raw.rsplit(".", maxsplit=1)[-1] or None
    marker = "/node:"
    if marker in semantic_key:
        node_key = semantic_key.split(marker, maxsplit=1)[-1].split(
            "/",
            maxsplit=1,
        )[0]
        return node_key.rsplit(".", maxsplit=1)[-1] or None
    return None


def _class_fqn_from_class_semantic_key(semantic_key: str) -> str | None:
    if semantic_key.startswith("meta.class:"):
        raw = semantic_key.split(":", maxsplit=1)[-1]
        return raw or None
    marker = "/node:"
    if marker in semantic_key:
        node_key = semantic_key.split(marker, maxsplit=1)[-1].split(
            "/",
            maxsplit=1,
        )[0]
        return node_key or None
    return None


def _enum_name_from_enum_semantic_key(semantic_key: str) -> str | None:
    if semantic_key.startswith("meta.enum:"):
        raw = semantic_key.split(":", maxsplit=1)[-1]
        return raw.rsplit(".", maxsplit=1)[-1] or None
    marker = "/node:"
    if marker in semantic_key:
        node_key = semantic_key.split(marker, maxsplit=1)[-1].split(
            "/",
            maxsplit=1,
        )[0]
        return node_key.rsplit(".", maxsplit=1)[-1] or None
    return None


def _enum_fqn_from_enum_semantic_key(semantic_key: str) -> str | None:
    if semantic_key.startswith("meta.enum:"):
        raw = semantic_key.split(":", maxsplit=1)[-1]
        return raw or None
    marker = "/node:"
    if marker in semantic_key:
        node_key = semantic_key.split(marker, maxsplit=1)[-1].split(
            "/",
            maxsplit=1,
        )[0]
        return node_key or None
    return None


def _enum_fqn_from_package_context(
    *,
    enum_name: str,
    raw_enum_fqn: str,
    operation: Mapping[str, object],
    source_refs: Sequence[str],
) -> str:
    if "." in raw_enum_fqn:
        return raw_enum_fqn
    fqn_prefix = _first_text(
        operation.get("fqn_prefix"),
        _fqn_prefix_from_package_root(operation.get("package_root")),
        _fqn_prefix_from_package_name(operation.get("package_name")),
    )
    source_namespace = _enum_source_namespace(source_refs=source_refs)
    if fqn_prefix is None or source_namespace is None:
        return raw_enum_fqn or enum_name
    return ".".join((fqn_prefix, "default", source_namespace, enum_name))


def _class_fqn_from_package_context(
    *,
    class_name: str,
    raw_class_fqn: str,
    operation: Mapping[str, object],
    source_refs: Sequence[str],
) -> str:
    if "." in raw_class_fqn:
        return raw_class_fqn
    fqn_prefix = _first_text(
        operation.get("fqn_prefix"),
        _fqn_prefix_from_package_root(operation.get("package_root")),
        _fqn_prefix_from_package_name(operation.get("package_name")),
    )
    source_namespace = _enum_source_namespace(source_refs=source_refs)
    if fqn_prefix is None or source_namespace is None:
        return raw_class_fqn or class_name
    return ".".join((fqn_prefix, "default", source_namespace, class_name))


def _enum_source_namespace(*, source_refs: Sequence[str]) -> str | None:
    for source_ref in source_refs:
        normalized = source_ref.replace("\\", "/").strip("/")
        if not normalized.endswith(".aware"):
            continue
        parts = tuple(part for part in normalized.split("/") if part)
        if "aware" in parts:
            parts = parts[parts.index("aware") + 1 :]
        if len(parts) < 2:
            continue
        namespace = ".".join(parts[:-1])
        if namespace:
            return namespace
    return None


def _graph_semantic_key_from_enum_semantic_key(value: str) -> str | None:
    graph_key, separator, _ = value.partition("/node:")
    if not separator:
        return None
    return optional_text(graph_key)


def _graph_semantic_key_from_class_semantic_key(value: str) -> str | None:
    graph_key, separator, _ = value.partition("/node:")
    if not separator:
        return None
    return optional_text(graph_key)


def _fqn_prefix_from_package_name(value: object) -> str | None:
    text = optional_text(value)
    if text is None or not text.endswith("-ontology"):
        return None
    package_key = text[: -len("-ontology")].replace("-", "_").strip("_")
    if not package_key:
        return None
    if package_key.startswith("aware_"):
        return package_key
    return f"aware_{package_key}"


def _fqn_prefix_from_package_root(value: object) -> str | None:
    text = optional_text(value)
    if text is None:
        return None
    parts = tuple(part for part in Path(text).parts if part)
    for index, part in enumerate(parts):
        if part == "modules" and index + 3 < len(parts):
            if parts[index + 2 : index + 4] == ("structure", "ontology"):
                module_key = parts[index + 1].replace("-", "_").strip("_")
                if module_key:
                    return (
                        module_key
                        if module_key.startswith("aware_")
                        else f"aware_{module_key}"
                    )
    return None


def _enum_semantic_key_from_option_semantic_key(value: str) -> str | None:
    enum_key, separator, _ = value.partition("/option:")
    if not separator:
        return None
    return optional_text(enum_key)


def _enum_option_value_from_semantic_key(value: str) -> str | None:
    _, separator, option_key = value.partition("/option:")
    if not separator:
        return None
    return optional_text(option_key)


def _class_fqn_from_class_name(class_name: str) -> str:
    return class_name


def _stable_attribute_config_id(
    *,
    owner_key: str,
    attribute_name: str,
) -> str | None:
    if not owner_key or not attribute_name:
        return None
    from aware_meta.graph.config.stable_ids import (  # noqa: WPS433
        stable_attribute_config_id,
    )

    return str(stable_attribute_config_id(owner_key=owner_key, name=attribute_name))


def _python_orm_relative_path_from_source_refs(
    *,
    source_refs: Sequence[str],
    package_name: str | None,
) -> str | None:
    sources_root = _python_orm_sources_root_from_package_name(package_name)
    for source_ref in source_refs:
        normalized = source_ref.replace("\\", "/").strip("/")
        if not normalized.endswith(".aware"):
            continue
        parts = tuple(part for part in normalized.split("/") if part)
        if "aware" in parts:
            parts = parts[parts.index("aware") + 1 :]
        if not parts:
            continue
        python_path = "/".join(parts)[: -len(".aware")] + ".py"
        return (
            python_path
            if sources_root is None or python_path.startswith(f"{sources_root}/")
            else f"{sources_root}/{python_path}"
        )
    return None


def _python_orm_sources_root_from_package_name(package_name: str | None) -> str | None:
    if package_name is None or not package_name.endswith("-ontology"):
        return None
    package_base = package_name[: -len("-ontology")].replace("-", "_").strip("_")
    if not package_base:
        return None
    if package_base.startswith("aware_"):
        return f"{package_base}_ontology"
    return f"aware_{package_base}_ontology"


def _first_text(*values: object) -> str | None:
    for value in values:
        text = optional_text(value)
        if text is not None:
            return text
    return None


def _int_value(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip():
        try:
            return int(value)
        except ValueError:
            return None
    return None


def _semantic_apply_source_refs(
    *,
    semantic_status: Mapping[str, object],
    source_refs: Sequence[str],
    source_text_by_ref: Mapping[str, str] | None,
    typed_operations: Sequence[Mapping[str, object]],
) -> tuple[str, ...]:
    operation_source_refs = tuple(
        source_ref
        for operation in typed_operations
        for source_ref in tuple_text(operation.get("source_refs"))
    )
    return _sorted_unique(
        (
            *source_refs,
            *(source_text_by_ref or {}).keys(),
            *operation_source_refs,
            *_semantic_status_source_refs(semantic_status=semantic_status),
        )
    )


def _semantic_status_source_refs(
    *,
    semantic_status: Mapping[str, object],
) -> tuple[str, ...]:
    packages = tuple(
        mapping_value(package)
        for package in _object_sequence(semantic_status.get("packages"))
    )
    return tuple(
        source_ref
        for package in packages
        for source_ref in tuple_text(package.get("source_refs"))
    )


def _semantic_status_delta_fingerprint(
    *,
    semantic_status: Mapping[str, object],
) -> str | None:
    for package in _object_sequence(semantic_status.get("packages")):
        package_payload = mapping_value(package)
        fingerprint = optional_text(package_payload.get("delta_fingerprint"))
        if fingerprint is not None:
            return fingerprint
        source_meaning = mapping_value(package_payload.get("semantic_source_meaning"))
        evidence = mapping_value(source_meaning.get("source_index_evidence"))
        current = mapping_value(evidence.get("current"))
        session = mapping_value(current.get("session"))
        fingerprint = optional_text(session.get("source_delta_fingerprint"))
        if fingerprint is not None:
            return fingerprint
    return None


def _source_text_fingerprint(source_text_by_ref: Mapping[str, str]) -> str:
    joined = "\n".join(
        f"{source_ref}\0{source_text}"
        for source_ref, source_text in sorted(source_text_by_ref.items())
    )
    return _sha256_text(joined)


def _semantic_apply_source_projection_stage_with_context(
    *,
    stage: Mapping[str, object],
    semantic_apply: Mapping[str, object],
    source_text_by_ref: Mapping[str, str],
    source_session_context: Mapping[str, object] | None,
    commit_ids: Sequence[str],
    head_commit_ids: Sequence[str],
    metadata: Mapping[str, object] | None,
) -> dict[str, object]:
    payload = {str(key): value for key, value in stage.items()}
    request = mapping_value(payload.get("grammar_anchor_render_delta_request"))
    request_metadata = {
        **mapping_value(request.get("metadata")),
        "source": "aware_meta.semantic_apply.source_projection_evidence",
        "contract_version": (
            META_SEMANTIC_APPLY_SOURCE_PROJECTION_EVIDENCE_CONTRACT_VERSION
        ),
        "semantic_apply_status": semantic_apply.get("status"),
        "semantic_apply_commit_ids": tuple(commit_ids),
        "semantic_apply_head_commit_ids": tuple(head_commit_ids),
        "semantic_source_session_context": dict(source_session_context or {}),
        "caller_metadata": (
            {str(key): value for key, value in metadata.items()} if metadata else {}
        ),
    }
    if request:
        sources = tuple(
            _grammar_anchor_render_source_with_text(
                source=mapping_value(source),
                source_text_by_ref=source_text_by_ref,
            )
            for source in _object_sequence(request.get("sources"))
        )
        baseline_fingerprint = optional_text(
            request.get("baseline_fingerprint")
        ) or _first_source_text_hash(source_text_by_ref=source_text_by_ref)
        request = {
            **request,
            "baseline_fingerprint": baseline_fingerprint,
            "baseline_fingerprint_algorithm": (
                optional_text(request.get("baseline_fingerprint_algorithm")) or "sha256"
            ),
            "sources": sources,
            "metadata": request_metadata,
        }
        payload["grammar_anchor_render_delta_request"] = request
    payload["metadata"] = {
        **mapping_value(payload.get("metadata")),
        "source": "aware_meta.semantic_apply.source_projection_evidence",
        "contract_version": (
            META_SEMANTIC_APPLY_SOURCE_PROJECTION_EVIDENCE_CONTRACT_VERSION
        ),
        "semantic_apply_status": semantic_apply.get("status"),
        "semantic_apply_commit_ids": tuple(commit_ids),
        "semantic_apply_head_commit_ids": tuple(head_commit_ids),
        "semantic_source_session_context": dict(source_session_context or {}),
        "caller_metadata": (
            {str(key): value for key, value in metadata.items()} if metadata else {}
        ),
    }
    return payload


def _grammar_anchor_render_source_with_text(
    *,
    source: Mapping[str, object],
    source_text_by_ref: Mapping[str, str],
) -> dict[str, object]:
    payload = {str(key): value for key, value in source.items()}
    source_key = optional_text(payload.get("source_key"))
    relative_path = optional_text(payload.get("relative_path"))
    for source_ref in (source_key, relative_path):
        if source_ref is not None and source_ref in source_text_by_ref:
            source_text = source_text_by_ref[source_ref]
            payload["source_text"] = source_text
            payload["before_hash"] = _sha256_text(source_text)
            return payload
    return payload


def _first_source_text_hash(
    *,
    source_text_by_ref: Mapping[str, str],
) -> str | None:
    for source_ref in sorted(source_text_by_ref):
        return _sha256_text(source_text_by_ref[source_ref])
    return None


def _sha256_text(text: str) -> str:
    return "sha256:" + sha256(text.encode("utf-8")).hexdigest()


def _object_sequence(value: object) -> tuple[object, ...]:
    if isinstance(value, (str, bytes)):
        return ()
    if isinstance(value, tuple):
        return value
    if isinstance(value, list):
        return tuple(value)
    return ()


def code_source_projection_request_from_meta_change_report(
    report_payload: Mapping[str, object] | MetaProviderDeltaSemanticChangeReport,
    *,
    package_name: str | None = None,
    package_root: str | None = None,
    sources_root: str | None = None,
    product_intent: str = META_SOURCE_PROJECTION_PRODUCT_INTENT,
    target_language: object | None = None,
    semantic_owner: str = "aware_meta.ocg",
    baseline_fingerprint: str | None = None,
    source_refs: Sequence[str] = (),
    require_ready: bool = True,
) -> CodeSourceProjectionRequest:
    """Translate Meta provider-delta change evidence into Code source_projection input."""

    report = (
        report_payload
        if isinstance(report_payload, MetaProviderDeltaSemanticChangeReport)
        else MetaProviderDeltaSemanticChangeReport.from_payload(report_payload)
    )
    if require_ready and not report.ready:
        blockers = ", ".join(report.blockers) or report.reason or "unknown"
        raise ValueError(
            "Meta source_projection request requires a ready semantic change "
            f"report; blockers={blockers}."
        )

    events = tuple(
        _event_ref_from_meta_world_change_event(event)
        for event in report.semantic_world_changes
    )
    if require_ready and not events:
        raise ValueError(
            "Meta source_projection request requires at least one semantic "
            "world change."
        )
    normalized_target_language = optional_text(target_language)

    action_bindings = tuple(
        _action_binding_from_meta_world_change_event(
            event,
            product_intent=product_intent,
            target_language=normalized_target_language,
        )
        for event in report.semantic_world_changes
    )
    request_source_refs = _sorted_unique(
        (
            *source_refs,
            *(
                source_ref
                for event in report.semantic_world_changes
                for source_ref in event.source_refs
            ),
        )
    )
    return CodeSourceProjectionRequest(
        provider_key=META_SOURCE_PROJECTION_PROVIDER_KEY,
        semantic_owner=semantic_owner,
        package_name=package_name,
        package_root=package_root,
        sources_root=sources_root,
        product_intent=product_intent,
        target_language=normalized_target_language,
        baseline_fingerprint=baseline_fingerprint,
        baseline_fingerprint_algorithm="sha256",
        events=list(events),
        action_bindings=list(action_bindings),
        source_refs=list(request_source_refs),
        metadata=_json_object(
            {
                "source": "aware_meta.provider_delta.semantic_change_report",
                "provider_report_contract_version": report.contract_version,
                "provider_report_status": report.status,
                "provider_report_reason": report.reason,
                "semantic_dirty_entry_count": report.semantic_dirty_entry_count,
                "semantic_world_change_count": (report.semantic_world_change_count),
                "readable_semantic_change_chain": (
                    report.readable_semantic_change_chain.evidence_payload()
                ),
            }
        ),
    )


def code_source_projection_result_from_meta_section_delta_entries(
    report_payload: Mapping[str, object] | MetaProviderDeltaSemanticChangeReport,
    *,
    projection: CodeSourceProjectionRequest,
    delta_entries: Sequence[CodeSectionDeltaEntry],
    handled_event_keys: Sequence[str] = (),
    diagnostics: Sequence[str] = (),
    receipt_refs: Sequence[str] = (),
    semantic_owner: str | None = None,
    require_ready: bool = True,
    require_projected: bool = True,
) -> CodeSourceProjectionResult:
    """Build Meta provider output evidence with Code-owned section deltas."""

    return _code_source_projection_result_from_entries(
        report_payload,
        projection=projection,
        entries=delta_entries,
        handled_event_keys=handled_event_keys,
        skipped_results=(),
        diagnostics=diagnostics,
        receipt_refs=receipt_refs,
        semantic_owner=semantic_owner,
        require_ready=require_ready,
        require_projected=require_projected,
    )


def _code_source_projection_result_from_entries(
    report_payload: Mapping[str, object] | MetaProviderDeltaSemanticChangeReport,
    *,
    projection: CodeSourceProjectionRequest,
    entries: Sequence[CodeSectionDeltaEntry],
    handled_event_keys: Sequence[str],
    skipped_results: Sequence[MetaProviderDeltaSourceProjectionFeatureResult],
    diagnostics: Sequence[str],
    receipt_refs: Sequence[str],
    semantic_owner: str | None,
    require_ready: bool,
    require_projected: bool,
) -> CodeSourceProjectionResult:
    """Build Meta provider output evidence with Code-owned section deltas."""

    report = _semantic_change_report(report_payload)
    if require_ready and not report.ready:
        blockers = ", ".join(report.blockers) or report.reason or "unknown"
        raise ValueError(
            "Meta source_projection result requires a ready semantic change "
            f"report; blockers={blockers}."
        )
    if projection.provider_key != META_SOURCE_PROJECTION_PROVIDER_KEY:
        raise ValueError(
            "Meta source_projection result requires a projection owned by "
            f"{META_SOURCE_PROJECTION_PROVIDER_KEY!r}."
        )

    report_event_keys = tuple(
        _event_key(event) for event in report.semantic_world_changes
    )
    if require_ready and not report_event_keys:
        raise ValueError(
            "Meta source_projection result requires at least one semantic "
            "world change."
        )

    normalized_entries = tuple(
        CodeSectionDeltaEntry.model_validate(entry.model_dump(mode="json"))
        for entry in entries
    )
    if require_projected and not normalized_entries:
        raise ValueError(
            "Meta source_projection result requires at least one Code section "
            "delta entry."
        )

    handled_keys = _handled_event_keys(
        entries=normalized_entries,
        handled_event_keys=handled_event_keys,
        report_event_keys=report_event_keys,
    )
    unknown_keys = sorted(set(handled_keys) - set(report_event_keys))
    if unknown_keys:
        raise ValueError(
            "Meta source_projection result references unknown event keys: "
            + ", ".join(unknown_keys)
        )

    skipped_result_by_event_key = _skipped_result_by_event_key(
        skipped_results=skipped_results,
    )
    skipped_events = tuple(
        _skipped_event_from_meta_world_change_event(
            event=event,
            projection=projection,
            feature_result=skipped_result_by_event_key.get(_event_key(event)),
        )
        for event in report.semantic_world_changes
        if _event_key(event) not in handled_keys
    )
    delta_set = (
        CodeSectionDeltaSet(
            package_name=projection.package_name,
            package_root=projection.package_root,
            sources_root=projection.sources_root,
            baseline_fingerprint=projection.baseline_fingerprint,
            baseline_fingerprint_algorithm=(
                projection.baseline_fingerprint_algorithm or "sha256"
            ),
            entries=list(normalized_entries),
            metadata=_json_object(
                {
                    "source": "aware_meta.source_projection.section_delta_entries",
                    "provider_key": META_SOURCE_PROJECTION_PROVIDER_KEY,
                    "product_intent": projection.product_intent,
                    "semantic_world_change_count": len(report_event_keys),
                    "projected_event_keys": tuple(sorted(handled_keys)),
                }
            ),
        )
        if normalized_entries
        else None
    )
    return CodeSourceProjectionResult(
        provider_key=META_SOURCE_PROJECTION_PROVIDER_KEY,
        semantic_owner=semantic_owner or projection.semantic_owner or "aware_meta.ocg",
        projected=bool(entries),
        delta_set=delta_set,
        diagnostics=list(diagnostics),
        skipped_events=list(skipped_events),
        receipt_refs=list(receipt_refs),
        metadata=_json_object(
            {
                "source": "aware_meta.provider_delta.source_projection_result",
                "provider_report_contract_version": report.contract_version,
                "provider_report_status": report.status,
                "provider_report_reason": report.reason,
                "semantic_dirty_entry_count": report.semantic_dirty_entry_count,
                "semantic_world_change_count": (report.semantic_world_change_count),
            }
        ),
    )


def code_section_delta_entries_from_meta_function_impl_typed_operations(
    provider_delta_typed_operation_plan: Mapping[str, object],
    *,
    package_name: str | None = None,
    target_language: object | None = None,
    require_ready: bool = True,
) -> tuple[CodeSectionDeltaEntry, ...]:
    """Build Code-owned section deltas from explicit FunctionImpl projection hints."""

    typed_plan = MetaProviderDeltaTypedOperationPlan.from_payload(
        provider_delta_typed_operation_plan
    )
    if require_ready and typed_plan.status != "typed_operation_plan_ready":
        raise ValueError(
            "Meta FunctionImpl section-delta adapter requires a ready typed "
            f"operation plan; status={typed_plan.status or 'unknown'}."
        )

    return tuple(
        entry
        for result in (
            source_projection_feature_results_from_meta_typed_operations(
                provider_delta_typed_operation_plan,
                package_name=package_name,
                target_language=target_language,
                require_ready=require_ready,
            )
        )
        for entry in result.entries
    )


def source_projection_feature_results_from_meta_typed_operations(
    provider_delta_typed_operation_plan: Mapping[str, object],
    *,
    package_name: str | None = None,
    package_root: str | None = None,
    sources_root: str | None = None,
    target_language: object | None = None,
    require_ready: bool = True,
) -> tuple[MetaProviderDeltaSourceProjectionFeatureResult, ...]:
    """Build per-feature source-projection evidence from Meta typed operations."""

    typed_plan = MetaProviderDeltaTypedOperationPlan.from_payload(
        provider_delta_typed_operation_plan
    )
    if require_ready and typed_plan.status != "typed_operation_plan_ready":
        raise ValueError(
            "Meta source-projection feature result adapter requires a ready "
            f"typed operation plan; status={typed_plan.status or 'unknown'}."
        )

    results: list[MetaProviderDeltaSourceProjectionFeatureResult] = []
    context = MetaProviderDeltaSourceProjectionContext(
        package_name=package_name,
        package_root=package_root,
        sources_root=sources_root,
        target_language=optional_text(target_language),
    )
    for operation in typed_plan.typed_operations:
        results.extend(
            source_projection_feature_results_from_typed_operation(
                operation=operation,
                context=context,
            )
        )
    return tuple(results)


def code_source_projection_result_from_meta_feature_results(
    report_payload: Mapping[str, object] | MetaProviderDeltaSemanticChangeReport,
    *,
    projection: CodeSourceProjectionRequest,
    feature_results: Sequence[MetaProviderDeltaSourceProjectionFeatureResult],
    diagnostics: Sequence[str] = (),
    receipt_refs: Sequence[str] = (),
    semantic_owner: str | None = None,
    require_ready: bool = True,
    require_projected: bool = True,
) -> CodeSourceProjectionResult:
    entries = tuple(entry for result in feature_results for entry in result.entries)
    handled_event_keys = tuple(
        event_ref
        for result in feature_results
        if result.projected
        for event_ref in result.event_refs
    )
    skipped_results = tuple(
        result for result in feature_results if not result.projected
    )
    return _code_source_projection_result_from_entries(
        report_payload,
        projection=projection,
        entries=entries,
        handled_event_keys=handled_event_keys,
        skipped_results=skipped_results,
        diagnostics=diagnostics,
        receipt_refs=receipt_refs,
        semantic_owner=semantic_owner,
        require_ready=require_ready,
        require_projected=require_projected,
    )


def code_grammar_anchor_render_delta_request_from_meta_feature_results(
    *,
    projection: CodeSourceProjectionRequest,
    feature_results: Sequence[MetaProviderDeltaSourceProjectionFeatureResult],
) -> ResolveCodeGrammarAnchorRenderDeltaRequest | None:
    bindings = _unique_grammar_anchor_bindings(
        binding
        for result in feature_results
        for binding in result.grammar_anchor_bindings
    )
    sources = _unique_grammar_anchor_sources(
        source for result in feature_results for source in result.grammar_anchor_sources
    )
    replacements = tuple(
        replacement
        for result in feature_results
        for replacement in result.grammar_anchor_replacements
    )
    if not bindings and not sources and not replacements:
        return None
    return ResolveCodeGrammarAnchorRenderDeltaRequest(
        package_name=projection.package_name,
        package_root=projection.package_root,
        sources_root=projection.sources_root,
        baseline_fingerprint=projection.baseline_fingerprint,
        baseline_fingerprint_algorithm=(
            projection.baseline_fingerprint_algorithm or "sha256"
        ),
        bindings=list(bindings),
        sources=list(sources),
        replacements=list(replacements),
        strict=True,
        metadata=_json_object(
            {
                "source": "aware_meta.provider_delta.grammar_anchor_render_delta_request",
                "provider_key": META_SOURCE_PROJECTION_PROVIDER_KEY,
                "product_intent": projection.product_intent,
                "source_projection_request_source": (
                    projection.metadata.get("source")
                    if projection.metadata is not None
                    else None
                ),
            }
        ),
    )


def _semantic_change_report(
    report_payload: Mapping[str, object] | MetaProviderDeltaSemanticChangeReport,
) -> MetaProviderDeltaSemanticChangeReport:
    return (
        report_payload
        if isinstance(report_payload, MetaProviderDeltaSemanticChangeReport)
        else MetaProviderDeltaSemanticChangeReport.from_payload(report_payload)
    )


def _provider_delta_source_projection_blocked_stage(
    *,
    reason: str,
    current_delta_fingerprint: str,
    report: MetaProviderDeltaSemanticChangeReport,
    typed_plan: MetaProviderDeltaTypedOperationPlan,
) -> dict[str, object]:
    return {
        "stage_kind": "meta_ocg_provider_delta_source_projection",
        "contract_version": META_PROVIDER_DELTA_SOURCE_PROJECTION_CONTRACT_VERSION,
        "status": "source_projection_blocked",
        "reason": reason,
        "available": False,
        "ready": False,
        "blocked": True,
        "projected": False,
        "provider_key": META_SOURCE_PROJECTION_PROVIDER_KEY,
        "current_delta_fingerprint": current_delta_fingerprint,
        "semantic_change_report_status": report.status,
        "typed_operation_plan_status": typed_plan.status,
        "change_count": report.semantic_world_change_count,
        "action_count": 0,
        "feature_result_count": 0,
        "projected_entry_count": 0,
        "grammar_anchor_binding_count": 0,
        "grammar_anchor_source_count": 0,
        "grammar_anchor_replacement_count": 0,
        "blocked_feature_result_count": 0,
        "skipped_feature_result_count": 0,
        "skipped_change_count": 0,
        "diagnostics": (),
        "projection": None,
        "result": None,
        "grammar_anchor_render_delta_request": None,
        "feature_results": (),
    }


def _provider_delta_source_projection_status_and_reason(
    *,
    projected_entry_count: int,
    grammar_anchor_replacement_count: int,
    blocked_count: int,
    skipped_count: int,
    feature_result_count: int,
) -> tuple[str, str]:
    if blocked_count:
        return (
            "source_projection_blocked",
            "meta_source_projection_feature_result_blocked",
        )
    if projected_entry_count:
        return (
            "source_projection_ready",
            "meta_source_projection_section_delta_entries_ready",
        )
    if grammar_anchor_replacement_count:
        return (
            "source_projection_ready",
            "meta_source_projection_grammar_anchor_render_delta_ready",
        )
    if skipped_count or feature_result_count:
        return (
            "source_projection_skipped",
            "meta_source_projection_no_projected_section_delta_entries",
        )
    return (
        "source_projection_not_required",
        "meta_source_projection_no_typed_operations",
    )


def _source_projection_feature_diagnostics(
    feature_results: Sequence[MetaProviderDeltaSourceProjectionFeatureResult],
) -> tuple[str, ...]:
    return tuple(
        diagnostic for result in feature_results for diagnostic in result.diagnostics
    )


def _unique_grammar_anchor_bindings(
    bindings: Iterable[CodeGrammarAnchorBinding],
) -> tuple[CodeGrammarAnchorBinding, ...]:
    by_key: dict[str, CodeGrammarAnchorBinding] = {}
    for binding in bindings:
        by_key.setdefault(binding.binding_key, binding)
    return tuple(by_key[key] for key in sorted(by_key))


def _unique_grammar_anchor_sources(
    sources: Iterable[CodeGrammarAnchorRenderSource],
) -> tuple[CodeGrammarAnchorRenderSource, ...]:
    by_key: dict[str, CodeGrammarAnchorRenderSource] = {}
    for source in sources:
        by_key.setdefault(source.source_key, source)
    return tuple(by_key[key] for key in sorted(by_key))


def _source_projection_package_name(
    *,
    package_payload: Mapping[str, object],
    code_package_delta: object | None,
) -> str | None:
    return (
        optional_text(getattr(code_package_delta, "package_name", None))
        or optional_text(package_payload.get("package_name"))
        or optional_text(package_payload.get("code_package_name"))
    )


def _source_projection_package_root(
    *,
    manifest_path: Path,
    code_package_delta: object | None,
) -> str:
    return _anchored_source_projection_package_root(
        manifest_path=manifest_path,
        package_root=(
            optional_text(_code_package_delta_value(code_package_delta, "package_root"))
            or manifest_path.parent.as_posix()
        ),
    )


def _source_projection_sources_root(
    *,
    code_package_delta: object | None,
) -> str | None:
    return optional_text(_code_package_delta_value(code_package_delta, "sources_root"))


def _source_projection_target_language(
    *,
    code_package_delta: object | None,
) -> str | None:
    paths = _code_package_delta_value(code_package_delta, "paths")
    if not isinstance(paths, (list, tuple)):
        return None
    for path in paths:
        language = optional_text(_code_package_delta_value(path, "language"))
        if language is not None:
            return language
    return None


def _source_projection_delta_source_refs(
    *,
    code_package_delta: object | None,
) -> tuple[str, ...]:
    paths = _code_package_delta_value(code_package_delta, "paths")
    if not isinstance(paths, (list, tuple)):
        return ()
    return tuple(
        relative_path
        for path in paths
        for relative_path in (
            optional_text(_code_package_delta_value(path, "relative_path")),
        )
        if relative_path is not None
    )


def _code_package_delta_value(value: object | None, key: str) -> object | None:
    if value is None:
        return None
    if isinstance(value, Mapping):
        return value.get(key)
    return getattr(value, key, None)


def _anchored_source_projection_package_root(
    *,
    manifest_path: Path,
    package_root: str,
) -> str:
    package_root_path = Path(package_root).expanduser()
    if package_root_path.is_absolute():
        return package_root_path.resolve().as_posix()

    if not manifest_path.is_absolute():
        return package_root_path.as_posix()

    resolved_manifest_path = manifest_path.expanduser().resolve()
    for owner_root in (
        resolved_manifest_path.parent,
        *resolved_manifest_path.parents,
    ):
        candidate = (owner_root / package_root_path).resolve()
        try:
            resolved_manifest_path.relative_to(candidate)
        except ValueError:
            continue
        return candidate.as_posix()
    return (resolved_manifest_path.parent / package_root_path).resolve().as_posix()


def _event_ref_from_meta_world_change_event(
    event: MetaProviderDeltaSemanticWorldChange,
) -> CodeSourceProjectionEventRef:
    event_key = _event_key(event)
    return CodeSourceProjectionEventRef(
        event_key=event_key,
        semantic_key=event.semantic_key,
        verb=event.verb,
        subject_type=event.ontology_subject_kind or event.subject_type,
        source=event.source or "aware_meta.provider_delta.semantic_world_change",
        source_refs=list(event.source_refs),
        payload=_json_object(event.evidence_payload()),
        metadata=_json_object(
            {
                "provider_key": META_SOURCE_PROJECTION_PROVIDER_KEY,
                "provider_change_kind": event.change_kind,
                "provider_change_contract_version": event.contract_version,
                "change_type": event.change_type,
                "subject_label": event.subject_label,
                "subject_description": event.subject_description,
                "provider_operation_type": event.provider_operation_type,
                "delta_keys": event.delta_keys,
                "condition_keys": event.condition_keys,
            }
        ),
    )


def _action_binding_from_meta_world_change_event(
    event: MetaProviderDeltaSemanticWorldChange,
    *,
    product_intent: str,
    target_language: str | None,
) -> CodeSourceProjectionActionBinding:
    event_key = _event_key(event)
    action_key = f"aware_meta.source_projection:{event_key}"
    policy_parts = (
        META_SOURCE_PROJECTION_POLICY_PREFIX,
        event.ontology_subject_kind,
        event.verb,
    )
    policy_key = ".".join(part for part in policy_parts if part)
    return CodeSourceProjectionActionBinding(
        action_key=action_key,
        event_key=event_key,
        action_type="source_projection",
        policy_key=policy_key,
        product_intent=product_intent,
        target_language=target_language,
        metadata=_json_object(
            {
                "provider_key": META_SOURCE_PROJECTION_PROVIDER_KEY,
                "semantic_key": event.semantic_key,
                "ontology_subject_kind": event.ontology_subject_kind,
                "subject_label": event.subject_label,
                "provider_operation_type": event.provider_operation_type,
            }
        ),
    )


def _skipped_event_from_meta_world_change_event(
    *,
    event: MetaProviderDeltaSemanticWorldChange,
    projection: CodeSourceProjectionRequest,
    feature_result: MetaProviderDeltaSourceProjectionFeatureResult | None = None,
) -> CodeSourceProjectionSkippedEvent:
    event_key = _event_key(event)
    return CodeSourceProjectionSkippedEvent(
        event_key=event_key,
        action_key=_action_key_for_event_key(
            projection=projection,
            event_key=event_key,
        ),
        semantic_key=event.semantic_key,
        reason=(
            feature_result.reason
            if feature_result is not None
            else "no CodeSectionDeltaEntry emitted for Meta world change"
        ),
        metadata=_json_object(
            {
                "provider_key": META_SOURCE_PROJECTION_PROVIDER_KEY,
                "ontology_subject_kind": event.ontology_subject_kind,
                "provider_operation_type": event.provider_operation_type,
                "feature_key": (
                    feature_result.feature_key if feature_result is not None else None
                ),
                "source_projection_status": (
                    feature_result.status if feature_result is not None else None
                ),
                "required_evidence_fields": (
                    feature_result.required_evidence_fields
                    if feature_result is not None
                    else ()
                ),
                "missing_evidence_fields": (
                    feature_result.missing_evidence_fields
                    if feature_result is not None
                    else ()
                ),
            }
        ),
    )


def _action_key_for_event_key(
    *,
    projection: CodeSourceProjectionRequest,
    event_key: str,
) -> str | None:
    for action in projection.action_bindings:
        if action.event_key == event_key:
            return action.action_key
    return None


def _event_key(event: MetaProviderDeltaSemanticWorldChange) -> str:
    return (
        optional_text(event.change_key)
        or optional_text(event.semantic_key)
        or "aware_meta.provider_delta.world_change.unknown"
    )


def _handled_event_keys(
    *,
    entries: Sequence[CodeSectionDeltaEntry],
    handled_event_keys: Sequence[str],
    report_event_keys: Sequence[str],
) -> frozenset[str]:
    keys = {text for item in handled_event_keys for text in tuple_text(item)}
    keys.update(text for entry in entries for text in tuple_text(entry.event_ref))
    if entries and not keys and len(report_event_keys) == 1:
        keys.add(report_event_keys[0])
    return frozenset(keys)


def _skipped_result_by_event_key(
    *,
    skipped_results: Sequence[MetaProviderDeltaSourceProjectionFeatureResult],
) -> dict[str, MetaProviderDeltaSourceProjectionFeatureResult]:
    result_by_event_key: dict[str, MetaProviderDeltaSourceProjectionFeatureResult] = {}
    for result in skipped_results:
        for event_ref in result.event_refs:
            result_by_event_key.setdefault(event_ref, result)
    return result_by_event_key


def _sorted_unique(values: Iterable[str | object]) -> tuple[str, ...]:
    return tuple(sorted({text for item in values for text in tuple_text(item)}))


def _json_object(payload: Mapping[str, object]) -> JsonObject:
    return JsonObject(cast(Any, dict(payload)))


__all__ = [
    "META_SOURCE_PROJECTION_POLICY_PREFIX",
    "META_SOURCE_PROJECTION_PRODUCT_INTENT",
    "META_SOURCE_PROJECTION_PROVIDER_KEY",
    "META_PROVIDER_DELTA_SOURCE_PROJECTION_CONTRACT_VERSION",
    "META_SEMANTIC_APPLY_SOURCE_PROJECTION_EVIDENCE_CONTRACT_VERSION",
    "code_section_delta_entries_from_meta_function_impl_typed_operations",
    "code_grammar_anchor_render_delta_request_from_meta_feature_results",
    "code_source_projection_result_from_meta_feature_results",
    "code_source_projection_request_from_meta_change_report",
    "code_source_projection_result_from_meta_section_delta_entries",
    "provider_delta_result_from_semantic_apply_source_projection_evidence",
    "provider_delta_source_projection_stage",
    "source_projection_feature_results_from_meta_typed_operations",
    "typed_operation_plan_from_semantic_source_meaning",
]
