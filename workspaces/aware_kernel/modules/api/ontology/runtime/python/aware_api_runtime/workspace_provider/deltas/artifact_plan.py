from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any, cast

from aware_api_runtime.ir import (
    APICompilePlan,
    APIRuntimeArtifacts,
    bind_api_endpoint_class_config_ids,
    emit_api_runtime_artifacts,
)
from aware_api_runtime.compile import resolve_api_runtime_package_dir
from aware_api_runtime.ontology_graph.ontology import build_api_ontology_plans
from aware_api_runtime.dependencies.runtime_resolution import (
    canonicalize_api_accessible_dependency_graphs,
    collect_api_dependency_class_config_ids_from_graphs,
    load_api_accessible_dependency_graphs_from_runtime_artifact,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_utils.string_transform import to_snake_case


API_PRODUCT_RUNTIME_DELTA_PLAN_CONTRACT_VERSION = (
    "aware.api.provider-delta-api-product-runtime-delta-plan.v1"
)
API_RUNTIME_ARTIFACT_FRAGMENT_PLAN_CONTRACT_VERSION = (
    "aware.api.provider-delta-runtime-artifact-fragment-plan.v1"
)
API_GENERATED_PATH_CANDIDATE_PLAN_CONTRACT_VERSION = (
    "aware.api.provider-delta-generated-path-candidate-plan.v1"
)
API_SERVICE_PROTOCOL_RENDER_SECTION_PLAN_CONTRACT_VERSION = (
    "aware.api.service-protocol-render-section-plan.v1"
)

_REQUIRED_BUNDLE_HEAD_REF_FIELDS = (
    "source_code_package_id",
    "source_object_instance_graph_commit_id",
    "semantic_package_id",
    "semantic_branch_id",
    "semantic_head_commit_id",
    "semantic_object_instance_graph_commit_id",
)
_SUPPORTED_FRAGMENT_SUBJECT_KINDS = (
    "api",
    "api_capability",
    "api_capability_endpoint",
)
_SUPPORTED_FRAGMENT_OPERATION_FAMILIES = ("create", "update")


def api_product_runtime_delta_plan(
    *,
    manifest_path: Path,
    package_name: str,
    current_delta_fingerprint: str,
    snapshot: object,
    analysis: object,
    provider_delta_head_move_plan: Mapping[str, object],
    provider_delta_typed_operation_plan: Mapping[str, object],
    operation_execution: Mapping[str, object],
    package_source_execution: Mapping[str, object],
    commit_ref_payload: Mapping[str, object],
    semantic_dirty_diff: Mapping[str, object] | None = None,
    workspace_root: Path | None = None,
    accessible_graphs: Sequence[ObjectConfigGraph] = (),
    runtime_artifact_emitter: Callable[..., Mapping[str, object]] | None = None,
) -> dict[str, object]:
    bundle_package = _mapping_payload(commit_ref_payload.get("bundle_package"))
    head_refs = _head_refs(bundle_package=bundle_package)
    missing_head_ref_fields = tuple(
        field_name
        for field_name in _REQUIRED_BUNDLE_HEAD_REF_FIELDS
        if field_name not in head_refs
    )
    preflight_candidate_plan = _api_generated_path_candidate_plan_preflight(
        semantic_dirty_diff=semantic_dirty_diff,
        analysis=analysis,
        snapshot=snapshot,
        package_name=package_name,
    )
    preflight_fragment_plan = _api_runtime_artifact_fragment_plan(
        semantic_dirty_diff=semantic_dirty_diff,
        provider_delta_typed_operation_plan=provider_delta_typed_operation_plan,
        package_source_execution=package_source_execution,
        generated_path_candidate_plan=preflight_candidate_plan,
    )
    blockers = _runtime_artifact_delta_plan_blockers(
        provider_delta_head_move_plan=provider_delta_head_move_plan,
        provider_delta_typed_operation_plan=provider_delta_typed_operation_plan,
        operation_execution=operation_execution,
        package_source_execution=package_source_execution,
        missing_head_ref_fields=missing_head_ref_fields,
        snapshot=snapshot,
        analysis=analysis,
    )
    if blockers:
        return _runtime_artifact_delta_plan_payload(
            status="api_product_runtime_delta_plan_blocked",
            reason="api_product_runtime_delta_plan_blocked",
            blocked=True,
            blockers=blockers,
            manifest_path=manifest_path,
            package_name=package_name,
            current_delta_fingerprint=current_delta_fingerprint,
            head_refs=head_refs,
            missing_head_ref_fields=missing_head_ref_fields,
            runtime_artifacts_current=False,
            allow_runtime_artifact_refresh=False,
            did_update_runtime_artifacts=False,
            emitted_runtime_artifacts=(),
            runtime_compile_plan_hash=None,
            runtime_package_dir=None,
            accessible_dependency_graph_count=None,
            accessible_dependency_graph_source=None,
            generated_path_candidate_plan=preflight_candidate_plan,
            runtime_artifact_fragment_plan=preflight_fragment_plan,
            provider_delta_head_move_plan=provider_delta_head_move_plan,
            provider_delta_typed_operation_plan=provider_delta_typed_operation_plan,
            operation_execution=operation_execution,
            package_source_execution=package_source_execution,
        )

    emitter = runtime_artifact_emitter or _emit_api_product_runtime_delta_artifacts
    try:
        emission = dict(
            emitter(
                manifest_path=manifest_path,
                package_name=package_name,
                snapshot=snapshot,
                analysis=analysis,
                workspace_root=workspace_root,
                accessible_graphs=accessible_graphs,
            )
        )
    except Exception as exc:
        return _runtime_artifact_delta_plan_payload(
            status="api_product_runtime_delta_plan_blocked",
            reason="api_product_runtime_delta_execution_failed",
            blocked=True,
            blockers=(
                f"runtime_artifact_delta_execution_failed:{type(exc).__name__}: {exc}",
            ),
            manifest_path=manifest_path,
            package_name=package_name,
            current_delta_fingerprint=current_delta_fingerprint,
            head_refs=head_refs,
            missing_head_ref_fields=missing_head_ref_fields,
            runtime_artifacts_current=False,
            allow_runtime_artifact_refresh=False,
            did_update_runtime_artifacts=False,
            emitted_runtime_artifacts=(),
            runtime_compile_plan_hash=None,
            runtime_package_dir=None,
            accessible_dependency_graph_count=None,
            accessible_dependency_graph_source=None,
            generated_path_candidate_plan=preflight_candidate_plan,
            runtime_artifact_fragment_plan=preflight_fragment_plan,
            provider_delta_head_move_plan=provider_delta_head_move_plan,
            provider_delta_typed_operation_plan=provider_delta_typed_operation_plan,
            operation_execution=operation_execution,
            package_source_execution=package_source_execution,
        )

    emitted_runtime_artifacts = tuple(
        dict(item)
        for item in _tuple_evidence(emission.get("emitted_runtime_artifacts"))
        if isinstance(item, Mapping)
    )
    runtime_compile_plan_hash = _optional_text(
        emission.get("runtime_compile_plan_hash")
    )
    runtime_package_dir = _optional_text(emission.get("runtime_package_dir"))
    accessible_dependency_graph_count = _int_value(
        emission.get("accessible_dependency_graph_count")
    )
    accessible_dependency_graph_source = _optional_text(
        emission.get("accessible_dependency_graph_source")
    )
    generated_path_candidate_plan = _api_generated_path_candidate_plan(
        semantic_dirty_diff=semantic_dirty_diff,
        analysis=analysis,
        runtime_package_dir=Path(runtime_package_dir) if runtime_package_dir else None,
        package_name=package_name,
        fqn_prefix=_snapshot_api_fqn_prefix(snapshot=snapshot),
    )
    runtime_artifact_fragment_plan = _api_runtime_artifact_fragment_plan(
        semantic_dirty_diff=semantic_dirty_diff,
        provider_delta_typed_operation_plan=provider_delta_typed_operation_plan,
        package_source_execution=package_source_execution,
        generated_path_candidate_plan=generated_path_candidate_plan,
    )
    return _runtime_artifact_delta_plan_payload(
        status="api_product_runtime_delta_plan_ready",
        reason="api_product_runtime_delta_plan_ready",
        blocked=False,
        blockers=(),
        manifest_path=manifest_path,
        package_name=package_name,
        current_delta_fingerprint=current_delta_fingerprint,
        head_refs=head_refs,
        missing_head_ref_fields=missing_head_ref_fields,
        runtime_artifacts_current=True,
        allow_runtime_artifact_refresh=True,
        did_update_runtime_artifacts=True,
        emitted_runtime_artifacts=emitted_runtime_artifacts,
        runtime_compile_plan_hash=runtime_compile_plan_hash,
        runtime_package_dir=runtime_package_dir,
        accessible_dependency_graph_count=accessible_dependency_graph_count,
        accessible_dependency_graph_source=accessible_dependency_graph_source,
        generated_path_candidate_plan=generated_path_candidate_plan,
        runtime_artifact_fragment_plan=runtime_artifact_fragment_plan,
        provider_delta_head_move_plan=provider_delta_head_move_plan,
        provider_delta_typed_operation_plan=provider_delta_typed_operation_plan,
        operation_execution=operation_execution,
        package_source_execution=package_source_execution,
    )


def _runtime_artifact_delta_plan_payload(
    *,
    status: str,
    reason: str,
    blocked: bool,
    blockers: tuple[str, ...],
    manifest_path: Path,
    package_name: str,
    current_delta_fingerprint: str,
    head_refs: Mapping[str, str],
    missing_head_ref_fields: tuple[str, ...],
    runtime_artifacts_current: bool,
    allow_runtime_artifact_refresh: bool,
    did_update_runtime_artifacts: bool,
    emitted_runtime_artifacts: tuple[dict[str, object], ...],
    runtime_compile_plan_hash: str | None,
    runtime_package_dir: str | None,
    accessible_dependency_graph_count: int | None,
    accessible_dependency_graph_source: str | None,
    generated_path_candidate_plan: Mapping[str, object],
    runtime_artifact_fragment_plan: Mapping[str, object],
    provider_delta_head_move_plan: Mapping[str, object],
    provider_delta_typed_operation_plan: Mapping[str, object],
    operation_execution: Mapping[str, object],
    package_source_execution: Mapping[str, object],
) -> dict[str, object]:
    return {
        "plan_kind": "api_product_runtime_delta_plan",
        "contract_version": API_PRODUCT_RUNTIME_DELTA_PLAN_CONTRACT_VERSION,
        "status": status,
        "reason": reason,
        "blocked": blocked,
        "blockers": blockers,
        "provider_key": "aware_api",
        "semantic_owner": "aware_api.provider",
        "producer_key": "aware_api.api_product_runtime_delta",
        "source": "aware_api.provider_delta.current_semantic_analysis",
        "runtime_artifact_delta_strategy": _runtime_artifact_delta_strategy(
            runtime_artifact_fragment_plan=runtime_artifact_fragment_plan,
        ),
        "runtime_artifact_execution_strategy": "current_analysis_runtime_emit",
        "patch_targets": ("api_client", "service_protocol"),
        "runtime_artifacts_current": runtime_artifacts_current,
        "allow_runtime_artifact_refresh": allow_runtime_artifact_refresh,
        "did_update_runtime_artifacts": did_update_runtime_artifacts,
        "emitted_runtime_artifacts": emitted_runtime_artifacts,
        "emitted_runtime_artifact_count": len(emitted_runtime_artifacts),
        "runtime_package_dir": runtime_package_dir,
        "runtime_compile_plan_hash": runtime_compile_plan_hash,
        "accessible_dependency_graph_count": accessible_dependency_graph_count,
        "accessible_dependency_graph_source": accessible_dependency_graph_source,
        "runtime_artifact_fragment_plan": dict(runtime_artifact_fragment_plan),
        "runtime_artifact_fragment_plan_status": _optional_text(
            runtime_artifact_fragment_plan.get("status")
        ),
        "runtime_artifact_fragment_ready": (
            runtime_artifact_fragment_plan.get("fragment_ready") is True
        ),
        "runtime_artifact_fragment_operation_count": _int_value(
            runtime_artifact_fragment_plan.get("fragment_operation_count")
        ),
        "generated_path_candidate_plan": dict(generated_path_candidate_plan),
        "generated_path_candidate_plan_status": _optional_text(
            generated_path_candidate_plan.get("status")
        ),
        "generated_path_candidate_count": _int_value(
            generated_path_candidate_plan.get("candidate_count")
        ),
        "generated_path_candidate_filter_ready": (
            generated_path_candidate_plan.get("candidate_filter_ready") is True
        ),
        "manifest_path": manifest_path.as_posix(),
        "package_name": package_name,
        "current_delta_fingerprint": current_delta_fingerprint,
        "head_refs": dict(head_refs),
        **dict(head_refs),
        "missing_head_ref_fields": missing_head_ref_fields,
        "provider_delta_head_move_status": _optional_text(
            provider_delta_head_move_plan.get("status")
        ),
        "provider_delta_typed_operation_status": _optional_text(
            provider_delta_typed_operation_plan.get("status")
        ),
        "operation_execution_status": _optional_text(operation_execution.get("status")),
        "package_source_execution_status": _optional_text(
            package_source_execution.get("status")
        ),
    }


def _runtime_artifact_delta_plan_blockers(
    *,
    provider_delta_head_move_plan: Mapping[str, object],
    provider_delta_typed_operation_plan: Mapping[str, object],
    operation_execution: Mapping[str, object],
    package_source_execution: Mapping[str, object],
    missing_head_ref_fields: tuple[str, ...],
    snapshot: object,
    analysis: object,
) -> tuple[str, ...]:
    blockers: list[str] = []
    if provider_delta_head_move_plan.get("status") != "head_move_plan_ready":
        blockers.append(
            "head_move_plan_not_ready:"
            f"{_optional_text(provider_delta_head_move_plan.get('status')) or 'unknown'}"
        )
    if (
        provider_delta_typed_operation_plan.get("status")
        != "typed_operation_plan_ready"
    ):
        blockers.append(
            "typed_operation_plan_not_ready:"
            f"{_optional_text(provider_delta_typed_operation_plan.get('status')) or 'unknown'}"
        )
    if operation_execution.get("status") != "executed":
        blockers.append(
            "operation_execution_not_applied:"
            f"{_optional_text(operation_execution.get('status')) or 'unknown'}"
        )
    if package_source_execution.get("status") != "executed":
        blockers.append(
            "package_source_execution_not_applied:"
            f"{_optional_text(package_source_execution.get('status')) or 'unknown'}"
        )
    if package_source_execution.get("source_update_strategy") != "code_package_delta":
        blockers.append(
            "source_update_strategy_not_delta:"
            f"{_optional_text(package_source_execution.get('source_update_strategy')) or 'unknown'}"
        )
    for field_name in missing_head_ref_fields:
        blockers.append(f"head_ref_missing:{field_name}")
    blockers.extend(
        _analysis_runtime_artifact_blockers(snapshot=snapshot, analysis=analysis)
    )
    return tuple(dict.fromkeys(blockers))


def _analysis_runtime_artifact_blockers(
    *,
    snapshot: object,
    analysis: object,
) -> tuple[str, ...]:
    blockers: list[str] = []
    diagnostics = tuple(getattr(analysis, "diagnostics", ()) or ())
    if diagnostics:
        blockers.append("current_semantic_analysis_diagnostics_present")
    api_ownership = tuple(getattr(analysis, "api_ownership", ()) or ())
    if not api_ownership:
        blockers.append("current_semantic_analysis_api_ownership_missing")
    snapshot_source_files = _snapshot_source_files(snapshot=snapshot)
    analysis_source_files = tuple(
        str(item) for item in getattr(analysis, "source_files", ()) or ()
    )
    if snapshot_source_files and tuple(sorted(analysis_source_files)) != tuple(
        sorted(snapshot_source_files)
    ):
        blockers.append("runtime_artifact_delta_requires_full_source_set")
    return tuple(blockers)


def _emit_api_product_runtime_delta_artifacts(
    *,
    manifest_path: Path,
    package_name: str,
    snapshot: object,
    analysis: object,
    workspace_root: Path | None,
    accessible_graphs: Sequence[ObjectConfigGraph],
) -> dict[str, object]:
    del manifest_path
    repo_root = _snapshot_repo_root(snapshot=snapshot, workspace_root=workspace_root)
    runtime_package_dir = resolve_api_runtime_package_dir(snapshot=cast(Any, snapshot))
    accessible_graphs, accessible_dependency_graph_source = (
        _runtime_accessible_dependency_graphs(
            snapshot=snapshot,
            runtime_package_dir=runtime_package_dir,
            context_accessible_graphs=accessible_graphs,
        )
    )
    api_ownership = tuple(getattr(analysis, "api_ownership", ()) or ())
    if _api_endpoint_class_refs(api_ownership=api_ownership) and not accessible_graphs:
        raise RuntimeError(
            "api_endpoint_class_refs_require_accessible_dependency_graphs"
        )
    class_config_id_by_ref = collect_api_dependency_class_config_ids_from_graphs(
        accessible_graphs=accessible_graphs,
    )
    api_ownership = bind_api_endpoint_class_config_ids(
        api_ownership=api_ownership,
        class_config_id_by_ref=class_config_id_by_ref,
    )
    compile_plan = APICompilePlan(
        schema_version=1,
        package_name=package_name,
        fqn_prefix=_snapshot_api_fqn_prefix(snapshot=snapshot),
        source_files=_snapshot_source_files(snapshot=snapshot),
        api_ownership=api_ownership,
        api_ontology=build_api_ontology_plans(api_ownership=api_ownership),
    )
    artifacts = emit_api_runtime_artifacts(
        plan=compile_plan,
        runtime_package_dir=runtime_package_dir,
        repo_root=repo_root,
        accessible_graphs=accessible_graphs,
    )
    return {
        "runtime_package_dir": runtime_package_dir.as_posix(),
        "runtime_compile_plan_hash": artifacts.compile_plan.hash_sha256,
        "accessible_dependency_graph_count": len(accessible_graphs),
        "accessible_dependency_graph_source": accessible_dependency_graph_source,
        "emitted_runtime_artifacts": _runtime_artifact_payloads(
            artifacts=artifacts,
        ),
    }


def _runtime_accessible_dependency_graphs(
    *,
    snapshot: object,
    runtime_package_dir: Path,
    context_accessible_graphs: Sequence[ObjectConfigGraph],
) -> tuple[tuple[ObjectConfigGraph, ...], str]:
    context_graphs = tuple(
        graph
        for graph in context_accessible_graphs
        if isinstance(graph, ObjectConfigGraph)
    )
    if context_graphs:
        return (
            canonicalize_api_accessible_dependency_graphs(
                accessible_graphs=context_graphs,
            ),
            "semantic_context",
        )
    dependencies = tuple(getattr(getattr(snapshot, "spec"), "dependencies", ()) or ())
    if not dependencies:
        return (), "none"
    try:
        return (
            load_api_accessible_dependency_graphs_from_runtime_artifact(
                runtime_package_dir=runtime_package_dir,
            ),
            "runtime_artifact",
        )
    except FileNotFoundError as exc:
        raise RuntimeError("accessible_dependency_graph_artifact_missing") from exc


def _api_endpoint_class_refs(*, api_ownership: tuple[object, ...]) -> tuple[str, ...]:
    refs: set[str] = set()
    for api in api_ownership:
        for capability in tuple(getattr(api, "capabilities", ()) or ()):
            for endpoint in tuple(getattr(capability, "endpoints", ()) or ()):
                request_config = getattr(endpoint, "request_config", None)
                request_ref = _optional_text(getattr(request_config, "class_ref", None))
                if request_ref is not None:
                    refs.add(request_ref)
                response_config = getattr(request_config, "response_config", None)
                response_ref = _optional_text(
                    getattr(response_config, "class_ref", None)
                )
                if response_ref is not None:
                    refs.add(response_ref)
                stream_config = getattr(request_config, "stream_config", None)
                for event_config in tuple(
                    getattr(stream_config, "event_configs", ()) or ()
                ):
                    event_ref = _optional_text(getattr(event_config, "class_ref", None))
                    if event_ref is not None:
                        refs.add(event_ref)
    return tuple(sorted(refs))


def _runtime_artifact_payloads(
    *,
    artifacts: APIRuntimeArtifacts,
) -> tuple[dict[str, object], ...]:
    return (
        _runtime_artifact_payload(
            kind="api.compile_plan", artifact=artifacts.compile_plan
        ),
        _runtime_artifact_payload(
            kind="api.interface_spec", artifact=artifacts.interface_spec
        ),
        _runtime_artifact_payload(
            kind="api.invocation_manifest",
            artifact=artifacts.invocation_manifest,
        ),
        _runtime_artifact_payload(
            kind="api.public_package_plan",
            artifact=artifacts.public_package_plan,
        ),
        _runtime_artifact_payload(
            kind="api.service_protocol_plan",
            artifact=artifacts.service_protocol_plan,
        ),
    )


def _runtime_artifact_payload(*, kind: str, artifact: object) -> dict[str, object]:
    return {
        "kind": kind,
        "path": getattr(artifact, "path").as_posix(),
        "relpath": str(getattr(artifact, "relpath")),
        "hash_sha256": str(getattr(artifact, "hash_sha256")),
    }


def _head_refs(*, bundle_package: Mapping[str, object]) -> dict[str, str]:
    head_refs: dict[str, str] = {}
    for field_name in _REQUIRED_BUNDLE_HEAD_REF_FIELDS:
        field_value = _optional_text(bundle_package.get(field_name))
        if field_value is not None:
            head_refs[field_name] = field_value
    return head_refs


def _snapshot_source_files(*, snapshot: object) -> tuple[str, ...]:
    return tuple(
        path.as_posix() if isinstance(path, Path) else str(path)
        for path in tuple(getattr(snapshot, "source_files", ()) or ())
    )


def _snapshot_repo_root(*, snapshot: object, workspace_root: Path | None) -> Path:
    if workspace_root is not None:
        return workspace_root.resolve()
    repo_root = getattr(snapshot, "repo_root", None)
    if isinstance(repo_root, Path):
        return repo_root.resolve()
    return Path(str(repo_root)).resolve()


def _snapshot_api_fqn_prefix(*, snapshot: object) -> str:
    spec = getattr(snapshot, "spec")
    fqn_prefix = _optional_text(getattr(spec.api, "fqn_prefix", None))
    if fqn_prefix is None:
        raise RuntimeError("API runtime artifact delta requires api.fqn_prefix.")
    return fqn_prefix


def _api_generated_path_candidate_plan_preflight(
    *,
    semantic_dirty_diff: Mapping[str, object] | None,
    analysis: object,
    snapshot: object,
    package_name: str,
) -> dict[str, object]:
    try:
        runtime_package_dir = resolve_api_runtime_package_dir(
            snapshot=cast(Any, snapshot),
        )
        fqn_prefix = _snapshot_api_fqn_prefix(snapshot=snapshot)
    except Exception as exc:
        return _generated_path_candidate_plan_unavailable(
            semantic_dirty_diff=semantic_dirty_diff,
            reason=(
                "runtime_artifact_fragment_context_unavailable:" f"{type(exc).__name__}"
            ),
        )
    return _api_generated_path_candidate_plan(
        semantic_dirty_diff=semantic_dirty_diff,
        analysis=analysis,
        runtime_package_dir=runtime_package_dir,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
    )


def _api_runtime_artifact_fragment_plan(
    *,
    semantic_dirty_diff: Mapping[str, object] | None,
    provider_delta_typed_operation_plan: Mapping[str, object],
    package_source_execution: Mapping[str, object],
    generated_path_candidate_plan: Mapping[str, object],
) -> dict[str, object]:
    dirty_entries = tuple(
        _mapping_payload(item)
        for item in (
            _tuple_evidence(semantic_dirty_diff.get("semantic_dirty_entries"))
            if isinstance(semantic_dirty_diff, Mapping)
            else ()
        )
        if isinstance(item, Mapping)
    )
    candidates = tuple(
        _mapping_payload(item)
        for item in _tuple_evidence(generated_path_candidate_plan.get("candidates"))
        if isinstance(item, Mapping)
    )
    candidate_by_semantic_key = _candidates_by_semantic_key(candidates=candidates)
    typed_operation_by_semantic_key = _typed_operation_by_semantic_key(
        provider_delta_typed_operation_plan=provider_delta_typed_operation_plan,
    )
    fragment_operations = tuple(
        _runtime_artifact_fragment_operation(
            dirty_entry=dirty_entry,
            typed_operation=typed_operation_by_semantic_key.get(
                _optional_text(dirty_entry.get("semantic_key")) or "",
            ),
            generated_path_candidates=candidate_by_semantic_key.get(
                _optional_text(dirty_entry.get("semantic_key")) or "",
                (),
            ),
        )
        for dirty_entry in dirty_entries
    )
    blocked_fragment_operations = tuple(
        operation
        for operation in fragment_operations
        if operation.get("fragment_ready") is not True
    )
    blockers = _runtime_artifact_fragment_plan_blockers(
        semantic_dirty_diff=semantic_dirty_diff,
        provider_delta_typed_operation_plan=provider_delta_typed_operation_plan,
        package_source_execution=package_source_execution,
        generated_path_candidate_plan=generated_path_candidate_plan,
        dirty_entries=dirty_entries,
        blocked_fragment_operations=blocked_fragment_operations,
    )
    ready_operations = tuple(
        operation
        for operation in fragment_operations
        if operation.get("fragment_ready") is True
    )
    fragment_ready = bool(ready_operations) and not blockers
    status = (
        "api_runtime_artifact_fragment_plan_ready"
        if fragment_ready
        else (
            "api_runtime_artifact_fragment_plan_empty"
            if not dirty_entries and not blockers
            else "api_runtime_artifact_fragment_plan_blocked"
        )
    )
    return {
        "plan_kind": "api_runtime_artifact_fragment_plan",
        "contract_version": API_RUNTIME_ARTIFACT_FRAGMENT_PLAN_CONTRACT_VERSION,
        "status": status,
        "reason": _runtime_artifact_fragment_plan_reason(status=status),
        "source": "aware_api.provider_delta.semantic_dirty_diff",
        "provider_key": "aware_api",
        "semantic_owner": "aware_api.provider",
        "fragment_strategy": "semantic_dirty_entry_generated_artifact_fragments",
        "fragment_ready": fragment_ready,
        "available": fragment_ready,
        "blocked": bool(blockers),
        "blockers": blockers,
        "blocker_count": len(blockers),
        "patch_targets": ("api_client", "service_protocol"),
        "supported_subject_kinds": _SUPPORTED_FRAGMENT_SUBJECT_KINDS,
        "supported_operation_families": _SUPPORTED_FRAGMENT_OPERATION_FAMILIES,
        "semantic_dirty_diff_status": (
            _optional_text(semantic_dirty_diff.get("status"))
            if isinstance(semantic_dirty_diff, Mapping)
            else None
        ),
        "provider_delta_typed_operation_status": _optional_text(
            provider_delta_typed_operation_plan.get("status")
        ),
        "package_source_execution_status": _optional_text(
            package_source_execution.get("status")
        ),
        "source_update_strategy": _optional_text(
            package_source_execution.get("source_update_strategy")
        ),
        "generated_path_candidate_plan_status": _optional_text(
            generated_path_candidate_plan.get("status")
        ),
        "generated_path_candidate_filter_ready": (
            generated_path_candidate_plan.get("candidate_filter_ready") is True
        ),
        "generated_path_candidate_count": _int_value(
            generated_path_candidate_plan.get("candidate_count")
        ),
        "dirty_entry_count": len(dirty_entries),
        "fragment_operation_count": len(ready_operations),
        "blocked_fragment_operation_count": len(blocked_fragment_operations),
        "fragment_operations": ready_operations,
        "blocked_fragment_operations": blocked_fragment_operations,
        "operation_family_counts": _candidate_counts_by_field(
            candidates=ready_operations,
            field_name="operation_family",
        ),
        "target_candidate_counts": _candidate_counts_by_field(
            candidates=candidates,
            field_name="target",
        ),
        "execution_wired": False,
        "would_execute": False,
        "did_execute": False,
    }


def _runtime_artifact_fragment_operation(
    *,
    dirty_entry: Mapping[str, object],
    typed_operation: Mapping[str, object] | None,
    generated_path_candidates: tuple[Mapping[str, object], ...],
) -> dict[str, object]:
    semantic_key = _optional_text(dirty_entry.get("semantic_key")) or ""
    subject_kind = _optional_text(dirty_entry.get("ontology_subject_kind")) or (
        "api_semantic_object"
    )
    operation_family = _runtime_fragment_operation_family(
        dirty_entry=dirty_entry,
        typed_operation=typed_operation,
    )
    candidate_payloads = tuple(
        _runtime_artifact_fragment_candidate_payload(candidate=candidate)
        for candidate in generated_path_candidates
    )
    artifact_targets = tuple(
        sorted(
            {
                target
                for target in (
                    _optional_text(candidate.get("target"))
                    for candidate in candidate_payloads
                )
                if target is not None
            }
        )
    )
    missing_patch_targets = tuple(
        target
        for target in ("api_client", "service_protocol")
        if target not in artifact_targets
    )
    blockers: list[str] = []
    if subject_kind not in _SUPPORTED_FRAGMENT_SUBJECT_KINDS:
        blockers.append(f"fragment_subject_kind_unsupported:{subject_kind}")
    if operation_family not in _SUPPORTED_FRAGMENT_OPERATION_FAMILIES:
        blockers.append(f"fragment_operation_family_unsupported:{operation_family}")
    if not candidate_payloads:
        blockers.append("fragment_generated_path_candidates_missing")
    for target in missing_patch_targets:
        blockers.append(f"fragment_patch_target_missing:{target}")
    fragment_ready = not blockers
    return {
        "operation_kind": "api_runtime_artifact_fragment_operation",
        "semantic_key": semantic_key,
        "ontology_subject_kind": subject_kind,
        "operation_family": operation_family,
        "provider_operation_type": (
            _optional_text(typed_operation.get("provider_operation_type"))
            if typed_operation is not None
            else None
        ),
        "dirty_operation": _optional_text(dirty_entry.get("dirty_operation")),
        "source_refs": tuple(
            str(item)
            for item in _tuple_evidence(dirty_entry.get("source_refs"))
            if _optional_text(item) is not None
        ),
        "fragment_ready": fragment_ready,
        "blockers": tuple(blockers),
        "artifact_targets": artifact_targets,
        "missing_patch_targets": missing_patch_targets,
        "generated_path_candidate_count": len(candidate_payloads),
        "generated_path_candidates": candidate_payloads,
        "target_candidate_counts": _candidate_counts_by_field(
            candidates=candidate_payloads,
            field_name="target",
        ),
    }


def _runtime_artifact_fragment_candidate_payload(
    *,
    candidate: Mapping[str, object],
) -> dict[str, object]:
    render_section_refs = tuple(
        dict(ref)
        for ref in _tuple_mapping_payloads(candidate.get("render_section_refs"))
    )
    payload: dict[str, object] = {
        "semantic_key": _optional_text(candidate.get("semantic_key")),
        "target": _optional_text(candidate.get("target")),
        "artifact_role": _optional_text(candidate.get("artifact_role")),
        "generated_path_kind": _optional_text(candidate.get("generated_path_kind")),
        "runtime_package_relpath": _optional_text(
            candidate.get("runtime_package_relpath")
        ),
        "class_ref": _optional_text(candidate.get("class_ref")),
        "endpoint_semantic_key": _optional_text(candidate.get("endpoint_semantic_key")),
    }
    if render_section_refs:
        payload["render_section_refs"] = render_section_refs
        payload["render_section_ref_count"] = _int_value(
            candidate.get("render_section_ref_count")
        ) or len(render_section_refs)
    return payload


def _runtime_artifact_fragment_plan_blockers(
    *,
    semantic_dirty_diff: Mapping[str, object] | None,
    provider_delta_typed_operation_plan: Mapping[str, object],
    package_source_execution: Mapping[str, object],
    generated_path_candidate_plan: Mapping[str, object],
    dirty_entries: tuple[Mapping[str, object], ...],
    blocked_fragment_operations: tuple[Mapping[str, object], ...],
) -> tuple[str, ...]:
    blockers: list[str] = []
    dirty_status = (
        _optional_text(semantic_dirty_diff.get("status"))
        if isinstance(semantic_dirty_diff, Mapping)
        else None
    )
    if dirty_status != "semantic_dirty_diff_ready":
        blockers.append(f"semantic_dirty_diff_not_ready:{dirty_status or 'unknown'}")
    if (
        provider_delta_typed_operation_plan.get("status")
        != "typed_operation_plan_ready"
    ):
        blockers.append(
            "typed_operation_plan_not_ready:"
            f"{_optional_text(provider_delta_typed_operation_plan.get('status')) or 'unknown'}"
        )
    if package_source_execution.get("source_update_strategy") != "code_package_delta":
        blockers.append(
            "source_update_strategy_not_delta:"
            f"{_optional_text(package_source_execution.get('source_update_strategy')) or 'unknown'}"
        )
    candidate_status = _optional_text(generated_path_candidate_plan.get("status"))
    if candidate_status != "generated_path_candidate_plan_ready":
        blockers.append(
            f"generated_path_candidate_plan_not_ready:{candidate_status or 'unknown'}"
        )
    if generated_path_candidate_plan.get("candidate_filter_ready") is not True:
        blockers.append("generated_path_candidate_filter_not_ready")
    if not dirty_entries:
        blockers.append("semantic_dirty_entries_missing")
    for operation in blocked_fragment_operations:
        semantic_key = _optional_text(operation.get("semantic_key")) or "unknown"
        for blocker in _tuple_evidence(operation.get("blockers")):
            blocker_text = _optional_text(blocker)
            if blocker_text is not None:
                blockers.append(f"{semantic_key}:{blocker_text}")
    return tuple(dict.fromkeys(blockers))


def _runtime_artifact_fragment_plan_reason(*, status: str) -> str:
    return {
        "api_runtime_artifact_fragment_plan_ready": (
            "api_provider_delta_runtime_artifact_fragments_ready"
        ),
        "api_runtime_artifact_fragment_plan_empty": (
            "api_provider_delta_runtime_artifact_fragments_empty"
        ),
        "api_runtime_artifact_fragment_plan_blocked": (
            "api_provider_delta_runtime_artifact_fragments_blocked"
        ),
    }[status]


def _runtime_artifact_delta_strategy(
    *,
    runtime_artifact_fragment_plan: Mapping[str, object],
) -> str:
    if runtime_artifact_fragment_plan.get("fragment_ready") is True:
        return "delta_fragment_guided_current_analysis_emit"
    return "delta_current_analysis_emit"


def _candidates_by_semantic_key(
    *,
    candidates: tuple[Mapping[str, object], ...],
) -> dict[str, tuple[Mapping[str, object], ...]]:
    grouped: dict[str, list[Mapping[str, object]]] = {}
    for candidate in candidates:
        semantic_key = _optional_text(candidate.get("semantic_key"))
        if semantic_key is None:
            continue
        grouped.setdefault(semantic_key, []).append(candidate)
    return {key: tuple(value) for key, value in grouped.items()}


def _typed_operation_by_semantic_key(
    *,
    provider_delta_typed_operation_plan: Mapping[str, object],
) -> dict[str, Mapping[str, object]]:
    indexed: dict[str, Mapping[str, object]] = {}
    for operation in _tuple_mapping_payloads(
        provider_delta_typed_operation_plan.get("typed_operations")
    ):
        semantic_key = _optional_text(operation.get("semantic_key"))
        if semantic_key is not None:
            indexed[semantic_key] = operation
    return indexed


def _runtime_fragment_operation_family(
    *,
    dirty_entry: Mapping[str, object],
    typed_operation: Mapping[str, object] | None,
) -> str:
    if typed_operation is not None:
        typed_family = _optional_text(typed_operation.get("operation_family"))
        if typed_family is not None:
            return typed_family
    return _dirty_entry_operation_family(dirty_entry=dirty_entry)


def _dirty_entry_operation_family(*, dirty_entry: Mapping[str, object]) -> str:
    operation = _optional_text(dirty_entry.get("baseline_compare_operation"))
    if operation is None:
        operation = _optional_text(dirty_entry.get("dirty_operation"))
    if operation is None:
        return "unknown"
    normalized = operation.strip().lower()
    if normalized == "create" or normalized.endswith("_create"):
        return "create"
    if normalized == "update" or normalized.endswith("_update"):
        return "update"
    if normalized == "delete" or normalized.endswith("_delete"):
        return "delete"
    if normalized == "noop" or normalized.endswith("_noop"):
        return "noop"
    if normalized == "blocked" or normalized.endswith("_blocked"):
        return "blocked"
    return "unknown"


def _generated_path_candidate_plan_unavailable(
    *,
    semantic_dirty_diff: Mapping[str, object] | None,
    reason: str,
) -> dict[str, object]:
    semantic_dirty_diff_status = (
        _optional_text(semantic_dirty_diff.get("status"))
        if isinstance(semantic_dirty_diff, Mapping)
        else None
    )
    return {
        "contract_version": API_GENERATED_PATH_CANDIDATE_PLAN_CONTRACT_VERSION,
        "plan_kind": "api_generated_path_candidate_plan",
        "status": "generated_path_candidate_plan_not_available",
        "reason": reason,
        "candidate_filter_ready": False,
        "semantic_dirty_diff_status": semantic_dirty_diff_status,
        "candidate_count": 0,
        "unique_generated_path_count": 0,
        "target_candidate_counts": {},
        "unmapped_dirty_entry_count": 0,
        "unmapped_dirty_entries": (),
        "candidates": (),
    }


def _api_generated_path_candidate_plan(
    *,
    semantic_dirty_diff: Mapping[str, object] | None,
    analysis: object,
    runtime_package_dir: Path | None,
    package_name: str,
    fqn_prefix: str,
) -> dict[str, object]:
    if runtime_package_dir is None:
        return _generated_path_candidate_plan_unavailable(
            semantic_dirty_diff=semantic_dirty_diff,
            reason="runtime_package_dir_missing",
        )
    if not isinstance(semantic_dirty_diff, Mapping):
        return _generated_path_candidate_plan_unavailable(
            semantic_dirty_diff=semantic_dirty_diff,
            reason="semantic_dirty_diff_missing",
        )

    semantic_dirty_diff_status = _optional_text(semantic_dirty_diff.get("status"))
    if semantic_dirty_diff_status != "semantic_dirty_diff_ready":
        return _generated_path_candidate_plan_unavailable(
            semantic_dirty_diff=semantic_dirty_diff,
            reason="semantic_dirty_diff_not_ready",
        )

    dirty_entries = tuple(
        item
        for item in _tuple_evidence(semantic_dirty_diff.get("semantic_dirty_entries"))
        if isinstance(item, Mapping)
    )
    endpoint_contexts = _api_endpoint_generated_path_contexts(analysis=analysis)
    if dirty_entries and not endpoint_contexts:
        return _generated_path_candidate_plan_unavailable(
            semantic_dirty_diff=semantic_dirty_diff,
            reason="api_ownership_endpoint_context_missing",
        )

    public_import_root = _python_public_import_root(
        package_name=package_name,
        fqn_prefix=fqn_prefix,
    )
    service_protocol_import_root = _python_service_protocol_import_root(
        public_import_root=public_import_root,
    )
    candidates: list[dict[str, object]] = []
    unmapped_dirty_entries: list[dict[str, object]] = []
    seen_candidate_keys: set[tuple[str, str, str, str, str | None]] = set()

    for dirty_entry in dirty_entries:
        matched_contexts = tuple(
            context
            for context in endpoint_contexts
            if _dirty_entry_matches_endpoint_context(
                dirty_entry=dirty_entry,
                endpoint_context=context,
            )
        )
        if not matched_contexts:
            unmapped_dirty_entries.append(_unmapped_dirty_entry_payload(dirty_entry))
            continue

        for endpoint_context in matched_contexts:
            for class_ref_payload in _tuple_mapping_payloads(
                endpoint_context.get("class_refs")
            ):
                candidate = _generated_path_candidate(
                    dirty_entry=dirty_entry,
                    endpoint_context=endpoint_context,
                    target="api_client",
                    artifact_role="public_package_file",
                    generated_path_kind=str(class_ref_payload["contract_role"]),
                    runtime_package_dir=runtime_package_dir,
                    runtime_relpath=(
                        Path("public_package")
                        / "python"
                        / "package"
                        / public_import_root
                        / "models"
                        / f"{to_snake_case(str(class_ref_payload['class_name']))}.py"
                    ),
                    class_ref=str(class_ref_payload["class_ref"]),
                )
                key = _candidate_dedupe_key(candidate)
                if key not in seen_candidate_keys:
                    seen_candidate_keys.add(key)
                    candidates.append(candidate)

            for runtime_relpath in (
                Path("public_package")
                / "python"
                / "package"
                / public_import_root
                / "client.py",
                Path("public_package")
                / "python"
                / "package"
                / public_import_root
                / "_bindings.py",
            ):
                candidate = _generated_path_candidate(
                    dirty_entry=dirty_entry,
                    endpoint_context=endpoint_context,
                    target="api_client",
                    artifact_role="public_package_file",
                    generated_path_kind=runtime_relpath.name,
                    runtime_package_dir=runtime_package_dir,
                    runtime_relpath=runtime_relpath,
                    class_ref=None,
                )
                key = _candidate_dedupe_key(candidate)
                if key not in seen_candidate_keys:
                    seen_candidate_keys.add(key)
                    candidates.append(candidate)

            service_protocol_relpath = (
                Path("service_protocol")
                / "python"
                / "package"
                / service_protocol_import_root
                / "protocols.py"
            )
            candidate = _generated_path_candidate(
                dirty_entry=dirty_entry,
                endpoint_context=endpoint_context,
                target="service_protocol",
                artifact_role="service_protocol_package_file",
                generated_path_kind="protocols.py",
                runtime_package_dir=runtime_package_dir,
                runtime_relpath=service_protocol_relpath,
                class_ref=None,
                render_section_refs=_service_protocol_render_section_refs(
                    dirty_entry=dirty_entry,
                    endpoint_context=endpoint_context,
                    runtime_relpath=service_protocol_relpath,
                ),
            )
            key = _candidate_dedupe_key(candidate)
            if key not in seen_candidate_keys:
                seen_candidate_keys.add(key)
                candidates.append(candidate)

    status = _generated_path_candidate_status(
        candidate_count=len(candidates),
        unmapped_dirty_entry_count=len(unmapped_dirty_entries),
        dirty_entry_count=len(dirty_entries),
    )
    reason = _generated_path_candidate_reason(status=status)
    target_candidate_counts = _candidate_counts_by_field(
        candidates=tuple(candidates),
        field_name="target",
    )
    return {
        "contract_version": API_GENERATED_PATH_CANDIDATE_PLAN_CONTRACT_VERSION,
        "plan_kind": "api_generated_path_candidate_plan",
        "status": status,
        "reason": reason,
        "candidate_filter_ready": bool(candidates) and not unmapped_dirty_entries,
        "semantic_dirty_diff_status": semantic_dirty_diff_status,
        "dirty_entry_count": len(dirty_entries),
        "candidate_count": len(candidates),
        "unique_generated_path_count": len(
            {str(candidate["runtime_package_relpath"]) for candidate in candidates}
        ),
        "target_candidate_counts": target_candidate_counts,
        "unmapped_dirty_entry_count": len(unmapped_dirty_entries),
        "unmapped_dirty_entries": tuple(unmapped_dirty_entries),
        "candidates": tuple(candidates),
    }


def _api_endpoint_generated_path_contexts(
    *,
    analysis: object,
) -> tuple[dict[str, object], ...]:
    contexts: list[dict[str, object]] = []
    for api in tuple(getattr(analysis, "api_ownership", ()) or ()):
        api_name = _optional_text(getattr(api, "name", None))
        if api_name is None:
            continue
        api_key = f"api:{api_name}"
        api_source_refs = _source_ref_set(getattr(api, "source_path", None))
        for capability in tuple(getattr(api, "capabilities", ()) or ()):
            capability_name = _optional_text(getattr(capability, "name", None))
            if capability_name is None:
                continue
            capability_key = f"{api_key}/capability:{capability_name}"
            capability_source_refs = api_source_refs | _source_ref_set(
                getattr(capability, "source_path", None)
            )
            for endpoint in tuple(getattr(capability, "endpoints", ()) or ()):
                endpoint_name = _optional_text(getattr(endpoint, "name", None))
                if endpoint_name is None:
                    continue
                endpoint_key = f"{capability_key}/endpoint:{endpoint_name}"
                class_refs, endpoint_source_refs = _endpoint_contract_class_refs(
                    endpoint=endpoint,
                )
                source_refs = tuple(
                    sorted(
                        capability_source_refs
                        | _source_ref_set(getattr(endpoint, "source_path", None))
                        | endpoint_source_refs
                    )
                )
                contexts.append(
                    {
                        "api_name": api_name,
                        "capability_name": capability_name,
                        "endpoint_name": endpoint_name,
                        "api_semantic_key": api_key,
                        "capability_semantic_key": capability_key,
                        "endpoint_semantic_key": endpoint_key,
                        "match_semantic_keys": (
                            api_key,
                            capability_key,
                            endpoint_key,
                        ),
                        "source_refs": source_refs,
                        "class_refs": class_refs,
                    }
                )
    return tuple(contexts)


def _endpoint_contract_class_refs(
    *,
    endpoint: object,
) -> tuple[tuple[dict[str, object], ...], set[str]]:
    class_refs: list[dict[str, object]] = []
    source_refs: set[str] = set()
    request_config = getattr(endpoint, "request_config", None)
    if request_config is None:
        return (), source_refs

    source_refs.update(_source_ref_set(getattr(request_config, "source_path", None)))
    _append_contract_class_ref(
        class_refs=class_refs,
        contract_role="request_model",
        config=request_config,
    )

    response_config = getattr(request_config, "response_config", None)
    if response_config is not None:
        source_refs.update(
            _source_ref_set(getattr(response_config, "source_path", None))
        )
        _append_contract_class_ref(
            class_refs=class_refs,
            contract_role="response_model",
            config=response_config,
        )

    stream_config = getattr(request_config, "stream_config", None)
    if stream_config is not None:
        source_refs.update(_source_ref_set(getattr(stream_config, "source_path", None)))
        for event_config in tuple(getattr(stream_config, "event_configs", ()) or ()):
            source_refs.update(
                _source_ref_set(getattr(event_config, "source_path", None))
            )
            event_kind = _optional_text(getattr(event_config, "kind", None))
            _append_contract_class_ref(
                class_refs=class_refs,
                contract_role=(
                    f"stream_event_model:{event_kind}"
                    if event_kind is not None
                    else "stream_event_model"
                ),
                config=event_config,
            )

    return tuple(class_refs), source_refs


def _append_contract_class_ref(
    *,
    class_refs: list[dict[str, object]],
    contract_role: str,
    config: object,
) -> None:
    class_ref = _optional_text(getattr(config, "class_ref", None))
    if class_ref is None:
        return
    class_refs.append(
        {
            "contract_role": contract_role,
            "class_ref": class_ref,
            "class_name": class_ref.rsplit(".", 1)[-1],
            "source_refs": tuple(
                sorted(_source_ref_set(getattr(config, "source_path", None)))
            ),
        }
    )


def _dirty_entry_matches_endpoint_context(
    *,
    dirty_entry: Mapping[str, object],
    endpoint_context: Mapping[str, object],
) -> bool:
    semantic_key = _optional_text(dirty_entry.get("semantic_key"))
    match_keys = {
        str(item)
        for item in _tuple_evidence(endpoint_context.get("match_semantic_keys"))
        if _optional_text(item) is not None
    }
    if semantic_key is not None and semantic_key in match_keys:
        return True

    dirty_source_refs = {
        str(item)
        for item in _tuple_evidence(dirty_entry.get("source_refs"))
        if _optional_text(item) is not None
    }
    context_source_refs = {
        str(item)
        for item in _tuple_evidence(endpoint_context.get("source_refs"))
        if _optional_text(item) is not None
    }
    return bool(dirty_source_refs and context_source_refs & dirty_source_refs)


def _service_protocol_render_section_refs(
    *,
    dirty_entry: Mapping[str, object],
    endpoint_context: Mapping[str, object],
    runtime_relpath: Path,
) -> tuple[dict[str, object], ...]:
    semantic_key = _optional_text(dirty_entry.get("semantic_key")) or ""
    subject_kind = _optional_text(dirty_entry.get("ontology_subject_kind")) or ""
    api_name = _optional_text(endpoint_context.get("api_name")) or ""
    capability_name = _optional_text(endpoint_context.get("capability_name")) or ""
    endpoint_name = _optional_text(endpoint_context.get("endpoint_name")) or ""
    api_semantic_key = (
        _optional_text(endpoint_context.get("api_semantic_key")) or semantic_key
    )
    capability_semantic_key = (
        _optional_text(endpoint_context.get("capability_semantic_key")) or semantic_key
    )
    endpoint_semantic_key = (
        _optional_text(endpoint_context.get("endpoint_semantic_key")) or semantic_key
    )
    runtime_relpath_text = runtime_relpath.as_posix()
    refs: list[dict[str, object]] = []
    seen: set[str] = set()

    def append_ref(
        *,
        section_kind: str,
        section_key: str,
        owner_semantic_key: str,
        api: str | None = api_name,
        capability: str | None = capability_name,
        endpoint: str | None = endpoint_name,
    ) -> None:
        if section_key in seen:
            return
        seen.add(section_key)
        refs.append(
            {
                "contract_version": (
                    API_SERVICE_PROTOCOL_RENDER_SECTION_PLAN_CONTRACT_VERSION
                ),
                "section_ref_kind": "api_service_protocol_render_section_ref",
                "section_kind": section_kind,
                "section_key": section_key,
                "semantic_key": owner_semantic_key,
                "runtime_package_relpath": runtime_relpath_text,
                "api_name": api,
                "capability_name": capability,
                "endpoint_name": endpoint,
                "section_render_wired": True,
            }
        )

    append_ref(
        section_kind="service_protocol_module_prelude",
        section_key="api.service_protocol.module_prelude",
        owner_semantic_key=api_semantic_key,
        capability=None,
        endpoint=None,
    )
    append_ref(
        section_kind="service_protocol_runtime_support",
        section_key="api.service_protocol.runtime_support",
        owner_semantic_key=api_semantic_key,
        capability=None,
        endpoint=None,
    )
    append_ref(
        section_kind="service_protocol_endpoint_binding_index",
        section_key="api.service_protocol.endpoint_bindings_index",
        owner_semantic_key=api_semantic_key,
        capability=None,
        endpoint=None,
    )
    append_ref(
        section_kind="service_protocol_module_exports",
        section_key="api.service_protocol.__all__",
        owner_semantic_key=api_semantic_key,
        capability=None,
        endpoint=None,
    )

    if api_name:
        append_ref(
            section_kind="service_protocol_root_protocol",
            section_key="api.service_protocol.root_protocol",
            owner_semantic_key=api_semantic_key,
            capability=None,
            endpoint=None,
        )
        append_ref(
            section_kind="service_protocol_api_protocol",
            section_key=f"api.service_protocol.api_protocol:{api_name}",
            owner_semantic_key=api_semantic_key,
            capability=None,
            endpoint=None,
        )

    if (
        subject_kind in {"api_capability", "api_capability_endpoint"}
        and capability_name
    ):
        append_ref(
            section_kind="service_protocol_capability_protocol",
            section_key=(
                "api.service_protocol.capability_protocol:"
                f"{api_name}.{capability_name}"
            ),
            owner_semantic_key=capability_semantic_key,
            endpoint=None,
        )

    if subject_kind == "api_capability_endpoint" and endpoint_name:
        endpoint_token = f"{api_name}.{capability_name}.{endpoint_name}"
        append_ref(
            section_kind="service_protocol_endpoint_binding",
            section_key=f"api.service_protocol.endpoint_binding:{endpoint_token}",
            owner_semantic_key=endpoint_semantic_key,
        )
        append_ref(
            section_kind="service_protocol_endpoint_invoker",
            section_key=f"api.service_protocol.endpoint_invoker:{endpoint_token}",
            owner_semantic_key=endpoint_semantic_key,
        )
        append_ref(
            section_kind="service_protocol_endpoint_execution",
            section_key=f"api.service_protocol.endpoint_execution:{endpoint_token}",
            owner_semantic_key=endpoint_semantic_key,
        )

    return tuple(refs)


def _generated_path_candidate(
    *,
    dirty_entry: Mapping[str, object],
    endpoint_context: Mapping[str, object],
    target: str,
    artifact_role: str,
    generated_path_kind: str,
    runtime_package_dir: Path,
    runtime_relpath: Path,
    class_ref: str | None,
    render_section_refs: tuple[Mapping[str, object], ...] = (),
) -> dict[str, object]:
    semantic_key = _optional_text(dirty_entry.get("semantic_key")) or ""
    generated_path = runtime_package_dir / runtime_relpath
    payload: dict[str, object] = {
        "candidate_kind": "api_generated_path_candidate",
        "semantic_key": semantic_key,
        "ontology_subject_kind": _optional_text(
            dirty_entry.get("ontology_subject_kind")
        ),
        "dirty_operation": _optional_text(dirty_entry.get("dirty_operation")),
        "source_refs": tuple(
            str(item)
            for item in _tuple_evidence(dirty_entry.get("source_refs"))
            if _optional_text(item) is not None
        ),
        "target": target,
        "artifact_role": artifact_role,
        "generated_path_kind": generated_path_kind,
        "generated_path": generated_path.as_posix(),
        "runtime_package_relpath": runtime_relpath.as_posix(),
        "class_ref": class_ref,
        "endpoint_semantic_key": _optional_text(
            endpoint_context.get("endpoint_semantic_key")
        ),
        "api_semantic_key": _optional_text(endpoint_context.get("api_semantic_key")),
        "capability_semantic_key": _optional_text(
            endpoint_context.get("capability_semantic_key")
        ),
        "confidence": "exact_from_current_api_analysis",
    }
    if render_section_refs:
        payload["render_section_refs"] = tuple(dict(ref) for ref in render_section_refs)
        payload["render_section_ref_count"] = len(render_section_refs)
    return payload


def _candidate_dedupe_key(
    candidate: Mapping[str, object],
) -> tuple[str, str, str, str, str | None]:
    return (
        _optional_text(candidate.get("semantic_key")) or "",
        _optional_text(candidate.get("target")) or "",
        _optional_text(candidate.get("artifact_role")) or "",
        _optional_text(candidate.get("runtime_package_relpath")) or "",
        _optional_text(candidate.get("class_ref")),
    )


def _unmapped_dirty_entry_payload(
    dirty_entry: Mapping[str, object],
) -> dict[str, object]:
    return {
        "semantic_key": _optional_text(dirty_entry.get("semantic_key")),
        "ontology_subject_kind": _optional_text(
            dirty_entry.get("ontology_subject_kind")
        ),
        "dirty_operation": _optional_text(dirty_entry.get("dirty_operation")),
        "source_refs": tuple(
            str(item)
            for item in _tuple_evidence(dirty_entry.get("source_refs"))
            if _optional_text(item) is not None
        ),
    }


def _generated_path_candidate_status(
    *,
    candidate_count: int,
    unmapped_dirty_entry_count: int,
    dirty_entry_count: int,
) -> str:
    if dirty_entry_count == 0:
        return "generated_path_candidate_plan_empty"
    if candidate_count and unmapped_dirty_entry_count == 0:
        return "generated_path_candidate_plan_ready"
    if candidate_count:
        return "generated_path_candidate_plan_partial"
    return "generated_path_candidate_plan_blocked"


def _generated_path_candidate_reason(*, status: str) -> str:
    return {
        "generated_path_candidate_plan_empty": (
            "api_provider_delta_generated_path_candidate_plan_empty"
        ),
        "generated_path_candidate_plan_ready": (
            "api_provider_delta_generated_path_candidate_plan_ready"
        ),
        "generated_path_candidate_plan_partial": (
            "api_provider_delta_generated_path_candidate_plan_partial"
        ),
        "generated_path_candidate_plan_blocked": (
            "api_provider_delta_generated_path_candidate_plan_blocked"
        ),
    }[status]


def _candidate_counts_by_field(
    *,
    candidates: tuple[Mapping[str, object], ...],
    field_name: str,
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for candidate in candidates:
        token = _optional_text(candidate.get(field_name)) or "unknown"
        counts[token] = counts.get(token, 0) + 1
    return counts


def _python_public_import_root(*, package_name: str, fqn_prefix: str) -> str:
    token = (fqn_prefix or package_name).strip().replace("-", "_")
    return token or "aware_api_public_package"


def _python_service_protocol_import_root(*, public_import_root: str) -> str:
    token = public_import_root
    if token.endswith("_api"):
        token = token[: -len("_api")]
    token = token.strip("_")
    return f"{token}_protocol" if token else "aware_api_protocol"


def _source_ref_set(value: object) -> set[str]:
    return {
        str(item) for item in _tuple_evidence(value) if _optional_text(item) is not None
    }


def _tuple_mapping_payloads(value: object) -> tuple[Mapping[str, object], ...]:
    return tuple(item for item in _tuple_evidence(value) if isinstance(item, Mapping))


def _mapping_payload(value: object) -> dict[str, object]:
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        payload = model_dump(mode="json")
        if isinstance(payload, Mapping):
            return {str(key): item for key, item in payload.items()}
    return {}


def _tuple_evidence(value: object) -> tuple[object, ...]:
    if isinstance(value, tuple):
        return value
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return tuple(value)
    return ()


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _int_value(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if value is None:
        return None
    try:
        return int(str(value))
    except ValueError:
        return None


__all__ = [
    "API_GENERATED_PATH_CANDIDATE_PLAN_CONTRACT_VERSION",
    "API_PRODUCT_RUNTIME_DELTA_PLAN_CONTRACT_VERSION",
    "API_RUNTIME_ARTIFACT_FRAGMENT_PLAN_CONTRACT_VERSION",
    "api_product_runtime_delta_plan",
]
