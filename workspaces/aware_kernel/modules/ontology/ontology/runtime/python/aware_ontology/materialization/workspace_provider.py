from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from hashlib import sha256
import json
from pathlib import Path
import shutil
from time import perf_counter
import tomllib
from types import SimpleNamespace
from typing import Any, Protocol, TypeGuard
from uuid import NAMESPACE_URL, UUID, uuid5

from aware_code.package.snapshot_commit import commit_code_package_text_snapshot
from aware_code.semantic_contract_config import source_code_package_config_ref
from aware_code.semantic_materialization import (
    SEMANTIC_MATERIALIZATION_LIFECYCLE_PROFILE_CONTEXT_KEY,
    SEMANTIC_PROVIDER_DELTA_DURABLE_EXECUTION_INPUTS_KEY,
    SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_CONTEXT_KEY,
    SemanticPackageMaterializationBundle,
    SemanticPackageMaterializationRequest,
    SemanticPackageMaterializationResult,
)
from aware_code.types import JsonArray
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.code.code_plan import CodePackageDelta
from aware_meta.manifest.loader import load_aware_toml_spec
from aware_ontology.manifest.loader import load_aware_ontology_toml_spec
from aware_meta.graph.instance.builder import (
    build_rooted_object_instance_graph_base,
)
from aware_meta.graph.instance.commit.committer import (
    FSLaneCommitter,
    LaneHeadPreHashMismatchError,
)
from aware_meta.graph.instance.commit.fs_store import (
    CommitActionDescriptor,
    FSCommitStore,
)
from aware_meta.graph.instance.commit.materialization_cache import (
    get_shared_materialization_cache,
)
from aware_meta.graph.instance.diff_orm import (
    build_object_instance_graph_changes_from_orm_change_set,
)
from aware_meta.materialization import service as meta_service
from aware_meta.materialization import workspace_provider as meta_workspace_provider
from aware_meta.materialization.service import (
    ObjectConfigGraphPackageLeafMaterializationResult,
)
from aware_meta.runtime.graph_lane import MetaGraphBoundRuntimeLane
from aware_meta.runtime.handler_executor import MetaGraphRuntimeIndex
from aware_meta.runtime.graph_context import (
    build_meta_graph_runtime_context_for_aware_package_manifests,
    find_meta_graph_projection_hash_by_name,
    resolve_meta_runtime_package_manifest_closure_for_package_names,
)
from aware_meta.semantic_contract import (
    META_MATERIALIZATION_REQUIRED_PROJECTIONS,
    META_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES,
)
from aware_meta.runtime.package_index import (
    MetaRuntimeSemanticObjectIndexEntry,
    load_meta_runtime_package_projection_index,
    stable_meta_runtime_package_branch_id,
)
from aware_meta_ontology.graph.config.object_config_graph import (
    ObjectConfigGraph,
)
from aware_meta_ontology.stable_ids import (
    stable_object_instance_graph_commit_id,
    stable_object_instance_graph_id,
    stable_object_instance_graph_identity_id,
)
from aware_ontology_ontology.ontology.ontology_config import OntologyConfig
from aware_ontology_ontology.ontology.ontology_package import OntologyPackage
from aware_ontology_ontology.stable_ids import (
    stable_ontology_config_id,
    stable_ontology_package_id,
)
from aware_orm.models.base_model import BaseORMModel
from aware_orm.session.change_collector import ORMChangeSet
from aware_meta.runtime.author import resolve_meta_author_id
from aware_meta.runtime.graph_identity import resolve_meta_graph_ocgi_opgi
from aware_meta.runtime.oig_post import materialize_meta_oig_post
from aware_ontology.semantic_runtime_catalog import (
    ONTOLOGY_RUNTIME_ARTIFACT_SET_OUTPUT_KEY,
    build_ontology_runtime_artifact_set_ownership_receipt,
    build_ontology_runtime_artifact_set_from_materialization_details,
)
from aware_ontology.runtime_bundle import (
    ONTOLOGY_RUNTIME_BUNDLE_RELATIVE_PATH,
    write_ontology_runtime_bundle,
)


_ONTOLOGY_PROVIDER_OWNER = "aware_ontology.provider"
_ONTOLOGY_PROVIDER_SCHEMA = "aware_ontology.workspace_materialize.ontology_package.v1"
_ONTOLOGY_SNAPSHOT_COMMIT_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware://ontology/workspace-materialization/" "ontology-package-snapshot-commit/v1",
)
_META_DELTA_PROVIDER_KEY = "aware_meta"
_META_DELTA_PROVIDER_ROLE = "aware_meta.provider"
_META_DELTA_CONTRACT_MODULE = "aware_meta.semantic_contract"
_META_DELTA_CONTRACT_NAME = "aware.semantic_provider"
_META_DELTA_BASELINE_PROJECTION_NAME = "ObjectConfigGraph"
_COMPLETE_LANGUAGE_PACKAGE_STATUSES = frozenset({"available", "materialized"})


@dataclass(frozen=True, slots=True)
class _OntologyPackageSource:
    ontology_toml_path: Path
    source_manifest_path: Path
    package_name: str
    fqn_prefix: str
    version_number: int
    title: str | None
    description: str | None
    manifest_relative_path: str
    package_root: str
    sources_root: str
    runtime_manifest: str | None = None
    runtime_project_name: str | None = None
    runtime_import_root: str | None = None


@dataclass(frozen=True, slots=True)
class _OntologyRuntimeCodePackageSnapshot:
    role: str
    code_package_id: UUID
    object_instance_graph_commit_id: UUID
    package_name: str
    manifest_relative_path: str
    package_root: str
    sources_root: str
    import_root: str
    language: str
    path_count: int

    def bundle_ref(self) -> dict[str, object]:
        return {
            "role": self.role,
            "source_code_package_id": self.code_package_id,
            "source_object_instance_graph_commit_id": (
                self.object_instance_graph_commit_id
            ),
            "package_name": self.package_name,
            "manifest_relative_path": self.manifest_relative_path,
            "package_root": self.package_root,
            "sources_root": self.sources_root,
            "import_root": self.import_root,
            "language": self.language,
            "path_count": self.path_count,
        }


@dataclass(frozen=True, slots=True)
class _OntologyConfigCommitResult:
    ontology_config_id: UUID
    config_commit_id: UUID
    config_head_commit_id: UUID
    config_object_instance_graph_commit_id: UUID
    commit_perf_ms: Mapping[str, int]


@dataclass(frozen=True, slots=True)
class _OntologyPackageCommitResult:
    ontology_package_id: UUID
    package_commit_id: UUID
    package_head_commit_id: UUID
    package_object_instance_graph_commit_id: UUID
    commit_perf_ms: Mapping[str, int]


class _MetaRuntimeBindProtocol(Protocol):
    def bind(
        self,
        *,
        projection: str,
        branch_id: UUID,
        actor_id: UUID | None = None,
    ) -> MetaGraphBoundRuntimeLane: ...


class _MaterializationRuntimeBindProtocol(Protocol):
    def bind_materialization_lane(
        self,
        *,
        index: MetaGraphRuntimeIndex,
        projection: str,
        branch_id: UUID | None = None,
        actor_id: UUID | None = None,
    ) -> MetaGraphBoundRuntimeLane: ...


_OntologyPackageRuntimeBinder = (
    _MetaRuntimeBindProtocol | _MaterializationRuntimeBindProtocol
)


def _bind_ontology_package_runtime_lane(
    *,
    runtime: _OntologyPackageRuntimeBinder,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    branch_id: UUID,
) -> MetaGraphBoundRuntimeLane:
    if _has_meta_runtime_bind(runtime):
        return runtime.bind(
            projection="OntologyPackage",
            branch_id=branch_id,
            actor_id=actor_id,
        )

    if _has_materialization_runtime_bind(runtime):
        return runtime.bind_materialization_lane(
            index=index,
            projection="OntologyPackage",
            branch_id=branch_id,
            actor_id=actor_id,
        )

    raise RuntimeError(
        "OntologyPackage materialization requires a Meta runtime lane binder. "
        "Expected runtime.bind(...) or runtime.bind_materialization_lane(...)."
    )


def _has_meta_runtime_bind(
    runtime: _OntologyPackageRuntimeBinder,
) -> TypeGuard[_MetaRuntimeBindProtocol]:
    return callable(getattr(runtime, "bind", None))


def _has_materialization_runtime_bind(
    runtime: _OntologyPackageRuntimeBinder,
) -> TypeGuard[_MaterializationRuntimeBindProtocol]:
    return callable(getattr(runtime, "bind_materialization_lane", None))


def _required_uuid_attribute(value: object, name: str, *, label: str) -> UUID:
    attr = getattr(value, name, None)
    if isinstance(attr, UUID):
        return attr
    raise RuntimeError(f"{label} must be a UUID: {name}={attr!r}")


def _required_uuid_mapping_value(
    value: Mapping[object, object],
    name: str,
    *,
    label: str,
) -> UUID:
    raw_value = value.get(name)
    if isinstance(raw_value, UUID):
        return raw_value
    if isinstance(raw_value, str) and raw_value.strip():
        try:
            return UUID(raw_value)
        except ValueError as exc:
            raise RuntimeError(f"{label} must be a UUID: {name}={raw_value!r}") from exc
    raise RuntimeError(f"{label} must be a UUID: {name}={raw_value!r}")


async def materialize_delta(request: object) -> dict[str, object]:
    source = _resolve_ontology_delta_source(request=request)
    meta_baseline_ref = _meta_ocg_baseline_ref_from_ontology_delta_request(
        request=request,
        source=source,
    )
    meta_request = _meta_delta_request_from_ontology_request(
        request=request,
        source=source,
        meta_baseline_ref=meta_baseline_ref,
    )
    meta_result = await meta_workspace_provider.materialize_delta(request=meta_request)
    return _ontology_delta_result_from_meta_result(
        request=request,
        source=source,
        meta_baseline_ref=meta_baseline_ref,
        meta_result=meta_result,
    )


async def materialize(
    request: SemanticPackageMaterializationRequest,
) -> SemanticPackageMaterializationResult:
    started_at = perf_counter()
    source = _resolve_ontology_package_source(request=request)
    phase_timings_s: dict[str, float] = {}
    request_context = _request_context_with_execution_context_entries(request=request)

    dependency_started_at = perf_counter()
    external_graphs = _external_object_config_graphs_for_request(
        request=request,
        source=source,
        context=request_context,
    )
    phase_timings_s["resolve_dependency_graphs_s"] = _duration_s(dependency_started_at)

    leaf_started_at = perf_counter()
    materialize_leaf = (
        meta_service.materialize_object_config_graph_package_leaf_from_manifest
    )
    leaf_result = await materialize_leaf(
        runtime=request.runtime,
        index=request.index,
        actor_id=request.actor_id,
        branch_id=request.branch_id,
        workspace_root=request.workspace_root,
        aware_toml_path=source.source_manifest_path,
        source_code_package_id=request.source_code_package_id,
        external_graphs=list(external_graphs),
        collect_telemetry=_context_bool(
            request.context.get("ontology_semantic_package_collect_telemetry"),
            default=True,
        ),
        force_fresh_semantic_materialization=(
            _force_fresh_semantic_materialization_from_context(request.context)
        ),
        progress_callback=request.progress_callback,
    )
    phase_timings_s["materialize_meta_leaf_package_s"] = _duration_s(leaf_started_at)

    render_profile = _render_profile_from_request(request=request)
    language_started_at = perf_counter()
    if _should_materialize_language_outputs(render_profile=render_profile):
        if _should_skip_language_outputs_for_reused_leaf(leaf_result=leaf_result):
            language_bridge_details = (
                _skipped_reused_leaf_language_materialization_details(
                    render_profile=render_profile,
                    semantic_commit_strategy=leaf_result.semantic_commit_strategy,
                    artifact_evidence=(
                        _reused_leaf_language_artifact_evidence(
                            leaf_result=leaf_result,
                        )
                    ),
                )
            )
            materialized_language_packages = ()
        else:
            language_request = _meta_source_manifest_request_from_ontology_request(
                request=request,
                source=source,
            )
            language_bridge = await meta_workspace_provider.materialize_object_config_graph_package_leaf_language_outputs(
                request=language_request,
                leaf_result=leaf_result,
            )
            leaf_result = language_bridge.leaf_result
            language_bridge_details = _object_payload(language_bridge.details)
            materialized_language_packages = tuple(
                getattr(language_bridge, "materialized_language_packages", ()) or ()
            )
    else:
        language_bridge_details = _skipped_language_materialization_details(
            render_profile=render_profile,
        )
        materialized_language_packages = ()
    phase_timings_s["materialize_meta_language_outputs_s"] = _duration_s(
        language_started_at
    )

    ontology_config_projection_hash = find_meta_graph_projection_hash_by_name(
        index=request.index,
        projection_name="OntologyConfig",
    )
    ontology_package_projection_hash = find_meta_graph_projection_hash_by_name(
        index=request.index,
        projection_name="OntologyPackage",
    )
    code_package_projection_hash = find_meta_graph_projection_hash_by_name(
        index=request.index,
        projection_name="CodePackage",
    )
    config_commit_started_at = perf_counter()
    ontology_config_commit = await _commit_ontology_config_snapshot(
        index=request.index,
        actor_id=request.actor_id,
        branch_id=leaf_result.package_branch_id,
        projection_hash=ontology_config_projection_hash,
        source=source,
        leaf_result=leaf_result,
    )
    phase_timings_s["commit_ontology_config_snapshot_s"] = _duration_s(
        config_commit_started_at
    )
    for metric_name, metric_value in ontology_config_commit.commit_perf_ms.items():
        phase_timings_s[f"commit_ontology_config_snapshot.{metric_name}"] = (
            _duration_ms(metric_value)
        )
    runtime_package_started_at = perf_counter()
    runtime_code_package_snapshot = (
        await _commit_ontology_runtime_code_package_snapshot(
            index=request.index,
            actor_id=request.actor_id,
            source=source,
            projection_hash=code_package_projection_hash,
            workspace_root=request.workspace_root,
        )
    )
    phase_timings_s["commit_ontology_runtime_code_package_snapshot_s"] = _duration_s(
        runtime_package_started_at
    )
    commit_started_at = perf_counter()
    ontology_commit = await _commit_ontology_package_snapshot(
        runtime=request.runtime,
        index=request.index,
        actor_id=request.actor_id,
        branch_id=leaf_result.package_branch_id,
        projection_hash=ontology_package_projection_hash,
        source=source,
        leaf_result=leaf_result,
        ontology_config_commit=ontology_config_commit,
        runtime_code_package_snapshot=runtime_code_package_snapshot,
    )
    phase_timings_s["commit_ontology_package_snapshot_s"] = _duration_s(
        commit_started_at
    )
    for metric_name, metric_value in ontology_commit.commit_perf_ms.items():
        phase_timings_s[f"commit_ontology_package_snapshot.{metric_name}"] = (
            _duration_ms(metric_value)
        )
    phase_timings_s["total_s"] = _duration_s(started_at)

    semantic_key = f"{source.package_name}:{source.fqn_prefix}"
    runtime_graph = _target_runtime_object_config_graph_from_context(
        context=request_context,
        source=source,
    ) or _target_runtime_object_config_graph_from_manifest_closure(
        request=request,
        source=source,
        context=request_context,
    )
    runtime_bundle_graph = runtime_graph or leaf_result.object_config_graph
    runtime_projection_descriptors = _runtime_projection_descriptors_for_ocg(
        runtime_bundle_graph
    )
    details = {
        "schema": _ONTOLOGY_PROVIDER_SCHEMA,
        "provider_key": "aware_ontology",
        "semantic_owner": _ONTOLOGY_PROVIDER_OWNER,
        "manifest_path": source.ontology_toml_path.as_posix(),
        "source_manifest_path": source.source_manifest_path.as_posix(),
        "package_name": source.package_name,
        "fqn_prefix": source.fqn_prefix,
        "version_number": source.version_number,
        "title": source.title,
        "description": source.description,
        "semantic_branch_id": str(leaf_result.package_branch_id),
        "ontology_config_id": str(ontology_config_commit.ontology_config_id),
        "ontology_config_commit_id": str(ontology_config_commit.config_commit_id),
        "ontology_config_head_commit_id": str(
            ontology_config_commit.config_head_commit_id
        ),
        "ontology_config_object_instance_graph_commit_id": str(
            ontology_config_commit.config_object_instance_graph_commit_id
        ),
        "ontology_package_id": str(ontology_commit.ontology_package_id),
        "ontology_package_commit_id": str(ontology_commit.package_commit_id),
        "ontology_package_head_commit_id": str(ontology_commit.package_head_commit_id),
        "ontology_package_object_instance_graph_commit_id": str(
            ontology_commit.package_object_instance_graph_commit_id
        ),
        "materialized_semantic_roots": (
            {
                "semantic_root_kind": "OntologyConfig",
                "semantic_projection_name": "OntologyConfig",
                "semantic_projection_hash": ontology_config_projection_hash,
                "semantic_package_id": str(ontology_config_commit.ontology_config_id),
                "semantic_root_id": str(ontology_config_commit.ontology_config_id),
                "semantic_head_commit_id": str(
                    ontology_config_commit.config_head_commit_id
                ),
                "semantic_object_instance_graph_commit_id": str(
                    ontology_config_commit.config_object_instance_graph_commit_id
                ),
                "semantic_root_object_instance_graph_commit_id": str(
                    ontology_config_commit.config_object_instance_graph_commit_id
                ),
            },
            {
                "semantic_root_kind": "OntologyPackage",
                "semantic_projection_name": "OntologyPackage",
                "semantic_projection_hash": ontology_package_projection_hash,
                "semantic_package_id": str(ontology_commit.ontology_package_id),
                "semantic_root_id": str(ontology_commit.ontology_package_id),
                "semantic_head_commit_id": str(ontology_commit.package_head_commit_id),
                "semantic_object_instance_graph_commit_id": str(
                    ontology_commit.package_object_instance_graph_commit_id
                ),
                "semantic_root_object_instance_graph_commit_id": str(
                    ontology_commit.package_object_instance_graph_commit_id
                ),
            },
        ),
        "source_code_package_id": str(leaf_result.code_package.id),
        "source_code_package_commit_id": _uuid_string(
            leaf_result.code_package_commit_id
        ),
        "source_code_package_head_commit_id": _uuid_string(
            leaf_result.code_package_head_commit_id
        ),
        "source_code_package_object_instance_graph_commit_id": (
            _uuid_string(leaf_result.code_package_object_instance_graph_commit_id)
        ),
        "runtime_code_package_refs": (
            [runtime_code_package_snapshot.bundle_ref()]
            if runtime_code_package_snapshot is not None
            else []
        ),
        "object_config_graph_id": str(leaf_result.object_config_graph.id),
        "object_config_graph_hash": leaf_result.object_config_graph.hash,
        "opg_hashes": [
            descriptor["projection_hash"]
            for descriptor in runtime_projection_descriptors
            if descriptor.get("projection_hash") is not None
        ],
        "runtime_projection_descriptors": runtime_projection_descriptors,
        "object_config_graph_commit_id": _uuid_string(
            leaf_result.object_config_graph_commit_id
        ),
        "object_config_graph_head_commit_id": _uuid_string(
            leaf_result.object_config_graph_head_commit_id
        ),
        "object_config_graph_object_instance_graph_commit_id": (
            _uuid_string(_leaf_ocg_oig_commit_id(leaf_result))
        ),
        "object_config_graph_package_id": str(
            leaf_result.object_config_graph_package.id
        ),
        "object_config_graph_package_commit_id": _uuid_string(
            leaf_result.object_config_graph_package_commit_id
        ),
        "object_config_graph_package_head_commit_id": _uuid_string(
            leaf_result.object_config_graph_package_head_commit_id
        ),
        "object_config_graph_package_object_instance_graph_commit_id": (
            _uuid_string(_leaf_ocg_package_oig_commit_id(leaf_result))
        ),
        "semantic_commit_strategy": leaf_result.semantic_commit_strategy,
        "semantic_commit_fallback_reset": (leaf_result.semantic_commit_fallback_reset),
        "meta_leaf_phase_timings_s": dict(
            sorted(_object_payload(getattr(leaf_result, "phase_timings_s", {})).items())
        ),
        "meta_leaf_semantic_commit_phase_timings_s": dict(
            sorted(
                _object_payload(
                    getattr(leaf_result, "semantic_commit_phase_timings_s", {})
                ).items()
            )
        ),
        "meta_language_materialization_bridge": {
            "provider_key": "aware_meta",
            "status": _meta_language_materialization_bridge_status(
                details=language_bridge_details,
                default="completed",
            ),
            "render_profile": render_profile,
            "materialized_language_package_count": len(materialized_language_packages),
        },
        **_meta_language_materialization_bridge_details(language_bridge_details),
        **_runtime_bundle_manifest_details(
            source=source,
            leaf_result=leaf_result,
            runtime_graph=runtime_bundle_graph,
            external_graphs=external_graphs,
        ),
        "phase_timings_s": dict(sorted(phase_timings_s.items())),
    }
    artifact_set = build_ontology_runtime_artifact_set_from_materialization_details(
        details=details,
    )
    details[ONTOLOGY_RUNTIME_ARTIFACT_SET_OUTPUT_KEY] = artifact_set
    details["artifact_ownership_receipts"] = (
        *tuple(
            receipt
            for receipt in details.get("artifact_ownership_receipts", ())
            if isinstance(receipt, Mapping)
        ),
        build_ontology_runtime_artifact_set_ownership_receipt(
            artifact_set=artifact_set,
        ),
    )
    return SemanticPackageMaterializationResult(
        details=details,
        bundle_packages=(
            SemanticPackageMaterializationBundle(
                package_key=source.package_name,
                manifest_toml_path=source.ontology_toml_path,
                semantic_package_id=ontology_config_commit.ontology_config_id,
                semantic_root_id=ontology_config_commit.ontology_config_id,
                semantic_branch_id=leaf_result.package_branch_id,
                semantic_head_commit_id=ontology_config_commit.config_head_commit_id,
                semantic_object_instance_graph_commit_id=(
                    ontology_config_commit.config_object_instance_graph_commit_id
                ),
                semantic_root_object_instance_graph_commit_id=(
                    ontology_config_commit.config_object_instance_graph_commit_id
                ),
                semantic_root_kind="OntologyConfig",
                semantic_projection_name="OntologyConfig",
                semantic_projection_hash=ontology_config_projection_hash,
                source_code_package_id=leaf_result.code_package.id,
                source_object_instance_graph_commit_id=(
                    leaf_result.code_package_object_instance_graph_commit_id
                ),
            ),
            SemanticPackageMaterializationBundle(
                package_key=source.package_name,
                manifest_toml_path=source.ontology_toml_path,
                semantic_package_id=ontology_commit.ontology_package_id,
                semantic_root_id=ontology_commit.ontology_package_id,
                semantic_branch_id=leaf_result.package_branch_id,
                semantic_head_commit_id=ontology_commit.package_head_commit_id,
                semantic_object_instance_graph_commit_id=(
                    ontology_commit.package_object_instance_graph_commit_id
                ),
                semantic_root_object_instance_graph_commit_id=(
                    ontology_commit.package_object_instance_graph_commit_id
                ),
                semantic_root_kind="OntologyPackage",
                semantic_projection_name="OntologyPackage",
                semantic_projection_hash=ontology_package_projection_hash,
                source_code_package_id=leaf_result.code_package.id,
                source_object_instance_graph_commit_id=(
                    leaf_result.code_package_object_instance_graph_commit_id
                ),
                runtime_code_package_refs=(
                    (runtime_code_package_snapshot.bundle_ref(),)
                    if runtime_code_package_snapshot is not None
                    else ()
                ),
            ),
        ),
        mode="full_rebuild",
        affected_semantic_keys=(semantic_key,),
        applied_semantic_keys=(semantic_key,),
        stale_semantic_keys=(),
        fallback_reason=(
            "Ontology provider delegated raw ObjectConfigGraph package "
            "materialization to the Meta leaf materializer and sealed "
            "ontology-owned OntologyConfig and OntologyPackage snapshots."
        ),
        commit_id=ontology_commit.package_commit_id,
        head_commit_id=ontology_commit.package_head_commit_id,
        semantic_object_config_graphs=(leaf_result.object_config_graph,),
    )


def _meta_language_materialization_bridge_details(
    details: Mapping[str, object],
) -> dict[str, object]:
    bridge_keys = (
        "language_materialization_status",
        "language_materialization_skip_reason",
        "language_materialization_reuse_strategy",
        "language_artifact_completeness_status",
        "language_artifact_completeness_reason",
        "language_artifact_completeness_target_count",
        "language_artifact_completeness_package_count",
        "requested_render_profile",
        "owned_file_paths",
        "lifecycle_receipts",
        "materialization_index_receipts",
        "artifact_ownership_receipts",
        "language_post_step_receipts",
        "language_materialization_tool_step_receipts",
        "language_materialization_code_package_refs",
        "generated_code_package_deltas",
        "language_materialization_code_package_deltas",
        "materialized_language_packages",
        "materialized_language_package_count",
        "language_materialization_tool_timings_s",
        "language_materialization_runtime_to_language_cache",
        "compile_parity_receipts",
    )
    return {key: details[key] for key in bridge_keys if key in details}


def _runtime_bundle_manifest_details(
    *,
    source: _OntologyPackageSource,
    leaf_result: ObjectConfigGraphPackageLeafMaterializationResult,
    runtime_graph: ObjectConfigGraph | None = None,
    external_graphs: tuple[ObjectConfigGraph, ...] = (),
) -> dict[str, object]:
    manifest_path = (
        source.source_manifest_path.parent / ONTOLOGY_RUNTIME_BUNDLE_RELATIVE_PATH
    ).resolve()
    workspace_relative_path = (
        f"{source.package_root.rstrip('/')}/{ONTOLOGY_RUNTIME_BUNDLE_RELATIVE_PATH}"
    )
    bundle = write_ontology_runtime_bundle(
        output_dir=manifest_path.parent,
        env_id=_leaf_object_config_graph_id(leaf_result=leaf_result),
        env_title=source.title or source.package_name,
        env_canonical_language=CodeLanguage.aware,
        aware_root=source.source_manifest_path.parent,
        canonical_graph=runtime_graph or leaf_result.object_config_graph,
        binding_graph=runtime_graph or leaf_result.object_config_graph,
        external_graphs=external_graphs,
        environment_service_provider_modules=(
            _runtime_handler_provider_modules(source=source)
        ),
        function_impl_policy=_ontology_package_function_impl_policy(source=source),
    )
    if bundle.manifest_path != manifest_path:
        raise RuntimeError(
            "Ontology runtime bundle writer returned unexpected manifest path: "
            f"expected={manifest_path} actual={bundle.manifest_path}"
        )
    details: dict[str, object] = {
        "runtime_bundle_manifest_path": manifest_path.as_posix(),
        "runtime_bundle_manifest_workspace_relative_path": workspace_relative_path,
    }
    payload = manifest_path.read_bytes()
    db_schema_registry_payload = (
        bundle.db_schema_registry_path.read_bytes()
        if bundle.db_schema_registry_path is not None
        else None
    )
    python_models_manifest_path = _python_models_manifest_path(
        source_root=source.source_manifest_path.parent,
    )
    python_models_manifest_payload = (
        python_models_manifest_path.read_bytes()
        if python_models_manifest_path is not None
        else None
    )
    details.update(
        {
            "runtime_bundle_manifest_status": "available",
            "runtime_bundle_manifest_digest": "sha256:" + sha256(payload).hexdigest(),
            "runtime_bundle_manifest_size_bytes": len(payload),
            "runtime_bundle_manifest_artifact_count": bundle.artifact_count,
            "runtime_bundle_contract_path": bundle.contract_path.as_posix(),
            "runtime_bundle_db_schema_registry_path": (
                bundle.db_schema_registry_path.as_posix()
                if bundle.db_schema_registry_path is not None
                else None
            ),
            "runtime_bundle_db_schema_registry_workspace_relative_path": (
                (
                    Path(workspace_relative_path).parent / "db.schema.registry.json"
                ).as_posix()
                if bundle.db_schema_registry_path is not None
                else None
            ),
            "runtime_bundle_db_schema_registry_digest": (
                "sha256:" + sha256(db_schema_registry_payload).hexdigest()
                if db_schema_registry_payload is not None
                else None
            ),
            "runtime_bundle_db_schema_registry_sql_roots": (
                _db_schema_registry_sql_roots(
                    bundle.db_schema_registry_path,
                )
                if bundle.db_schema_registry_path is not None
                else ()
            ),
            "python_models_manifest_path": (
                python_models_manifest_path.as_posix()
                if python_models_manifest_path is not None
                else None
            ),
            "python_models_manifest_workspace_relative_path": (
                (
                    Path(source.package_root.rstrip("/"))
                    / "python"
                    / "orm_runtime"
                    / ".aware"
                    / "materializations"
                    / "python.models.json"
                ).as_posix()
                if python_models_manifest_path is not None
                else None
            ),
            "python_models_manifest_status": (
                "available" if python_models_manifest_path is not None else "missing"
            ),
            "python_models_manifest_digest": (
                "sha256:" + sha256(python_models_manifest_payload).hexdigest()
                if python_models_manifest_payload is not None
                else None
            ),
            "python_models_manifest_size_bytes": (
                len(python_models_manifest_payload)
                if python_models_manifest_payload is not None
                else None
            ),
            "python_models_manifest_error": (
                None
                if python_models_manifest_path is not None
                else "python models manifest missing"
            ),
        }
    )
    return details


def _runtime_handler_provider_modules(
    *,
    source: _OntologyPackageSource,
) -> tuple[str, ...]:
    import_root = _non_empty_string(source.runtime_import_root)
    if import_root is None:
        return ()
    return (f"{import_root}.handlers._generated.meta_handlers",)


def _python_models_manifest_path(*, source_root: Path) -> Path | None:
    candidates = (
        source_root / ".aware" / "materializations" / "python.models.json",
        source_root
        / "python"
        / "orm_runtime"
        / ".aware"
        / "materializations"
        / "python.models.json",
        source_root / "python" / ".aware" / "materializations" / "python.models.json",
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    return None


def _db_schema_registry_sql_roots(path: Path) -> tuple[str, ...]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    entries = payload.get("entries")
    if not isinstance(entries, list):
        return ()
    sql_roots: list[str] = []
    for entry in entries:
        if not isinstance(entry, Mapping):
            continue
        sql_root = _non_empty_string(entry.get("sql_root"))
        if sql_root is not None:
            sql_roots.append(sql_root)
    return tuple(dict.fromkeys(sql_roots))


def _leaf_object_config_graph_id(
    *,
    leaf_result: ObjectConfigGraphPackageLeafMaterializationResult,
) -> UUID:
    graph_id = getattr(getattr(leaf_result, "object_config_graph", None), "id", None)
    if isinstance(graph_id, UUID):
        return graph_id
    if graph_id is not None:
        return UUID(str(graph_id))
    raise RuntimeError("Ontology runtime bundle production requires OCG id.")


def _ontology_package_function_impl_policy(
    *,
    source: _OntologyPackageSource,
) -> dict[str, str]:
    package_spec = load_aware_toml_spec(toml_path=source.source_manifest_path)
    package = getattr(package_spec, "package", None)
    return {
        "ownership": str(getattr(package, "function_impl_ownership", "authored")),
        "parity_policy": str(getattr(package, "function_impl_parity_policy", "off")),
    }


def _render_profile_from_request(
    *,
    request: SemanticPackageMaterializationRequest,
) -> str:
    profile = _object_payload(
        request.context.get(SEMANTIC_MATERIALIZATION_LIFECYCLE_PROFILE_CONTEXT_KEY)
    )
    render_profile = _non_empty_string(profile.get("render_profile"))
    return render_profile or "compile_parity"


def _should_materialize_language_outputs(*, render_profile: str) -> bool:
    return render_profile == "compile_parity"


def _should_skip_language_outputs_for_reused_leaf(*, leaf_result: object) -> bool:
    strategy = str(getattr(leaf_result, "semantic_commit_strategy", "") or "").strip()
    if strategy not in {"fingerprint_reuse", "unchanged"}:
        return False
    return (
        getattr(leaf_result, "object_config_graph_package_head_commit_id", None)
        is not None
        and getattr(leaf_result, "object_config_graph_head_commit_id", None) is not None
        and getattr(leaf_result, "code_package_head_commit_id", None) is not None
        and _reused_leaf_language_artifact_evidence(leaf_result=leaf_result)["status"]
        == "complete"
    )


def _reused_leaf_language_artifact_evidence(
    *,
    leaf_result: object,
) -> dict[str, object]:
    package = getattr(leaf_result, "object_config_graph_package", None)
    materializations = tuple(getattr(package, "language_materializations", ()) or ())
    if not materializations:
        return {
            "status": "incomplete",
            "reason": "language_materializations_missing",
            "target_count": 0,
            "package_count": 0,
        }
    package_count = 0
    for materialization in materializations:
        materialized_packages = tuple(
            getattr(materialization, "materialized_packages", ()) or ()
        )
        if not materialized_packages:
            return {
                "status": "incomplete",
                "reason": "materialized_packages_missing",
                "target_count": len(materializations),
                "package_count": package_count,
            }
        for materialized_package in materialized_packages:
            package_count += 1
            status = _non_empty_string(getattr(materialized_package, "status", None))
            if status not in _COMPLETE_LANGUAGE_PACKAGE_STATUSES:
                return {
                    "status": "incomplete",
                    "reason": "materialized_package_status_incomplete",
                    "target_count": len(materializations),
                    "package_count": package_count,
                }
            required_values = (
                getattr(materialized_package, "code_package_id", None),
                getattr(
                    materialized_package,
                    "object_config_graph_object_instance_graph_commit_id",
                    None,
                ),
                getattr(
                    materialized_package,
                    "code_package_object_instance_graph_commit_id",
                    None,
                ),
            )
            if any(value is None for value in required_values):
                return {
                    "status": "incomplete",
                    "reason": "materialized_package_commit_evidence_missing",
                    "target_count": len(materializations),
                    "package_count": package_count,
                }
    return {
        "status": "complete",
        "reason": "materialized_language_packages_present",
        "target_count": len(materializations),
        "package_count": package_count,
    }


def _skipped_reused_leaf_language_materialization_details(
    *,
    render_profile: str,
    semantic_commit_strategy: str,
    artifact_evidence: Mapping[str, object],
) -> dict[str, object]:
    details = _skipped_language_materialization_details(
        render_profile=render_profile,
    )
    details["language_materialization_skip_reason"] = "semantic_leaf_reused"
    details["language_materialization_reuse_strategy"] = semantic_commit_strategy
    details["language_artifact_completeness_status"] = artifact_evidence.get("status")
    details["language_artifact_completeness_reason"] = artifact_evidence.get("reason")
    details["language_artifact_completeness_target_count"] = artifact_evidence.get(
        "target_count"
    )
    details["language_artifact_completeness_package_count"] = artifact_evidence.get(
        "package_count"
    )
    return details


def _meta_source_manifest_request_from_ontology_request(
    *,
    request: SemanticPackageMaterializationRequest,
    source: _OntologyPackageSource,
) -> SemanticPackageMaterializationRequest:
    return replace(request, manifest_path=source.source_manifest_path)


def _skipped_language_materialization_details(
    *,
    render_profile: str,
) -> dict[str, object]:
    return {
        "language_materialization_status": "skipped",
        "language_materialization_skip_reason": ("render_profile_not_compile_parity"),
        "requested_render_profile": render_profile,
        "owned_file_paths": (),
        "lifecycle_receipts": (),
        "materialization_index_receipts": (),
        "artifact_ownership_receipts": (),
        "language_post_step_receipts": (),
        "language_materialization_tool_step_receipts": (),
        "language_materialization_code_package_refs": (),
        "materialized_language_packages": (),
        "materialized_language_package_count": 0,
        "language_materialization_tool_timings_s": {},
        "language_materialization_runtime_to_language_cache": {},
        "compile_parity_receipts": (),
    }


def _meta_language_materialization_bridge_status(
    *,
    details: Mapping[str, object],
    default: str,
) -> str:
    status = _non_empty_string(details.get("language_materialization_status"))
    return status or default


def _runtime_projection_descriptors_for_ocg(
    ocg: ObjectConfigGraph,
) -> list[dict[str, object]]:
    edge_to_function_id: dict[object, object] = {}
    for node in getattr(ocg, "object_config_graph_nodes", ()) or ():
        class_config = getattr(node, "class_config", None)
        if class_config is None:
            continue
        for link in getattr(class_config, "class_config_function_configs", ()) or ():
            function_config = getattr(link, "function_config", None)
            function_id = getattr(function_config, "id", None)
            link_id = getattr(link, "id", None)
            if link_id is not None and function_id is not None:
                edge_to_function_id[link_id] = function_id

    opgs = tuple(getattr(ocg, "object_projection_graphs", ()) or ())
    opg_hashes = sorted(
        str(projection_hash)
        for opg in opgs
        for projection_hash in (getattr(opg, "projection_hash", None),)
        if projection_hash is not None
    )
    descriptors: list[dict[str, object]] = []
    for opg in opgs:
        constructor_function_ids = sorted(
            str(edge_to_function_id[function_edge_id])
            for constructor in (
                getattr(opg, "object_projection_graph_constructors", ()) or ()
            )
            for function_edge_id in (
                getattr(constructor, "function_constructor_id", None),
            )
            if function_edge_id in edge_to_function_id
        )
        projection_hash = getattr(opg, "projection_hash", None)
        descriptors.append(
            {
                "projection_name": getattr(opg, "name", None),
                "projection_hash": (
                    str(projection_hash) if projection_hash is not None else None
                ),
                "object_projection_graph_id": _uuid_string(getattr(opg, "id", None)),
                "constructor_function_id": (
                    constructor_function_ids[0] if constructor_function_ids else None
                ),
                "object_config_graph_id": _uuid_string(getattr(ocg, "id", None)),
                "opg_hashes": opg_hashes,
                "required_for": ["runtime_index", "service_boot"],
                "metadata": {
                    "supports_virtual_build": getattr(
                        opg,
                        "supports_virtual_build",
                        None,
                    ),
                },
            }
        )
    return sorted(
        descriptors,
        key=lambda descriptor: (
            str(descriptor.get("projection_name") or ""),
            str(descriptor.get("projection_hash") or ""),
        ),
    )


def _resolve_ontology_delta_source(*, request: object) -> _OntologyPackageSource:
    package_payload = _object_payload(_request_attr(request, "package"))
    manifest_text = _non_empty_string(package_payload.get("manifest_path"))
    if manifest_text is None:
        raise RuntimeError("Ontology provider delta request missing manifest_path.")
    manifest_path = Path(manifest_text).expanduser()
    workspace_root = _delta_workspace_root(request=request, manifest_path=manifest_path)
    if not manifest_path.is_absolute():
        manifest_path = workspace_root / manifest_path
    return _resolve_ontology_package_source_from_path(
        workspace_root=workspace_root,
        ontology_toml_path=manifest_path.resolve(),
    )


def _meta_delta_request_from_ontology_request(
    *,
    request: object,
    source: _OntologyPackageSource,
    meta_baseline_ref: Mapping[str, object],
) -> object:
    fields = _request_fields(request=request)
    package_payload = _object_payload(fields.get("package"))
    package_payload.update(
        {
            "manifest_path": source.source_manifest_path.as_posix(),
            "workspace_manifest_kind": "module_package",
        }
    )
    fields["package"] = SimpleNamespace(**package_payload)
    fields["semantic_contract"] = SimpleNamespace(
        module=_META_DELTA_CONTRACT_MODULE,
        provider_key=_META_DELTA_PROVIDER_KEY,
        role=_META_DELTA_PROVIDER_ROLE,
        name=_META_DELTA_CONTRACT_NAME,
    )
    code_package_delta = _meta_code_package_delta_from_ontology_delta(
        value=fields.get("code_package_delta"),
        source=source,
    )
    if code_package_delta is not None:
        fields["code_package_delta"] = code_package_delta
    fields["baseline_ref"] = dict(meta_baseline_ref)
    fields["baseline_source_object_instance_graph_commit_id"] = _non_empty_string(
        meta_baseline_ref.get("source_object_instance_graph_commit_id")
    )
    fields["baseline_semantic_object_instance_graph_commit_id"] = _non_empty_string(
        meta_baseline_ref.get("semantic_object_instance_graph_commit_id")
    )
    fields["baseline_semantic_root_object_instance_graph_commit_id"] = (
        _non_empty_string(
            meta_baseline_ref.get("semantic_root_object_instance_graph_commit_id")
        )
    )
    fields["previous_materialization_evidence"] = (
        _meta_previous_materialization_evidence(
            request=request,
            source=source,
            meta_baseline_ref=meta_baseline_ref,
        )
    )
    fields["context"] = _meta_delta_context_from_ontology_request(
        request=request,
        meta_baseline_ref=meta_baseline_ref,
    )
    if "semantic_function_call_execution_context" in fields:
        fields["semantic_function_call_execution_context"] = fields["context"]
    return SimpleNamespace(**fields)


def _meta_code_package_delta_from_ontology_delta(
    *,
    value: object,
    source: _OntologyPackageSource,
) -> object | None:
    if value is None:
        return None
    delta = (
        value
        if isinstance(value, CodePackageDelta)
        else CodePackageDelta.model_validate(value)
    )
    paths = [
        path.model_copy(
            update={
                "relative_path": _meta_delta_source_relative_path(
                    relative_path=path.relative_path,
                    source=source,
                    source_delta_package_root=delta.package_root,
                ),
            }
        )
        for path in delta.paths
    ]
    return delta.model_copy(
        update={
            "package_name": source.package_name,
            "package_root": source.package_root,
            "sources_root": _meta_delta_sources_root(source=source),
            "manifest_relative_path": _meta_delta_manifest_relative_path(
                source=source,
            ),
            "paths": paths,
        }
    )


def _meta_delta_source_relative_path(
    *,
    relative_path: str,
    source: _OntologyPackageSource,
    source_delta_package_root: str,
) -> str:
    normalized = relative_path.strip().strip("/")
    package_root = source.package_root.strip().strip("/")
    if package_root and package_root != ".":
        prefix = f"{package_root}/"
        if normalized.startswith(prefix):
            return normalized.removeprefix(prefix)
        delta_package_root = source_delta_package_root.strip().strip("/")
        if delta_package_root and delta_package_root != ".":
            workspace_relative = f"{delta_package_root}/{normalized}"
            if workspace_relative.startswith(prefix):
                return workspace_relative.removeprefix(prefix)
    return normalized


def _meta_delta_sources_root(*, source: _OntologyPackageSource) -> str:
    package_root = source.package_root.strip().strip("/")
    sources_root = source.sources_root.strip().strip("/")
    if package_root and package_root != ".":
        prefix = f"{package_root}/"
        if sources_root.startswith(prefix):
            return sources_root.removeprefix(prefix)
    return sources_root


def _meta_delta_manifest_relative_path(*, source: _OntologyPackageSource) -> str:
    manifest_path = source.manifest_relative_path.strip().strip("/")
    package_root = source.package_root.strip().strip("/")
    if package_root and package_root != ".":
        prefix = f"{package_root}/"
        if manifest_path.startswith(prefix):
            return manifest_path.removeprefix(prefix)
    return manifest_path


def _meta_previous_materialization_evidence(
    *,
    request: object,
    source: _OntologyPackageSource,
    meta_baseline_ref: Mapping[str, object],
) -> dict[str, object]:
    evidence = _object_payload(
        _request_attr(request, "previous_materialization_evidence")
    )
    evidence["baseline_ref"] = dict(meta_baseline_ref)
    evidence["commit_refs"] = _meta_commit_refs_from_baseline_ref(
        baseline_ref=meta_baseline_ref,
    )
    baseline_index = _meta_baseline_semantic_object_index_from_package_index(
        workspace_root=_delta_workspace_root(
            request=request,
            manifest_path=source.ontology_toml_path,
        ),
        source=source,
    )
    if baseline_index:
        evidence["baseline_semantic_object_index"] = baseline_index
    return evidence


def _meta_delta_context_from_ontology_request(
    *,
    request: object,
    meta_baseline_ref: Mapping[str, object],
) -> dict[str, object]:
    context = _object_payload(_request_attr(request, "context"))
    context["required_projection_names"] = tuple(
        META_MATERIALIZATION_REQUIRED_PROJECTIONS
    )
    context["runtime_ontology_package_names"] = tuple(
        META_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES
    )
    durable_inputs = _object_payload(
        context.get(SEMANTIC_PROVIDER_DELTA_DURABLE_EXECUTION_INPUTS_KEY)
    )
    durable_inputs.update(
        _meta_durable_input_refs_from_baseline_ref(
            baseline_ref=meta_baseline_ref,
        )
    )
    durable_inputs["provider_key"] = _META_DELTA_PROVIDER_KEY
    durable_inputs["semantic_owner"] = _META_DELTA_PROVIDER_ROLE
    durable_inputs["provider_inputs"] = {}
    context[SEMANTIC_PROVIDER_DELTA_DURABLE_EXECUTION_INPUTS_KEY] = durable_inputs
    return context


def _meta_ocg_baseline_ref_from_ontology_delta_request(
    *,
    request: object,
    source: _OntologyPackageSource,
) -> dict[str, object]:
    original_ref = _object_payload(_request_attr(request, "baseline_ref"))
    lane_state = _object_payload(_request_attr(request, "provider_delta_lane_state"))
    lane_package = _object_payload(lane_state.get("package"))
    evidence = _object_payload(
        _request_attr(request, "previous_materialization_evidence")
    )
    ocg_evidence = _first_mapping_with_keys(
        evidence,
        keys=(
            "object_config_graph_package_id",
            "object_config_graph_package_object_instance_graph_commit_id",
        ),
    )
    projection_hash = _first_nested_text(
        evidence,
        path=("lane_projection_hashes", "object_config_graph"),
    )
    workspace_root = _delta_workspace_root(
        request=request,
        manifest_path=source.ontology_toml_path,
    )
    indexed_baseline = _meta_ocg_baseline_from_package_index(
        workspace_root=workspace_root,
        source=source,
    )
    latest_delta_baseline = _meta_ocg_delta_baseline_from_original_ref(
        original_ref=original_ref,
    )
    source_oig_commit_id = (
        _non_empty_string(lane_state.get("source_object_instance_graph_commit_id"))
        or _non_empty_string(lane_package.get("source_object_instance_graph_commit_id"))
        or _non_empty_string(
            ocg_evidence.get("source_code_package_object_instance_graph_commit_id")
        )
        or _non_empty_string(original_ref.get("source_object_instance_graph_commit_id"))
        or _uuid_string(
            None
            if indexed_baseline is None
            else indexed_baseline.source_object_instance_graph_commit_id
        )
    )
    source_code_package_id = (
        _non_empty_string(lane_state.get("source_code_package_id"))
        or _non_empty_string(lane_package.get("source_code_package_id"))
        or _non_empty_string(ocg_evidence.get("source_code_package_id"))
        or _non_empty_string(original_ref.get("source_code_package_id"))
    )
    semantic_branch_id = (
        _non_empty_string(latest_delta_baseline.get("semantic_branch_id"))
        or _non_empty_string(original_ref.get("semantic_branch_id"))
        or _non_empty_string(lane_state.get("semantic_branch_id"))
        or _uuid_string(
            stable_meta_runtime_package_branch_id(
                workspace_root=workspace_root,
                aware_toml_path=source.source_manifest_path,
                package_name=source.package_name,
                fqn_prefix=source.fqn_prefix,
            )
        )
    )
    return {
        **original_ref,
        "source": "aware_ontology.provider_delta_meta_ocg_bridge",
        "manifest_path": source.source_manifest_path.as_posix(),
        "manifest_toml_path": source.source_manifest_path.as_posix(),
        "semantic_contract_module": _META_DELTA_CONTRACT_MODULE,
        "semantic_contract_name": _META_DELTA_CONTRACT_NAME,
        "semantic_contract_provider_key": _META_DELTA_PROVIDER_KEY,
        "semantic_contract_role": _META_DELTA_PROVIDER_ROLE,
        "semantic_owner_module": _META_DELTA_PROVIDER_KEY,
        "semantic_provider_key": _META_DELTA_PROVIDER_KEY,
        "semantic_package_kind": "object_config_graph_package",
        "semantic_package_name": source.package_name,
        "semantic_branch_id": semantic_branch_id,
        "semantic_projection_name": _META_DELTA_BASELINE_PROJECTION_NAME,
        "semantic_projection_hash": (
            _non_empty_string(latest_delta_baseline.get("semantic_projection_hash"))
            or projection_hash
        ),
        "semantic_root_kind": "object_config_graph",
        "semantic_package_id": _non_empty_string(
            latest_delta_baseline.get("semantic_package_id")
        )
        or _non_empty_string(ocg_evidence.get("object_config_graph_package_id"))
        or _uuid_string(
            None if indexed_baseline is None else indexed_baseline.object_id
        ),
        "semantic_package_commit_id": (
            _non_empty_string(latest_delta_baseline.get("semantic_package_commit_id"))
            or _non_empty_string(
                ocg_evidence.get("object_config_graph_package_head_commit_id")
            )
            or _non_empty_string(
                ocg_evidence.get("object_config_graph_package_commit_id")
            )
            or _uuid_string(
                None
                if indexed_baseline is None
                else (
                    indexed_baseline.semantic_package_head_commit_id
                    or indexed_baseline.semantic_package_object_instance_graph_commit_id
                )
            )
        ),
        "semantic_object_instance_graph_commit_id": (
            _non_empty_string(
                latest_delta_baseline.get("semantic_object_instance_graph_commit_id")
            )
            or _non_empty_string(ocg_evidence.get("object_config_graph_head_commit_id"))
            or _non_empty_string(ocg_evidence.get("object_config_graph_commit_id"))
            or _uuid_string(
                None
                if indexed_baseline is None
                else indexed_baseline.semantic_root_head_commit_id
            )
        ),
        "semantic_package_object_instance_graph_commit_id": _non_empty_string(
            latest_delta_baseline.get(
                "semantic_package_object_instance_graph_commit_id"
            )
        )
        or _non_empty_string(
            ocg_evidence.get(
                "object_config_graph_package_object_instance_graph_commit_id"
            )
        )
        or _uuid_string(
            None
            if indexed_baseline is None
            else indexed_baseline.semantic_package_object_instance_graph_commit_id
        ),
        "semantic_root_commit_id": (
            _non_empty_string(latest_delta_baseline.get("semantic_root_commit_id"))
            or _non_empty_string(ocg_evidence.get("object_config_graph_head_commit_id"))
            or _uuid_string(
                None
                if indexed_baseline is None
                else indexed_baseline.semantic_root_head_commit_id
            )
        ),
        "semantic_root_id": _non_empty_string(
            latest_delta_baseline.get("semantic_root_id")
        )
        or _non_empty_string(ocg_evidence.get("object_config_graph_id"))
        or _uuid_string(
            None
            if indexed_baseline is None
            else indexed_baseline.object_config_graph_id
        ),
        "semantic_root_object_instance_graph_commit_id": _non_empty_string(
            latest_delta_baseline.get("semantic_root_object_instance_graph_commit_id")
        )
        or _non_empty_string(
            ocg_evidence.get("object_config_graph_object_instance_graph_commit_id")
        )
        or _uuid_string(
            None
            if indexed_baseline is None
            else indexed_baseline.semantic_root_object_instance_graph_commit_id
        ),
        "source_code_package_id": source_code_package_id,
        "source_object_instance_graph_commit_id": source_oig_commit_id,
        "revision_code_package_id": source_code_package_id,
        "revision_code_package_object_instance_graph_commit_id": (source_oig_commit_id),
    }


def _meta_ocg_delta_baseline_from_original_ref(
    *,
    original_ref: Mapping[str, object],
) -> dict[str, object]:
    if (
        _non_empty_string(original_ref.get("semantic_projection_name"))
        != _META_DELTA_BASELINE_PROJECTION_NAME
    ):
        return {}
    domain_commit_id = _non_empty_string(
        original_ref.get("semantic_head_commit_id")
    ) or _non_empty_string(original_ref.get("semantic_package_commit_id"))
    if domain_commit_id is None:
        return {}
    object_instance_graph_commit_id = _non_empty_string(
        original_ref.get("semantic_root_object_instance_graph_commit_id")
    ) or _non_empty_string(original_ref.get("semantic_object_instance_graph_commit_id"))
    package_object_instance_graph_commit_id = (
        _non_empty_string(
            original_ref.get("semantic_package_object_instance_graph_commit_id")
        )
        or object_instance_graph_commit_id
    )
    return {
        "semantic_package_id": _non_empty_string(
            original_ref.get("semantic_package_id")
        ),
        "semantic_projection_hash": _non_empty_string(
            original_ref.get("semantic_projection_hash")
        ),
        "semantic_package_commit_id": domain_commit_id,
        # Meta baseline hydration expects the domain lane commit id here. The
        # object-instance graph commit id is carried separately below.
        "semantic_object_instance_graph_commit_id": domain_commit_id,
        "semantic_package_object_instance_graph_commit_id": (
            package_object_instance_graph_commit_id
        ),
        "semantic_root_commit_id": domain_commit_id,
        "semantic_root_id": _non_empty_string(original_ref.get("semantic_root_id")),
        "semantic_root_object_instance_graph_commit_id": (
            object_instance_graph_commit_id
        ),
    }


def _meta_ocg_baseline_from_package_index(
    *,
    workspace_root: Path,
    source: _OntologyPackageSource,
) -> MetaRuntimeSemanticObjectIndexEntry | None:
    package_index = load_meta_runtime_package_projection_index(
        aware_root=workspace_root,
    )
    if package_index is None:
        return None
    semantic_key = f"ocg_package:{source.package_name}"
    candidate = package_index.semantic_objects_by_key.get(semantic_key)
    if candidate is not None and _meta_ocg_package_index_entry_matches(
        candidate=candidate,
        source=source,
    ):
        return candidate
    for entry in package_index.semantic_objects_by_key.values():
        if _meta_ocg_package_index_entry_matches(candidate=entry, source=source):
            return entry
    return None


def _meta_ocg_package_index_entry_matches(
    *,
    candidate: MetaRuntimeSemanticObjectIndexEntry,
    source: _OntologyPackageSource,
) -> bool:
    if candidate.object_kind != "object_config_graph_package":
        return False
    return _meta_index_entry_package_matches(candidate=candidate, source=source)


def _meta_baseline_semantic_object_index_from_package_index(
    *,
    workspace_root: Path,
    source: _OntologyPackageSource,
) -> dict[str, dict[str, object]]:
    package_index = load_meta_runtime_package_projection_index(
        aware_root=workspace_root,
    )
    if package_index is None:
        return {}
    entries: dict[str, dict[str, object]] = {}
    for entry in package_index.semantic_objects_by_key.values():
        if not _meta_index_entry_package_matches(candidate=entry, source=source):
            continue
        payload = _meta_semantic_object_index_entry_payload(entry=entry)
        entries[entry.semantic_key] = payload
    return dict(sorted(entries.items()))


def _meta_index_entry_package_matches(
    *,
    candidate: MetaRuntimeSemanticObjectIndexEntry,
    source: _OntologyPackageSource,
) -> bool:
    if candidate.package_name != source.package_name:
        return False
    if candidate.fqn_prefix != source.fqn_prefix:
        return False
    return candidate.manifest_path.expanduser().resolve() == (
        source.source_manifest_path.expanduser().resolve()
    )


def _meta_semantic_object_index_entry_payload(
    *,
    entry: MetaRuntimeSemanticObjectIndexEntry,
) -> dict[str, object]:
    payload = dict(entry.payload)
    payload.update(
        {
            "semantic_key": entry.semantic_key,
            "object_kind": entry.object_kind,
            "object_id": _uuid_string(entry.object_id),
            "entity_id": entry.entity_id,
            "graph_semantic_key": entry.graph_semantic_key,
            "parent_semantic_key": entry.parent_semantic_key,
            "owner_semantic_key": entry.owner_semantic_key,
            "node_key": entry.node_key,
            "attribute_name": entry.attribute_name,
            "source_refs": tuple(entry.source_refs),
            "object_config_graph_id": _uuid_string(entry.object_config_graph_id),
            "object_config_graph_hash": entry.object_config_graph_hash,
            "semantic_root_object_instance_graph_commit_id": _uuid_string(
                entry.semantic_root_object_instance_graph_commit_id
            ),
            "semantic_package_object_instance_graph_commit_id": _uuid_string(
                entry.semantic_package_object_instance_graph_commit_id
            ),
            "semantic_root_head_commit_id": _uuid_string(
                entry.semantic_root_head_commit_id
            ),
            "semantic_package_head_commit_id": _uuid_string(
                entry.semantic_package_head_commit_id
            ),
            "source_head_commit_id": _uuid_string(entry.source_head_commit_id),
            "source_object_instance_graph_commit_id": _uuid_string(
                entry.source_object_instance_graph_commit_id
            ),
            "runtime_delta_fingerprint": entry.runtime_delta_fingerprint,
            "evidence_source": entry.evidence_source,
        }
    )
    return payload


def _ontology_delta_result_from_meta_result(
    *,
    request: object,
    source: _OntologyPackageSource,
    meta_baseline_ref: Mapping[str, object],
    meta_result: object,
) -> dict[str, object]:
    payload = _object_payload(meta_result)
    payload["package"] = _object_payload(_request_attr(request, "package"))
    payload["semantic_contract"] = _object_payload(
        _request_attr(request, "semantic_contract")
    )
    details = _object_payload(payload.get("details"))
    details["ontology_provider_delta_bridge"] = {
        "status": "delegated_to_meta",
        "provider_key": "aware_ontology",
        "bridge_provider_key": _META_DELTA_PROVIDER_KEY,
        "manifest_path": source.ontology_toml_path.as_posix(),
        "source_manifest_path": source.source_manifest_path.as_posix(),
        "meta_baseline_ref": dict(meta_baseline_ref),
    }
    payload["details"] = details
    return payload


def _meta_commit_refs_from_baseline_ref(
    *,
    baseline_ref: Mapping[str, object],
) -> dict[str, object]:
    return {
        "source_code_package_id": baseline_ref.get("source_code_package_id"),
        "source_object_instance_graph_commit_id": baseline_ref.get(
            "source_object_instance_graph_commit_id"
        ),
        "semantic_package_id": baseline_ref.get("semantic_package_id"),
        "semantic_branch_id": baseline_ref.get("semantic_branch_id"),
        "semantic_object_instance_graph_commit_id": baseline_ref.get(
            "semantic_object_instance_graph_commit_id"
        ),
        "semantic_root_object_instance_graph_commit_id": baseline_ref.get(
            "semantic_root_object_instance_graph_commit_id"
        ),
        "semantic_projection_name": baseline_ref.get("semantic_projection_name"),
        "semantic_projection_hash": baseline_ref.get("semantic_projection_hash"),
        "semantic_root_id": baseline_ref.get("semantic_root_id"),
        "semantic_root_kind": baseline_ref.get("semantic_root_kind"),
    }


def _meta_durable_input_refs_from_baseline_ref(
    *,
    baseline_ref: Mapping[str, object],
) -> dict[str, object]:
    return {
        "semantic_branch_id": baseline_ref.get("semantic_branch_id"),
        "semantic_projection_hash": baseline_ref.get("semantic_projection_hash"),
        "semantic_projection_name": baseline_ref.get("semantic_projection_name"),
        "source_object_instance_graph_commit_id": baseline_ref.get(
            "source_object_instance_graph_commit_id"
        ),
        "semantic_object_instance_graph_commit_id": baseline_ref.get(
            "semantic_object_instance_graph_commit_id"
        ),
        "semantic_root_object_instance_graph_commit_id": baseline_ref.get(
            "semantic_root_object_instance_graph_commit_id"
        ),
        "semantic_package_id": baseline_ref.get("semantic_package_id"),
        "semantic_package_commit_id": baseline_ref.get("semantic_package_commit_id"),
        "semantic_root_kind": baseline_ref.get("semantic_root_kind"),
        "semantic_root_id": baseline_ref.get("semantic_root_id"),
    }


def _resolve_ontology_package_source(
    *,
    request: SemanticPackageMaterializationRequest,
) -> _OntologyPackageSource:
    return _resolve_ontology_package_source_from_path(
        workspace_root=request.workspace_root.resolve(),
        ontology_toml_path=request.manifest_path.resolve(),
    )


def _resolve_ontology_package_source_from_path(
    *,
    workspace_root: Path,
    ontology_toml_path: Path,
) -> _OntologyPackageSource:
    _assert_workspace_child_path(
        workspace_root=workspace_root,
        path=ontology_toml_path,
        label="aware.ontology.toml",
    )
    if ontology_toml_path.name != "aware.ontology.toml":
        raise RuntimeError(
            "Ontology provider materialization requires aware.ontology.toml: "
            f"{ontology_toml_path}"
        )

    ontology_spec = load_aware_ontology_toml_spec(toml_path=ontology_toml_path)
    source_manifest_path = (
        ontology_toml_path.parent / ontology_spec.ontology.source_manifest
    ).resolve()
    if not source_manifest_path.is_file():
        raise FileNotFoundError(
            "aware.ontology.toml source_manifest was not found: "
            f"{ontology_spec.ontology.source_manifest!r}"
        )
    _assert_workspace_child_path(
        workspace_root=workspace_root,
        path=source_manifest_path,
        label="aware.ontology.toml source_manifest",
    )

    aware_spec = load_aware_toml_spec(toml_path=source_manifest_path)
    if aware_spec.package.package_name != ontology_spec.ontology.package_name:
        raise RuntimeError(
            "aware.ontology.toml package_name does not match source "
            "aware.toml: "
            f"ontology={ontology_spec.ontology.package_name!r} "
            f"source={aware_spec.package.package_name!r}"
        )
    if aware_spec.package.fqn_prefix != ontology_spec.ontology.fqn_prefix:
        raise RuntimeError(
            "aware.ontology.toml fqn_prefix does not match source aware.toml: "
            f"ontology={ontology_spec.ontology.fqn_prefix!r} "
            f"source={aware_spec.package.fqn_prefix!r}"
        )

    package_root = source_manifest_path.parent.resolve()
    sources_root = (package_root / aware_spec.build.sources_dir).resolve()
    return _OntologyPackageSource(
        ontology_toml_path=ontology_toml_path,
        source_manifest_path=source_manifest_path,
        package_name=aware_spec.package.package_name,
        fqn_prefix=aware_spec.package.fqn_prefix,
        version_number=int(aware_spec.package.version_number or 1),
        title=_non_empty_string(aware_spec.package.title),
        description=_non_empty_string(aware_spec.package.description),
        manifest_relative_path=_relative_to(
            path=source_manifest_path,
            root=workspace_root,
            label="source_manifest",
        ),
        package_root=_relative_to(
            path=package_root,
            root=workspace_root,
            label="package_root",
        ),
        sources_root=_relative_to(
            path=sources_root,
            root=workspace_root,
            label="sources_root",
        ),
        runtime_manifest=(
            _non_empty_string(ontology_spec.runtime.manifest)
            if ontology_spec.runtime is not None
            else None
        ),
        runtime_project_name=(
            _non_empty_string(ontology_spec.runtime.project_name)
            if ontology_spec.runtime is not None
            else None
        ),
        runtime_import_root=(
            _non_empty_string(ontology_spec.runtime.import_root)
            if ontology_spec.runtime is not None
            else None
        ),
    )


def _delta_workspace_root(*, request: object, manifest_path: Path) -> Path:
    for key in ("workspace_root", "repo_root", "root_path"):
        value = _request_attr(request, key)
        text = _non_empty_string(value)
        if text is not None:
            return Path(text).expanduser().resolve()
    context = _object_payload(_request_attr(request, "context"))
    for key in ("workspace_root", "repo_root", "root_path"):
        text = _non_empty_string(context.get(key))
        if text is not None:
            return Path(text).expanduser().resolve()
    resolved_manifest = manifest_path.expanduser().resolve()
    for parent in (resolved_manifest.parent, *resolved_manifest.parents):
        if (parent / "aware.workspace.toml").is_file():
            return parent
    return resolved_manifest.parent


def _request_fields(*, request: object) -> dict[str, object]:
    payload = _object_payload(request)
    field_names = (
        "contract_version",
        "provider_delta_request_key",
        "requested_mode",
        "rejection_reason",
        "package",
        "semantic_contract",
        "current_delta_fingerprint",
        "code_package_delta",
        "delta_cause_hints",
        "previous_materialization_evidence",
        "baseline_ref",
        "baseline_source_object_instance_graph_commit_id",
        "baseline_semantic_object_instance_graph_commit_id",
        "baseline_semantic_root_object_instance_graph_commit_id",
        "provider_delta_lane_state",
        "enable_commit_ref_probe",
        "runtime",
        "index",
        "actor_id",
        "environment_id",
        "process_id",
        "thread_id",
        "branch_id",
        "workspace_root",
        "execute_provider_delta_materialization",
        "semantic_function_call_execution_context",
        "semantic_materialization_execution_context",
        "context",
    )
    return {
        field_name: payload[field_name]
        for field_name in field_names
        if field_name in payload
    }


def _request_attr(request: object, key: str) -> object | None:
    if isinstance(request, Mapping):
        return request.get(key)
    return getattr(request, key, None)


def _object_payload(value: object) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        dumped = model_dump(mode="json")
        if isinstance(dumped, Mapping):
            return {str(key): item for key, item in dumped.items()}
    raw_vars = getattr(value, "__dict__", None)
    if isinstance(raw_vars, Mapping):
        return {str(key): item for key, item in raw_vars.items()}
    return {}


def _first_mapping_with_keys(
    value: object,
    *,
    keys: tuple[str, ...],
    depth: int = 0,
) -> dict[str, object]:
    if depth > 8:
        return {}
    if isinstance(value, Mapping):
        payload = {str(key): item for key, item in value.items()}
        if all(_non_empty_string(payload.get(key)) is not None for key in keys):
            return payload
        for item in payload.values():
            found = _first_mapping_with_keys(item, keys=keys, depth=depth + 1)
            if found:
                return found
        return {}
    if isinstance(value, (list, tuple)):
        for item in value:
            found = _first_mapping_with_keys(item, keys=keys, depth=depth + 1)
            if found:
                return found
    return {}


def _first_nested_text(
    value: object,
    *,
    path: tuple[str, ...],
    depth: int = 0,
) -> str | None:
    if depth > 8:
        return None
    if isinstance(value, Mapping):
        payload = {str(key): item for key, item in value.items()}
        nested: object = payload
        for key in path:
            if not isinstance(nested, Mapping):
                nested = None
                break
            nested = nested.get(key)
        text = _non_empty_string(nested)
        if text is not None:
            return text
        for item in payload.values():
            text = _first_nested_text(item, path=path, depth=depth + 1)
            if text is not None:
                return text
    if isinstance(value, (list, tuple)):
        for item in value:
            text = _first_nested_text(item, path=path, depth=depth + 1)
            if text is not None:
                return text
    return None


async def _commit_ontology_package_snapshot(
    *,
    runtime: _OntologyPackageRuntimeBinder,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    branch_id: UUID,
    projection_hash: str,
    source: _OntologyPackageSource,
    leaf_result: ObjectConfigGraphPackageLeafMaterializationResult,
    ontology_config_commit: _OntologyConfigCommitResult,
    runtime_code_package_snapshot: _OntologyRuntimeCodePackageSnapshot | None,
) -> _OntologyPackageCommitResult:
    opg = index.opg_by_hash.get(projection_hash)
    if opg is None:
        raise RuntimeError(
            "OntologyPackage snapshot commit missing projection hash: "
            f"{projection_hash}"
        )

    package_id = stable_ontology_package_id(
        name=source.package_name,
        fqn_prefix=source.fqn_prefix,
    )
    runtime_lane = _bind_ontology_package_runtime_lane(
        runtime=runtime,
        index=index,
        actor_id=actor_id,
        branch_id=branch_id,
    )
    with runtime_lane.activate(commit=True, publish=False):
        package = await OntologyPackage.build(
            name=source.package_name,
            fqn_prefix=source.fqn_prefix,
            ontology_config_id=ontology_config_commit.ontology_config_id,
            ontology_config_object_instance_graph_commit_id=(
                ontology_config_commit.config_object_instance_graph_commit_id
            ),
            source_code_package_id=leaf_result.code_package.id,
            object_config_graph_package_id=leaf_result.object_config_graph_package.id,
            object_config_graph_package_object_instance_graph_commit_id=(
                _leaf_ocg_package_oig_commit_id(leaf_result)
            ),
            object_config_graph_object_instance_graph_commit_id=(
                _leaf_ocg_oig_commit_id(leaf_result)
            ),
            version_number=source.version_number,
            title=source.title,
            description=source.description,
            manifest_relative_path=source.manifest_relative_path,
            package_root=source.package_root,
            sources_root=source.sources_root,
        )
    if package.id != package_id:
        raise RuntimeError(
            "OntologyPackage.build returned unexpected package id: "
            f"expected={package_id} actual={package.id}"
        )

    if runtime_code_package_snapshot is not None:
        with runtime_lane.activate(commit=True, publish=False):
            await package.attach_runtime_code_package(
                code_package_id=runtime_code_package_snapshot.code_package_id,
                package_name=runtime_code_package_snapshot.package_name,
                language=CodeLanguage.python,
                import_root=runtime_code_package_snapshot.import_root,
                manifest_relative_path=(
                    runtime_code_package_snapshot.manifest_relative_path
                ),
                package_root=runtime_code_package_snapshot.package_root,
                role=runtime_code_package_snapshot.role,
                object_instance_graph_commit_id=(
                    runtime_code_package_snapshot.object_instance_graph_commit_id
                ),
                include_paths=JsonArray(
                    [
                        "pyproject.toml",
                        (
                            runtime_code_package_snapshot.import_root.replace(".", "/")
                            + "/**/*.py"
                        ),
                    ]
                ),
                exclude_paths=JsonArray(),
            )

    commit_id, object_instance_graph_commit_id = (
        await _resolve_ontology_package_lane_commit_ids(
            runtime_lane=runtime_lane,
            source=source,
        )
    )
    return _OntologyPackageCommitResult(
        ontology_package_id=package.id,
        package_commit_id=commit_id,
        package_head_commit_id=object_instance_graph_commit_id,
        package_object_instance_graph_commit_id=(object_instance_graph_commit_id),
        commit_perf_ms={},
    )


async def _resolve_ontology_package_lane_commit_ids(
    *,
    runtime_lane: MetaGraphBoundRuntimeLane,
    source: _OntologyPackageSource,
) -> tuple[UUID, UUID]:
    commit_id = runtime_lane.last_commit_id
    object_instance_graph_commit_id = runtime_lane.last_head_commit_id
    if isinstance(commit_id, UUID) and isinstance(
        object_instance_graph_commit_id, UUID
    ):
        return commit_id, object_instance_graph_commit_id
    if commit_id is not None or object_instance_graph_commit_id is not None:
        raise RuntimeError(
            "OntologyPackage materialization received partial lane commit evidence: "
            f"name={source.package_name!r} commit_id={commit_id!r} "
            f"object_instance_graph_commit_id={object_instance_graph_commit_id!r}"
        )

    response = runtime_lane.last_response
    if response is None:
        raise RuntimeError(
            "OntologyPackage materialization did not invoke the runtime lane: "
            f"name={source.package_name!r}"
        )
    if response.status != "succeeded":
        raise RuntimeError(
            "OntologyPackage materialization cannot reuse lane head after failed "
            f"runtime response: name={source.package_name!r} status={response.status!r} "
            f"error={response.error!r}"
        )
    if (
        response.commit_id is not None
        or response.object_instance_graph_commit_id is not None
    ):
        raise RuntimeError(
            "OntologyPackage materialization runtime response carried commit evidence "
            "that was not recorded on the bound lane: "
            f"name={source.package_name!r} commit_id={response.commit_id!r} "
            "object_instance_graph_commit_id="
            f"{response.object_instance_graph_commit_id!r}"
        )
    if response.changes:
        raise RuntimeError(
            "OntologyPackage materialization cannot reuse lane head when the runtime "
            f"response reports unapplied changes: name={source.package_name!r} "
            f"change_count={len(response.changes)}"
        )

    head = await FSCommitStore().head(
        branch_id=runtime_lane.binding.branch_id,
        projection_hash=runtime_lane.binding.projection_hash,
    )
    if not isinstance(head, Mapping):
        raise RuntimeError(
            "OntologyPackage materialization had no new commit and no committed "
            "lane HEAD to reuse: "
            f"name={source.package_name!r} branch_id={runtime_lane.binding.branch_id} "
            f"projection_hash={runtime_lane.binding.projection_hash}"
        )

    head_graph_hash_post = _non_empty_string(head.get("graph_hash_post"))
    if (
        response.graph_hash_post
        and head_graph_hash_post
        and head_graph_hash_post != response.graph_hash_post
    ):
        raise RuntimeError(
            "OntologyPackage materialization no-op response does not match lane HEAD: "
            f"name={source.package_name!r} head_graph_hash_post={head_graph_hash_post!r} "
            f"response_graph_hash_post={response.graph_hash_post!r}"
        )

    return (
        _required_uuid_mapping_value(
            head,
            "commit_id",
            label="OntologyPackage materialization lane HEAD commit id",
        ),
        _required_uuid_mapping_value(
            head,
            "object_instance_graph_commit_id",
            label=(
                "OntologyPackage materialization lane HEAD "
                "object_instance_graph_commit_id"
            ),
        ),
    )


async def _commit_ontology_runtime_code_package_snapshot(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    source: _OntologyPackageSource,
    projection_hash: str,
    workspace_root: Path,
) -> _OntologyRuntimeCodePackageSnapshot | None:
    if (
        source.runtime_manifest is None
        or source.runtime_project_name is None
        or source.runtime_import_root is None
    ):
        return None
    runtime_manifest_path = (
        source.ontology_toml_path.parent / source.runtime_manifest
    ).resolve()
    if runtime_manifest_path.name != "pyproject.toml":
        raise RuntimeError(
            "Ontology runtime CodePackage materialization requires "
            f"[runtime].manifest to point to pyproject.toml: {source.runtime_manifest!r}"
        )
    if not runtime_manifest_path.is_file():
        raise FileNotFoundError(
            "Ontology runtime CodePackage manifest was not found: "
            f"{source.runtime_manifest!r}"
        )
    _assert_workspace_child_path(
        workspace_root=workspace_root,
        path=runtime_manifest_path,
        label="[runtime].manifest",
    )
    runtime_package_root = runtime_manifest_path.parent
    runtime_import_root = source.runtime_import_root
    runtime_sources_root = (
        runtime_package_root / runtime_import_root.replace(".", "/")
    ).resolve()
    if not runtime_sources_root.is_dir():
        raise FileNotFoundError(
            "Ontology runtime CodePackage import root was not found: "
            f"import_root={runtime_import_root!r} path={runtime_sources_root}"
        )
    _assert_workspace_child_path(
        workspace_root=workspace_root,
        path=runtime_sources_root,
        label="[runtime].import_root",
    )

    pyproject_payload = _load_runtime_pyproject_manifest(
        runtime_manifest_path=runtime_manifest_path,
    )
    project = pyproject_payload.get("project")
    if not isinstance(project, Mapping):
        raise RuntimeError(
            "Ontology runtime CodePackage pyproject.toml is missing [project]: "
            f"{runtime_manifest_path}"
        )
    project_name = _non_empty_string(project.get("name"))
    if project_name != source.runtime_project_name:
        raise RuntimeError(
            "Ontology runtime CodePackage project name mismatch: "
            f"declared={source.runtime_project_name!r} pyproject={project_name!r}"
        )

    config_ref = source_code_package_config_ref(
        manifest_kind="pyproject_toml",
        surface="runtime",
    )
    package_root_relative = _relative_to(
        path=runtime_package_root,
        root=workspace_root,
        label="[runtime].package_root",
    )
    manifest_relative_path = _relative_to(
        path=runtime_manifest_path,
        root=workspace_root,
        label="[runtime].manifest",
    )
    sources_root_relative = _relative_to(
        path=runtime_sources_root,
        root=workspace_root,
        label="[runtime].import_root",
    )
    unparsed_texts_by_relative_path = _runtime_code_package_unparsed_texts(
        runtime_package_root=runtime_package_root,
        runtime_manifest_path=runtime_manifest_path,
        runtime_import_root=runtime_import_root,
        pyproject_payload=pyproject_payload,
    )
    snapshot = await commit_code_package_text_snapshot(
        index=index,
        actor_id=actor_id,
        branch_id=_ontology_runtime_code_package_branch_id(
            package_name=source.runtime_project_name,
            manifest_relative_path=manifest_relative_path,
        ),
        projection_hash=projection_hash,
        code_package_config_id=config_ref.config_id,
        package_name=source.runtime_project_name,
        language=CodeLanguage.python,
        surface=config_ref.surface,
        manifest_kind=config_ref.manifest_kind,
        manifest_relative_path=manifest_relative_path,
        package_root=package_root_relative,
        sources_root=sources_root_relative,
        fqn_prefix=runtime_import_root,
        source_texts_by_relative_path={},
        unparsed_texts_by_relative_path=unparsed_texts_by_relative_path,
    )
    return _OntologyRuntimeCodePackageSnapshot(
        role="ontology_runtime_handler_package",
        code_package_id=snapshot.code_package.id,
        object_instance_graph_commit_id=snapshot.object_instance_graph_commit_id,
        package_name=source.runtime_project_name,
        manifest_relative_path=manifest_relative_path,
        package_root=package_root_relative,
        sources_root=sources_root_relative,
        import_root=runtime_import_root,
        language=CodeLanguage.python.value,
        path_count=len(unparsed_texts_by_relative_path),
    )


async def _commit_ontology_config_snapshot(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    branch_id: UUID,
    projection_hash: str,
    source: _OntologyPackageSource,
    leaf_result: ObjectConfigGraphPackageLeafMaterializationResult,
) -> _OntologyConfigCommitResult:
    opg = index.opg_by_hash.get(projection_hash)
    if opg is None:
        raise RuntimeError(
            "OntologyConfig snapshot commit missing projection hash: "
            f"{projection_hash}"
        )

    config_id = stable_ontology_config_id(
        name=source.package_name,
        fqn_prefix=source.fqn_prefix,
    )
    config = OntologyConfig.model_construct(
        id=config_id,
        name=source.package_name,
        fqn_prefix=source.fqn_prefix,
        object_config_graph=None,
        object_config_graph_id=leaf_result.object_config_graph.id,
        object_config_graph_object_instance_graph_commit=None,
        object_config_graph_object_instance_graph_commit_id=(
            _leaf_ocg_oig_commit_id(leaf_result)
        ),
        ontologies=[],
        version_number=source.version_number,
        title=source.title,
        description=source.description,
        schema_hash=leaf_result.object_config_graph.hash,
    )

    domain_oig_id = stable_object_instance_graph_id(
        object_projection_graph_id=opg.id,
        key=str(branch_id),
    )
    _ocgi, opgi = resolve_meta_graph_ocgi_opgi(
        index=index,
        projection_hash=projection_hash,
    )
    if opgi is None:
        raise RuntimeError(
            "OntologyConfig snapshot commit missing "
            "ObjectProjectionGraphIdentity: "
            f"projection_hash={projection_hash}"
        )
    oigi_id = stable_object_instance_graph_identity_id(
        object_projection_graph_identity_id=opgi.id,
        object_instance_graph_id=domain_oig_id,
    )
    before_oig = build_rooted_object_instance_graph_base(
        key=str(branch_id),
        name=f"OIG_{branch_id.hex[:8]}",
        description="ROOTED_BASE",
        object_config_graph=index.ocg,
        object_projection_graph=opg,
        root_source_object_id=config.id,
        oig_id=domain_oig_id,
    )
    objects_by_id: dict[UUID, BaseORMModel] = {config.id: config}
    created_ids = frozenset(objects_by_id)
    change_set = ORMChangeSet(
        collected_at=datetime.now(UTC),
        created_ids=created_ids,
        touched_ids=created_ids,
        deleted_ids=frozenset(),
        objects_by_id=objects_by_id,
        scalar_fields_by_id={},
        list_fields_by_id={},
        scalar_baseline={},
        list_baseline={},
        list_added={},
        list_removed={},
    )
    changes = build_object_instance_graph_changes_from_orm_change_set(
        before_oig=before_oig,
        object_instance_graph_identity_id=oigi_id,
        ocg=index.ocg,
        opg=opg,
        change_set=change_set,
        class_configs_by_id=index.class_configs_by_id,
        relationships_by_id=index.relationships_by_id,
        enum_option_resolver=None,
        class_instance_resolver=None,
        union_selections=None,
    )
    if not changes:
        raise RuntimeError(
            "OntologyConfig snapshot commit produced no OIG changes: "
            f"name={source.package_name!r}"
        )
    after_oig = materialize_meta_oig_post(
        before_oig=before_oig,
        changes=changes,
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )
    commit_id = _ontology_config_snapshot_commit_id(
        branch_id=branch_id,
        projection_hash=projection_hash,
        source=source,
        ontology_config_id=config.id,
        leaf_result=leaf_result,
    )
    commit_action = CommitActionDescriptor(
        operation_label="OntologyConfig.materialize",
        call_target="aware_ontology.materialization.workspace_provider",
        object_id=config.id,
    )
    committer = FSLaneCommitter()
    try:
        commit = await committer.commit(
            branch_id=branch_id,
            projection_hash=projection_hash,
            object_instance_graph_identity_id=oigi_id,
            object_instance_graph_id=domain_oig_id,
            before_oig=before_oig,
            root_object_id=config.id,
            changes=changes,
            graph_hash_pre=before_oig.hash,
            graph_hash_post=after_oig.hash,
            author_id=resolve_meta_author_id(actor_id),
            commit_id=commit_id,
            commit_action=commit_action,
        )
    except LaneHeadPreHashMismatchError as exc:
        if (
            exc.details.branch_id != branch_id
            or exc.details.projection_hash != projection_hash
            or exc.details.object_instance_graph_id != domain_oig_id
        ):
            raise
        _reset_generated_projection_lane(
            branch_id=branch_id,
            projection_hash=projection_hash,
        )
        committer = FSLaneCommitter()
        commit = await committer.commit(
            branch_id=branch_id,
            projection_hash=projection_hash,
            object_instance_graph_identity_id=oigi_id,
            object_instance_graph_id=domain_oig_id,
            before_oig=before_oig,
            root_object_id=config.id,
            changes=changes,
            graph_hash_pre=before_oig.hash,
            graph_hash_post=after_oig.hash,
            author_id=resolve_meta_author_id(actor_id),
            commit_id=commit_id,
            commit_action=commit_action,
        )
    if commit is None or commit.commit is None:
        raise RuntimeError(
            "OntologyConfig snapshot commit did not append a lane commit: "
            f"name={source.package_name!r}"
        )
    object_instance_graph_commit_id = stable_object_instance_graph_commit_id(
        object_instance_graph_identity_id=(commit.object_instance_graph_identity_id),
        commit_id=commit.commit.id,
    )
    return _OntologyConfigCommitResult(
        ontology_config_id=config.id,
        config_commit_id=commit.commit.id,
        config_head_commit_id=object_instance_graph_commit_id,
        config_object_instance_graph_commit_id=object_instance_graph_commit_id,
        commit_perf_ms=committer.last_commit_perf_profile_snapshot(),
    )


def _ontology_config_snapshot_commit_id(
    *,
    branch_id: UUID,
    projection_hash: str,
    source: _OntologyPackageSource,
    ontology_config_id: UUID,
    leaf_result: ObjectConfigGraphPackageLeafMaterializationResult,
) -> UUID:
    ocg_oig_commit_id = _leaf_ocg_oig_commit_id(leaf_result)
    return uuid5(
        _ONTOLOGY_SNAPSHOT_COMMIT_NAMESPACE,
        "aware:ontology_config_snapshot_commit:"
        + f"{branch_id}:{projection_hash}:{ontology_config_id}:"
        + f"{source.package_name}:{source.fqn_prefix}:"
        + f"{source.version_number}:{source.title or ''}:"
        + f"{source.description or ''}:"
        + f"{leaf_result.object_config_graph.id}:"
        + f"{leaf_result.object_config_graph.hash}:"
        + f"{ocg_oig_commit_id}:"
        + f"{source.manifest_relative_path}:"
        + f"{source.package_root}:"
        + f"{source.sources_root or ''}",
    )


def _ontology_package_snapshot_commit_id(
    *,
    branch_id: UUID,
    projection_hash: str,
    source: _OntologyPackageSource,
    ontology_package_id: UUID,
    leaf_result: ObjectConfigGraphPackageLeafMaterializationResult,
    ontology_config_commit: _OntologyConfigCommitResult,
) -> UUID:
    ocg_package_oig_commit_id = _leaf_ocg_package_oig_commit_id(leaf_result)
    ocg_oig_commit_id = _leaf_ocg_oig_commit_id(leaf_result)
    return uuid5(
        _ONTOLOGY_SNAPSHOT_COMMIT_NAMESPACE,
        "aware:ontology_package_snapshot_commit:"
        + f"{branch_id}:{projection_hash}:{ontology_package_id}:"
        + f"{source.package_name}:{source.fqn_prefix}:"
        + f"{source.version_number}:{source.title or ''}:"
        + f"{source.description or ''}:"
        + f"{leaf_result.code_package.id}:"
        + f"{ontology_config_commit.ontology_config_id}:"
        + f"{ontology_config_commit.config_object_instance_graph_commit_id}:"
        + f"{leaf_result.object_config_graph_package.id}:"
        + f"{leaf_result.object_config_graph.id}:"
        + f"{ocg_package_oig_commit_id}:"
        + f"{ocg_oig_commit_id}:"
        + f"{source.manifest_relative_path}:"
        + f"{source.package_root}:"
        + f"{source.sources_root or ''}",
    )


def _reset_generated_projection_lane(
    *,
    branch_id: UUID,
    projection_hash: str,
) -> None:
    store = FSCommitStore()
    lane_dir = store.aware_root / ".aware" / "oig" / str(branch_id) / projection_hash
    if lane_dir.exists():
        shutil.rmtree(lane_dir)
    get_shared_materialization_cache().invalidate_lane(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )


def _external_object_config_graphs_for_request(
    *,
    request: SemanticPackageMaterializationRequest,
    source: _OntologyPackageSource,
    context: Mapping[str, object] | None = None,
) -> tuple[ObjectConfigGraph, ...]:
    if context is None:
        context = _request_context_with_execution_context_entries(request=request)
    return _target_dependency_object_config_graphs(
        request=request,
        source=source,
        context=context,
    )


def _target_runtime_object_config_graph_from_context(
    *,
    context: Mapping[str, object],
    source: _OntologyPackageSource,
) -> ObjectConfigGraph | None:
    runtime_by_package_name = _object_config_graphs_by_package_name_from_context(
        context=context,
        graph_kind="runtime",
    )
    runtime_graph = runtime_by_package_name.get(source.package_name)
    if runtime_graph is not None:
        return runtime_graph
    for graph in _object_config_graphs_for_kind_from_context(
        context=context,
        graph_kind="runtime",
    ):
        if str(getattr(graph, "fqn_prefix", "") or "") == source.fqn_prefix:
            return graph
    return None


def _target_runtime_object_config_graph_from_manifest_closure(
    *,
    request: SemanticPackageMaterializationRequest,
    source: _OntologyPackageSource,
    context: Mapping[str, object],
) -> ObjectConfigGraph | None:
    package_manifest_paths = (
        resolve_meta_runtime_package_manifest_closure_for_package_names(
            repo_root=request.workspace_root,
            package_names=(source.package_name,),
            semantic_ontology_package_catalog=(
                _semantic_ontology_package_catalog_from_context(request.context)
            ),
        )
    )
    if not package_manifest_paths:
        return None
    dependency_package_names = _dependency_package_names_for_manifest_paths(
        package_manifest_paths=package_manifest_paths,
        source_package_name=source.package_name,
    )
    context_dependency_graphs = (
        _complete_dependency_graphs_from_context_by_package_name(
            context=context,
            package_names=dependency_package_names,
        )
    )
    if context_dependency_graphs is not None:
        runtime_graph = _target_runtime_object_config_graph_from_context(
            context=context,
            source=source,
        )
        if runtime_graph is not None:
            return runtime_graph

    runtime_context = build_meta_graph_runtime_context_for_aware_package_manifests(
        package_manifest_paths=package_manifest_paths,
        workspace_root=request.workspace_root,
        composite_name=(
            "Aware Ontology Package Runtime Bundle Context: " f"{source.package_name}"
        ),
    )
    runtime_graph = runtime_context.runtime_graph_by_package_name.get(
        source.package_name
    )
    if runtime_graph is not None:
        return runtime_graph
    for graph in runtime_context.runtime_graphs:
        if str(getattr(graph, "fqn_prefix", "") or "") == source.fqn_prefix:
            return graph
    return None


def _request_context_with_execution_context_entries(
    *,
    request: object,
) -> dict[str, object]:
    payload = _object_payload(_request_attr(request, "context"))
    execution_context = _request_attr(request, "execution_context")
    entries = getattr(execution_context, "entries", None)
    if isinstance(entries, Mapping):
        payload.update(entries)
    provider_entries = getattr(execution_context, "provider_entries", None)
    if isinstance(provider_entries, Mapping):
        for raw_provider_payload in provider_entries.values():
            if isinstance(raw_provider_payload, Mapping):
                payload.update(raw_provider_payload)
    return payload


def _target_dependency_object_config_graphs(
    *,
    request: SemanticPackageMaterializationRequest,
    source: _OntologyPackageSource,
    context: Mapping[str, object],
) -> tuple[ObjectConfigGraph, ...]:
    package_manifest_paths = (
        resolve_meta_runtime_package_manifest_closure_for_package_names(
            repo_root=request.workspace_root,
            package_names=(source.package_name,),
            semantic_ontology_package_catalog=(
                _semantic_ontology_package_catalog_from_context(request.context)
            ),
        )
    )
    if not package_manifest_paths:
        return ()
    dependency_package_names = _dependency_package_names_for_manifest_paths(
        package_manifest_paths=package_manifest_paths,
        source_package_name=source.package_name,
    )
    context_dependency_graphs = (
        _complete_dependency_graphs_from_context_by_package_name(
            context=context,
            package_names=dependency_package_names,
        )
    )
    if context_dependency_graphs is not None:
        return context_dependency_graphs
    dependency_context = build_meta_graph_runtime_context_for_aware_package_manifests(
        package_manifest_paths=package_manifest_paths,
        workspace_root=request.workspace_root,
        composite_name=(
            "Aware Ontology Package Dependency Context: " f"{source.package_name}"
        ),
    )
    return tuple(
        graph
        for graph in (
            *dependency_context.runtime_graphs,
            *dependency_context.source_graphs,
        )
        if graph.fqn_prefix != source.fqn_prefix
    )


def _dependency_package_names_for_manifest_paths(
    *,
    package_manifest_paths: Iterable[Path],
    source_package_name: str,
) -> tuple[str, ...]:
    names: list[str] = []
    seen: set[str] = set()
    for manifest_path in package_manifest_paths:
        try:
            spec = load_aware_toml_spec(toml_path=manifest_path)
        except Exception:
            continue
        package_name = str(spec.package.package_name).strip()
        if (
            not package_name
            or package_name == source_package_name
            or package_name in seen
        ):
            continue
        seen.add(package_name)
        names.append(package_name)
    return tuple(names)


def _complete_dependency_graphs_from_context_by_package_name(
    *,
    context: Mapping[str, object],
    package_names: tuple[str, ...],
) -> tuple[ObjectConfigGraph, ...] | None:
    if not package_names:
        return ()
    source_graph_by_name = _object_config_graphs_by_package_name_from_context(
        context=context,
        graph_kind="source",
    )
    runtime_graph_by_name = _object_config_graphs_by_package_name_from_context(
        context=context,
        graph_kind="runtime",
    )
    graphs: list[ObjectConfigGraph] = []
    for package_name in package_names:
        runtime_graph = runtime_graph_by_name.get(package_name)
        if runtime_graph is None:
            return None
        graphs.append(runtime_graph)
        source_graph = source_graph_by_name.get(package_name)
        if source_graph is not None:
            graphs.append(source_graph)
    return _dedupe_object_config_graphs(graphs)


def _object_config_graphs_by_package_name_from_context(
    *,
    context: Mapping[str, object],
    graph_kind: str,
) -> dict[str, ObjectConfigGraph]:
    mapping_attr = (
        "runtime_graph_by_package_name"
        if graph_kind == "runtime"
        else "source_graph_by_package_name"
    )
    direct_mapping_attr = (
        "runtime_object_config_graphs_by_package_name"
        if graph_kind == "runtime"
        else "semantic_object_config_graphs_by_package_name"
    )
    graphs: dict[str, ObjectConfigGraph] = {}
    raw_direct_mapping = context.get(direct_mapping_attr)
    if isinstance(raw_direct_mapping, Mapping):
        for raw_package_name, graph in raw_direct_mapping.items():
            package_name = str(raw_package_name).strip()
            if package_name and isinstance(graph, ObjectConfigGraph):
                graphs.setdefault(package_name, graph)
    for meta_context in _meta_context_candidates_from_context(context=context):
        raw_mapping = _context_value(meta_context, key=mapping_attr)
        if not isinstance(raw_mapping, Mapping):
            continue
        for raw_package_name, graph in raw_mapping.items():
            package_name = str(raw_package_name).strip()
            if package_name and isinstance(graph, ObjectConfigGraph):
                graphs.setdefault(package_name, graph)
    return graphs


def _meta_context_candidates_from_context(
    *,
    context: Mapping[str, object],
) -> tuple[object, ...]:
    candidates: list[object] = []
    seen: set[int] = set()

    def _add(value: object) -> None:
        if value is None:
            return
        identity = id(value)
        if identity in seen:
            return
        seen.add(identity)
        candidates.append(value)
        nested = _context_value(value, key="meta_context")
        if nested is not None and id(nested) not in seen:
            _add(nested)

    _add(context.get("aware_meta.graph_runtime_context"))
    _add(context.get("provider_runtime_context"))
    return tuple(candidates)


def _semantic_ontology_package_catalog_from_context(
    context: Mapping[str, object],
) -> Mapping[str, object] | None:
    raw_catalog = context.get(SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_CONTEXT_KEY)
    return raw_catalog if isinstance(raw_catalog, Mapping) else None


def _external_object_config_graphs_from_context(
    context: Mapping[str, object],
) -> tuple[ObjectConfigGraph, ...]:
    graphs: list[ObjectConfigGraph] = []
    seen: set[UUID] = set()
    # Runtime graphs carry ObjectProjectionGraph declarations. Source/runtime
    # OCGs can share the same id, so runtime graphs must be seen first.
    for graph_kind in ("runtime", "source"):
        for graph in _object_config_graphs_for_kind_from_context(
            context=context,
            graph_kind=graph_kind,
        ):
            if graph.id in seen:
                continue
            seen.add(graph.id)
            graphs.append(graph)
    return tuple(graphs)


def _dedupe_object_config_graphs(
    graphs: Iterable[ObjectConfigGraph],
) -> tuple[ObjectConfigGraph, ...]:
    result: list[ObjectConfigGraph] = []
    seen: set[UUID] = set()
    for graph in graphs:
        if graph.id in seen:
            continue
        seen.add(graph.id)
        result.append(graph)
    return tuple(result)


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
    for key in explicit_keys:
        graph_values = _object_config_graphs_from_context_value(context.get(key))
        for graph in graph_values:
            if graph.id in seen:
                continue
            seen.add(graph.id)
            graphs.append(graph)
    meta_context = context.get("aware_meta.graph_runtime_context")
    meta_context_graph_attr = (
        "runtime_object_config_graphs"
        if graph_kind == "runtime"
        else "semantic_object_config_graphs"
    )
    for context_candidate in _meta_context_candidates_from_context(
        context={"aware_meta.graph_runtime_context": meta_context},
    ):
        for attr_name in (meta_context_attr, meta_context_graph_attr):
            for graph in _object_config_graphs_from_context_value(
                _context_value(context_candidate, key=attr_name)
            ):
                if graph.id in seen:
                    continue
                seen.add(graph.id)
                graphs.append(graph)
        for graph in _object_config_graphs_from_mapping_value(
            _context_value(context_candidate, key=meta_context_mapping_attr)
        ):
            if graph.id in seen:
                continue
            seen.add(graph.id)
            graphs.append(graph)
    provider_context = context.get("provider_runtime_context")
    for key in (*explicit_keys, meta_context_attr):
        for graph in _object_config_graphs_from_context_value(
            _context_value(provider_context, key=key)
        ):
            if graph.id in seen:
                continue
            seen.add(graph.id)
            graphs.append(graph)
    provider_meta_context = _context_value(
        provider_context,
        key="meta_context",
    )
    for graph in _object_config_graphs_from_context_value(
        _context_value(provider_meta_context, key=meta_context_attr)
    ):
        if graph.id in seen:
            continue
        seen.add(graph.id)
        graphs.append(graph)
    for graph in _object_config_graphs_from_mapping_value(
        _context_value(provider_meta_context, key=meta_context_mapping_attr)
    ):
        if graph.id in seen:
            continue
        seen.add(graph.id)
        graphs.append(graph)
    return tuple(graphs)


def _object_config_graphs_from_context_value(
    value: object,
) -> tuple[ObjectConfigGraph, ...]:
    if isinstance(value, ObjectConfigGraph):
        return (value,)
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(item for item in value if isinstance(item, ObjectConfigGraph))


def _object_config_graphs_from_mapping_value(
    value: object,
) -> tuple[ObjectConfigGraph, ...]:
    if not isinstance(value, Mapping):
        return ()
    return tuple(item for item in value.values() if isinstance(item, ObjectConfigGraph))


def _assert_workspace_child_path(
    *,
    workspace_root: Path,
    path: Path,
    label: str,
) -> None:
    try:
        path.resolve().relative_to(workspace_root)
    except ValueError as exc:
        raise RuntimeError(
            f"Ontology package materialization {label} must stay inside "
            f"workspace root: {path}"
        ) from exc


def _relative_to(*, path: Path, root: Path, label: str) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise RuntimeError(
            f"Ontology package materialization could not resolve {label} "
            f"relative to module root: path={path} root={root}"
        ) from exc


def _load_runtime_pyproject_manifest(
    *,
    runtime_manifest_path: Path,
) -> Mapping[str, object]:
    try:
        payload = tomllib.loads(runtime_manifest_path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise RuntimeError(
            "Ontology runtime CodePackage pyproject.toml could not be parsed: "
            f"{runtime_manifest_path}"
        ) from exc
    return payload


def _runtime_code_package_unparsed_texts(
    *,
    runtime_package_root: Path,
    runtime_manifest_path: Path,
    runtime_import_root: str,
    pyproject_payload: Mapping[str, object],
) -> dict[str, str]:
    texts: dict[str, str] = {
        runtime_manifest_path.relative_to(runtime_package_root).as_posix(): (
            runtime_manifest_path.read_text(encoding="utf-8")
        )
    }
    import_root_path = (
        runtime_package_root / runtime_import_root.replace(".", "/")
    ).resolve()
    for source_file in sorted(import_root_path.rglob("*.py")):
        if not source_file.is_file():
            continue
        relative_path = source_file.relative_to(runtime_package_root).as_posix()
        if _is_runtime_support_path_excluded(relative_path):
            continue
        texts[relative_path] = source_file.read_text(encoding="utf-8")
    for support_file in _runtime_pyproject_support_files(
        runtime_package_root=runtime_package_root,
        pyproject_payload=pyproject_payload,
    ):
        relative_path = support_file.relative_to(runtime_package_root).as_posix()
        texts.setdefault(relative_path, support_file.read_text(encoding="utf-8"))
    return texts


def _runtime_pyproject_support_files(
    *,
    runtime_package_root: Path,
    pyproject_payload: Mapping[str, object],
) -> tuple[Path, ...]:
    support_paths = _runtime_pyproject_support_paths(
        pyproject_payload=pyproject_payload
    )
    support_files: dict[str, Path] = {}
    for support_path in support_paths:
        candidate = (runtime_package_root / support_path).resolve()
        try:
            candidate.relative_to(runtime_package_root)
        except ValueError:
            continue
        if candidate.is_file():
            support_files[candidate.relative_to(runtime_package_root).as_posix()] = (
                candidate
            )
    return tuple(support_files[key] for key in sorted(support_files))


def _runtime_pyproject_support_paths(
    *,
    pyproject_payload: Mapping[str, object],
) -> tuple[str, ...]:
    paths: list[str] = []
    project = pyproject_payload.get("project")
    if isinstance(project, Mapping):
        readme = project.get("readme")
        if isinstance(readme, str) and readme.strip():
            paths.append(readme.strip())
        elif isinstance(readme, Mapping):
            file_value = readme.get("file")
            if isinstance(file_value, str) and file_value.strip():
                paths.append(file_value.strip())

    tool = pyproject_payload.get("tool")
    hatch = tool.get("hatch") if isinstance(tool, Mapping) else None
    build = hatch.get("build") if isinstance(hatch, Mapping) else None
    targets = build.get("targets") if isinstance(build, Mapping) else None
    wheel = targets.get("wheel") if isinstance(targets, Mapping) else None
    include_value = wheel.get("include") if isinstance(wheel, Mapping) else None
    paths.extend(_string_sequence(include_value))
    return tuple(
        dict.fromkeys(path for path in paths if path and not Path(path).is_absolute())
    )


def _string_sequence(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        normalized = value.strip()
        return (normalized,) if normalized else ()
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(
        normalized
        for item in value
        if isinstance(item, str) and (normalized := item.strip())
    )


def _is_runtime_support_path_excluded(relative_path: str) -> bool:
    return bool(
        {
            "__pycache__",
            ".mypy_cache",
            ".pytest_cache",
            ".ruff_cache",
            ".venv",
            "build",
            "dist",
        }.intersection(Path(relative_path).parts)
    )


def _ontology_runtime_code_package_branch_id(
    *,
    package_name: str,
    manifest_relative_path: str,
) -> UUID:
    return uuid5(
        NAMESPACE_URL,
        (
            "aware://ontology/runtime-code-package/v1/"
            f"{package_name.casefold().strip()}/"
            f"{manifest_relative_path.casefold().strip()}"
        ),
    )


def _context_value(value: object, *, key: str) -> object | None:
    if isinstance(value, Mapping):
        return value.get(key)
    return getattr(value, key, None) if value is not None else None


def _context_bool(value: object, *, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().casefold()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
    return default


def _force_fresh_semantic_materialization_from_context(
    context: Mapping[str, object],
) -> bool:
    raw_value = context.get("semantic_materialization_force_fresh")
    if isinstance(raw_value, bool):
        return raw_value
    if isinstance(raw_value, Mapping):
        return _context_bool(raw_value.get("enabled"), default=False)
    return False


def _non_empty_string(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _uuid_string(value: UUID | None) -> str | None:
    return str(value) if value is not None else None


def _leaf_ocg_package_oig_commit_id(
    leaf_result: ObjectConfigGraphPackageLeafMaterializationResult,
) -> UUID | None:
    return leaf_result.object_config_graph_package_object_instance_graph_commit_id


def _leaf_ocg_oig_commit_id(
    leaf_result: ObjectConfigGraphPackageLeafMaterializationResult,
) -> UUID | None:
    return leaf_result.object_config_graph_object_instance_graph_commit_id


def _duration_s(started_at: float) -> float:
    return round(max(perf_counter() - started_at, 0.0), 6)


def _duration_ms(value: int) -> float:
    return round(max(float(value), 0.0) / 1000.0, 6)
