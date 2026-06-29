from __future__ import annotations

import asyncio
import json
import traceback
from concurrent.futures import Future, ThreadPoolExecutor
from collections.abc import Callable, Iterable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass, field
from hashlib import sha256
from inspect import isawaitable
from pathlib import Path
from time import perf_counter
from uuid import NAMESPACE_URL, UUID, uuid5

from aware_code.package.snapshot_commit import commit_code_package_text_snapshot
from aware_code.stable_ids import (
    code_package_generated_config_key,
    stable_code_package_config_id,
    stable_code_package_id,
)
from aware_code_ontology.code.code_plan import (
    CodePackageDelta,
    CodePackageDeltaAuthorityKind,
    CodePackageDeltaKind,
    CodePackageDeltaPath,
    CodePackageDeltaProducerRef,
    CodePackageDeltaProduction,
    CodePackagePathRole,
)
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.materialization.language_service import (
    LanguagePluginMaterializationRequest,
    RuntimeObjectConfigGraphDerivationCache,
    RuntimeToLanguageLoweringCache,
    materialize_object_config_graph_via_language_plugin,
)
from aware_meta.materialization.deltas.target_impact import (
    provider_delta_language_target_impact_plan,
)
from aware_meta.materialization.post_step_plan import (
    LanguageMaterializationPostStepPlanRequest,
    plan_language_materialization_post_steps,
)
from aware_code.semantic_function_call_execution import (
    SemanticFunctionCallExecutionConfig,
)
from aware_code.semantic_materialization import (
    SEMANTIC_LANGUAGE_MATERIALIZATION_TARGETS_CONTEXT_KEY,
    SEMANTIC_LANGUAGE_MATERIALIZATION_TOOLING_CONTEXT_KEY,
    SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_CONTEXT_KEY,
    SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_SCHEMA,
    SemanticFunctionCallContext,
    SemanticPackageMaterializationBundle,
    SemanticPackageMaterializationRequest,
    SemanticPackageMaterializationResult,
)
from aware_meta.materialization.artifact_lifecycle import (
    build_object_config_graph_package_language_lifecycle_receipts,
)
from aware_meta.materialization.service import (
    ObjectConfigGraphPackageLeafMaterializationResult,
    materialize_object_config_graph_package_leaf_from_manifest,
    realize_object_config_graph_package_language_materialization_packages,
)
from aware_meta.materialization.deltas.service import (
    build_meta_runtime_ocg_function_call_plan_previews,
)
from aware_meta.graph.config.migration_artifacts import (
    ARTIFACT_ROLE_DIALECT_MIGRATION,
    ARTIFACT_ROLE_LANE_INDEX,
    ARTIFACT_ROLE_OCG_DELTA,
    MetaOcgMigrationArtifact,
    MetaOcgMigrationArtifactBundle,
)
from aware_meta.materialization.semantic_function_call_execution import (
    execute_meta_semantic_function_call_resolutions,
    meta_semantic_function_call_execution_backend_from_context,
)
from aware_meta.materialization.semantic_function_call_resolution import (
    MetaSemanticFunctionCallResolution,
    resolve_meta_semantic_function_call_plan_previews,
)
from aware_meta.semantic_contract import (
    META_LANGUAGE_MATERIALIZATION_ARTIFACT_FAMILY,
    META_LANGUAGE_MATERIALIZATION_CODE_PACKAGE_DELTAS_OUTPUT_KEY,
    META_LANGUAGE_MATERIALIZATION_GENERATED_FILES_OUTPUT_KEY,
    META_LANGUAGE_MATERIALIZATION_LIFECYCLE_RECEIPT_OUTPUT_KEY,
    META_LANGUAGE_MATERIALIZATION_PACKAGE_OUTPUT_KEY,
    META_LANGUAGE_MATERIALIZATION_PRODUCER_KEY,
    META_OCG_MIGRATION_ARTIFACT_FAMILY,
    META_OCG_MIGRATION_ARTIFACT_MEDIA_TYPE,
    META_OCG_MIGRATION_ARTIFACT_PRODUCER_KEY,
    META_OCG_MIGRATION_ARTIFACT_PRODUCER_PROVIDER_KEY,
    META_OCG_MIGRATION_ARTIFACT_RUNTIME_CONTRACT_VERSION,
    META_OCG_MIGRATION_DELTA_OUTPUT_KEY,
    META_OCG_MIGRATION_DIALECT_OUTPUT_KEY,
    META_OCG_MIGRATION_LANE_INDEX_OUTPUT_KEY,
    META_OBJECT_CONFIG_GRAPH_OWNER,
)
from aware_meta_ontology.graph.config.object_config_graph import (
    ObjectConfigGraph,
)
from aware_meta.runtime.graph_context import find_meta_graph_projection_hash_by_name


_NON_MUTATING_REASON = (
    "Meta provider emitted runtime OCG semantic function-call plan/resolution "
    "evidence only; OCG lane mutation is not enabled in this slice."
)
_COMPILE_PARITY_RECEIPT_SCHEMA = (
    "aware.meta.workspace_materialize.compile_parity_receipt.v1"
)
_PROVIDER_DELTA_OUTPUT_PHASE_TIMINGS_CONTRACT_VERSION = (
    "aware.meta.provider-delta.output-phase-timings.v1"
)
_COMPILE_PARITY_RECEIPT_KIND = "meta_workspace_materialize_compile_parity"
_MATERIALIZED_LANGUAGE_PACKAGE_SCHEMA = (
    "aware.meta.object_config_graph_package.materialized_language_package.v1"
)
_LANGUAGE_TARGET_PROGRESS_DRAIN_TIMEOUT_S = 0.1
_LANGUAGE_TARGET_WORKER_POLL_INTERVAL_S = 1.0
_COMPILE_PARITY_AVAILABLE_STATUSES = frozenset({"available", "materialized"})
_COMPILE_PARITY_BASE_REQUIRED_ARTIFACT_ROLES = (
    "lifecycle_receipt",
    "materialization_index_receipt",
)
_COMPILE_PARITY_LANGUAGE_TARGET_REQUIRED_ARTIFACT_ROLES = (
    "package",
    "source_code",
)
_LANGUAGE_MATERIALIZATION_CODE_PACKAGE_BRANCH_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware://meta/language-materialization-code-package-branch/v1",
)
_COMPILE_PARITY_REQUIRED_ARTIFACT_ROLES_BY_SOURCE = {
    "api": (
        "dependency_import_resolution",
        "package_bootstrap",
        "runtime_binding_snapshot",
        "runtime_model_index",
    ),
    "ontology": (
        "dependency_import_resolution",
        "package_bootstrap",
        "runtime_binding_snapshot",
        "runtime_model_index",
    ),
    "ontology_orm_models": (
        "dependency_import_resolution",
        "package_bootstrap",
        "runtime_binding_snapshot",
        "runtime_model_index",
    ),
    "ontology_dto": (
        "dependency_import_resolution",
        "package_bootstrap",
    ),
    "runtime_handlers": ("meta_runtime_handler_provider",),
}


@dataclass(frozen=True, slots=True)
class _LanguageMaterializationTarget:
    target_language_plugin_id: CodeLanguage
    output_root: Path
    import_root: str
    package_name: str
    materialization_source: str
    code_package_surface: str
    source_is_runtime: bool = False
    renderer_profile: str | None = None
    renderer_kind: str | None = None
    stable_ids_import_root: str | None = None
    stable_ids_ownership: str | None = None
    stable_ids_resolution_policy: str | None = None


@dataclass(frozen=True, slots=True)
class _LanguageMaterializationSourceGraph:
    graph: ObjectConfigGraph
    source_is_runtime: bool


@dataclass(frozen=True, slots=True)
class _LanguageMaterializationReceipts:
    artifact_ownership_receipts: tuple[dict[str, object], ...] = ()
    post_step_receipts: tuple[dict[str, object], ...] = ()
    tool_step_receipts: tuple[dict[str, object], ...] = ()
    generated_code_package_refs: tuple[dict[str, object], ...] = ()
    generated_code_package_deltas: tuple[dict[str, object], ...] = ()
    tool_timings_s: Mapping[str, float] = field(default_factory=dict)
    runtime_to_language_cache: Mapping[str, object] = field(default_factory=dict)
    runtime_derivation_cache: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class _LanguageMaterializationCodePackageOutputs:
    refs: tuple[dict[str, object], ...] = ()
    deltas: tuple[dict[str, object], ...] = ()

    def __iter__(self) -> Iterator[dict[str, object]]:
        return iter(self.refs)

    def __len__(self) -> int:
        return len(self.refs)

    def __getitem__(self, index: int) -> dict[str, object]:
        return self.refs[index]


class _ProviderDeltaOutputPhaseTimings:
    def __init__(self) -> None:
        self._started_at = perf_counter()
        self._phases_s: dict[str, float] = {}
        self._phase_order: list[str] = []

    @contextmanager
    def record(self, phase_name: str) -> Iterator[None]:
        started_at = perf_counter()
        try:
            yield
        finally:
            self.record_duration(
                phase_name=phase_name,
                duration_s=perf_counter() - started_at,
            )

    def record_duration(self, *, phase_name: str, duration_s: float) -> None:
        if phase_name not in self._phases_s:
            self._phase_order.append(phase_name)
        self._phases_s[phase_name] = round(
            max(float(self._phases_s.get(phase_name, 0.0)) + duration_s, 0.0),
            6,
        )

    def payload(self) -> dict[str, object]:
        total_s = round(max(perf_counter() - self._started_at, 0.0), 6)
        phases_s = {
            phase_name: self._phases_s[phase_name]
            for phase_name in self._phase_order
            if phase_name in self._phases_s
        }
        return {
            "timing_kind": "meta_provider_delta_output_phase_timings",
            "contract_version": _PROVIDER_DELTA_OUTPUT_PHASE_TIMINGS_CONTRACT_VERSION,
            "phase_order": tuple(self._phase_order),
            "phase_count": len(self._phase_order),
            "phases_s": phases_s,
            "total_s": total_s,
        }


async def _emit_semantic_materialization_progress(
    *,
    request: SemanticPackageMaterializationRequest,
    phase_name: str,
    status: str,
    started_at: float | None = None,
    duration_s: float | None = None,
    error: str | None = None,
    detail_payload: Mapping[str, object] | None = None,
) -> None:
    callback = getattr(request, "progress_callback", None)
    if callback is None:
        return
    payload: dict[str, object] = {
        "phase_name": phase_name,
        "status": status,
        "detail_payload": dict(detail_payload or {}),
    }
    if duration_s is not None and status != "running":
        payload["duration_s"] = round(max(duration_s, 0.0), 6)
    elif started_at is not None and status != "running":
        payload["duration_s"] = round(max(perf_counter() - started_at, 0.0), 6)
    if error:
        payload["error"] = error
    try:
        result = callback(payload)
        if isawaitable(result):
            await result
    except Exception:
        return


def _language_target_progress_payload(
    *,
    target: _LanguageMaterializationTarget,
    source_graph: _LanguageMaterializationSourceGraph | None = None,
    target_index: int,
    target_count: int,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "target_index": target_index,
        "target_count": target_count,
        "target_language_plugin_id": target.target_language_plugin_id.value,
        "output_root": target.output_root.as_posix(),
        "import_root": target.import_root,
        "package_name": target.package_name,
        "materialization_source": target.materialization_source,
        "renderer_profile": target.renderer_profile,
        "renderer_kind": target.renderer_kind,
        "source_is_runtime": target.source_is_runtime,
        "target_source_is_runtime": target.source_is_runtime,
    }
    if source_graph is not None:
        payload.update(
            {
                "materialization_source_graph_is_runtime": (
                    source_graph.source_is_runtime
                ),
                "materialization_source_graph_id": str(source_graph.graph.id),
                "materialization_source_graph_hash": source_graph.graph.hash,
                "materialization_source_graph_fqn_prefix": source_graph.graph.fqn_prefix,
            }
        )
    return payload


def _schedule_language_target_subphase_progress(
    *,
    request: SemanticPackageMaterializationRequest,
    target_payload: Mapping[str, object],
    loop: asyncio.AbstractEventLoop,
    futures: list[Future[None]],
    payload: Mapping[str, object],
) -> None:
    event = _language_target_subphase_progress_event(
        target_payload=target_payload,
        payload=payload,
    )
    if event is None:
        return
    future = asyncio.run_coroutine_threadsafe(
        _emit_semantic_materialization_progress(
            request=request,
            phase_name=event["phase_name"],
            status=event["status"],
            duration_s=event.get("duration_s"),
            error=event.get("error"),
            detail_payload=event["detail_payload"],
        ),
        loop,
    )
    future.add_done_callback(_consume_language_target_subphase_progress)
    if future.done():
        return
    futures.append(future)


def _consume_language_target_subphase_progress(future: Future[None]) -> None:
    try:
        future.result()
    except Exception:
        return


async def _drain_language_target_subphase_progress(
    futures: list[Future[None]],
) -> None:
    loop = asyncio.get_running_loop()
    deadline = loop.time() + _LANGUAGE_TARGET_PROGRESS_DRAIN_TIMEOUT_S
    while futures:
        future = futures.pop(0)
        if future.done():
            _consume_language_target_subphase_progress(future)
            continue
        remaining_s = deadline - loop.time()
        if remaining_s <= 0:
            continue
        done, _pending = await asyncio.wait(
            {asyncio.wrap_future(future)},
            timeout=remaining_s,
        )
        for completed in done:
            try:
                completed.result()
            except Exception:
                continue


async def _await_language_target_worker(worker: Callable[[], object]) -> object:
    loop = asyncio.get_running_loop()
    executor = ThreadPoolExecutor(
        max_workers=1,
        thread_name_prefix="aware-language-target",
    )
    task = loop.run_in_executor(executor, worker)
    try:
        while not task.done():
            await asyncio.wait(
                {task},
                timeout=_LANGUAGE_TARGET_WORKER_POLL_INTERVAL_S,
            )
        return task.result()
    except BaseException:
        task.cancel()
        raise
    finally:
        executor.shutdown(wait=task.done(), cancel_futures=True)


def _language_target_subphase_progress_event(
    *,
    target_payload: Mapping[str, object],
    payload: Mapping[str, object],
) -> dict[str, object] | None:
    phase_name = _optional_string_value(payload.get("phase_name"))
    if phase_name not in {None, "meta.language_target.subphase"}:
        return None
    status = _optional_string_value(payload.get("status")) or "running"
    detail_payload = payload.get("detail_payload")
    if not isinstance(detail_payload, Mapping):
        detail_payload = {}
    detail = {**dict(target_payload), **dict(detail_payload)}
    subphase_name = _optional_string_value(detail.get("subphase_name"))
    if subphase_name is None:
        return None
    event: dict[str, object] = {
        "phase_name": "meta.language_target.subphase",
        "status": status,
        "detail_payload": detail,
    }
    duration_s = _progress_duration_s(payload.get("duration_s"))
    if duration_s is not None:
        event["duration_s"] = duration_s
    error = _optional_string_value(payload.get("error"))
    if error is not None:
        event["error"] = error
    return event


async def _forward_leaf_package_subphase_progress(
    *,
    request: SemanticPackageMaterializationRequest,
    payload: Mapping[str, object],
) -> None:
    event = _leaf_package_subphase_progress_event(request=request, payload=payload)
    if event is None:
        return
    await _emit_semantic_materialization_progress(
        request=request,
        phase_name=event["phase_name"],
        status=event["status"],
        duration_s=event.get("duration_s"),
        error=event.get("error"),
        detail_payload=event["detail_payload"],
    )


def _leaf_package_subphase_progress_event(
    *,
    request: SemanticPackageMaterializationRequest,
    payload: Mapping[str, object],
) -> dict[str, object] | None:
    phase_name = _optional_string_value(payload.get("phase_name"))
    if phase_name not in {None, "meta.leaf_package.subphase"}:
        return None
    status = _optional_string_value(payload.get("status")) or "running"
    detail_payload = payload.get("detail_payload")
    if not isinstance(detail_payload, Mapping):
        detail_payload = {}
    detail = {
        "manifest_path": request.manifest_path.as_posix(),
        **dict(detail_payload),
    }
    subphase_name = _optional_string_value(detail.get("subphase_name"))
    if subphase_name is None:
        return None
    event: dict[str, object] = {
        "phase_name": "meta.leaf_package.subphase",
        "status": status,
        "detail_payload": detail,
    }
    duration_s = _progress_duration_s(payload.get("duration_s"))
    if duration_s is not None:
        event["duration_s"] = duration_s
    error = _optional_string_value(payload.get("error"))
    if error is not None:
        event["error"] = error
    return event


def _progress_duration_s(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        return round(max(float(value), 0.0), 6)
    except (TypeError, ValueError):
        return None


def _should_emit_generated_code_package_deltas(
    *,
    request: SemanticPackageMaterializationRequest,
) -> bool:
    persistence = request.context.get("workspace_materialization_persistence")
    if isinstance(persistence, Mapping) and persistence.get("required") is False:
        return False
    return True


@dataclass(frozen=True, slots=True)
class MetaObjectConfigGraphPackageLeafLanguageMaterializationResult:
    leaf_result: ObjectConfigGraphPackageLeafMaterializationResult
    language_materialization_receipts: _LanguageMaterializationReceipts
    materialized_language_packages: tuple[dict[str, object], ...]
    details: Mapping[str, object]


async def materialize_object_config_graph_package_leaf_language_outputs(
    *,
    request: SemanticPackageMaterializationRequest,
    leaf_result: ObjectConfigGraphPackageLeafMaterializationResult,
) -> MetaObjectConfigGraphPackageLeafLanguageMaterializationResult:
    """Run Meta language materialization for an already materialized OCG leaf."""

    language_materialization_receipts = await _leaf_language_materialization_receipts(
        request=request,
        leaf_result=leaf_result,
    )
    if language_materialization_receipts.generated_code_package_refs:
        realize_started_at = perf_counter()
        await _emit_semantic_materialization_progress(
            request=request,
            phase_name="meta.language_package_realization",
            status="running",
            detail_payload={
                "generated_code_package_ref_count": len(
                    language_materialization_receipts.generated_code_package_refs
                ),
            },
        )
        leaf_result = (
            await realize_object_config_graph_package_language_materialization_packages(
                result=leaf_result,
                index=request.index,
                object_config_graph_package_projection_hash=(
                    find_meta_graph_projection_hash_by_name(
                        index=request.index,
                        projection_name="ObjectConfigGraphPackage",
                    )
                ),
                generated_code_package_refs=(
                    language_materialization_receipts.generated_code_package_refs
                ),
                workspace_root=request.workspace_root,
                actor_id=request.actor_id,
            )
        )
        await _emit_semantic_materialization_progress(
            request=request,
            phase_name="meta.language_package_realization",
            status="succeeded",
            started_at=realize_started_at,
            detail_payload={
                "generated_code_package_ref_count": len(
                    language_materialization_receipts.generated_code_package_refs
                ),
            },
        )
    materialized_language_packages = _materialized_language_packages_from_leaf_result(
        leaf_result=leaf_result,
        generated_code_package_refs=(
            language_materialization_receipts.generated_code_package_refs
        ),
    )
    details = await _leaf_materialization_details(
        request=request,
        leaf_result=leaf_result,
        language_materialization_receipts=language_materialization_receipts,
        materialized_language_packages=materialized_language_packages,
    )
    return MetaObjectConfigGraphPackageLeafLanguageMaterializationResult(
        leaf_result=leaf_result,
        language_materialization_receipts=language_materialization_receipts,
        materialized_language_packages=materialized_language_packages,
        details=details,
    )


async def materialize(
    request: SemanticPackageMaterializationRequest,
) -> SemanticPackageMaterializationResult:
    function_call_plans = build_meta_runtime_ocg_function_call_plan_previews(
        change_preview=request.change_preview,
    )
    function_call_context = SemanticFunctionCallContext.from_materialization_context(
        request.context,
        provider_key="aware_meta",
    )
    function_call_resolutions = resolve_meta_semantic_function_call_plan_previews(
        plans=function_call_plans,
        current_semantic_object_ids=(function_call_context.current_semantic_object_ids),
    )
    leaf_started_at = perf_counter()
    await _emit_semantic_materialization_progress(
        request=request,
        phase_name="meta.leaf_package",
        status="running",
        detail_payload={
            "manifest_path": request.manifest_path.as_posix(),
        },
    )
    try:
        leaf_result = await _materialize_leaf_package_if_supported(request=request)
    except Exception as exc:
        await _emit_semantic_materialization_progress(
            request=request,
            phase_name="meta.leaf_package",
            status="failed",
            started_at=leaf_started_at,
            error=str(exc),
            detail_payload={
                "manifest_path": request.manifest_path.as_posix(),
            },
        )
        raise
    await _emit_semantic_materialization_progress(
        request=request,
        phase_name="meta.leaf_package",
        status="succeeded",
        started_at=leaf_started_at,
        detail_payload={
            "manifest_path": request.manifest_path.as_posix(),
            "materialized": leaf_result is not None,
        },
    )
    language_materialization_receipts = _LanguageMaterializationReceipts()
    if leaf_result is not None:
        language_materialization_receipts = (
            await _leaf_language_materialization_receipts(
                request=request,
                leaf_result=leaf_result,
            )
        )
        if language_materialization_receipts.generated_code_package_refs:
            realize_started_at = perf_counter()
            await _emit_semantic_materialization_progress(
                request=request,
                phase_name="meta.language_package_realization",
                status="running",
                detail_payload={
                    "generated_code_package_ref_count": len(
                        language_materialization_receipts.generated_code_package_refs
                    ),
                },
            )
            leaf_result = await realize_object_config_graph_package_language_materialization_packages(
                result=leaf_result,
                index=request.index,
                object_config_graph_package_projection_hash=(
                    find_meta_graph_projection_hash_by_name(
                        index=request.index,
                        projection_name="ObjectConfigGraphPackage",
                    )
                ),
                generated_code_package_refs=(
                    language_materialization_receipts.generated_code_package_refs
                ),
                workspace_root=request.workspace_root,
                actor_id=request.actor_id,
            )
            await _emit_semantic_materialization_progress(
                request=request,
                phase_name="meta.language_package_realization",
                status="succeeded",
                started_at=realize_started_at,
                detail_payload={
                    "generated_code_package_ref_count": len(
                        language_materialization_receipts.generated_code_package_refs
                    ),
                },
            )
    function_call_execution = (
        _leaf_materialization_execution_detail(leaf_result=leaf_result)
        if leaf_result is not None
        else await _function_call_execution_detail(
            context=request.context,
            function_call_resolutions=function_call_resolutions,
        )
    )
    if _execution_has_terminal_failure(function_call_execution):
        raise RuntimeError(_execution_failure_message(function_call_execution))
    affected_semantic_keys = _semantic_keys_from_request(request)
    applied_semantic_keys = (
        affected_semantic_keys
        if leaf_result is not None
        else _execution_semantic_keys(
            function_call_execution,
            status="invoked",
        )
    )
    skipped_semantic_keys = _execution_semantic_keys(
        function_call_execution,
        status="skipped_noop",
    )
    graph_metadata = _runtime_graph_metadata_from_preview(request.change_preview)
    commit_id = (
        leaf_result.object_config_graph_package_commit_id
        if leaf_result is not None
        else _last_execution_commit_id(function_call_execution)
    )
    head_commit_id = (
        leaf_result.object_config_graph_package_head_commit_id
        if leaf_result is not None
        else commit_id
    )
    materialized_language_packages: tuple[dict[str, object], ...] = ()
    if leaf_result is not None:
        materialized_language_packages = (
            _materialized_language_packages_from_leaf_result(
                leaf_result=leaf_result,
                generated_code_package_refs=(
                    language_materialization_receipts.generated_code_package_refs
                ),
            )
        )
    bundle_packages = (
        _bundle_packages_from_leaf_result(
            leaf_result=leaf_result,
            workspace_root=request.workspace_root,
            materialized_language_packages=materialized_language_packages,
        )
        if leaf_result is not None
        else _bundle_packages_from_execution(
            request=request,
            execution_payload=function_call_execution,
            head_commit_id=head_commit_id,
        )
    )
    leaf_materialization_details = await _leaf_materialization_details(
        request=request,
        leaf_result=leaf_result,
        language_materialization_receipts=language_materialization_receipts,
        materialized_language_packages=materialized_language_packages,
    )
    if (
        leaf_result is None
        and function_call_execution.get("status") == "executed"
        and applied_semantic_keys
        and not bundle_packages
    ):
        raise RuntimeError(
            "Meta semantic materialization executed OCG function calls but did "
            "not produce sealable ObjectConfigGraph package evidence."
        )
    return SemanticPackageMaterializationResult(
        details={
            "schema": "aware_meta.runtime_ocg.materialization.plan_evidence.v1",
            "provider_key": "aware_meta",
            "semantic_owner": "aware_meta.object_config_graph",
            "manifest_path": request.manifest_path.as_posix(),
            "semantic_branch_id": str(request.branch_id),
            "semantic_truth_graph": graph_metadata.get("semantic_truth_graph"),
            "source_graph_role": graph_metadata.get("source_graph_role"),
            "runtime_graph_role": graph_metadata.get("runtime_graph_role"),
            "source_graph_hash": graph_metadata.get("source_graph_hash"),
            "runtime_graph_hash": graph_metadata.get("runtime_graph_hash"),
            "semantic_function_call_plan_count": len(function_call_plans),
            "semantic_function_call_plans": tuple(
                plan.evidence_payload() for plan in function_call_plans
            ),
            "semantic_function_call_resolution_count": len(function_call_resolutions),
            "semantic_function_call_resolution_status_counts": (
                _resolution_status_counts(function_call_resolutions)
            ),
            "semantic_function_call_resolutions": tuple(
                resolution.evidence_payload()
                for resolution in function_call_resolutions
            ),
            "semantic_function_call_resolution_context": {
                "current_semantic_object_id_count": len(
                    function_call_context.current_semantic_object_ids
                ),
                "resolved_argument_ref_object_id_count": len(
                    function_call_context.resolved_argument_ref_object_ids
                ),
                "schema": "semantic_function_call_context",
            },
            "semantic_function_call_execution": function_call_execution,
            **leaf_materialization_details,
        },
        bundle_packages=bundle_packages,
        mode=(
            "full_rebuild"
            if leaf_result is not None
            else (
                "delta"
                if function_call_execution.get("status") == "executed"
                and bool(applied_semantic_keys)
                else "noop"
            )
        ),
        affected_semantic_keys=affected_semantic_keys,
        applied_semantic_keys=applied_semantic_keys,
        skipped_semantic_keys=(
            ()
            if leaf_result is not None
            else (
                skipped_semantic_keys
                if function_call_execution.get("status") == "executed"
                else affected_semantic_keys
            )
        ),
        stale_semantic_keys=(),
        semantic_function_call_plans=function_call_plans,
        fallback_reason=(
            "Meta provider replayed the full ObjectConfigGraph package manifest."
            if leaf_result is not None
            else (
                None
                if function_call_execution.get("status") == "executed"
                else _NON_MUTATING_REASON
            )
        ),
        commit_id=commit_id,
        head_commit_id=head_commit_id,
        semantic_object_config_graphs=(
            (leaf_result.object_config_graph,) if leaf_result is not None else ()
        ),
    )


async def materialize_delta(request: object) -> dict[str, object]:
    from aware_meta.materialization.deltas.service import (  # noqa: WPS433
        materialize_delta as _materialize_delta,
    )

    return await _materialize_delta(request=request)


async def materialize_provider_delta_outputs(
    *,
    request: object,
    provider_delta_head_move_applied_receipt: Mapping[str, object],
    provider_delta_oig_commit_receipt: Mapping[str, object],
    provider_delta_typed_operation_plan: Mapping[str, object] | None = None,
) -> dict[str, object]:
    started_at = perf_counter()
    phase_timings = _ProviderDeltaOutputPhaseTimings()
    with phase_timings.record("request_context_resolution"):
        context = _provider_delta_request_context(request=request)
    with phase_timings.record("workspace_root_resolution"):
        workspace_root = _provider_delta_workspace_root(
            request=request,
            context=context,
        )
    if workspace_root is None:
        return _provider_delta_output_materialization_payload(
            status="provider_delta_output_materialization_blocked",
            reason="provider_delta_workspace_root_unavailable",
            started_at=started_at,
            blockers=("workspace_root_unavailable",),
            provider_delta_output_phase_timings=phase_timings.payload(),
        )
    with phase_timings.record("head_move_preflight"):
        head_status = _optional_string_value(
            provider_delta_head_move_applied_receipt.get("status")
        )
    if head_status != "head_move_applied_receipt_ready":
        return _provider_delta_output_materialization_payload(
            status="provider_delta_output_materialization_blocked",
            reason="provider_delta_head_move_not_ready",
            started_at=started_at,
            blockers=(f"head_move_status:{head_status or 'unknown'}",),
            provider_delta_output_phase_timings=phase_timings.payload(),
        )
    with phase_timings.record("commit_preflight"):
        commit_status = _optional_string_value(
            provider_delta_oig_commit_receipt.get("status")
        )
    if commit_status == "execute_flag_commit_noop":
        return _provider_delta_output_materialization_payload(
            status="provider_delta_output_materialization_not_required",
            reason="provider_delta_noop_outputs_not_required",
            started_at=started_at,
            target_count=0,
            provider_delta_output_phase_timings=phase_timings.payload(),
        )
    with phase_timings.record("language_target_collection"):
        targets = _language_materialization_targets_from_context(
            context=context,
            workspace_root=workspace_root,
        )
    if not targets:
        return _provider_delta_output_materialization_payload(
            status="provider_delta_output_materialization_not_required",
            reason="provider_delta_language_targets_not_required",
            started_at=started_at,
            target_count=0,
            provider_delta_output_phase_timings=phase_timings.payload(),
        )
    with phase_timings.record("language_target_payload_build"):
        target_payloads = tuple(
            _provider_delta_language_target_payload(
                target_index=target_index,
                target=target,
                workspace_root=workspace_root,
            )
            for target_index, target in enumerate(targets)
        )
    with phase_timings.record("language_target_impact_plan"):
        language_target_impact_plan = provider_delta_language_target_impact_plan(
            provider_delta_typed_operation_plan=provider_delta_typed_operation_plan,
            target_payloads=target_payloads,
        )
        selected_target_indexes = _provider_delta_selected_language_target_indexes(
            language_target_impact_plan=language_target_impact_plan,
            target_count=len(targets),
        )
    with phase_timings.record("head_reference_resolution"):
        head_refs = _mapping_value(
            provider_delta_head_move_applied_receipt.get("head_refs")
        )
        source_code_package_id = _provider_delta_uuid_value(
            _provider_delta_request_package_value(
                request=request,
                key="source_code_package_id",
            )
            or head_refs.get("source_code_package_id")
        )
        object_config_graph_package_id = _provider_delta_uuid_value(
            head_refs.get("semantic_package_id")
        )
        object_config_graph_commit_id = _provider_delta_uuid_value(
            head_refs.get("semantic_root_object_instance_graph_commit_id")
            or head_refs.get("semantic_object_instance_graph_commit_id")
            or provider_delta_oig_commit_receipt.get("object_instance_graph_commit_id")
        )
        source_object_instance_graph_commit_id = _provider_delta_uuid_value(
            head_refs.get("source_object_instance_graph_commit_id")
        )
    with phase_timings.record("manifest_path_resolution"):
        manifest_path = _provider_delta_manifest_path(
            request=request,
            workspace_root=workspace_root,
        )
    receipts: list[dict[str, object]] = []
    post_step_receipts: list[dict[str, object]] = []
    tool_step_receipts: list[dict[str, object]] = []
    tool_timings_s: dict[str, float] = {}
    top_level_tool_duration_s = 0.0
    blockers: list[str] = []
    dependency_runtime_graphs_by_source_key: dict[
        tuple[str, str, str],
        tuple[ObjectConfigGraph, ...],
    ] = {}
    with phase_timings.record("cache_initialization"):
        runtime_to_language_cache = RuntimeToLanguageLoweringCache(
            deep_copy_hits=False,
            deep_copy_stores=False,
            store_language_results=(
                _provider_delta_should_store_runtime_to_language_results(
                    targets=targets,
                    selected_target_indexes=selected_target_indexes,
                )
            ),
        )
        runtime_derivation_cache = RuntimeObjectConfigGraphDerivationCache(
            deep_copy_hits=False,
            deep_copy_stores=False,
        )
    rendered_target_count = 0
    for target_index, target in (
        (index, target)
        for index, target in enumerate(targets)
        if index in selected_target_indexes
    ):
        with phase_timings.record("source_graph_resolution"):
            source_graph = _provider_delta_output_source_graph(
                target=target,
                context=context,
            )
            if (
                source_graph is None
                and _provider_delta_target_allows_hydrated_source_graph(target=target)
            ):
                source_graph = await _provider_delta_hydrated_output_source_graph(
                    context=context,
                    workspace_root=workspace_root,
                    provider_delta_head_move_applied_receipt=(
                        provider_delta_head_move_applied_receipt
                    ),
                    target=target,
                )
        if source_graph is None:
            blockers.append(
                "source_graph_unavailable:"
                f"{_provider_delta_target_fqn_prefix(target=target) or 'unknown'}"
            )
            continue
        with phase_timings.record("dependency_graph_resolution"):
            dependency_cache_key = _language_dependency_source_graph_cache_key(
                source_graph.graph,
            )
            dependency_runtime_graphs = dependency_runtime_graphs_by_source_key.get(
                dependency_cache_key,
            )
            if dependency_runtime_graphs is None:
                dependency_runtime_graphs = (
                    _provider_delta_output_dependency_runtime_graphs(
                        context=context,
                        source_graph=source_graph.graph,
                        manifest_path=manifest_path,
                        workspace_root=workspace_root,
                    )
                )
                dependency_runtime_graphs_by_source_key[dependency_cache_key] = (
                    dependency_runtime_graphs
                )
            external_runtime_graphs = (
                dependency_runtime_graphs
                if manifest_path is not None
                else _external_runtime_object_config_graphs_from_context(
                    context=context,
                    source_graph=source_graph,
                )
            )
        try:
            with phase_timings.record("language_plugin_invocation"):
                result = materialize_object_config_graph_via_language_plugin(
                    LanguagePluginMaterializationRequest(
                        source_graph=source_graph.graph,
                        target_language_plugin_id=target.target_language_plugin_id,
                        external_runtime_graphs=external_runtime_graphs,
                        package_dependency_graphs=dependency_runtime_graphs,
                        source_is_runtime=source_graph.source_is_runtime,
                        output_root=target.output_root,
                        import_root=target.import_root,
                        package_name=target.package_name,
                        renderer_profile=target.renderer_profile,
                        renderer_kind=target.renderer_kind,
                        materialization_source=target.materialization_source,
                        stable_ids_import_root=target.stable_ids_import_root,
                        stable_ids_ownership=target.stable_ids_ownership,
                        stable_ids_resolution_policy=(
                            target.stable_ids_resolution_policy
                        ),
                        function_impl_ownership=None,
                        function_impl_parity_policy=None,
                        source_code_package_id=source_code_package_id,
                        object_config_graph_package_id=object_config_graph_package_id,
                        object_config_graph_commit_id=object_config_graph_commit_id,
                        emit_files=True,
                        post_step_tool_env_by_tool_id=(
                            _language_materialization_post_step_tool_mapping_by_tool_id(
                                context=context,
                                mapping_key="state_env",
                            )
                        ),
                        post_step_executable_overrides_by_tool_id=(
                            _language_materialization_post_step_tool_mapping_by_tool_id(
                                context=context,
                                mapping_key="executable_overrides",
                            )
                        ),
                        runtime_to_language_cache=runtime_to_language_cache,
                        runtime_derivation_cache=runtime_derivation_cache,
                        reuse_external_runtime_graphs=source_graph.source_is_runtime,
                        derive_external_projection_graphs=(
                            _language_materialization_target_should_lower_external_graphs(
                                target=target,
                            )
                        ),
                        lower_language_external_graphs=(
                            _language_materialization_target_should_lower_external_graphs(
                                target=target,
                            )
                        ),
                    )
                )
        except Exception as exc:
            return _provider_delta_output_materialization_payload(
                status="provider_delta_output_materialization_failed",
                reason="provider_delta_language_materialization_failed",
                started_at=started_at,
                target_count=len(targets),
                rendered_target_count=rendered_target_count,
                artifact_ownership_receipts=tuple(receipts),
                post_step_receipts=tuple(post_step_receipts),
                tool_step_receipts=tuple(tool_step_receipts),
                tool_timings_s=tool_timings_s,
                blockers=tuple(dict.fromkeys(blockers)),
                runtime_to_language_cache=runtime_to_language_cache.stats_payload(),
                runtime_derivation_cache=runtime_derivation_cache.stats_payload(),
                error=f"{type(exc).__name__}: {exc}",
                provider_delta_language_target_impact_plan=(
                    language_target_impact_plan
                ),
                provider_delta_output_phase_timings=phase_timings.payload(),
            )
        rendered_target_count += 1
        with phase_timings.record("language_receipt_assembly"):
            receipts.extend(
                _provider_delta_language_receipt_payload(
                    receipt_payload=receipt.as_payload(),
                    output_root=target.output_root,
                    source_object_instance_graph_commit_id=(
                        source_object_instance_graph_commit_id
                    ),
                )
                for receipt in result.ownership_receipts
            )
            post_step_receipts.extend(
                dict(receipt) for receipt in result.post_step_receipts
            )
        with phase_timings.record("tool_step_timing_assembly"):
            for step in getattr(result, "tool_steps", ()):
                step_name = str(getattr(step, "name", "") or "").strip()
                if not step_name:
                    continue
                duration_s = _provider_delta_tool_step_duration_s(step=step)
                step_details = getattr(step, "details", {})
                if not isinstance(step_details, Mapping):
                    step_details = {}
                timing_scope = str(step_details.get("timing_scope") or "step")
                if timing_scope != "substep":
                    top_level_tool_duration_s += duration_s
                timing_key = _language_materialization_tool_timing_key(
                    target=target,
                    target_index=target_index,
                    step_name=step_name,
                )
                tool_timings_s[timing_key] = duration_s
                tool_step_receipts.append(
                    {
                        "name": step_name,
                        "timing_key": timing_key,
                        "tool_id": timing_key,
                        "duration_s": duration_s,
                        "status": str(getattr(step, "status", "") or "succeeded"),
                        "timing_scope": timing_scope,
                        "timing_parent_step": step_details.get("timing_parent_step"),
                        "graph_role": step_details.get("graph_role"),
                        "target_language_plugin_id": (
                            target.target_language_plugin_id.value
                        ),
                        "materialization_source": target.materialization_source,
                        "renderer_profile": target.renderer_profile,
                        "renderer_kind": target.renderer_kind,
                        "source_is_runtime": target.source_is_runtime,
                    }
                )
    with phase_timings.record("tool_timing_total_assembly"):
        if tool_timings_s:
            tool_timings_s["total"] = round(
                top_level_tool_duration_s or sum(tool_timings_s.values()),
                6,
            )
    if blockers:
        return _provider_delta_output_materialization_payload(
            status="provider_delta_output_materialization_blocked",
            reason="provider_delta_language_materialization_inputs_incomplete",
            started_at=started_at,
            target_count=len(targets),
            rendered_target_count=rendered_target_count,
            artifact_ownership_receipts=tuple(receipts),
            post_step_receipts=tuple(post_step_receipts),
            tool_step_receipts=tuple(tool_step_receipts),
            tool_timings_s=tool_timings_s,
            blockers=tuple(dict.fromkeys(blockers)),
            runtime_to_language_cache=runtime_to_language_cache.stats_payload(),
            runtime_derivation_cache=runtime_derivation_cache.stats_payload(),
            provider_delta_language_target_impact_plan=language_target_impact_plan,
            provider_delta_output_phase_timings=phase_timings.payload(),
        )
    return _provider_delta_output_materialization_payload(
        status="provider_delta_output_materialization_ready",
        reason="provider_delta_language_outputs_materialized",
        started_at=started_at,
        target_count=len(targets),
        rendered_target_count=rendered_target_count,
        artifact_ownership_receipts=tuple(receipts),
        post_step_receipts=tuple(post_step_receipts),
        tool_step_receipts=tuple(tool_step_receipts),
        tool_timings_s=tool_timings_s,
        runtime_to_language_cache=runtime_to_language_cache.stats_payload(),
        runtime_derivation_cache=runtime_derivation_cache.stats_payload(),
        provider_delta_language_target_impact_plan=language_target_impact_plan,
        provider_delta_output_phase_timings=phase_timings.payload(),
    )


async def _provider_delta_hydrated_output_source_graph(
    *,
    context: Mapping[str, object],
    workspace_root: Path,
    provider_delta_head_move_applied_receipt: Mapping[str, object],
    target: _LanguageMaterializationTarget,
) -> _LanguageMaterializationSourceGraph | None:
    _ = target
    graph_context = context.get("aware_meta.graph_runtime_context")
    index = getattr(graph_context, "index", None)
    if index is None:
        return None
    head_refs = _mapping_value(
        provider_delta_head_move_applied_receipt.get("head_refs")
    )
    branch_id = _provider_delta_uuid_value(head_refs.get("semantic_branch_id"))
    root_id = _provider_delta_uuid_value(head_refs.get("semantic_root_id"))
    if branch_id is None or root_id is None:
        return None
    projection_hashes = _provider_delta_output_projection_hashes(
        graph_context=graph_context,
        head_refs=head_refs,
    )
    if not projection_hashes:
        return None
    from aware_meta.graph.instance.commit.fs_store import (  # noqa: WPS433
        FSCommitStore,
        FSSnapshotStore,
    )
    from aware_meta.graph.instance.commit.materialization_cache import (  # noqa: WPS433,E501
        CachedLaneMaterializer,
    )
    from aware_meta.runtime.oig_model_reifier import (  # noqa: WPS433
        reify_oig_root_model,
    )

    materializer = CachedLaneMaterializer(
        commits=FSCommitStore(root_dir=workspace_root),
        snaps=FSSnapshotStore(root_dir=workspace_root),
    )
    for projection_hash in projection_hashes:
        opg = getattr(index, "opg_by_hash", {}).get(projection_hash)
        if opg is None:
            continue
        try:
            snapshot = await materializer.get(
                branch_id=branch_id,
                ocg=index.ocg,
                opg=opg,
                commit_id=None,
                attribute_configs_by_id=index.attribute_configs_by_id,
                class_configs_by_id=index.class_configs_by_id,
            )
            oig = getattr(snapshot, "oig", None)
            if oig is None and isinstance(snapshot, tuple) and snapshot:
                oig = snapshot[0]
            if oig is None:
                continue
            graph = reify_oig_root_model(
                index=index,
                opg=opg,
                oig=oig,
                model_type=ObjectConfigGraph,
                root_id=root_id,
                branch_id=branch_id,
            )
            if isinstance(graph, ObjectConfigGraph):
                return _LanguageMaterializationSourceGraph(
                    graph=graph,
                    source_is_runtime=False,
                )
        except Exception:
            continue
    return None


def _provider_delta_should_store_runtime_to_language_results(
    *,
    targets: tuple[_LanguageMaterializationTarget, ...],
    selected_target_indexes: frozenset[int],
) -> bool:
    signatures: list[tuple[str, str | None, bool]] = []
    for target_index, target in enumerate(targets):
        if target_index not in selected_target_indexes:
            continue
        if target.target_language_plugin_id == CodeLanguage.aware:
            continue
        signatures.append(
            (
                target.target_language_plugin_id.value,
                target.renderer_profile.strip() if target.renderer_profile else None,
                target.source_is_runtime,
            )
        )
    return len(signatures) != len(frozenset(signatures))


def _provider_delta_target_allows_hydrated_source_graph(
    *,
    target: _LanguageMaterializationTarget,
) -> bool:
    """Return whether a target may fall back to committed OIG hydration."""

    materialization_source = (target.materialization_source or "").strip().lower()
    renderer_profile = (target.renderer_profile or "").strip().lower()
    if materialization_source in {"api", "ontology_dto"}:
        return False
    if renderer_profile in {
        "api_public_package",
        "api_service_protocol",
        "ontology_dto",
    }:
        return False
    return True


def _provider_delta_output_projection_hashes(
    *,
    graph_context: object,
    head_refs: Mapping[str, object],
) -> tuple[str, ...]:
    candidates: list[str] = []
    for raw_value in (
        head_refs.get("semantic_projection_hash"),
        _graph_context_projection_hash(
            graph_context=graph_context,
            projection_name="ObjectConfigGraph",
        ),
        _graph_context_projection_hash(
            graph_context=graph_context,
            projection_name="ObjectConfigGraphPackage",
        ),
    ):
        value = _optional_string_value(raw_value)
        if value is not None:
            candidates.append(value)
    return tuple(dict.fromkeys(candidates))


def _graph_context_projection_hash(
    *,
    graph_context: object,
    projection_name: str,
) -> str | None:
    projection_hash_for_name = getattr(graph_context, "projection_hash_for_name", None)
    if callable(projection_hash_for_name):
        try:
            value = projection_hash_for_name(projection_name)
        except Exception:
            value = None
        return _optional_string_value(value)
    projection_hash_by_name = getattr(graph_context, "projection_hash_by_name", None)
    if isinstance(projection_hash_by_name, Mapping):
        return _optional_string_value(projection_hash_by_name.get(projection_name))
    return None


def _provider_delta_output_materialization_payload(
    *,
    status: str,
    reason: str,
    started_at: float,
    target_count: int = 0,
    rendered_target_count: int = 0,
    artifact_ownership_receipts: tuple[Mapping[str, object], ...] = (),
    post_step_receipts: tuple[Mapping[str, object], ...] = (),
    tool_step_receipts: tuple[Mapping[str, object], ...] = (),
    tool_timings_s: Mapping[str, float] | None = None,
    blockers: tuple[str, ...] = (),
    runtime_to_language_cache: Mapping[str, object] | None = None,
    runtime_derivation_cache: Mapping[str, object] | None = None,
    provider_delta_language_target_impact_plan: Mapping[str, object] | None = None,
    provider_delta_output_phase_timings: Mapping[str, object] | None = None,
    error: str | None = None,
) -> dict[str, object]:
    language_target_impact_plan = dict(provider_delta_language_target_impact_plan or {})
    output_phase_timings = dict(provider_delta_output_phase_timings or {})
    return {
        "receipt_kind": "meta_provider_delta_output_materialization",
        "contract_version": "aware.meta.provider-delta.output-materialization.v1",
        "status": status,
        "reason": reason,
        "available": status == "provider_delta_output_materialization_ready",
        "blocked": status == "provider_delta_output_materialization_blocked",
        "target_count": target_count,
        "rendered_target_count": rendered_target_count,
        "language_target_impact_selected_target_count": (
            language_target_impact_plan.get("selected_target_count")
        ),
        "language_target_impact_skipped_target_count": (
            language_target_impact_plan.get("skipped_target_count")
        ),
        "provider_delta_language_target_impact_plan": language_target_impact_plan,
        "artifact_ownership_receipt_count": len(artifact_ownership_receipts),
        "artifact_ownership_receipts": tuple(
            dict(receipt) for receipt in artifact_ownership_receipts
        ),
        "post_step_receipt_count": len(post_step_receipts),
        "post_step_receipts": tuple(dict(receipt) for receipt in post_step_receipts),
        "tool_step_receipt_count": len(tool_step_receipts),
        "tool_step_receipts": tuple(dict(receipt) for receipt in tool_step_receipts),
        "tool_timings_s": dict(tool_timings_s or {}),
        "runtime_to_language_cache": dict(runtime_to_language_cache or {}),
        "runtime_derivation_cache": dict(runtime_derivation_cache or {}),
        "provider_delta_output_phase_timings": output_phase_timings,
        "provider_delta_output_phase_timings_s": (
            _provider_delta_output_phase_timings_flat_payload(
                output_phase_timings=output_phase_timings,
            )
        ),
        "blockers": blockers,
        "blocker_count": len(blockers),
        "duration_s": round(max(perf_counter() - started_at, 0.0), 6),
        "error": error,
    }


def _provider_delta_output_phase_timings_flat_payload(
    *,
    output_phase_timings: Mapping[str, object],
) -> dict[str, float]:
    phases = output_phase_timings.get("phases_s")
    timings_s: dict[str, float] = {}
    if isinstance(phases, Mapping):
        for key, value in phases.items():
            if isinstance(value, int | float):
                timings_s[str(key)] = round(float(value), 6)
    total_s = output_phase_timings.get("total_s")
    if isinstance(total_s, int | float):
        timings_s["total_s"] = round(float(total_s), 6)
    return timings_s


def _provider_delta_request_context(
    *,
    request: object,
) -> Mapping[str, object]:
    payload: dict[str, object] = {}
    for field_name in ("context", "semantic_function_call_execution_context"):
        value = getattr(request, field_name, None)
        if isinstance(value, Mapping):
            payload.update(value)
    for field_name in (
        "aware_meta.graph_runtime_context",
        "runtime_object_config_graphs",
        "runtime_graphs",
        "semantic_object_config_graphs",
        "source_graphs",
        "provider_runtime_context",
        "runtime",
        "index",
    ):
        value = getattr(request, field_name, None)
        if value is not None:
            payload.setdefault(field_name, value)
    execution_context = getattr(request, "execution_context", None)
    _merge_provider_delta_execution_context_entries(
        payload=payload,
        execution_context=execution_context,
    )
    return payload


def _merge_provider_delta_execution_context_entries(
    *,
    payload: dict[str, object],
    execution_context: object,
) -> None:
    entries = getattr(execution_context, "entries", None)
    if isinstance(entries, Mapping):
        payload.update(entries)
    provider_entries = getattr(execution_context, "provider_entries", None)
    if not isinstance(provider_entries, Mapping):
        return
    for raw_provider_payload in provider_entries.values():
        if isinstance(raw_provider_payload, Mapping):
            payload.update(raw_provider_payload)


def _provider_delta_workspace_root(
    *,
    request: object,
    context: Mapping[str, object],
) -> Path | None:
    raw_value = getattr(request, "workspace_root", None) or context.get(
        "workspace_root"
    )
    if raw_value is None:
        return None
    try:
        return Path(raw_value).resolve()
    except TypeError:
        return None


def _provider_delta_request_package_value(
    *,
    request: object,
    key: str,
) -> object:
    package = getattr(request, "package", None)
    if isinstance(package, Mapping):
        return package.get(key)
    return getattr(package, key, None)


def _provider_delta_manifest_path(
    *,
    request: object,
    workspace_root: Path,
) -> Path | None:
    raw_value = _optional_string_value(
        _provider_delta_request_package_value(
            request=request,
            key="manifest_path",
        )
    )
    if raw_value is None:
        return None
    path = Path(raw_value)
    return path if path.is_absolute() else workspace_root / path


def _provider_delta_output_source_graph(
    *,
    target: _LanguageMaterializationTarget,
    context: Mapping[str, object],
) -> _LanguageMaterializationSourceGraph | None:
    fqn_prefix = _provider_delta_target_fqn_prefix(target=target)
    if fqn_prefix is None:
        return None
    if target.source_is_runtime:
        runtime_graph = _object_config_graph_for_fqn_prefix_from_context(
            context=context,
            graph_kind="runtime",
            fqn_prefix=fqn_prefix,
        )
        if runtime_graph is not None:
            return _LanguageMaterializationSourceGraph(
                graph=runtime_graph,
                source_is_runtime=True,
            )
        source_graph = _object_config_graph_for_fqn_prefix_from_context(
            context=context,
            graph_kind="source",
            fqn_prefix=fqn_prefix,
        )
        if source_graph is not None:
            return _LanguageMaterializationSourceGraph(
                graph=source_graph,
                source_is_runtime=False,
            )
        return None
    source_graph = _object_config_graph_for_fqn_prefix_from_context(
        context=context,
        graph_kind="source",
        fqn_prefix=fqn_prefix,
    )
    if source_graph is not None:
        return _LanguageMaterializationSourceGraph(
            graph=source_graph,
            source_is_runtime=False,
        )
    runtime_graph = _object_config_graph_for_fqn_prefix_from_context(
        context=context,
        graph_kind="runtime",
        fqn_prefix=fqn_prefix,
    )
    if runtime_graph is not None:
        return _LanguageMaterializationSourceGraph(
            graph=runtime_graph,
            source_is_runtime=True,
        )
    return None


def _object_config_graph_for_fqn_prefix_from_context(
    *,
    context: Mapping[str, object],
    graph_kind: str,
    fqn_prefix: str,
) -> ObjectConfigGraph | None:
    graphs = _object_config_graphs_for_kind_from_context(
        context=context,
        graph_kind=graph_kind,
    )
    for graph in graphs:
        if fqn_prefix in _object_config_graph_identity_tokens(graph=graph):
            return graph
    if len(graphs) == 1:
        return graphs[0]
    return None


def _object_config_graphs_for_kind_from_context(
    *,
    context: Mapping[str, object],
    graph_kind: str,
) -> tuple[ObjectConfigGraph, ...]:
    if graph_kind == "runtime":
        explicit_keys = ("runtime_object_config_graphs", "runtime_graphs")
        meta_context_attr = "runtime_graphs"
        meta_context_mapping_attr = "runtime_graph_by_package_name"
    else:
        explicit_keys = ("semantic_object_config_graphs", "source_graphs")
        meta_context_attr = "source_graphs"
        meta_context_mapping_attr = "source_graph_by_package_name"
    graphs: list[ObjectConfigGraph] = []
    seen: set[UUID] = set()
    seen_fqn_prefixes: set[str] = set()
    for key in explicit_keys:
        for graph in _object_config_graphs_from_context_value(context.get(key)):
            _append_unique_object_config_graph(
                graphs=graphs,
                graph=graph,
                seen=seen,
                seen_fqn_prefixes=seen_fqn_prefixes,
            )
    meta_context = context.get("aware_meta.graph_runtime_context")
    for graph in _object_config_graphs_from_context_value(
        getattr(meta_context, meta_context_attr, ()),
    ):
        _append_unique_object_config_graph(
            graphs=graphs,
            graph=graph,
            seen=seen,
            seen_fqn_prefixes=seen_fqn_prefixes,
        )
    for graph in _object_config_graphs_from_mapping_value(
        getattr(meta_context, meta_context_mapping_attr, {}),
    ):
        _append_unique_object_config_graph(
            graphs=graphs,
            graph=graph,
            seen=seen,
            seen_fqn_prefixes=seen_fqn_prefixes,
        )
    index_graph = getattr(getattr(meta_context, "index", None), "ocg", None)
    if isinstance(index_graph, ObjectConfigGraph):
        _append_unique_object_config_graph(
            graphs=graphs,
            graph=index_graph,
            seen=seen,
            seen_fqn_prefixes=seen_fqn_prefixes,
        )
    provider_context = context.get("provider_runtime_context")
    for key in (*explicit_keys, meta_context_attr):
        for graph in _object_config_graphs_from_context_value(
            _context_value(provider_context, key=key)
        ):
            _append_unique_object_config_graph(
                graphs=graphs,
                graph=graph,
                seen=seen,
                seen_fqn_prefixes=seen_fqn_prefixes,
            )
    provider_meta_context = _context_value(provider_context, key="meta_context")
    for graph in _object_config_graphs_from_context_value(
        _context_value(provider_meta_context, key=meta_context_attr)
    ):
        _append_unique_object_config_graph(
            graphs=graphs,
            graph=graph,
            seen=seen,
            seen_fqn_prefixes=seen_fqn_prefixes,
        )
    for graph in _object_config_graphs_from_mapping_value(
        _context_value(provider_meta_context, key=meta_context_mapping_attr)
    ):
        _append_unique_object_config_graph(
            graphs=graphs,
            graph=graph,
            seen=seen,
            seen_fqn_prefixes=seen_fqn_prefixes,
        )
    return tuple(graphs)


def _append_unique_object_config_graph(
    *,
    graphs: list[ObjectConfigGraph],
    graph: ObjectConfigGraph,
    seen: set[UUID],
    seen_fqn_prefixes: set[str],
) -> None:
    if graph.id in seen:
        return
    fqn_prefix = _object_config_graph_fqn_prefix_key(graph=graph)
    if fqn_prefix is not None and fqn_prefix in seen_fqn_prefixes:
        return
    seen.add(graph.id)
    if fqn_prefix is not None:
        seen_fqn_prefixes.add(fqn_prefix)
    graphs.append(graph)


def _object_config_graph_fqn_prefix_key(*, graph: ObjectConfigGraph) -> str | None:
    fqn_prefix = str(graph.fqn_prefix or "").strip()
    if not fqn_prefix:
        return None
    return fqn_prefix


def _object_config_graph_for_fqn_prefix(
    *,
    value: object,
    fqn_prefix: str,
) -> ObjectConfigGraph | None:
    for graph in _object_config_graphs_from_context_value(value):
        if graph.fqn_prefix == fqn_prefix:
            return graph
    return None


def _object_config_graph_identity_tokens(
    *,
    graph: ObjectConfigGraph,
) -> tuple[str, ...]:
    raw_values = (
        getattr(graph, "fqn_prefix", None),
        getattr(graph, "name", None),
        getattr(getattr(graph, "object_config_graph_identity", None), "name", None),
        getattr(
            getattr(graph, "object_config_graph_identity", None),
            "fqn_prefix",
            None,
        ),
    )
    return tuple(
        dict.fromkeys(
            value
            for value in (_optional_string_value(raw_value) for raw_value in raw_values)
            if value is not None
        )
    )


def _object_config_graphs_from_mapping_value(
    value: object,
) -> tuple[ObjectConfigGraph, ...]:
    if not isinstance(value, Mapping):
        return ()
    return tuple(item for item in value.values() if isinstance(item, ObjectConfigGraph))


def _context_value(value: object, *, key: str) -> object | None:
    if isinstance(value, Mapping):
        return value.get(key)
    return getattr(value, key, None) if value is not None else None


def _provider_delta_target_fqn_prefix(
    *,
    target: _LanguageMaterializationTarget,
) -> str | None:
    if target.source_is_runtime:
        return _optional_string_value(target.import_root)
    materialization_source = _optional_string_value(target.materialization_source)
    stable_ids_import_root = _optional_string_value(target.stable_ids_import_root)
    if (
        materialization_source == "ontology_orm_models"
        and stable_ids_import_root is not None
        and stable_ids_import_root.endswith("_ontology_orm_models")
    ):
        return stable_ids_import_root.removesuffix("_ontology_orm_models")
    if (
        materialization_source == "ontology_dto"
        and stable_ids_import_root is not None
        and stable_ids_import_root.endswith("_ontology_dto")
    ):
        return stable_ids_import_root.removesuffix("_ontology_dto")
    if stable_ids_import_root is not None and stable_ids_import_root.endswith(
        "_ontology"
    ):
        return stable_ids_import_root.removesuffix("_ontology")
    import_root = _optional_string_value(target.import_root)
    if (
        materialization_source == "ontology_orm_models"
        and import_root is not None
        and import_root.endswith("_ontology_orm_models")
    ):
        return import_root.removesuffix("_ontology_orm_models")
    if (
        materialization_source == "ontology_dto"
        and import_root is not None
        and import_root.endswith("_ontology_dto")
    ):
        return import_root.removesuffix("_ontology_dto")
    if import_root is not None and import_root.endswith("_ontology"):
        return import_root.removesuffix("_ontology")
    return import_root


def _provider_delta_language_receipt_payload(
    *,
    receipt_payload: Mapping[str, object],
    output_root: Path,
    source_object_instance_graph_commit_id: UUID | None,
) -> dict[str, object]:
    payload = _workspace_language_receipt_payload(
        receipt_payload=receipt_payload,
        output_root=output_root,
    )
    if (
        source_object_instance_graph_commit_id is not None
        and payload.get("source_object_instance_graph_commit_id") is None
    ):
        payload["source_object_instance_graph_commit_id"] = str(
            source_object_instance_graph_commit_id
        )
    if payload.get("producer_step") is None:
        payload["producer_step"] = "provider_delta_output_materialization"
    provider_payload = payload.get("provider_payload")
    payload["provider_payload"] = {
        **(dict(provider_payload) if isinstance(provider_payload, Mapping) else {}),
        "provider_delta_output_materialization": True,
    }
    return payload


def meta_ocg_migration_artifact_ownership_receipts_from_bundle(
    *,
    bundle: MetaOcgMigrationArtifactBundle,
    workspace_root: Path,
) -> tuple[dict[str, object], ...]:
    """Convert Meta-owned migration artifacts into Workspace ownership receipts."""

    lane_index_path = _required_ocg_migration_artifact_path(
        artifact=bundle.lane_index,
        role=ARTIFACT_ROLE_LANE_INDEX,
    )
    lane_index_manifest_path = _relative_to_workspace_root(
        path=lane_index_path,
        workspace_root=workspace_root,
    )
    return tuple(
        _meta_ocg_migration_artifact_ownership_receipt(
            bundle=bundle,
            artifact=artifact,
            workspace_root=workspace_root,
            manifest_path=lane_index_manifest_path,
        )
        for artifact in bundle.artifacts
    )


def _meta_ocg_migration_artifact_ownership_receipt(
    *,
    bundle: MetaOcgMigrationArtifactBundle,
    artifact: MetaOcgMigrationArtifact,
    workspace_root: Path,
    manifest_path: str,
) -> dict[str, object]:
    artifact_path = _required_ocg_migration_artifact_path(
        artifact=artifact,
        role=artifact.artifact_role,
    )
    payload = artifact.payload
    commit_id = (
        _optional_string_value(payload.get("commit_id"))
        or _optional_string_value(payload.get("head_commit_id"))
        or str(bundle.head_commit_id)
    )
    source_object_instance_graph_id = (
        _optional_string_value(payload.get("source_object_instance_graph_id"))
        or _optional_string_value(bundle.receipt.get("source_object_instance_graph_id"))
        or _optional_string_value(bundle.receipt.get("object_instance_graph_id"))
        or str(bundle.object_config_graph_id)
    )
    provider_payload: dict[str, object] = {
        "package_key": bundle.package_key,
        "object_config_graph_package_id": _uuid_text(
            bundle.object_config_graph_package_id
        ),
        "object_config_graph_id": str(bundle.object_config_graph_id),
        "source_object_instance_graph_id": source_object_instance_graph_id,
        "branch_id": str(bundle.branch_id),
        "projection_hash": bundle.projection_hash,
        "head_commit_id": str(bundle.head_commit_id),
        "commit_id": commit_id,
        "artifact_key": artifact.artifact_key,
        "artifact_role": artifact.artifact_role,
    }
    for key in (
        "parent_commit_id",
        "dialect",
        "migration_kind",
        "source_delta_artifact_key",
        "node_delta_count",
        "delta_source",
    ):
        value = payload.get(key)
        if value is not None:
            provider_payload[key] = value
    return {
        "producer_provider_key": META_OCG_MIGRATION_ARTIFACT_PRODUCER_PROVIDER_KEY,
        "producer_key": META_OCG_MIGRATION_ARTIFACT_PRODUCER_KEY,
        "producer_kind": "semantic_materializer",
        "semantic_owner": META_OBJECT_CONFIG_GRAPH_OWNER,
        "output_key": _meta_ocg_migration_artifact_output_key(
            artifact_role=artifact.artifact_role
        ),
        "artifact_family": META_OCG_MIGRATION_ARTIFACT_FAMILY,
        "artifact_key": artifact.artifact_key,
        "artifact_role": artifact.artifact_role,
        "required_for": (
            "workspace_revision",
            "sdk_local_state",
            "service_local_state",
        ),
        "status": "available",
        "path": artifact_path.as_posix(),
        "digest": artifact.digest,
        "digest_algorithm": artifact.digest_algorithm,
        "source_object_instance_graph_commit_id": commit_id,
        "manifest_path": manifest_path,
        "media_type": META_OCG_MIGRATION_ARTIFACT_MEDIA_TYPE,
        "runtime_contract_version": (
            META_OCG_MIGRATION_ARTIFACT_RUNTIME_CONTRACT_VERSION
        ),
        "provider_payload": provider_payload,
        "size_bytes": artifact_path.stat().st_size if artifact_path.exists() else None,
    }


def _meta_ocg_migration_artifact_output_key(*, artifact_role: str) -> str:
    if artifact_role == ARTIFACT_ROLE_LANE_INDEX:
        return META_OCG_MIGRATION_LANE_INDEX_OUTPUT_KEY
    if artifact_role == ARTIFACT_ROLE_OCG_DELTA:
        return META_OCG_MIGRATION_DELTA_OUTPUT_KEY
    if artifact_role == ARTIFACT_ROLE_DIALECT_MIGRATION:
        return META_OCG_MIGRATION_DIALECT_OUTPUT_KEY
    raise ValueError(f"Unknown OCG migration artifact role: {artifact_role}")


def _required_ocg_migration_artifact_path(
    *,
    artifact: MetaOcgMigrationArtifact,
    role: str,
) -> Path:
    if artifact.path is None:
        raise ValueError(f"OCG migration {role} artifact must have a written path")
    return artifact.path


def _provider_delta_tool_step_duration_s(*, step: object) -> float:
    raw_duration_s = getattr(step, "duration_s", None)
    if isinstance(raw_duration_s, bool):
        return 0.0
    try:
        return round(max(float(raw_duration_s), 0.0), 6)
    except (TypeError, ValueError):
        return 0.0


def _provider_delta_uuid_value(value: object) -> UUID | None:
    if isinstance(value, UUID):
        return value
    text = _optional_string_value(value)
    if text is None:
        return None
    try:
        return UUID(text)
    except ValueError:
        return None


def _semantic_keys_from_request(
    request: SemanticPackageMaterializationRequest,
) -> tuple[str, ...]:
    raw_keys = request.change_preview.get("affected_semantic_keys")
    if not isinstance(raw_keys, (list, tuple, set)):
        return ()
    return tuple(sorted({str(key).strip() for key in raw_keys if str(key).strip()}))


def _runtime_graph_metadata_from_preview(
    change_preview: Mapping[str, object],
) -> dict[str, object]:
    metadata = _mapping_value(change_preview.get("metadata"))
    return {
        key: metadata.get(key)
        for key in (
            "semantic_truth_graph",
            "source_graph_role",
            "runtime_graph_role",
            "source_graph_hash",
            "runtime_graph_hash",
        )
    }


def _resolution_status_counts(
    resolutions: tuple[MetaSemanticFunctionCallResolution, ...],
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for resolution in resolutions:
        status = str(getattr(resolution, "status", "")).strip()
        if not status:
            continue
        counts[status] = counts.get(status, 0) + 1
    return dict(sorted(counts.items()))


async def _function_call_execution_detail(
    *,
    context: Mapping[str, object],
    function_call_resolutions: tuple[MetaSemanticFunctionCallResolution, ...],
) -> dict[str, object]:
    config = SemanticFunctionCallExecutionConfig.from_materialization_context(context)
    payload = config.evidence_payload()
    if not config.enabled:
        payload["status"] = "disabled"
        payload["reason"] = _NON_MUTATING_REASON
        return payload
    backend = meta_semantic_function_call_execution_backend_from_context(context)
    if backend is None:
        payload["status"] = "backend_unavailable"
        payload["reason"] = (
            "Semantic function-call execution was enabled, but no Meta graph "
            "execution backend was provided in materialization context."
        )
        return payload
    result = await execute_meta_semantic_function_call_resolutions(
        resolutions=function_call_resolutions,
        backend=backend,
        continue_on_failure=config.continue_on_failure,
    )
    payload["status"] = "executed"
    payload.update(result.evidence_payload())
    return payload


def _execution_semantic_keys(
    execution_payload: Mapping[str, object],
    *,
    status: str,
) -> tuple[str, ...]:
    steps = execution_payload.get("steps")
    if not isinstance(steps, (list, tuple)):
        return ()
    semantic_keys: set[str] = set()
    for step in steps:
        if not isinstance(step, Mapping):
            continue
        if str(step.get("status") or "").strip() != status:
            continue
        semantic_key = _optional_string_value(step.get("semantic_key"))
        if semantic_key is not None:
            semantic_keys.add(semantic_key)
    return tuple(sorted(semantic_keys))


def _last_execution_commit_id(
    execution_payload: Mapping[str, object],
) -> UUID | None:
    steps = execution_payload.get("steps")
    if not isinstance(steps, (list, tuple)):
        return None
    for step in reversed(tuple(steps)):
        if not isinstance(step, Mapping):
            continue
        if str(step.get("status") or "").strip() != "invoked":
            continue
        evidence = step.get("evidence")
        if not isinstance(evidence, Mapping):
            continue
        result = evidence.get("result")
        if not isinstance(result, Mapping):
            continue
        commit_id = _optional_string_value(result.get("commit_id"))
        if commit_id is None:
            result_evidence = result.get("evidence")
            if isinstance(result_evidence, Mapping):
                response = result_evidence.get("response")
                if isinstance(response, Mapping):
                    commit_id = _optional_string_value(
                        response.get("object_instance_graph_commit_id")
                    )
        if commit_id is None:
            continue
        try:
            return UUID(commit_id)
        except ValueError:
            continue
    return None


async def _materialize_leaf_package_if_supported(
    *,
    request: SemanticPackageMaterializationRequest,
) -> ObjectConfigGraphPackageLeafMaterializationResult | None:
    if not _looks_like_meta_runtime_index(request.index):
        return None
    progress_forwarder = None
    if getattr(request, "progress_callback", None) is not None:

        async def _forward_progress(payload: Mapping[str, object]) -> None:
            await _forward_leaf_package_subphase_progress(
                request=request,
                payload=payload,
            )

        progress_forwarder = _forward_progress

    leaf_result = await materialize_object_config_graph_package_leaf_from_manifest(
        runtime=request.runtime,
        index=request.index,
        actor_id=request.actor_id,
        branch_id=request.branch_id,
        workspace_root=request.workspace_root,
        aware_toml_path=request.manifest_path,
        source_code_package_id=request.source_code_package_id,
        external_graphs=list(
            _leaf_external_object_config_graphs_from_context(
                context=request.context,
                aware_toml_path=request.manifest_path,
                workspace_root=request.workspace_root,
            )
        ),
        force_fresh_semantic_materialization=(
            _force_fresh_semantic_materialization_from_context(request.context)
        ),
        progress_callback=progress_forwarder,
    )
    _validate_declared_generated_package_pin(
        request=request,
        leaf_result=leaf_result,
    )
    return leaf_result


def _validate_declared_generated_package_pin(
    *,
    request: SemanticPackageMaterializationRequest,
    leaf_result: ObjectConfigGraphPackageLeafMaterializationResult,
) -> None:
    materialization_input = request.materialization_input
    if materialization_input is None:
        return
    raw_pin = materialization_input.input_artifact_payload.get(
        "object_instance_graph_commit_id"
    )
    if not isinstance(raw_pin, str) or not raw_pin.strip():
        return
    expected = UUID(raw_pin.strip())
    actual = leaf_result.object_config_graph_package_object_instance_graph_commit_id
    if actual != expected:
        raise RuntimeError(
            "Generated ObjectConfigGraphPackage OIG pin does not match the "
            "materialized package head: "
            f"manifest_path={request.manifest_path} expected={expected} "
            f"actual={actual}"
        )


def _looks_like_meta_runtime_index(value: object) -> bool:
    return hasattr(value, "ocg") and hasattr(value, "opg_by_hash")


def _external_object_config_graphs_from_context(
    context: Mapping[str, object],
) -> tuple[ObjectConfigGraph, ...]:
    graphs: list[ObjectConfigGraph] = []
    seen: set[UUID] = set()
    seen_fqn_prefixes: set[str] = set()
    # Runtime graphs carry ObjectProjectionGraph declarations. Source/runtime
    # OCGs can have different ids for the same semantic FQN, so runtime graphs
    # must be seen first and source duplicates must not re-enter the external
    # closure.
    for graph_kind in ("runtime", "source"):
        for graph in _object_config_graphs_for_kind_from_context(
            context=context,
            graph_kind=graph_kind,
        ):
            _append_unique_object_config_graph(
                graphs=graphs,
                graph=graph,
                seen=seen,
                seen_fqn_prefixes=seen_fqn_prefixes,
            )
    return tuple(graphs)


def _leaf_external_object_config_graphs_from_context(
    *,
    context: Mapping[str, object],
    aware_toml_path: Path,
    workspace_root: Path,
) -> tuple[ObjectConfigGraph, ...]:
    source_fqn_prefix = _manifest_fqn_prefix(aware_toml_path=aware_toml_path)
    dependency_fqn_prefixes = _dependency_fqn_prefixes_for_manifest(
        aware_toml_path=aware_toml_path,
        workspace_root=workspace_root,
        context=context,
    )
    if not dependency_fqn_prefixes:
        return ()
    external_graphs = _external_object_config_graphs_from_context(context)
    if not external_graphs:
        return ()
    available_graphs_by_id: dict[UUID, ObjectConfigGraph] = {
        graph.id: graph for graph in external_graphs
    }
    available_graphs_by_fqn_prefix: dict[str, ObjectConfigGraph] = {}
    for graph in external_graphs:
        fqn_prefix = (graph.fqn_prefix or "").strip()
        if not fqn_prefix:
            continue
        available_graphs_by_fqn_prefix.setdefault(fqn_prefix, graph)
    graphs_by_fqn_prefix: dict[str, ObjectConfigGraph] = {}
    for fqn_prefix in dependency_fqn_prefixes:
        graph = available_graphs_by_fqn_prefix.get(fqn_prefix)
        if graph is None:
            continue
        graphs_by_fqn_prefix.setdefault(fqn_prefix, graph)
    dependency_fqn_prefixes = _dependency_fqn_prefixes_with_loaded_relationship_targets(
        dependency_fqn_prefixes=dependency_fqn_prefixes,
        source_fqn_prefix=source_fqn_prefix,
        graphs_by_fqn_prefix=graphs_by_fqn_prefix,
        available_graphs_by_id=available_graphs_by_id,
    )
    return tuple(
        graph
        for fqn_prefix in dependency_fqn_prefixes
        for graph in (graphs_by_fqn_prefix.get(fqn_prefix),)
        if graph is not None
    )


def _object_config_graphs_from_context_value(
    value: object,
) -> tuple[ObjectConfigGraph, ...]:
    if isinstance(value, ObjectConfigGraph):
        return (value,)
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(item for item in value if isinstance(item, ObjectConfigGraph))


def _external_runtime_object_config_graphs_from_context(
    *,
    context: Mapping[str, object],
    source_graph: ObjectConfigGraph,
) -> tuple[ObjectConfigGraph, ...]:
    return tuple(
        graph
        for graph in _object_config_graphs_for_kind_from_context(
            context=context,
            graph_kind="runtime",
        )
        if graph.id != source_graph.id
        and graph.fqn_prefix != source_graph.fqn_prefix
        and not _is_composite_runtime_context_graph(graph=graph)
    )


def _provider_delta_output_dependency_runtime_graphs(
    *,
    context: Mapping[str, object],
    source_graph: ObjectConfigGraph,
    manifest_path: Path | None,
    workspace_root: Path,
) -> tuple[ObjectConfigGraph, ...]:
    if manifest_path is None:
        return ()
    return _package_dependency_runtime_object_config_graphs_from_context(
        context=context,
        source_graph=source_graph,
        aware_toml_path=manifest_path,
        workspace_root=workspace_root,
        include_transitive_dependencies=False,
    )


def _is_composite_runtime_context_graph(
    *,
    graph: ObjectConfigGraph,
) -> bool:
    tokens = set(_object_config_graph_identity_tokens(graph=graph))
    return (
        "aware.runtime_context" in tokens
        or "Aware Workspace Meta Materialization Context" in tokens
        or "Aware Meta Graph Runtime Context" in tokens
    )


def _package_dependency_runtime_object_config_graphs_from_context(
    *,
    context: Mapping[str, object],
    source_graph: ObjectConfigGraph,
    aware_toml_path: Path,
    workspace_root: Path,
    include_transitive_dependencies: bool = True,
) -> tuple[ObjectConfigGraph, ...]:
    dependency_fqn_prefixes = _dependency_fqn_prefixes_for_manifest(
        aware_toml_path=aware_toml_path,
        workspace_root=workspace_root,
        context=context,
        include_transitive_dependencies=include_transitive_dependencies,
    )
    known_fqn_prefixes = _known_dependency_fqn_prefixes_from_catalog(context=context)
    if not include_transitive_dependencies:
        dependency_fqn_prefixes = _dependency_fqn_prefixes_with_source_references(
            dependency_fqn_prefixes=dependency_fqn_prefixes,
            source_graph=source_graph,
            known_fqn_prefixes=known_fqn_prefixes,
        )
    if not dependency_fqn_prefixes:
        return ()
    context_graphs = _external_runtime_object_config_graphs_from_context(
        context=context,
        source_graph=source_graph,
    )
    known_fqn_prefixes = _known_dependency_fqn_prefixes_from_context(
        context=context,
        context_graphs=context_graphs,
    )
    if not include_transitive_dependencies:
        dependency_fqn_prefixes = _dependency_fqn_prefixes_with_source_references(
            dependency_fqn_prefixes=dependency_fqn_prefixes,
            source_graph=source_graph,
            known_fqn_prefixes=known_fqn_prefixes,
        )
    if not dependency_fqn_prefixes:
        return ()
    graphs_by_fqn_prefix: dict[str, ObjectConfigGraph] = {}
    available_graphs_by_id: dict[UUID, ObjectConfigGraph] = {
        graph.id: graph for graph in context_graphs
    }
    manifest_graphs: tuple[ObjectConfigGraph, ...] | None = None

    def load_available_graphs_for_prefixes(
        prefixes: tuple[str, ...],
    ) -> None:
        nonlocal manifest_graphs
        dependency_fqn_prefix_set = set(prefixes)
        for graph in context_graphs:
            if graph.fqn_prefix not in dependency_fqn_prefix_set:
                continue
            if (
                graph.id == source_graph.id
                or graph.fqn_prefix == source_graph.fqn_prefix
            ):
                continue
            graphs_by_fqn_prefix.setdefault(graph.fqn_prefix, graph)
        if all(fqn_prefix in graphs_by_fqn_prefix for fqn_prefix in prefixes):
            return
        if manifest_graphs is None:
            manifest_graphs = (
                _package_dependency_runtime_object_config_graphs_from_manifest(
                    context=context,
                    source_graph=source_graph,
                    aware_toml_path=aware_toml_path,
                    workspace_root=workspace_root,
                )
            )
            available_graphs_by_id.update(
                {graph.id: graph for graph in manifest_graphs}
            )
        for graph in manifest_graphs:
            if graph.fqn_prefix not in dependency_fqn_prefix_set:
                continue
            if (
                graph.id == source_graph.id
                or graph.fqn_prefix == source_graph.fqn_prefix
            ):
                continue
            graphs_by_fqn_prefix.setdefault(graph.fqn_prefix, graph)

    load_available_graphs_for_prefixes(dependency_fqn_prefixes)
    if not include_transitive_dependencies:
        dependency_fqn_prefixes = (
            _dependency_fqn_prefixes_with_loaded_projection_references(
                dependency_fqn_prefixes=dependency_fqn_prefixes,
                source_graph=source_graph,
                graphs_by_fqn_prefix=graphs_by_fqn_prefix,
                known_fqn_prefixes=known_fqn_prefixes,
                load_available_graphs_for_prefixes=load_available_graphs_for_prefixes,
            )
        )
    dependency_fqn_prefixes = _dependency_fqn_prefixes_with_loaded_relationship_targets(
        dependency_fqn_prefixes=dependency_fqn_prefixes,
        source_fqn_prefix=(source_graph.fqn_prefix or "").strip() or None,
        graphs_by_fqn_prefix=graphs_by_fqn_prefix,
        available_graphs_by_id=available_graphs_by_id,
        load_available_graphs_for_prefixes=load_available_graphs_for_prefixes,
    )
    return tuple(
        graph
        for fqn_prefix in dependency_fqn_prefixes
        for graph in (graphs_by_fqn_prefix.get(fqn_prefix),)
        if graph is not None
    )


def _package_dependency_runtime_object_config_graphs_from_manifest(
    *,
    context: Mapping[str, object],
    source_graph: ObjectConfigGraph,
    aware_toml_path: Path,
    workspace_root: Path,
) -> tuple[ObjectConfigGraph, ...]:
    from aware_meta.manifest.loader import load_aware_toml_spec  # noqa: WPS433
    from aware_meta.runtime.graph_context import (  # noqa: WPS433
        build_meta_graph_runtime_context_for_aware_package_manifests,
        resolve_meta_runtime_package_manifest_closure_for_package_names,
    )

    spec = load_aware_toml_spec(toml_path=aware_toml_path)
    package_manifest_paths = (
        resolve_meta_runtime_package_manifest_closure_for_package_names(
            repo_root=workspace_root,
            package_names=(spec.package.package_name,),
            semantic_ontology_package_catalog=(
                _semantic_ontology_package_catalog_from_context(context)
            ),
        )
    )
    if not package_manifest_paths:
        return ()
    dependency_context = build_meta_graph_runtime_context_for_aware_package_manifests(
        package_manifest_paths=package_manifest_paths,
        workspace_root=workspace_root,
        composite_name=(
            "Aware Meta Language Materialization Dependency Context: "
            f"{spec.package.package_name}"
        ),
    )
    return tuple(
        graph
        for graph in dependency_context.runtime_graphs
        if graph.id != source_graph.id and graph.fqn_prefix != source_graph.fqn_prefix
    )


def _semantic_ontology_package_catalog_from_context(
    context: Mapping[str, object],
) -> Mapping[str, object] | None:
    raw_catalog = context.get(SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_CONTEXT_KEY)
    if not isinstance(raw_catalog, Mapping):
        return None
    if raw_catalog.get("schema") != SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_SCHEMA:
        return None
    return raw_catalog


def _dependency_fqn_prefixes_for_manifest(
    *,
    aware_toml_path: Path,
    workspace_root: Path,
    context: Mapping[str, object] | None = None,
    include_transitive_dependencies: bool = True,
) -> tuple[str, ...]:
    if include_transitive_dependencies and context is not None:
        catalog_prefixes = _semantic_catalog_dependency_fqn_prefix_closure_for_manifest(
            context=context,
            aware_toml_path=aware_toml_path,
            workspace_root=workspace_root,
        )
        if catalog_prefixes is not None:
            return catalog_prefixes
    return _direct_dependency_fqn_prefixes_for_manifest(
        aware_toml_path=aware_toml_path,
        workspace_root=workspace_root,
        context=context,
    )


def _dependency_fqn_prefixes_with_source_references(
    *,
    dependency_fqn_prefixes: tuple[str, ...],
    source_graph: ObjectConfigGraph,
    known_fqn_prefixes: Iterable[str] = (),
) -> tuple[str, ...]:
    prefixes: list[str] = []
    seen: set[str] = set()
    source_fqn_prefix = (source_graph.fqn_prefix or "").strip()
    for prefix in (
        *dependency_fqn_prefixes,
        *_projection_binding_dependency_fqn_prefixes(
            source_graph,
            known_fqn_prefixes=known_fqn_prefixes,
        ),
    ):
        normalized = prefix.strip()
        if not normalized or normalized == source_fqn_prefix or normalized in seen:
            continue
        seen.add(normalized)
        prefixes.append(normalized)
    return tuple(prefixes)


def _dependency_fqn_prefixes_with_loaded_projection_references(
    *,
    dependency_fqn_prefixes: tuple[str, ...],
    source_graph: ObjectConfigGraph,
    graphs_by_fqn_prefix: Mapping[str, ObjectConfigGraph],
    known_fqn_prefixes: Iterable[str],
    load_available_graphs_for_prefixes: Callable[[tuple[str, ...]], None],
) -> tuple[str, ...]:
    prefixes = list(dependency_fqn_prefixes)
    seen = set(prefixes)
    source_fqn_prefix = (source_graph.fqn_prefix or "").strip()
    while True:
        added = False
        for graph in (source_graph, *tuple(graphs_by_fqn_prefix.values())):
            for prefix in _projection_binding_dependency_fqn_prefixes(
                graph,
                known_fqn_prefixes=known_fqn_prefixes,
            ):
                normalized = prefix.strip()
                if (
                    not normalized
                    or normalized == source_fqn_prefix
                    or normalized in seen
                ):
                    continue
                seen.add(normalized)
                prefixes.append(normalized)
                added = True
        if not added:
            return tuple(prefixes)
        load_available_graphs_for_prefixes(tuple(prefixes))


def _dependency_fqn_prefixes_with_loaded_relationship_targets(
    *,
    dependency_fqn_prefixes: tuple[str, ...],
    source_fqn_prefix: str | None,
    graphs_by_fqn_prefix: dict[str, ObjectConfigGraph],
    available_graphs_by_id: dict[UUID, ObjectConfigGraph],
    load_available_graphs_for_prefixes: Callable[[tuple[str, ...]], None] | None = None,
) -> tuple[str, ...]:
    prefixes = list(dependency_fqn_prefixes)
    seen = set(prefixes)
    normalized_source_fqn_prefix = (source_fqn_prefix or "").strip()
    while True:
        added = False
        for graph in tuple(graphs_by_fqn_prefix.values()):
            for relationship in graph.object_config_graph_relationships:
                target_graph = getattr(
                    relationship,
                    "target_object_config_graph",
                    None,
                )
                if not isinstance(target_graph, ObjectConfigGraph):
                    target_graph_id = getattr(
                        relationship,
                        "target_object_config_graph_id",
                        None,
                    )
                    target_graph = available_graphs_by_id.get(target_graph_id)
                if not isinstance(target_graph, ObjectConfigGraph):
                    continue
                target_fqn_prefix = (target_graph.fqn_prefix or "").strip()
                if (
                    not target_fqn_prefix
                    or target_fqn_prefix == normalized_source_fqn_prefix
                    or target_fqn_prefix in seen
                ):
                    continue
                seen.add(target_fqn_prefix)
                prefixes.append(target_fqn_prefix)
                graphs_by_fqn_prefix.setdefault(target_fqn_prefix, target_graph)
                available_graphs_by_id.setdefault(target_graph.id, target_graph)
                added = True
        if not added:
            return tuple(prefixes)
        if load_available_graphs_for_prefixes is not None:
            load_available_graphs_for_prefixes(tuple(prefixes))


def _projection_binding_dependency_fqn_prefixes(
    source_graph: ObjectConfigGraph,
    *,
    known_fqn_prefixes: Iterable[str],
) -> tuple[str, ...]:
    prefixes: list[str] = []
    seen: set[str] = set()
    for prefix in (
        *_source_projection_binding_fqn_prefixes(source_graph),
        *_qualified_projection_target_fqn_prefixes(
            source_graph,
            known_fqn_prefixes=known_fqn_prefixes,
        ),
    ):
        normalized = prefix.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        prefixes.append(normalized)
    return tuple(prefixes)


def _source_projection_binding_fqn_prefixes(
    source_graph: ObjectConfigGraph,
) -> tuple[str, ...]:
    prefixes: list[str] = []
    seen: set[str] = set()
    for declaration in source_graph.object_projection_graph_declarations:
        for binding in getattr(declaration, "object_projection_graph_bindings", ()):
            prefix = str(getattr(binding, "fqn_prefix", "") or "").strip()
            if not prefix or prefix in seen:
                continue
            seen.add(prefix)
            prefixes.append(prefix)
    return tuple(prefixes)


def _qualified_projection_target_fqn_prefixes(
    source_graph: ObjectConfigGraph,
    *,
    known_fqn_prefixes: Iterable[str],
) -> tuple[str, ...]:
    known = {prefix.strip() for prefix in known_fqn_prefixes if prefix.strip()}
    prefixes: list[str] = []
    seen: set[str] = set()
    for declaration in source_graph.object_projection_graph_declarations:
        for binding in getattr(declaration, "object_projection_graph_bindings", ()):
            raw_target = str(
                getattr(binding, "target_projection_name", "") or ""
            ).strip()
            parts = [part.strip() for part in raw_target.split(".") if part.strip()]
            if len(parts) != 2:
                continue
            owner = parts[0]
            if owner not in known or owner in seen:
                continue
            seen.add(owner)
            prefixes.append(owner)
    return tuple(prefixes)


def _known_dependency_fqn_prefixes_from_context(
    *,
    context: Mapping[str, object],
    context_graphs: Iterable[ObjectConfigGraph],
) -> frozenset[str]:
    prefixes = {
        graph.fqn_prefix.strip()
        for graph in context_graphs
        if (graph.fqn_prefix or "").strip()
    }
    prefixes.update(_known_dependency_fqn_prefixes_from_catalog(context=context))
    return frozenset(prefixes)


def _known_dependency_fqn_prefixes_from_catalog(
    *,
    context: Mapping[str, object],
) -> frozenset[str]:
    prefixes: set[str] = set()
    catalog = _semantic_ontology_package_catalog_from_context(context)
    if catalog is not None:
        raw_entries = catalog.get("entries")
        if isinstance(raw_entries, (list, tuple)):
            for raw_entry in raw_entries:
                if not isinstance(raw_entry, Mapping):
                    continue
                fqn_prefix = str(raw_entry.get("fqn_prefix") or "").strip()
                if fqn_prefix:
                    prefixes.add(fqn_prefix)
    return frozenset(prefixes)


def _semantic_catalog_dependency_fqn_prefix_closure_for_manifest(
    *,
    context: Mapping[str, object],
    aware_toml_path: Path,
    workspace_root: Path,
) -> tuple[str, ...] | None:
    raw_catalog = context.get(SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_CONTEXT_KEY)
    if raw_catalog is None:
        return None
    if not isinstance(raw_catalog, Mapping):
        return None
    if raw_catalog.get("schema") != SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_SCHEMA:
        return None
    raw_entries = raw_catalog.get("entries")
    if not isinstance(raw_entries, (list, tuple)):
        return None

    entries_by_package_name: dict[str, Mapping[str, object]] = {}
    package_name_by_manifest_path: dict[Path, str] = {}
    package_name_by_fqn_prefix: dict[str, str] = {}
    for raw_entry in raw_entries:
        if not isinstance(raw_entry, Mapping):
            continue
        package_name = _non_empty_text(raw_entry.get("package_name"))
        fqn_prefix = _non_empty_text(raw_entry.get("fqn_prefix"))
        if package_name is None or fqn_prefix is None:
            continue
        entries_by_package_name[package_name] = raw_entry
        package_name_by_fqn_prefix.setdefault(fqn_prefix, package_name)
        manifest_path = _catalog_manifest_path(
            raw_entry=raw_entry,
            workspace_root=workspace_root,
        )
        if manifest_path is not None:
            package_name_by_manifest_path.setdefault(manifest_path, package_name)

    if not entries_by_package_name:
        return None

    source_package_name = package_name_by_manifest_path.get(
        aware_toml_path.expanduser().resolve()
    )
    if source_package_name is None:
        source_fqn_prefix = _manifest_fqn_prefix(
            aware_toml_path=aware_toml_path,
        )
        if source_fqn_prefix is not None:
            source_package_name = package_name_by_fqn_prefix.get(source_fqn_prefix)
    if source_package_name is None:
        return None
    if source_package_name not in entries_by_package_name:
        return None

    ordered_package_names: list[str] = []
    visited: set[str] = set()
    visiting: set[str] = set()

    def visit(package_name: str) -> None:
        if package_name in visited:
            return
        if package_name in visiting:
            raise ValueError(
                "Cyclic semantic package dependency in Workspace catalog: "
                + " -> ".join((*visiting, package_name))
            )
        entry = entries_by_package_name.get(package_name)
        if entry is None:
            raise ValueError(
                "Missing semantic package dependency in Workspace catalog: "
                f"{package_name!r}"
            )
        visiting.add(package_name)
        for dependency_package_name in _string_tuple(
            entry.get("dependency_package_names")
        ):
            visit(dependency_package_name)
        visiting.remove(package_name)
        visited.add(package_name)
        if package_name != source_package_name:
            ordered_package_names.append(package_name)

    visit(source_package_name)

    fqn_prefixes: list[str] = []
    seen: set[str] = set()
    for package_name in ordered_package_names:
        entry = entries_by_package_name[package_name]
        fqn_prefix = _non_empty_text(entry.get("fqn_prefix"))
        if fqn_prefix is None or fqn_prefix in seen:
            continue
        seen.add(fqn_prefix)
        fqn_prefixes.append(fqn_prefix)
    return tuple(fqn_prefixes)


def _catalog_manifest_path(
    *,
    raw_entry: Mapping[str, object],
    workspace_root: Path,
) -> Path | None:
    manifest_path_text = _non_empty_text(raw_entry.get("manifest_path"))
    if manifest_path_text is None:
        return None
    manifest_path = Path(manifest_path_text).expanduser()
    if not manifest_path.is_absolute():
        manifest_path = workspace_root / manifest_path
    return manifest_path.resolve()


def _manifest_fqn_prefix(*, aware_toml_path: Path) -> str | None:
    from aware_meta.manifest.loader import load_aware_toml_spec  # noqa: WPS433

    if not aware_toml_path.exists():
        return None
    spec = load_aware_toml_spec(toml_path=aware_toml_path)
    return _non_empty_text(spec.package.fqn_prefix)


def _string_tuple(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        text = value.strip()
        return (text,) if text else ()
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(
        text for item in value for text in (_non_empty_text(item),) if text is not None
    )


def _non_empty_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _direct_dependency_fqn_prefixes_for_manifest(
    *,
    aware_toml_path: Path,
    workspace_root: Path,
    context: Mapping[str, object] | None = None,
) -> tuple[str, ...]:
    from aware_meta.manifest.loader import load_aware_toml_spec  # noqa: WPS433

    spec = load_aware_toml_spec(toml_path=aware_toml_path)
    dependency_package_names = tuple(
        str(dependency.package_name).strip()
        for dependency in spec.dependencies
        if str(dependency.package_name).strip()
    )
    if not dependency_package_names:
        return ()
    fqn_prefix_by_package_name: dict[str, str] = {}
    if context is not None:
        fqn_prefix_by_package_name.update(
            _semantic_runtime_package_catalog_fqn_prefix_by_package_name(
                context=context,
            )
        )
    fallback_fqn_prefix_by_package_name = _ontology_package_fqn_prefix_catalog(
        workspace_root=workspace_root,
    )
    prefixes: list[str] = []
    seen: set[str] = set()
    for package_name in dependency_package_names:
        fqn_prefix = (
            fqn_prefix_by_package_name.get(package_name)
            or fallback_fqn_prefix_by_package_name.get(package_name)
            or ""
        ).strip()
        if not fqn_prefix or fqn_prefix in seen:
            continue
        seen.add(fqn_prefix)
        prefixes.append(fqn_prefix)
    return tuple(prefixes)


def _semantic_runtime_package_catalog_fqn_prefix_by_package_name(
    *,
    context: Mapping[str, object],
) -> dict[str, str]:
    raw_catalog = context.get(SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_CONTEXT_KEY)
    if not isinstance(raw_catalog, Mapping):
        return {}
    raw_entries = raw_catalog.get("entries")
    if not isinstance(raw_entries, (list, tuple)):
        return {}
    fqn_prefix_by_package_name: dict[str, str] = {}
    for raw_entry in raw_entries:
        if not isinstance(raw_entry, Mapping):
            continue
        package_name = str(raw_entry.get("package_name") or "").strip()
        fqn_prefix = str(raw_entry.get("fqn_prefix") or "").strip()
        if package_name and fqn_prefix:
            fqn_prefix_by_package_name.setdefault(package_name, fqn_prefix)
    return fqn_prefix_by_package_name


def _ontology_package_fqn_prefix_catalog(
    *,
    workspace_root: Path,
) -> Mapping[str, str]:
    from aware_grammar.module.loader import load_aware_module_spec  # noqa: WPS433
    from aware_meta.manifest.loader import load_aware_toml_spec  # noqa: WPS433
    from aware_ontology.manifest.loader import (  # noqa: WPS433
        load_aware_ontology_toml_spec,
    )

    modules_root = (workspace_root / "modules").resolve()
    if not modules_root.is_dir():
        return {}
    fqn_prefix_by_package_name: dict[str, str] = {}
    for module_root in sorted(path for path in modules_root.iterdir() if path.is_dir()):
        module_toml = module_root / "aware.module.toml"
        if not module_toml.is_file():
            continue
        module_spec = load_aware_module_spec(toml_path=module_toml)
        for package in module_spec.packages:
            package_kind = str(getattr(package.kind, "value", package.kind)).strip()
            if package_kind != "ontology":
                continue
            manifest_path = (module_root / package.manifest).resolve()
            if manifest_path.name == "aware.ontology.toml":
                ontology_spec = load_aware_ontology_toml_spec(toml_path=manifest_path)
                manifest_path = (
                    manifest_path.parent / ontology_spec.ontology.source_manifest
                ).resolve()
            aware_spec = load_aware_toml_spec(toml_path=manifest_path)
            package_name = str(aware_spec.package.package_name).strip()
            fqn_prefix = str(aware_spec.package.fqn_prefix).strip()
            if package_name and fqn_prefix:
                fqn_prefix_by_package_name.setdefault(package_name, fqn_prefix)
    return fqn_prefix_by_package_name


def _leaf_materialization_execution_detail(
    *,
    leaf_result: ObjectConfigGraphPackageLeafMaterializationResult,
) -> dict[str, object]:
    return {
        "enabled": True,
        "continue_on_failure": False,
        "status": "full_rebuild",
        "reason": (
            "Meta ObjectConfigGraph package leaf materialization committed "
            "CodePackage, ObjectConfigGraph, and ObjectConfigGraphPackage truth."
        ),
        "step_count": 0,
        "status_counts": {"full_rebuild": 1},
        "package_branch_id": str(leaf_result.package_branch_id),
    }


async def _leaf_materialization_details(
    *,
    request: SemanticPackageMaterializationRequest,
    leaf_result: ObjectConfigGraphPackageLeafMaterializationResult | None,
    language_materialization_receipts: _LanguageMaterializationReceipts,
    materialized_language_packages: tuple[dict[str, object], ...] | None = None,
) -> dict[str, object]:
    if leaf_result is None:
        return {}
    lifecycle_receipts = _leaf_lifecycle_receipts(
        request=request,
        leaf_result=leaf_result,
    )
    materialization_index_receipts = (
        (dict(leaf_result.materialization_index_receipt),)
        if leaf_result.materialization_index_receipt is not None
        else ()
    )
    artifact_ownership_receipts = (
        tuple(receipt.ownership_receipt for receipt in lifecycle_receipts)
        + language_materialization_receipts.artifact_ownership_receipts
    )
    if materialized_language_packages is None:
        materialized_language_packages = (
            _materialized_language_packages_from_leaf_result(
                leaf_result=leaf_result,
                generated_code_package_refs=(
                    language_materialization_receipts.generated_code_package_refs
                ),
            )
        )
    compile_parity_receipts = _leaf_compile_parity_receipts(
        request=request,
        leaf_result=leaf_result,
        lifecycle_receipts=tuple(receipt.payload for receipt in lifecycle_receipts),
        materialization_index_receipts=materialization_index_receipts,
        artifact_ownership_receipts=artifact_ownership_receipts,
        post_step_receipts=language_materialization_receipts.post_step_receipts,
        materialized_language_packages=materialized_language_packages,
    )
    return {
        "aware_toml_path": leaf_result.aware_toml_path.as_posix(),
        "package_branch_id": str(leaf_result.package_branch_id),
        "package_name": leaf_result.object_config_graph_package.package_name,
        "fqn_prefix": leaf_result.object_config_graph_package.fqn_prefix,
        "source_code_package_id": str(leaf_result.code_package.id),
        "code_package_commit_id": (
            str(leaf_result.code_package_commit_id)
            if leaf_result.code_package_commit_id is not None
            else None
        ),
        "code_package_head_commit_id": (
            str(leaf_result.code_package_head_commit_id)
            if leaf_result.code_package_head_commit_id is not None
            else None
        ),
        "code_package_object_instance_graph_commit_id": (
            str(leaf_result.code_package_object_instance_graph_commit_id)
            if leaf_result.code_package_object_instance_graph_commit_id is not None
            else None
        ),
        "object_config_graph_id": str(leaf_result.object_config_graph.id),
        "object_config_graph_commit_id": (
            str(leaf_result.object_config_graph_commit_id)
            if leaf_result.object_config_graph_commit_id is not None
            else None
        ),
        "object_config_graph_head_commit_id": (
            str(leaf_result.object_config_graph_head_commit_id)
            if leaf_result.object_config_graph_head_commit_id is not None
            else None
        ),
        "object_config_graph_object_instance_graph_commit_id": (
            str(leaf_result.object_config_graph_object_instance_graph_commit_id)
            if leaf_result.object_config_graph_object_instance_graph_commit_id
            is not None
            else None
        ),
        "object_config_graph_package_id": str(
            leaf_result.object_config_graph_package.id
        ),
        "object_config_graph_package_commit_id": (
            str(leaf_result.object_config_graph_package_commit_id)
            if leaf_result.object_config_graph_package_commit_id is not None
            else None
        ),
        "object_config_graph_package_head_commit_id": (
            str(leaf_result.object_config_graph_package_head_commit_id)
            if leaf_result.object_config_graph_package_head_commit_id is not None
            else None
        ),
        "object_config_graph_package_object_instance_graph_commit_id": (
            str(leaf_result.object_config_graph_package_object_instance_graph_commit_id)
            if leaf_result.object_config_graph_package_object_instance_graph_commit_id
            is not None
            else None
        ),
        "owned_file_paths": leaf_result.owned_file_paths,
        "meta_phase_timings_s": dict(leaf_result.phase_timings_s),
        "semantic_commit_strategy": leaf_result.semantic_commit_strategy,
        "semantic_commit_fallback_reset": leaf_result.semantic_commit_fallback_reset,
        "semantic_commit_phase_timings_s": dict(
            leaf_result.semantic_commit_phase_timings_s
        ),
        "lifecycle_receipts": tuple(receipt.payload for receipt in lifecycle_receipts),
        "materialization_index_receipts": materialization_index_receipts,
        "artifact_ownership_receipts": artifact_ownership_receipts,
        "language_post_step_receipts": (
            language_materialization_receipts.post_step_receipts
        ),
        "language_materialization_tool_step_receipts": (
            language_materialization_receipts.tool_step_receipts
        ),
        "language_materialization_code_package_refs": (
            language_materialization_receipts.generated_code_package_refs
        ),
        "generated_code_package_deltas": (
            language_materialization_receipts.generated_code_package_deltas
        ),
        "language_materialization_code_package_deltas": (
            language_materialization_receipts.generated_code_package_deltas
        ),
        "materialized_language_packages": materialized_language_packages,
        "materialized_language_package_count": len(materialized_language_packages),
        "language_materialization_tool_timings_s": dict(
            language_materialization_receipts.tool_timings_s
        ),
        "language_materialization_runtime_to_language_cache": dict(
            language_materialization_receipts.runtime_to_language_cache
        ),
        "language_materialization_runtime_derivation_cache": dict(
            language_materialization_receipts.runtime_derivation_cache
        ),
        "compile_parity_receipts": compile_parity_receipts,
    }


def _materialized_language_packages_from_leaf_result(
    *,
    leaf_result: ObjectConfigGraphPackageLeafMaterializationResult,
    generated_code_package_refs: Iterable[Mapping[str, object]],
) -> tuple[dict[str, object], ...]:
    refs_by_code_package_id = _generated_code_package_refs_by_code_package_id(
        generated_code_package_refs
    )
    object_config_graph_package = leaf_result.object_config_graph_package
    object_config_graph_package_id = _object_value_text(
        object_config_graph_package,
        "id",
    )
    root_oig_commit_id = _uuidish_text(
        leaf_result.object_config_graph_object_instance_graph_commit_id
    )
    rows: list[dict[str, object]] = []
    for language_materialization in tuple(
        getattr(object_config_graph_package, "language_materializations", ()) or ()
    ):
        language_materialization_id = _object_value_text(
            language_materialization,
            "id",
        )
        language_materialization_target_key = _object_value_text(
            language_materialization,
            "target_key",
        )
        materialized_packages = tuple(
            getattr(language_materialization, "materialized_packages", ()) or ()
        )
        for materialized_package in materialized_packages:
            code_package_id = _object_value_text(
                materialized_package,
                "code_package_id",
            )
            ref = refs_by_code_package_id.get(code_package_id or "", {})
            package_name = (
                _object_value_text(materialized_package, "package_name")
                or _optional_string_value(ref.get("package_name"))
                or _object_value_text(language_materialization, "package_name")
            )
            language = (
                _object_value_text(materialized_package, "language")
                or _object_value_text(language_materialization, "language")
                or _optional_string_value(ref.get("target_language_plugin_id"))
            )
            if code_package_id is None and package_name is None:
                continue
            rows.append(
                {
                    "schema": _MATERIALIZED_LANGUAGE_PACKAGE_SCHEMA,
                    "object_config_graph_package_id": object_config_graph_package_id,
                    "language_materialization_id": language_materialization_id,
                    "language_materialization_target_key": (
                        language_materialization_target_key
                    ),
                    "code_package_id": code_package_id,
                    "code_package_branch_id": _optional_string_value(
                        ref.get("code_package_branch_id")
                    ),
                    "code_package_commit_id": _optional_string_value(
                        ref.get("code_package_commit_id")
                    ),
                    "code_package_head_commit_id": _optional_string_value(
                        ref.get("code_package_head_commit_id")
                    ),
                    "code_package_object_instance_graph_commit_id": (
                        _object_value_text(
                            materialized_package,
                            "code_package_object_instance_graph_commit_id",
                        )
                        or _optional_string_value(
                            ref.get(
                                "code_package_object_instance_graph_commit_id",
                            )
                        )
                    ),
                    "object_config_graph_object_instance_graph_commit_id": (
                        _object_value_text(
                            materialized_package,
                            "object_config_graph_object_instance_graph_commit_id",
                        )
                        or _optional_string_value(
                            ref.get(
                                "object_config_graph_object_instance_graph_commit_id",
                            )
                        )
                        or root_oig_commit_id
                    ),
                    "package_output_key": _object_value_text(
                        materialized_package,
                        "package_output_key",
                    ),
                    "package_name": package_name,
                    "language": language,
                    "output_dir": (
                        _object_value_text(materialized_package, "output_dir")
                        or _object_value_text(language_materialization, "output_dir")
                    ),
                    "package_root": (
                        _object_value_text(materialized_package, "package_root")
                        or _optional_string_value(ref.get("package_root"))
                    ),
                    "sources_root": (
                        _object_value_text(materialized_package, "sources_root")
                        or _optional_string_value(ref.get("sources_root"))
                    ),
                    "import_root": (
                        _object_value_text(materialized_package, "import_root")
                        or _optional_string_value(ref.get("import_root"))
                        or _object_value_text(language_materialization, "import_root")
                    ),
                    "materialization_source": (
                        _object_value_text(
                            materialized_package,
                            "materialization_source",
                        )
                        or _optional_string_value(ref.get("materialization_source"))
                        or _object_value_text(
                            language_materialization,
                            "materialization_source",
                        )
                    ),
                    "renderer_kind": (
                        _object_value_text(materialized_package, "renderer_kind")
                        or _optional_string_value(ref.get("renderer_kind"))
                        or _object_value_text(language_materialization, "renderer_kind")
                    ),
                    "renderer_profile": (
                        _object_value_text(materialized_package, "renderer_profile")
                        or _optional_string_value(ref.get("renderer_profile"))
                        or _object_value_text(
                            language_materialization,
                            "renderer_profile",
                        )
                    ),
                    "status": (
                        _object_value_text(materialized_package, "status")
                        or _optional_string_value(ref.get("status"))
                        or "declared"
                    ),
                }
            )
    return tuple(
        sorted(
            rows,
            key=lambda item: (
                str(item.get("package_name") or ""),
                str(item.get("language") or ""),
                str(item.get("code_package_id") or ""),
            ),
        )
    )


def _generated_code_package_refs_by_code_package_id(
    generated_code_package_refs: Iterable[Mapping[str, object]],
) -> dict[str, Mapping[str, object]]:
    refs: dict[str, Mapping[str, object]] = {}
    for ref in generated_code_package_refs:
        code_package_id = _optional_string_value(ref.get("code_package_id"))
        if code_package_id is None:
            continue
        refs[code_package_id] = ref
    return refs


def _leaf_compile_parity_receipts(
    *,
    request: SemanticPackageMaterializationRequest,
    leaf_result: ObjectConfigGraphPackageLeafMaterializationResult,
    lifecycle_receipts: tuple[Mapping[str, object], ...],
    materialization_index_receipts: tuple[Mapping[str, object], ...],
    artifact_ownership_receipts: tuple[Mapping[str, object], ...],
    post_step_receipts: tuple[Mapping[str, object], ...] = (),
    materialized_language_packages: tuple[Mapping[str, object], ...] = (),
) -> tuple[dict[str, object], ...]:
    targets = _leaf_language_materialization_targets(
        request=request,
        leaf_result=leaf_result,
    )
    required_artifact_roles = _compile_parity_required_artifact_roles(
        targets=targets,
    )
    available_artifact_roles = _compile_parity_available_artifact_roles(
        materialization_index_receipts=materialization_index_receipts,
        artifact_ownership_receipts=artifact_ownership_receipts,
    )
    package_oig_commit_id = (
        leaf_result.object_config_graph_package_object_instance_graph_commit_id
    )
    missing_required_artifact_roles = tuple(
        role for role in required_artifact_roles if role not in available_artifact_roles
    )
    required_post_step_tools = _compile_parity_required_post_step_tools(
        targets=targets,
    )
    available_post_step_tools = _compile_parity_available_post_step_tools(
        post_step_receipts=post_step_receipts,
    )
    missing_required_post_step_tools = tuple(
        item
        for item in required_post_step_tools
        if _compile_parity_post_step_tool_key(item) not in available_post_step_tools
    )
    payload: dict[str, object] = {
        "schema": _COMPILE_PARITY_RECEIPT_SCHEMA,
        "provider_key": "aware_meta",
        "semantic_owner": META_OBJECT_CONFIG_GRAPH_OWNER,
        "producer_key": META_LANGUAGE_MATERIALIZATION_PRODUCER_KEY,
        "receipt_kind": _COMPILE_PARITY_RECEIPT_KIND,
        "status": (
            "compile_equivalent"
            if (
                not missing_required_artifact_roles
                and not missing_required_post_step_tools
            )
            else "incomplete"
        ),
        "env_artifacts_required": False,
        "replacement_target": "aware-cli compile module/package",
        "workspace_command": "workspace materialize",
        "package_name": leaf_result.object_config_graph_package.package_name,
        "fqn_prefix": leaf_result.object_config_graph_package.fqn_prefix,
        "aware_toml_path": leaf_result.aware_toml_path.as_posix(),
        "source_code_package_id": str(leaf_result.code_package.id),
        "source_object_instance_graph_commit_id": _uuid_text(
            leaf_result.code_package_object_instance_graph_commit_id
        ),
        "object_config_graph_id": str(leaf_result.object_config_graph.id),
        "object_config_graph_object_instance_graph_commit_id": _uuid_text(
            leaf_result.object_config_graph_object_instance_graph_commit_id
        ),
        "object_config_graph_package_id": str(
            leaf_result.object_config_graph_package.id
        ),
        "object_config_graph_package_object_instance_graph_commit_id": (
            _uuid_text(package_oig_commit_id)
        ),
        "object_config_graph_package_head_commit_id": _uuid_text(
            leaf_result.object_config_graph_package_head_commit_id
        ),
        "semantic_commit_strategy": leaf_result.semantic_commit_strategy,
        "language_materialization_target_count": len(targets),
        "language_materialization_targets": tuple(
            _compile_parity_target_payload(target=target) for target in targets
        ),
        "materialized_language_package_count": len(materialized_language_packages),
        "materialized_language_packages": materialized_language_packages,
        "required_artifact_roles": required_artifact_roles,
        "available_artifact_roles": tuple(sorted(available_artifact_roles)),
        "missing_required_artifact_roles": missing_required_artifact_roles,
        "required_post_step_tools": required_post_step_tools,
        "available_post_step_tools": tuple(sorted(available_post_step_tools)),
        "missing_required_post_step_tools": missing_required_post_step_tools,
        "post_step_receipt_count": len(post_step_receipts),
        "available_output_keys": _compile_parity_available_output_keys(
            artifact_ownership_receipts=artifact_ownership_receipts,
        ),
        "available_package_names": _compile_parity_available_package_names(
            artifact_ownership_receipts=artifact_ownership_receipts,
        ),
        "artifact_role_counts": _compile_parity_artifact_role_counts(
            materialization_index_receipts=materialization_index_receipts,
            artifact_ownership_receipts=artifact_ownership_receipts,
        ),
        "artifact_ownership_receipt_count": len(artifact_ownership_receipts),
        "lifecycle_receipt_count": len(lifecycle_receipts),
        "materialization_index_receipt_count": len(materialization_index_receipts),
        "materialization_index_receipt_kinds": tuple(
            sorted(
                {
                    receipt_kind
                    for receipt in materialization_index_receipts
                    if (
                        receipt_kind := _optional_string_value(
                            receipt.get("receipt_kind")
                        )
                    )
                    is not None
                }
            )
        ),
        "canonical_output_keys": (
            META_LANGUAGE_MATERIALIZATION_GENERATED_FILES_OUTPUT_KEY,
            META_LANGUAGE_MATERIALIZATION_PACKAGE_OUTPUT_KEY,
            META_LANGUAGE_MATERIALIZATION_LIFECYCLE_RECEIPT_OUTPUT_KEY,
        ),
    }
    digest = _compile_parity_digest(payload)
    payload["digest_algorithm"] = "sha256"
    payload["digest"] = digest
    payload["receipt_id"] = f"sha256:{digest}"
    return (payload,)


def _compile_parity_required_artifact_roles(
    *,
    targets: tuple[_LanguageMaterializationTarget, ...],
) -> tuple[str, ...]:
    roles: set[str] = set(_COMPILE_PARITY_BASE_REQUIRED_ARTIFACT_ROLES)
    if targets:
        roles.update(_COMPILE_PARITY_LANGUAGE_TARGET_REQUIRED_ARTIFACT_ROLES)
    for target in targets:
        roles.update(
            _COMPILE_PARITY_REQUIRED_ARTIFACT_ROLES_BY_SOURCE.get(
                target.materialization_source,
                (),
            )
        )
    return tuple(sorted(roles))


def _compile_parity_required_post_step_tools(
    *,
    targets: tuple[_LanguageMaterializationTarget, ...],
) -> tuple[dict[str, object], ...]:
    required: list[dict[str, object]] = []
    for target in targets:
        plan = plan_language_materialization_post_steps(
            LanguageMaterializationPostStepPlanRequest(
                target_language_plugin_id=target.target_language_plugin_id,
                has_packages=True,
            )
        )
        for step in plan.steps:
            required.append(
                {
                    "target_language_plugin_id": (
                        target.target_language_plugin_id.value
                    ),
                    "materialization_source": target.materialization_source,
                    "output_root": target.output_root.resolve().as_posix(),
                    "package_name": target.package_name,
                    "tool_id": step.tool_id,
                    "source": step.source,
                }
            )
    return tuple(required)


def _compile_parity_available_post_step_tools(
    *,
    post_step_receipts: tuple[Mapping[str, object], ...],
) -> frozenset[str]:
    return frozenset(
        _compile_parity_post_step_tool_key(receipt)
        for receipt in post_step_receipts
        if _optional_string_value(receipt.get("status")) == "succeeded"
    )


def _compile_parity_post_step_tool_key(item: Mapping[str, object]) -> str:
    return "|".join(
        (
            _optional_string_value(item.get("target_language_plugin_id")) or "",
            _optional_string_value(item.get("materialization_source")) or "",
            _optional_string_value(item.get("output_root")) or "",
            _optional_string_value(item.get("tool_id")) or "",
        )
    )


def _compile_parity_available_artifact_roles(
    *,
    materialization_index_receipts: tuple[Mapping[str, object], ...],
    artifact_ownership_receipts: tuple[Mapping[str, object], ...],
) -> frozenset[str]:
    roles = {
        "materialization_index_receipt"
        for receipt in materialization_index_receipts
        if _optional_string_value(receipt.get("receipt_kind")) is not None
    }
    roles.update(
        role
        for receipt in artifact_ownership_receipts
        if _compile_parity_receipt_is_available(receipt)
        if (role := _optional_string_value(receipt.get("artifact_role"))) is not None
    )
    return frozenset(roles)


def _compile_parity_receipt_is_available(
    receipt: Mapping[str, object],
) -> bool:
    status = _optional_string_value(receipt.get("status"))
    return status in _COMPILE_PARITY_AVAILABLE_STATUSES


def _compile_parity_available_output_keys(
    *,
    artifact_ownership_receipts: tuple[Mapping[str, object], ...],
) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                output_key
                for receipt in artifact_ownership_receipts
                if _compile_parity_receipt_is_available(receipt)
                if (output_key := _optional_string_value(receipt.get("output_key")))
                is not None
            }
        )
    )


def _compile_parity_available_package_names(
    *,
    artifact_ownership_receipts: tuple[Mapping[str, object], ...],
) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                package_name
                for receipt in artifact_ownership_receipts
                if _compile_parity_receipt_is_available(receipt)
                if (package_name := _optional_string_value(receipt.get("package_name")))
                is not None
            }
        )
    )


def _compile_parity_artifact_role_counts(
    *,
    materialization_index_receipts: tuple[Mapping[str, object], ...],
    artifact_ownership_receipts: tuple[Mapping[str, object], ...],
) -> dict[str, int]:
    counts: dict[str, int] = {}
    if materialization_index_receipts:
        counts["materialization_index_receipt"] = len(materialization_index_receipts)
    for receipt in artifact_ownership_receipts:
        if not _compile_parity_receipt_is_available(receipt):
            continue
        role = _optional_string_value(receipt.get("artifact_role"))
        if role is None:
            continue
        counts[role] = counts.get(role, 0) + 1
    return dict(sorted(counts.items()))


def _compile_parity_target_payload(
    *,
    target: _LanguageMaterializationTarget,
) -> dict[str, object]:
    return {
        "target_language_plugin_id": target.target_language_plugin_id.value,
        "output_root": target.output_root.as_posix(),
        "import_root": target.import_root,
        "package_name": target.package_name,
        "materialization_source": target.materialization_source,
        "source_is_runtime": target.source_is_runtime,
        "renderer_profile": target.renderer_profile,
        "renderer_kind": target.renderer_kind,
        "stable_ids_import_root": target.stable_ids_import_root,
        "stable_ids_ownership": target.stable_ids_ownership,
        "stable_ids_resolution_policy": target.stable_ids_resolution_policy,
    }


def _compile_parity_digest(payload: Mapping[str, object]) -> str:
    return sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()


def _uuid_text(value: UUID | None) -> str | None:
    return str(value) if value is not None else None


def _uuidish_text(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, UUID):
        return str(value)
    return _optional_string_value(value)


def _enum_value_text(value: object) -> str | None:
    enum_value = getattr(value, "value", None)
    return _optional_string_value(enum_value if enum_value is not None else value)


def _object_value_text(value: object, field_name: str) -> str | None:
    if isinstance(value, Mapping):
        raw_value = value.get(field_name)
    else:
        raw_value = getattr(value, field_name, None)
    enum_value = getattr(raw_value, "value", None)
    if enum_value is not None:
        raw_value = enum_value
    return _uuidish_text(raw_value)


def _leaf_lifecycle_receipts(
    *,
    request: SemanticPackageMaterializationRequest,
    leaf_result: ObjectConfigGraphPackageLeafMaterializationResult,
):
    return build_object_config_graph_package_language_lifecycle_receipts(
        aware_root=request.workspace_root,
        aware_toml_path=leaf_result.aware_toml_path,
        package_name=leaf_result.object_config_graph_package.package_name,
        source_code_package_id=leaf_result.code_package.id,
        object_config_graph_package_id=leaf_result.object_config_graph_package.id,
        object_config_graph_commit_id=(
            leaf_result.object_config_graph_object_instance_graph_commit_id
        ),
        source_object_instance_graph_commit_id=(
            leaf_result.code_package_object_instance_graph_commit_id
        ),
        input_object_instance_graph_commit_id=(
            leaf_result.object_config_graph_object_instance_graph_commit_id
        ),
    )


async def _leaf_language_materialization_receipts(
    *,
    request: SemanticPackageMaterializationRequest,
    leaf_result: ObjectConfigGraphPackageLeafMaterializationResult,
) -> _LanguageMaterializationReceipts:
    receipts: list[dict[str, object]] = []
    post_step_receipts: list[dict[str, object]] = []
    tool_step_receipts: list[dict[str, object]] = []
    generated_code_package_refs: list[dict[str, object]] = []
    generated_code_package_deltas: list[dict[str, object]] = []
    tool_timings_s: dict[str, float] = {}
    top_level_tool_duration_s = 0.0
    runtime_to_language_cache = RuntimeToLanguageLoweringCache(
        deep_copy_hits=False,
        deep_copy_stores=False,
    )
    runtime_derivation_cache = RuntimeObjectConfigGraphDerivationCache(
        deep_copy_hits=False,
        deep_copy_stores=False,
    )
    dependency_runtime_graphs_by_source_key: dict[
        tuple[str, str, str],
        tuple[ObjectConfigGraph, ...],
    ] = {}
    targets = _leaf_language_materialization_targets(
        request=request,
        leaf_result=leaf_result,
    )
    await _emit_semantic_materialization_progress(
        request=request,
        phase_name="meta.language_materialization",
        status="running",
        detail_payload={
            "target_count": len(targets),
            "package_name": leaf_result.object_config_graph_package.package_name,
            "full_generated_code_package_deltas": (
                _should_emit_generated_code_package_deltas(request=request)
            ),
        },
    )
    language_started_at = perf_counter()
    for target_index, target in enumerate(targets):
        target_started_at = perf_counter()
        source_graph = _language_materialization_source_graph(
            target=target,
            leaf_result=leaf_result,
            context=request.context,
        )
        target_payload = _language_target_progress_payload(
            target=target,
            source_graph=source_graph,
            target_index=target_index,
            target_count=len(targets),
        )
        await _emit_semantic_materialization_progress(
            request=request,
            phase_name="meta.language_target",
            status="running",
            detail_payload=target_payload,
        )
        dependency_cache_key = _language_dependency_source_graph_cache_key(
            source_graph.graph,
        )
        dependency_runtime_graphs = dependency_runtime_graphs_by_source_key.get(
            dependency_cache_key,
        )
        if dependency_runtime_graphs is None:
            dependency_runtime_graphs = (
                _package_dependency_runtime_object_config_graphs_from_context(
                    context=request.context,
                    source_graph=source_graph.graph,
                    aware_toml_path=leaf_result.aware_toml_path,
                    workspace_root=request.workspace_root,
                    include_transitive_dependencies=False,
                )
            )
            dependency_runtime_graphs_by_source_key[dependency_cache_key] = (
                dependency_runtime_graphs
            )
        language_subphase_futures: list[Future[None]] = []
        language_progress_loop = asyncio.get_running_loop()

        def _language_progress_callback(payload: Mapping[str, object]) -> None:
            _schedule_language_target_subphase_progress(
                request=request,
                target_payload=target_payload,
                loop=language_progress_loop,
                futures=language_subphase_futures,
                payload=payload,
            )

        def _materialize_language_target() -> object:
            return materialize_object_config_graph_via_language_plugin(
                LanguagePluginMaterializationRequest(
                    source_graph=source_graph.graph,
                    target_language_plugin_id=target.target_language_plugin_id,
                    external_runtime_graphs=dependency_runtime_graphs,
                    package_dependency_graphs=dependency_runtime_graphs,
                    source_is_runtime=source_graph.source_is_runtime,
                    output_root=target.output_root,
                    import_root=target.import_root,
                    package_name=target.package_name,
                    renderer_profile=target.renderer_profile,
                    renderer_kind=target.renderer_kind,
                    materialization_source=target.materialization_source,
                    stable_ids_import_root=target.stable_ids_import_root,
                    stable_ids_ownership=target.stable_ids_ownership,
                    stable_ids_resolution_policy=target.stable_ids_resolution_policy,
                    function_impl_ownership=(
                        _enum_value_text(
                            getattr(
                                leaf_result.object_config_graph_package,
                                "function_impl_ownership",
                                None,
                            )
                        )
                    ),
                    function_impl_parity_policy=(
                        _enum_value_text(
                            getattr(
                                leaf_result.object_config_graph_package,
                                "function_impl_parity_policy",
                                None,
                            )
                        )
                    ),
                    source_code_package_id=leaf_result.code_package.id,
                    object_config_graph_package_id=(
                        leaf_result.object_config_graph_package.id
                    ),
                    object_config_graph_commit_id=(
                        leaf_result.object_config_graph_object_instance_graph_commit_id
                    ),
                    emit_files=True,
                    post_step_tool_env_by_tool_id=(
                        _language_materialization_post_step_tool_mapping_by_tool_id(
                            context=request.context,
                            mapping_key="state_env",
                        )
                    ),
                    post_step_executable_overrides_by_tool_id=(
                        _language_materialization_post_step_tool_mapping_by_tool_id(
                            context=request.context,
                            mapping_key="executable_overrides",
                        )
                    ),
                    runtime_to_language_cache=runtime_to_language_cache,
                    runtime_derivation_cache=runtime_derivation_cache,
                    reuse_external_runtime_graphs=source_graph.source_is_runtime,
                    derive_external_projection_graphs=(
                        _language_materialization_target_should_lower_external_graphs(
                            target=target,
                        )
                    ),
                    lower_language_external_graphs=(
                        _language_materialization_target_should_lower_external_graphs(
                            target=target,
                        )
                    ),
                    progress_callback=_language_progress_callback,
                )
            )

        try:
            result = await _await_language_target_worker(_materialize_language_target)
        except Exception as exc:
            await _drain_language_target_subphase_progress(language_subphase_futures)
            error_traceback = traceback.format_exception(
                type(exc),
                exc,
                exc.__traceback__,
            )
            await _emit_semantic_materialization_progress(
                request=request,
                phase_name="meta.language_target",
                status="failed",
                started_at=target_started_at,
                error=str(exc),
                detail_payload={
                    **target_payload,
                    "error_type": type(exc).__name__,
                    "error_traceback_tail": tuple(error_traceback[-30:]),
                },
            )
            raise
        await _drain_language_target_subphase_progress(language_subphase_futures)
        receipts.extend(
            _workspace_language_receipt_payload(
                receipt_payload=receipt.as_payload(),
                output_root=target.output_root,
            )
            for receipt in result.ownership_receipts
        )
        code_package_outputs = await _commit_language_materialization_code_packages(
            request=request,
            leaf_result=leaf_result,
            target=target,
            result=result,
        )
        generated_code_package_refs.extend(code_package_outputs.refs)
        generated_code_package_deltas.extend(code_package_outputs.deltas)
        await _emit_semantic_materialization_progress(
            request=request,
            phase_name="meta.language_target",
            status="succeeded",
            started_at=target_started_at,
            detail_payload={
                **target_payload,
                "generated_file_count": len(getattr(result, "generated_files", ())),
                "package_output_count": len(getattr(result, "package_outputs", ())),
                "generated_code_package_ref_count": len(code_package_outputs.refs),
                "generated_code_package_delta_count": len(code_package_outputs.deltas),
            },
        )
        post_step_receipts.extend(
            dict(receipt) for receipt in result.post_step_receipts
        )
        for step in getattr(result, "tool_steps", ()):
            step_name = str(getattr(step, "name", "") or "").strip()
            if not step_name:
                continue
            raw_duration_s = getattr(step, "duration_s", None)
            if isinstance(raw_duration_s, bool):
                continue
            try:
                duration_s = round(max(float(raw_duration_s), 0.0), 6)
            except (TypeError, ValueError):
                continue
            step_details = getattr(step, "details", {})
            if not isinstance(step_details, Mapping):
                step_details = {}
            timing_scope = str(step_details.get("timing_scope") or "step")
            timing_parent_step = step_details.get("timing_parent_step")
            graph_role = step_details.get("graph_role")
            if timing_scope != "substep":
                top_level_tool_duration_s += duration_s
            timing_key = _language_materialization_tool_timing_key(
                target=target,
                target_index=target_index,
                step_name=step_name,
            )
            tool_timings_s[timing_key] = duration_s
            tool_step_receipts.append(
                {
                    "name": step_name,
                    "timing_key": timing_key,
                    "tool_id": timing_key,
                    "duration_s": duration_s,
                    "status": str(getattr(step, "status", "") or "succeeded"),
                    "timing_scope": timing_scope,
                    "timing_parent_step": timing_parent_step,
                    "graph_role": graph_role,
                    "target_language_plugin_id": target.target_language_plugin_id.value,
                    "materialization_source": target.materialization_source,
                    "renderer_profile": target.renderer_profile,
                    "renderer_kind": target.renderer_kind,
                    "source_is_runtime": target.source_is_runtime,
                }
            )
    if tool_timings_s:
        tool_timings_s["total"] = round(
            top_level_tool_duration_s or sum(tool_timings_s.values()),
            6,
        )
    await _emit_semantic_materialization_progress(
        request=request,
        phase_name="meta.language_materialization",
        status="succeeded",
        started_at=language_started_at,
        detail_payload={
            "target_count": len(targets),
            "artifact_ownership_receipt_count": len(receipts),
            "post_step_receipt_count": len(post_step_receipts),
            "generated_code_package_ref_count": len(generated_code_package_refs),
            "generated_code_package_delta_count": len(generated_code_package_deltas),
        },
    )
    return _LanguageMaterializationReceipts(
        artifact_ownership_receipts=tuple(receipts),
        post_step_receipts=tuple(post_step_receipts),
        tool_step_receipts=tuple(tool_step_receipts),
        generated_code_package_refs=tuple(generated_code_package_refs),
        generated_code_package_deltas=tuple(generated_code_package_deltas),
        tool_timings_s=dict(sorted(tool_timings_s.items())),
        runtime_to_language_cache=runtime_to_language_cache.stats_payload(),
        runtime_derivation_cache=runtime_derivation_cache.stats_payload(),
    )


def _language_dependency_source_graph_cache_key(
    graph: ObjectConfigGraph,
) -> tuple[str, str, str]:
    return (
        str(graph.id),
        str(graph.hash or graph.id),
        graph.fqn_prefix,
    )


def _language_materialization_target_should_lower_external_graphs(
    *,
    target: _LanguageMaterializationTarget,
) -> bool:
    # Python and SQL package renderers consume runtime dependency graphs for
    # import overrides, external class lookup, and relationship analysis. They
    # do not need every dependency lowered into a separate language OCG during
    # Workspace package generation.
    return target.target_language_plugin_id not in {
        CodeLanguage.python,
        CodeLanguage.sql,
    }


def _force_fresh_semantic_materialization_from_context(
    context: Mapping[str, object],
) -> bool:
    raw_value = context.get("semantic_materialization_force_fresh")
    if isinstance(raw_value, bool):
        return raw_value
    if isinstance(raw_value, Mapping):
        return bool(raw_value.get("enabled"))
    return False


async def _commit_language_materialization_code_packages(
    *,
    request: SemanticPackageMaterializationRequest,
    leaf_result: ObjectConfigGraphPackageLeafMaterializationResult,
    target: _LanguageMaterializationTarget,
    result: object,
) -> _LanguageMaterializationCodePackageOutputs:
    package_outputs = tuple(getattr(result, "package_outputs", ()) or ())
    if not package_outputs:
        return _LanguageMaterializationCodePackageOutputs()
    code_package_projection_hash = find_meta_graph_projection_hash_by_name(
        index=request.index,
        projection_name="CodePackage",
    )
    emit_generated_code_package_deltas = _should_emit_generated_code_package_deltas(
        request=request
    )
    refs: list[dict[str, object]] = []
    deltas: list[dict[str, object]] = []
    for package_output_index, package_output in enumerate(package_outputs):
        package_started_at = perf_counter()
        package_name = str(
            getattr(package_output, "package_name", None) or target.package_name
        ).strip()
        output_root = Path(getattr(package_output, "output_root")).resolve()
        include_package_inventory = (
            _generated_package_snapshot_should_include_inventory(target=target)
        )
        collect_texts_started_at = perf_counter()
        collect_texts_payload = {
            "package_output_index": package_output_index,
            "package_output_count": len(package_outputs),
            "package_name": package_name,
            "output_root": output_root.as_posix(),
            "target_language_plugin_id": target.target_language_plugin_id.value,
            "materialization_source": target.materialization_source,
            "renderer_profile": target.renderer_profile,
            "renderer_kind": target.renderer_kind,
            "include_package_inventory": include_package_inventory,
        }
        await _emit_semantic_materialization_progress(
            request=request,
            phase_name="meta.generated_code_package_snapshot.collect_texts",
            status="running",
            detail_payload=collect_texts_payload,
        )
        try:
            generated_texts = _generated_package_texts_by_relative_path(
                package_output=package_output,
                output_root=output_root,
                workspace_root=request.workspace_root,
                include_package_inventory=include_package_inventory,
            )
            deleted_relative_paths = _generated_package_deleted_relative_paths(
                package_output=package_output,
                output_root=output_root,
                workspace_root=request.workspace_root,
            )
        except Exception as exc:
            await _emit_semantic_materialization_progress(
                request=request,
                phase_name="meta.generated_code_package_snapshot.collect_texts",
                status="failed",
                started_at=collect_texts_started_at,
                error=str(exc),
                detail_payload=collect_texts_payload,
            )
            raise
        await _emit_semantic_materialization_progress(
            request=request,
            phase_name="meta.generated_code_package_snapshot.collect_texts",
            status="succeeded",
            started_at=collect_texts_started_at,
            detail_payload={
                **collect_texts_payload,
                "generated_path_count": len(generated_texts),
                "delete_path_count": len(deleted_relative_paths),
            },
        )
        if not package_name or (not generated_texts and not deleted_relative_paths):
            continue
        path_count = len(generated_texts) + len(deleted_relative_paths)
        manifest_kind, manifest_relative_path = (
            _generated_language_code_package_manifest(
                output_root=output_root,
                workspace_root=request.workspace_root,
            )
        )
        code_package_config_key = code_package_generated_config_key(
            materialization_source=target.materialization_source,
            renderer_kind=target.renderer_kind,
            language=target.target_language_plugin_id,
            surface=target.code_package_surface,
            manifest_kind=manifest_kind,
        )
        code_package_config_id = stable_code_package_config_id(
            config_key=code_package_config_key,
        )
        code_package_id = stable_code_package_id(
            code_package_config_id=code_package_config_id,
            package_name=package_name,
            language=target.target_language_plugin_id.value,
        )
        declared_code_package_id = stable_code_package_id(
            code_package_config_id=code_package_config_id,
            package_name=target.package_name,
            language=target.target_language_plugin_id.value,
        )
        branch_id = _stable_language_materialization_code_package_branch_id(
            object_config_graph_package_id=leaf_result.object_config_graph_package.id,
            code_package_id=code_package_id,
        )
        package_root = _relative_to_workspace_root(
            path=output_root,
            workspace_root=request.workspace_root,
        )
        sources_root = _generated_language_code_package_sources_root(
            output_root=output_root,
            import_root=str(
                getattr(package_output, "import_root", None) or target.import_root
            ),
        )
        progress_payload = {
            "package_output_index": package_output_index,
            "package_output_count": len(package_outputs),
            "package_name": package_name,
            "output_root": output_root.as_posix(),
            "target_language_plugin_id": target.target_language_plugin_id.value,
            "materialization_source": target.materialization_source,
            "renderer_profile": target.renderer_profile,
            "renderer_kind": target.renderer_kind,
            "path_count": path_count,
            "generated_path_count": len(generated_texts),
            "delete_path_count": len(deleted_relative_paths),
            "full_delta_payload": emit_generated_code_package_deltas,
        }
        await _emit_semantic_materialization_progress(
            request=request,
            phase_name="meta.generated_code_package_snapshot",
            status="running",
            detail_payload=progress_payload,
        )
        try:
            snapshot = await commit_code_package_text_snapshot(
                index=request.index,
                actor_id=request.actor_id,
                branch_id=branch_id,
                projection_hash=code_package_projection_hash,
                code_package_config_id=code_package_config_id,
                package_name=package_name,
                language=target.target_language_plugin_id,
                surface=target.code_package_surface,
                manifest_kind=manifest_kind,
                manifest_relative_path=manifest_relative_path,
                package_root=package_root,
                sources_root=sources_root,
                fqn_prefix=str(
                    getattr(package_output, "import_root", None) or target.import_root
                ),
                source_texts_by_relative_path={},
                unparsed_texts_by_relative_path=generated_texts,
                path_roles_by_relative_path={
                    relative_path: _generated_code_package_path_role(relative_path)
                    for relative_path in generated_texts
                },
            )
        except Exception as exc:
            await _emit_semantic_materialization_progress(
                request=request,
                phase_name="meta.generated_code_package_snapshot",
                status="failed",
                started_at=package_started_at,
                error=str(exc),
                detail_payload=progress_payload,
            )
            raise
        if emit_generated_code_package_deltas:
            delta = _language_materialization_code_package_delta(
                leaf_result=leaf_result,
                target=target,
                package_name=package_name,
                package_root=package_root,
                sources_root=sources_root,
                manifest_relative_path=manifest_relative_path,
                declared_code_package_id=declared_code_package_id,
                code_package_config_key=code_package_config_key,
                code_package_config_id=code_package_config_id,
                generated_texts=generated_texts,
                deleted_relative_paths=deleted_relative_paths,
                code_package_id=snapshot.code_package.id,
                code_package_commit_id=snapshot.commit_id,
                manifest_kind=manifest_kind,
            )
            deltas.append(delta.model_dump(mode="json"))
        refs.append(
            {
                "schema": "aware.meta.language_materialization.code_package_ref.v1",
                "target_language_plugin_id": target.target_language_plugin_id.value,
                "materialization_source": target.materialization_source,
                "renderer_profile": target.renderer_profile,
                "renderer_kind": target.renderer_kind,
                "object_config_graph_package_id": str(
                    leaf_result.object_config_graph_package.id
                ),
                "object_config_graph_object_instance_graph_commit_id": (
                    str(leaf_result.object_config_graph_object_instance_graph_commit_id)
                    if leaf_result.object_config_graph_object_instance_graph_commit_id
                    is not None
                    else None
                ),
                "declared_code_package_id": str(declared_code_package_id),
                "declared_package_name": target.package_name,
                "code_package_id": str(snapshot.code_package.id),
                "code_package_branch_id": str(branch_id),
                "code_package_commit_id": str(snapshot.commit_id),
                "code_package_head_commit_id": str(snapshot.head_commit_id),
                "code_package_object_instance_graph_commit_id": str(
                    snapshot.object_instance_graph_commit_id
                ),
                "package_name": package_name,
                "package_root": package_root,
                "sources_root": sources_root,
                "code_package_surface": target.code_package_surface,
                "code_package_config_key": code_package_config_key,
                "code_package_config_id": str(code_package_config_id),
                "manifest_kind": manifest_kind,
                "manifest_relative_path": manifest_relative_path,
                "path_count": path_count,
                "delete_path_count": len(deleted_relative_paths),
                "full_delta_payload": emit_generated_code_package_deltas,
            }
        )
        await _emit_semantic_materialization_progress(
            request=request,
            phase_name="meta.generated_code_package_snapshot",
            status="succeeded",
            started_at=package_started_at,
            detail_payload={
                **progress_payload,
                "code_package_id": str(snapshot.code_package.id),
                "code_package_commit_id": str(snapshot.commit_id),
                "code_package_head_commit_id": str(snapshot.head_commit_id),
                "code_package_object_instance_graph_commit_id": str(
                    snapshot.object_instance_graph_commit_id
                ),
                "object_count": snapshot.object_count,
                "change_count": snapshot.change_count,
                "generated_code_package_delta_count": (
                    1 if emit_generated_code_package_deltas else 0
                ),
            },
        )
    return _LanguageMaterializationCodePackageOutputs(
        refs=tuple(refs),
        deltas=tuple(deltas),
    )


def _language_materialization_code_package_delta(
    *,
    leaf_result: ObjectConfigGraphPackageLeafMaterializationResult,
    target: _LanguageMaterializationTarget,
    package_name: str,
    package_root: str,
    sources_root: str | None,
    manifest_relative_path: str,
    declared_code_package_id: UUID,
    code_package_config_key: str,
    code_package_config_id: UUID,
    generated_texts: Mapping[str, str],
    deleted_relative_paths: tuple[str, ...],
    code_package_id: UUID,
    code_package_commit_id: UUID,
    manifest_kind: str,
) -> CodePackageDelta:
    output_digest = _generated_code_package_delta_output_digest(
        generated_texts=generated_texts,
    )
    producer = CodePackageDeltaProducerRef(
        provider_key="aware_meta",
        producer_key=META_LANGUAGE_MATERIALIZATION_PRODUCER_KEY,
        producer_kind="semantic_materializer",
        provider_payload={
            "semantic_owner": META_OBJECT_CONFIG_GRAPH_OWNER,
            "output_key": META_LANGUAGE_MATERIALIZATION_CODE_PACKAGE_DELTAS_OUTPUT_KEY,
            "artifact_family": META_LANGUAGE_MATERIALIZATION_ARTIFACT_FAMILY,
            "target_language_plugin_id": target.target_language_plugin_id.value,
            "materialization_source": target.materialization_source,
            "renderer_profile": target.renderer_profile,
            "renderer_kind": target.renderer_kind,
            "code_package_surface": target.code_package_surface,
            "code_package_config_key": code_package_config_key,
            "code_package_config_id": str(code_package_config_id),
            "manifest_kind": manifest_kind,
            "declared_code_package_id": str(declared_code_package_id),
            "code_package_id": str(code_package_id),
            "code_package_commit_id": str(code_package_commit_id),
        },
    )
    production = CodePackageDeltaProduction(
        producer=producer,
        input_code_package_id=(
            getattr(getattr(leaf_result, "code_package", None), "id", None)
            or declared_code_package_id
        ),
        input_object_instance_graph_commit_id=(
            leaf_result.object_config_graph_object_instance_graph_commit_id
        ),
        output_digest=output_digest,
        emission_payload={
            "contract_version": (
                "aware.meta.language_materialization.code_package_delta.v1"
            ),
            "package_name": package_name,
            "package_root": package_root,
            "sources_root": sources_root,
            "code_package_surface": target.code_package_surface,
            "code_package_config_key": code_package_config_key,
            "code_package_config_id": str(code_package_config_id),
            "manifest_kind": manifest_kind,
            "manifest_relative_path": manifest_relative_path,
            "path_count": len(generated_texts) + len(deleted_relative_paths),
            "delete_path_count": len(deleted_relative_paths),
        },
    )
    paths = [
        CodePackageDeltaPath(
            relative_path=relative_path,
            kind=CodePackageDeltaKind.update,
            content_text=generated_texts[relative_path],
            after_hash=sha256(
                generated_texts[relative_path].encode("utf-8")
            ).hexdigest(),
            size_bytes=len(generated_texts[relative_path].encode("utf-8")),
            language=target.target_language_plugin_id,
            is_structural=True,
            path_role=_generated_code_package_path_role(relative_path),
            production=production,
        )
        for relative_path in sorted(generated_texts)
    ]
    paths.extend(
        CodePackageDeltaPath(
            relative_path=relative_path,
            kind=CodePackageDeltaKind.delete,
            language=target.target_language_plugin_id,
            is_structural=True,
            path_role=_generated_code_package_path_role(relative_path),
            production=production,
        )
        for relative_path in sorted(deleted_relative_paths)
        if relative_path not in generated_texts
    )
    return CodePackageDelta(
        package_name=package_name,
        package_root=package_root,
        sources_root=sources_root,
        manifest_relative_path=manifest_relative_path,
        authority=CodePackageDeltaAuthorityKind.semantic_materialization,
        authority_kind=CodePackageDeltaAuthorityKind.semantic_materialization.value,
        source_revision_id=(
            "semantic_materialization:"
            f"aware_meta:{META_LANGUAGE_MATERIALIZATION_PRODUCER_KEY}:"
            f"{leaf_result.object_config_graph_package.id}"
        ),
        production=production,
        paths=paths,
    )


def _stable_language_materialization_code_package_branch_id(
    *,
    object_config_graph_package_id: UUID,
    code_package_id: UUID,
) -> UUID:
    return uuid5(
        _LANGUAGE_MATERIALIZATION_CODE_PACKAGE_BRANCH_NAMESPACE,
        f"{object_config_graph_package_id}:{code_package_id}",
    )


def _generated_package_texts_by_relative_path(
    *,
    package_output: object,
    output_root: Path,
    workspace_root: Path | None = None,
    include_package_inventory: bool = True,
) -> dict[str, str]:
    texts: dict[str, str] = {}
    resolved_output_root = output_root.resolve()
    resolved_workspace_root = (
        workspace_root.resolve() if workspace_root is not None else None
    )
    candidate_paths = list(
        tuple(getattr(package_output, "generated_file_refs", ()) or ())
    )
    if include_package_inventory:
        candidate_paths.extend(
            _generated_package_inventory_candidate_paths(
                output_root=resolved_output_root
            )
        )
    for raw_ref in candidate_paths:
        path = Path(raw_ref)
        absolute_path = _generated_package_ref_absolute_path(
            path=path,
            output_root=resolved_output_root,
            workspace_root=resolved_workspace_root,
        )
        if absolute_path is None:
            continue
        if not absolute_path.is_file():
            continue
        try:
            relative_path = (
                absolute_path.resolve().relative_to(resolved_output_root).as_posix()
            )
        except ValueError:
            continue
        if not _generated_package_relative_path_allowed(relative_path=relative_path):
            continue
        try:
            texts[relative_path] = absolute_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
    return texts


def _generated_package_snapshot_should_include_inventory(
    *,
    target: _LanguageMaterializationTarget,
) -> bool:
    materialization_source = (target.materialization_source or "").strip().lower()
    if materialization_source == "runtime_handlers":
        return False
    return True


def _generated_package_deleted_relative_paths(
    *,
    package_output: object,
    output_root: Path,
    workspace_root: Path | None = None,
) -> tuple[str, ...]:
    resolved_output_root = output_root.resolve()
    resolved_workspace_root = (
        workspace_root.resolve() if workspace_root is not None else None
    )
    paths: set[str] = set()
    for raw_ref in tuple(getattr(package_output, "deleted_file_refs", ()) or ()):
        path = Path(raw_ref)
        absolute_path = _generated_package_ref_absolute_path_for_deleted_path(
            path=path,
            output_root=resolved_output_root,
            workspace_root=resolved_workspace_root,
        )
        if absolute_path is None:
            continue
        try:
            relative_path = (
                absolute_path.resolve().relative_to(resolved_output_root).as_posix()
            )
        except ValueError:
            continue
        if not _generated_package_relative_path_allowed(relative_path=relative_path):
            continue
        paths.add(relative_path)
    return tuple(sorted(paths))


_GENERATED_PACKAGE_TEXT_DENYLIST_PARTS = frozenset(
    {
        "__pycache__",
        ".aware",
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        ".venv",
        "build",
        "dist",
        "node_modules",
    }
)
_GENERATED_PACKAGE_TEXT_DENYLIST_SUFFIXES = frozenset({".pyc", ".pyo"})


def _generated_package_relative_path_allowed(*, relative_path: str) -> bool:
    path = Path(relative_path)
    if any(part in _GENERATED_PACKAGE_TEXT_DENYLIST_PARTS for part in path.parts):
        return False
    return path.suffix.lower() not in _GENERATED_PACKAGE_TEXT_DENYLIST_SUFFIXES


def _generated_package_inventory_candidate_paths(
    *, output_root: Path
) -> tuple[Path, ...]:
    if not output_root.is_dir():
        return ()
    candidates: list[Path] = []
    for candidate in output_root.rglob("*"):
        if not candidate.is_file() or candidate.is_symlink():
            continue
        try:
            relative_parts = candidate.relative_to(output_root).parts
        except ValueError:
            continue
        if not _generated_package_relative_path_allowed(
            relative_path=Path(*relative_parts).as_posix(),
        ):
            continue
        candidates.append(candidate)
    return tuple(sorted(candidates, key=lambda item: item.as_posix()))


def _generated_package_ref_absolute_path(
    *,
    path: Path,
    output_root: Path,
    workspace_root: Path | None,
) -> Path | None:
    if path.is_absolute():
        return path
    output_candidate = output_root / path
    if output_candidate.is_file():
        return output_candidate
    if workspace_root is None:
        return output_candidate
    workspace_candidate = workspace_root / path
    if workspace_candidate.is_file():
        return workspace_candidate
    return output_candidate


def _generated_package_ref_absolute_path_for_deleted_path(
    *,
    path: Path,
    output_root: Path,
    workspace_root: Path | None,
) -> Path | None:
    if path.is_absolute():
        return path
    output_candidate = output_root / path
    try:
        output_candidate.resolve().relative_to(output_root)
    except ValueError:
        return None
    if workspace_root is None:
        return output_candidate
    workspace_candidate = workspace_root / path
    try:
        workspace_candidate.resolve().relative_to(output_root)
    except ValueError:
        return output_candidate
    return workspace_candidate


def _generated_code_package_delta_output_digest(
    *,
    generated_texts: Mapping[str, str],
) -> str:
    return sha256(
        json.dumps(
            {
                relative_path: generated_texts[relative_path]
                for relative_path in sorted(generated_texts)
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _generated_language_code_package_manifest(
    *,
    output_root: Path,
    workspace_root: Path,
) -> tuple[str, str]:
    manifest_candidates = (
        ("pyproject_toml", output_root / "pyproject.toml"),
        ("setup_py", output_root / "setup.py"),
        ("pubspec_yaml", output_root / "pubspec.yaml"),
        (
            "generated_materialization",
            output_root / "_aware" / "sqlite_orm_schema_contract.json",
        ),
    )
    for manifest_kind, manifest_path in manifest_candidates:
        if manifest_path.is_file():
            return manifest_kind, _relative_to_workspace_root(
                path=manifest_path,
                workspace_root=workspace_root,
            )
    return (
        "generated_materialization",
        _relative_to_workspace_root(path=output_root, workspace_root=workspace_root),
    )


def _generated_language_code_package_sources_root(
    *,
    output_root: Path,
    import_root: str,
) -> str | None:
    normalized = (import_root or "").strip()
    if normalized and (output_root / normalized).is_dir():
        return normalized
    return None


def _generated_code_package_path_role(relative_path: str) -> CodePackagePathRole:
    path = Path(relative_path)
    if path.name in {"pyproject.toml", "setup.py", "pubspec.yaml"}:
        return CodePackagePathRole.generated_manifest
    if path.parts and path.parts[0] in {"_aware", ".aware"}:
        return CodePackagePathRole.generated_metadata
    if path.suffix in {".json", ".msgpack", ".yaml", ".yml", ".toml"}:
        return CodePackagePathRole.generated_metadata
    return CodePackagePathRole.generated_code


def _relative_to_workspace_root(*, path: Path, workspace_root: Path) -> str:
    try:
        return path.resolve().relative_to(workspace_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _language_materialization_tool_timing_key(
    *,
    target: _LanguageMaterializationTarget,
    target_index: int,
    step_name: str,
) -> str:
    profile = (
        target.renderer_kind
        or target.renderer_profile
        or target.materialization_source
        or "default"
    )
    return ".".join(
        (
            f"target_{target_index}",
            target.target_language_plugin_id.value,
            str(target.materialization_source or "unknown"),
            str(profile),
            step_name,
        )
    )


def _provider_delta_language_target_payload(
    *,
    target_index: int,
    target: _LanguageMaterializationTarget,
    workspace_root: Path,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "target_index": target_index,
        "target_language_plugin_id": target.target_language_plugin_id.value,
        "output_root": _relative_to_workspace_root(
            path=target.output_root,
            workspace_root=workspace_root,
        ),
        "import_root": target.import_root,
        "package_name": target.package_name,
        "materialization_source": target.materialization_source,
        "code_package_surface": target.code_package_surface,
        "source_is_runtime": target.source_is_runtime,
    }
    if target.renderer_profile is not None:
        payload["renderer_profile"] = target.renderer_profile
    if target.renderer_kind is not None:
        payload["renderer_kind"] = target.renderer_kind
    if target.stable_ids_import_root is not None:
        payload["stable_ids_import_root"] = target.stable_ids_import_root
    if target.stable_ids_ownership is not None:
        payload["stable_ids_ownership"] = target.stable_ids_ownership
    if target.stable_ids_resolution_policy is not None:
        payload["stable_ids_resolution_policy"] = target.stable_ids_resolution_policy
    return payload


def _provider_delta_selected_language_target_indexes(
    *,
    language_target_impact_plan: Mapping[str, object],
    target_count: int,
) -> frozenset[int]:
    raw_indexes = language_target_impact_plan.get("selected_target_indexes")
    if not isinstance(raw_indexes, (list, tuple)):
        return frozenset(range(target_count))
    indexes = {
        index
        for index in raw_indexes
        if isinstance(index, int) and 0 <= index < target_count
    }
    return frozenset(indexes or range(target_count))


def _language_materialization_source_graph(
    *,
    target: _LanguageMaterializationTarget,
    leaf_result: ObjectConfigGraphPackageLeafMaterializationResult,
    context: Mapping[str, object],
) -> _LanguageMaterializationSourceGraph:
    if not target.source_is_runtime:
        return _LanguageMaterializationSourceGraph(
            graph=leaf_result.object_config_graph,
            source_is_runtime=False,
        )
    # Leaf materialization owns the fresh source graph. Derive the runtime graph
    # from it inside the language service so selected-package rebuilds cannot
    # render runtime handlers from stale context runtime graphs.
    _ = context
    return _LanguageMaterializationSourceGraph(
        graph=leaf_result.object_config_graph,
        source_is_runtime=False,
    )


def _runtime_object_config_graph_for_fqn_prefix(
    *,
    context: Mapping[str, object],
    fqn_prefix: str,
) -> ObjectConfigGraph | None:
    for graph in _object_config_graphs_from_context_value(
        context.get("runtime_object_config_graphs")
    ):
        if graph.fqn_prefix == fqn_prefix:
            return graph
    return None


def _leaf_language_materialization_targets(
    *,
    request: SemanticPackageMaterializationRequest,
    leaf_result: ObjectConfigGraphPackageLeafMaterializationResult,
) -> tuple[_LanguageMaterializationTarget, ...]:
    targets = _language_materialization_targets_from_context(
        context=request.context,
        workspace_root=request.workspace_root,
    )
    return tuple(
        target
        for target in targets
        if _language_materialization_target_matches_leaf(
            target=target,
            leaf_result=leaf_result,
        )
    )


def _language_materialization_target_matches_leaf(
    *,
    target: _LanguageMaterializationTarget,
    leaf_result: ObjectConfigGraphPackageLeafMaterializationResult,
) -> bool:
    package = leaf_result.object_config_graph_package
    package_name = (package.package_name or "").strip()
    fqn_prefix = (package.fqn_prefix or "").strip() or (
        leaf_result.object_config_graph.fqn_prefix or ""
    ).strip()
    if package_name and _target_token_matches_package(
        value=target.package_name,
        package_name=package_name,
    ):
        return True
    if fqn_prefix:
        for value in (
            target.import_root,
            target.stable_ids_import_root,
            target.package_name,
        ):
            if _target_token_matches_fqn_prefix(value=value, fqn_prefix=fqn_prefix):
                return True
    return False


def _target_token_matches_package(*, value: str | None, package_name: str) -> bool:
    token = (value or "").strip()
    package = package_name.strip()
    return token == package or token.startswith(f"{package}-")


def _target_token_matches_fqn_prefix(*, value: str | None, fqn_prefix: str) -> bool:
    token = (value or "").strip()
    fqn = fqn_prefix.strip()
    return token == fqn or token.startswith(f"{fqn}_") or token.startswith(f"{fqn}.")


def _language_materialization_targets_from_context(
    *,
    context: Mapping[str, object],
    workspace_root: Path,
) -> tuple[_LanguageMaterializationTarget, ...]:
    raw_targets = context.get(SEMANTIC_LANGUAGE_MATERIALIZATION_TARGETS_CONTEXT_KEY)
    if not isinstance(raw_targets, (list, tuple)):
        return ()

    targets: list[_LanguageMaterializationTarget] = []
    for raw_target in raw_targets:
        if not isinstance(raw_target, Mapping):
            continue
        target = _language_materialization_target_from_payload(
            payload=raw_target,
            workspace_root=workspace_root,
        )
        if target is not None:
            targets.append(target)
    return tuple(targets)


def _language_materialization_post_step_tool_mapping_by_tool_id(
    *,
    context: Mapping[str, object],
    mapping_key: str,
) -> Mapping[str, Mapping[str, str]]:
    raw_tooling = context.get(SEMANTIC_LANGUAGE_MATERIALIZATION_TOOLING_CONTEXT_KEY)
    if not isinstance(raw_tooling, Mapping):
        return {}
    raw_tools = raw_tooling.get("tools")
    if not isinstance(raw_tools, (list, tuple)):
        return {}
    mappings: dict[str, dict[str, str]] = {}
    for raw_tool in raw_tools:
        if not isinstance(raw_tool, Mapping):
            continue
        tool_id = _optional_string_value(raw_tool.get("tool_id"))
        if tool_id is None:
            continue
        raw_mapping = raw_tool.get(mapping_key)
        if not isinstance(raw_mapping, Mapping):
            continue
        normalized = {
            str(key): str(value)
            for key, value in raw_mapping.items()
            if str(key).strip()
        }
        if normalized:
            mappings[tool_id] = normalized
    return mappings


def _language_materialization_target_from_payload(
    *,
    payload: Mapping[str, object],
    workspace_root: Path,
) -> _LanguageMaterializationTarget | None:
    target_language = _code_language_from_payload(
        payload.get("target_language_plugin_id")
        or payload.get("target_language")
        or payload.get("language")
    )
    output_root = _target_output_root_from_payload(
        payload=payload,
        workspace_root=workspace_root,
    )
    import_root = _optional_string_value(payload.get("import_root"))
    materialization_source = _optional_string_value(
        payload.get("materialization_source")
    )
    code_package_surface = _code_package_surface_from_payload(
        payload.get("code_package_surface") or payload.get("surface")
    )
    if (
        target_language is None
        or output_root is None
        or import_root is None
        or materialization_source is None
        or code_package_surface is None
    ):
        return None
    return _LanguageMaterializationTarget(
        target_language_plugin_id=target_language,
        output_root=output_root,
        import_root=import_root,
        package_name=(
            _optional_string_value(payload.get("package_name")) or import_root
        ),
        materialization_source=materialization_source,
        code_package_surface=code_package_surface,
        source_is_runtime=bool(payload.get("source_is_runtime")),
        renderer_profile=_optional_string_value(payload.get("renderer_profile")),
        renderer_kind=_optional_string_value(payload.get("renderer_kind")),
        stable_ids_import_root=_optional_string_value(
            payload.get("stable_ids_import_root")
        ),
        stable_ids_ownership=_optional_string_value(
            payload.get("stable_ids_ownership")
        ),
        stable_ids_resolution_policy=_optional_string_value(
            payload.get("stable_ids_resolution_policy")
        ),
    )


def _code_language_from_payload(value: object) -> CodeLanguage | None:
    raw_value = _optional_string_value(value)
    if raw_value is None:
        return None
    try:
        return CodeLanguage(raw_value)
    except ValueError:
        return None


def _code_package_surface_from_payload(value: object) -> str | None:
    raw_value = _optional_string_value(value)
    if raw_value is None:
        return None
    return raw_value


def _target_output_root_from_payload(
    *,
    payload: Mapping[str, object],
    workspace_root: Path,
) -> Path | None:
    raw_output_root = _optional_string_value(payload.get("output_root"))
    if raw_output_root is None:
        return None
    output_root = Path(raw_output_root)
    return output_root if output_root.is_absolute() else workspace_root / output_root


def _workspace_language_receipt_payload(
    *,
    receipt_payload: Mapping[str, object],
    output_root: Path,
) -> dict[str, object]:
    payload = dict(receipt_payload)
    raw_path = payload.get("path")
    if isinstance(raw_path, str) and raw_path.strip():
        path = Path(raw_path)
        if not path.is_absolute():
            payload["path"] = (output_root / path).resolve().as_posix()
    return payload


def _bundle_packages_from_leaf_result(
    *,
    leaf_result: ObjectConfigGraphPackageLeafMaterializationResult,
    workspace_root: Path,
    materialized_language_packages: tuple[Mapping[str, object], ...] = (),
) -> tuple[SemanticPackageMaterializationBundle, ...]:
    return (
        SemanticPackageMaterializationBundle(
            package_key=leaf_result.object_config_graph_package.package_name,
            manifest_toml_path=leaf_result.aware_toml_path,
            semantic_package_id=leaf_result.object_config_graph_package.id,
            semantic_root_id=leaf_result.object_config_graph.id,
            semantic_branch_id=leaf_result.package_branch_id,
            semantic_head_commit_id=(
                leaf_result.object_config_graph_package_head_commit_id
            ),
            semantic_object_instance_graph_commit_id=(
                leaf_result.object_config_graph_package_object_instance_graph_commit_id
            ),
            semantic_root_object_instance_graph_commit_id=(
                leaf_result.object_config_graph_object_instance_graph_commit_id
            ),
            semantic_root_kind="object_config_graph",
            source_code_package_id=leaf_result.code_package.id,
            source_object_instance_graph_commit_id=(
                leaf_result.code_package_object_instance_graph_commit_id
            ),
            semantic_packages=(
                _semantic_package_detail_from_leaf_result(
                    leaf_result=leaf_result,
                    workspace_root=workspace_root,
                    materialized_language_packages=materialized_language_packages,
                ),
            ),
        ),
    )


def _semantic_package_detail_from_leaf_result(
    *,
    leaf_result: ObjectConfigGraphPackageLeafMaterializationResult,
    workspace_root: Path,
    materialized_language_packages: tuple[Mapping[str, object], ...] = (),
) -> dict[str, object]:
    code_package = leaf_result.code_package
    object_config_graph_package = leaf_result.object_config_graph_package
    object_config_graph = leaf_result.object_config_graph
    aware_toml_path = leaf_result.aware_toml_path
    return {
        "module_name": _module_name_from_aware_toml_path(
            aware_toml_path=aware_toml_path,
        ),
        "aware_toml_path": _workspace_relative_path(
            path=aware_toml_path,
            workspace_root=workspace_root,
        ),
        "manifest_relative_path": _workspace_relative_path(
            path=aware_toml_path,
            workspace_root=workspace_root,
        ),
        "package_root": _object_value_text(code_package, "package_root")
        or _workspace_relative_path(
            path=aware_toml_path.parent,
            workspace_root=workspace_root,
        ),
        "sources_root": _object_value_text(code_package, "sources_root"),
        "package_name": object_config_graph_package.package_name,
        "fqn_prefix": object_config_graph_package.fqn_prefix,
        "semantic_branch_id": str(leaf_result.package_branch_id),
        "semantic_head_commit_id": _uuid_text(
            leaf_result.object_config_graph_package_head_commit_id,
        ),
        "code_package_id": str(code_package.id),
        "code_package_head_commit_id": _uuidish_text(
            getattr(leaf_result, "code_package_head_commit_id", None),
        ),
        "code_package_object_instance_graph_commit_id": _uuidish_text(
            getattr(
                leaf_result,
                "code_package_object_instance_graph_commit_id",
                None,
            ),
        ),
        "object_config_graph_package_id": str(object_config_graph_package.id),
        "object_config_graph_package_head_commit_id": _uuid_text(
            leaf_result.object_config_graph_package_head_commit_id,
        ),
        "object_config_graph_package_object_instance_graph_commit_id": _uuid_text(
            leaf_result.object_config_graph_package_object_instance_graph_commit_id,
        ),
        "object_config_graph_id": str(object_config_graph.id),
        "object_config_graph_head_commit_id": _uuidish_text(
            getattr(leaf_result, "object_config_graph_head_commit_id", None),
        ),
        "object_config_graph_object_instance_graph_commit_id": _uuidish_text(
            getattr(
                leaf_result,
                "object_config_graph_object_instance_graph_commit_id",
                None,
            ),
        ),
        "semantic_root_object_instance_graph_commit_id": _uuidish_text(
            getattr(
                leaf_result,
                "object_config_graph_object_instance_graph_commit_id",
                None,
            ),
        ),
        "semantic_commit_strategy": leaf_result.semantic_commit_strategy,
        "semantic_commit_fallback_reset": getattr(
            leaf_result,
            "semantic_commit_fallback_reset",
            False,
        ),
        "materialized_language_packages": tuple(
            dict(item) for item in materialized_language_packages
        ),
    }


def _module_name_from_aware_toml_path(*, aware_toml_path: Path) -> str:
    parts = aware_toml_path.parts
    for marker in ("modules", "sdks", "apis", "services", "interfaces", "panes"):
        if marker not in parts:
            continue
        index = parts.index(marker)
        if index + 1 < len(parts):
            return parts[index + 1]
    return aware_toml_path.parent.name


def _workspace_relative_path(*, path: Path, workspace_root: Path) -> str:
    try:
        return path.resolve().relative_to(workspace_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _bundle_packages_from_execution(
    *,
    request: SemanticPackageMaterializationRequest,
    execution_payload: Mapping[str, object],
    head_commit_id: UUID | None,
) -> tuple[SemanticPackageMaterializationBundle, ...]:
    if execution_payload.get("status") != "executed":
        return ()
    package_name, fqn_prefix = _ocg_package_identity(request.change_preview)
    if package_name is None or fqn_prefix is None:
        return ()
    package_semantic_key = f"ocg_package:{package_name}"
    graph_semantic_key = f"ocg:{fqn_prefix}"
    package_id = _execution_result_uuid(
        execution_payload=execution_payload,
        semantic_key=package_semantic_key,
        field_name="result_object_id",
    )
    graph_id = _execution_result_uuid(
        execution_payload=execution_payload,
        semantic_key=graph_semantic_key,
        field_name="result_object_id",
    )
    if package_id is None or graph_id is None:
        return ()
    graph_oig_commit_id = _execution_result_uuid(
        execution_payload=execution_payload,
        semantic_key=graph_semantic_key,
        field_name="object_instance_graph_commit_id",
    )
    package_oig_commit_id = _execution_result_uuid(
        execution_payload=execution_payload,
        semantic_key=package_semantic_key,
        field_name="object_instance_graph_commit_id",
    )
    return (
        SemanticPackageMaterializationBundle(
            package_key=package_name,
            manifest_toml_path=request.manifest_path,
            semantic_package_id=package_id,
            semantic_root_id=graph_id,
            semantic_branch_id=request.branch_id,
            semantic_head_commit_id=head_commit_id,
            semantic_object_instance_graph_commit_id=package_oig_commit_id,
            semantic_root_object_instance_graph_commit_id=graph_oig_commit_id,
            semantic_root_kind="object_config_graph",
        ),
    )


def _ocg_package_identity(
    change_preview: Mapping[str, object],
) -> tuple[str | None, str | None]:
    for delta in _tuple_evidence(change_preview.get("semantic_deltas")):
        payload = _mapping_value(delta)
        if _string_value(payload.get("subject_type")) != (
            "aware_meta.ObjectConfigGraphPackage"
        ):
            continue
        after_payload = _mapping_value(payload.get("after_payload"))
        return (
            _optional_string_value(after_payload.get("package_name")),
            _optional_string_value(after_payload.get("fqn_prefix")),
        )
    return None, None


def _execution_result_uuid(
    *,
    execution_payload: Mapping[str, object],
    semantic_key: str,
    field_name: str,
) -> UUID | None:
    raw_value = _execution_result_value(
        execution_payload=execution_payload,
        semantic_key=semantic_key,
        field_name=field_name,
    )
    if raw_value is None:
        return None
    try:
        return UUID(raw_value)
    except ValueError:
        return None


def _execution_result_value(
    *,
    execution_payload: Mapping[str, object],
    semantic_key: str,
    field_name: str,
) -> str | None:
    for step in _execution_steps(execution_payload):
        if str(step.get("status") or "").strip() != "invoked":
            continue
        if _optional_string_value(step.get("semantic_key")) != semantic_key:
            continue
        if field_name == "result_object_id":
            return _optional_string_value(step.get("result_object_id"))
        evidence = step.get("evidence")
        if not isinstance(evidence, Mapping):
            continue
        result = evidence.get("result")
        if not isinstance(result, Mapping):
            continue
        if field_name in result:
            return _optional_string_value(result.get(field_name))
        result_evidence = result.get("evidence")
        if not isinstance(result_evidence, Mapping):
            continue
        response = result_evidence.get("response")
        if isinstance(response, Mapping):
            value = _optional_string_value(response.get(field_name))
            if value is not None:
                return value
    return None


def _execution_has_terminal_failure(
    execution_payload: Mapping[str, object],
) -> bool:
    status_counts = execution_payload.get("status_counts")
    if not isinstance(status_counts, Mapping):
        return False
    for status in ("blocked", "failed"):
        raw_count = status_counts.get(status)
        if isinstance(raw_count, int):
            count = raw_count
        elif isinstance(raw_count, str) and raw_count.strip():
            try:
                count = int(raw_count)
            except ValueError:
                count = 0
        else:
            count = 0
        if count > 0:
            return True
    return False


def _execution_failure_message(
    execution_payload: Mapping[str, object],
) -> str:
    for step in _execution_steps(execution_payload):
        status = str(step.get("status") or "").strip()
        if status not in {"blocked", "failed"}:
            continue
        function_ref = _optional_string_value(step.get("function_ref")) or "unknown"
        semantic_key = _optional_string_value(step.get("semantic_key")) or "unknown"
        reason = _optional_string_value(step.get("reason"))
        error = _optional_string_value(step.get("error"))
        detail = error or reason or "unknown execution failure"
        return (
            "Meta semantic function-call execution failed: "
            f"function_ref={function_ref} semantic_key={semantic_key} detail={detail}"
        )
    return "Meta semantic function-call execution failed."


def _execution_steps(
    execution_payload: Mapping[str, object],
) -> tuple[Mapping[str, object], ...]:
    steps = execution_payload.get("steps")
    if not isinstance(steps, (list, tuple)):
        return ()
    return tuple(step for step in steps if isinstance(step, Mapping))


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


def _optional_string_value(value: object) -> str | None:
    text = _string_value(value)
    return text or None


__all__ = [
    "build_meta_runtime_ocg_function_call_plan_previews",
    "materialize",
    "materialize_delta",
    "materialize_provider_delta_outputs",
    "meta_ocg_migration_artifact_ownership_receipts_from_bundle",
]
