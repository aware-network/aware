from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from hashlib import sha256
from inspect import isawaitable
import json
import os
from pathlib import Path
from pathlib import PurePosixPath
import shutil
from time import perf_counter
import tomllib
from typing import TYPE_CHECKING, Protocol, TypeVar, cast
from uuid import NAMESPACE_URL, UUID, uuid5

from aware_api_ontology.api.api import Api
from aware_api_ontology.api.api_capability import ApiCapability
from aware_api_ontology.api.api_capability_endpoint import ApiCapabilityEndpoint
from aware_api_ontology.api.api_package import ApiPackage
from aware_api_ontology.stable_ids import stable_api_id, stable_api_package_id
from aware_code.semantic_contract_config import source_code_package_config_ref
from aware_code.types import JsonArray, JsonObject, JsonValue
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.package.code_package import CodePackage

from aware_code_ontology.stable_ids import stable_code_package_id
from aware_code.package.snapshot_commit import commit_code_package_text_snapshot
from aware_api_runtime.manifest.spec import (
    AwareApiTomlDartTargetSpec,
    AwareApiTomlPythonProductTargetSpec,
    AwareApiTomlPythonTargetSpec,
    AwareApiTomlSpec,
    AwareApiSemanticPackageExportKind,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.config.object_config_graph_node import (
    ObjectConfigGraphNode,
)
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_meta_ontology.stable_ids import (
    stable_class_config_id,
    stable_object_config_graph_id,
    stable_object_config_graph_node_id,
    stable_object_instance_graph_commit_id,
)
from aware_meta.graph.config.handlers import build_object_projection_graphs
from aware_meta.fqn_resolver import authored_ref_from_fqn as _authored_ref_from_fqn
from aware_meta.graph.instance.commit.fs_store import FSCommitStore
from aware_meta.graph.instance.commit.materialization_cache import (
    get_shared_materialization_cache,
)
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
from aware_meta.materialization import (
    MaterializationLaneContext,
    MaterializationRunReceipt,
    materialize_object_config_graph_package_leaf_from_manifest,
    stable_object_config_graph_package_branch_id,
)
from aware_meta.runtime import MetaGraphRuntimeIndex
from aware_meta.runtime.graph_context import find_meta_graph_projection_hash_by_name
from aware_meta.runtime.oig_model_reifier import reify_oig_root_model, reify_oig_session
from aware_orm.models.orm_model import ORMModel
from aware_orm.session.session import Session
from ..ontology_graph.materialization.service import (
    materialize_api_graph_ontology,
)
from ..snapshots.commit import (
    ApiPackageLanguagePackageSnapshotRef,
    commit_api_package_manifest_snapshot,
)
from aware_utils.logging import logger
from ..workspace import APIWorkspace, APIWorkspaceSnapshot
from ..ontology_graph.ontology import (
    APIOntologyPlan,
    decode_api_ontology_plan_payload,
    encode_api_ontology_plan_payload,
)
from ..dependencies.runtime_resolution import (
    API_ACCESSIBLE_DEPENDENCY_GRAPHS_FILENAME,
    _resolve_api_dependency_packages,
    _compute_runtime_dependency_source_digest,
    _ensure_dependency_object_projection_graphs as _ensure_runtime_dependency_object_projection_graphs,
    _load_existing_dependency_object_config_graph as _load_existing_runtime_dependency_object_config_graph,
    _load_required_dependency_object_config_graph as _load_required_runtime_dependency_object_config_graph,
    _runtime_dependency_latest_input_mtime_ns,
    canonicalize_api_accessible_dependency_graphs,
    collect_api_dependency_class_config_ids_from_graphs,
    load_api_accessible_dependency_graphs,
    load_api_accessible_dependency_graph_source_digests,
    load_api_accessible_dependency_graphs_from_runtime_artifact,
)
from ..source.semantic_analysis import analyze_api_sources

if TYPE_CHECKING:
    from ..ir import APICompilePlan

_TRoot = TypeVar("_TRoot", bound=ORMModel)
ApiEndpointCatalog = dict[str, dict[str, tuple[str, ...]]]


class ApiMaterializationProgressCallback(Protocol):
    def __call__(self, payload: Mapping[str, object]) -> object: ...


_API_MATERIALIZATION_PROGRESS_CALLBACK: ContextVar[
    ApiMaterializationProgressCallback | None
] = ContextVar("api_materialization_progress_callback", default=None)
_API_MATERIALIZATION_PROGRESS_DETAIL: ContextVar[Mapping[str, object] | None] = (
    ContextVar("api_materialization_progress_detail", default=None)
)

_API_LANGUAGE_CODE_PACKAGE_EXCLUDED_PATH_PARTS = frozenset(
    {
        ".aware",
        "_aware",
        ".dart_tool",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "__pycache__",
        "build",
        "dist",
    }
)


def _resolve_repo_root_from_aware_repo_toml(*, start: Path) -> Path:
    candidate = start.expanduser().resolve()
    if not candidate.is_dir():
        candidate = candidate.parent
    for parent in (candidate, *candidate.parents):
        manifest_path = parent / "aware.repo.toml"
        if manifest_path.is_file():
            _validate_aware_repo_toml_manifest(
                repo_root=parent,
                manifest_path=manifest_path,
            )
            return parent
    raise RuntimeError(
        "Unable to resolve Aware repo root from "
        f"{start.expanduser().resolve()}. Expected an ancestor aware.repo.toml."
    )


def _validate_aware_repo_toml_manifest(*, repo_root: Path, manifest_path: Path) -> None:
    try:
        payload = tomllib.loads(manifest_path.read_text(encoding="utf-8") or "")
    except Exception as exc:
        raise RuntimeError(
            f"Invalid aware.repo.toml at {manifest_path}: {exc}"
        ) from exc
    if payload.get("aware_repo") != 1:
        raise RuntimeError(f"{manifest_path} must declare aware_repo = 1.")
    repo_section = payload.get("repo")
    if not isinstance(repo_section, dict):
        raise RuntimeError(f"{manifest_path} must declare a [repo] table.")
    workspaces_dir = repo_section.get("workspaces_dir")
    if not isinstance(workspaces_dir, str) or not workspaces_dir.strip():
        raise RuntimeError(f"{manifest_path} must declare repo.workspaces_dir.")
    if Path(workspaces_dir).is_absolute():
        raise RuntimeError(f"{manifest_path} repo.workspaces_dir must be relative.")
    workspaces_path = repo_root / workspaces_dir
    if not workspaces_path.is_dir():
        raise RuntimeError(
            f"{manifest_path} declares missing workspaces_dir: {workspaces_path}"
        )


_API_LANGUAGE_CODE_PACKAGE_BRANCH_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware://api/materialization/language-code-package-branch:v1",
)


class _RuntimeProtocol(Protocol):
    @property
    def manifest_path(self) -> Path: ...

    @property
    def invoker(self) -> object: ...


@dataclass(frozen=True, slots=True)
class ApiPackageMaterializationSpec:
    api_toml_path: Path
    workspace_root: Path
    manifest_spec: AwareApiTomlSpec
    package_name: str
    package_fqn_prefix: str
    api_name: str
    api_source_path: str
    source_files: tuple[str, ...]
    api_endpoint_catalog: ApiEndpointCatalog
    compile_plan_payload: dict[str, object]
    runtime_compile_plan_payload: dict[str, object]
    dependency_accessible_graphs: tuple[ObjectConfigGraph, ...]
    dependency_graph_context_source: str
    runtime_compile_plan_hash: str


@dataclass(frozen=True, slots=True)
class _ApiDependencyGraphContext:
    class_config_ids: dict[str, UUID]
    accessible_graphs: tuple[ObjectConfigGraph, ...]
    source: str


@dataclass(frozen=True, slots=True)
class _GeneratedDtoNamespaceRoot:
    path: str
    namespace: str


@dataclass(frozen=True, slots=True)
class ApiLanguageCodePackageTarget:
    language: CodeLanguage
    package_name: str
    import_root: str
    package_root: Path
    manifest_path: Path
    sources_root: Path
    manifest_kind: str
    role: str
    output_key: str
    include_paths: tuple[str, ...]
    exclude_paths: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ApiLanguageCodePackageMaterialization:
    code_package: CodePackage
    branch_id: UUID
    domain_commit_id: UUID
    object_instance_graph_commit_id: UUID
    role: str
    output_key: str
    include_paths: tuple[str, ...]
    exclude_paths: tuple[str, ...]

    def to_payload(self) -> dict[str, object]:
        return {
            "code_package_id": self.code_package.id,
            "source_code_package_id": self.code_package.id,
            "branch_id": self.branch_id,
            "domain_commit_id": self.domain_commit_id,
            "object_instance_graph_commit_id": self.object_instance_graph_commit_id,
            "package_name": self.code_package.package_name,
            "language": self.code_package.language.value,
            "manifest_relative_path": self.code_package.manifest_relative_path,
            "package_root": self.code_package.package_root,
            "sources_root": self.code_package.sources_root,
            "fqn_prefix": self.code_package.fqn_prefix,
            "role": self.role,
            "output_key": self.output_key,
            "include_paths": list(self.include_paths),
            "exclude_paths": list(self.exclude_paths),
        }


@dataclass(frozen=True, slots=True)
class ApiPackageMaterializationResult:
    api_toml_path: Path
    workspace_root: Path
    manifest_spec: AwareApiTomlSpec
    api: Api
    api_package: ApiPackage
    api_source_path: str
    source_files: tuple[str, ...]
    phase_timings_s: Mapping[str, float]
    runtime_compile_plan_hash: str
    api_endpoint_catalog: ApiEndpointCatalog
    source_code_package_id: UUID | None
    source_object_instance_graph_commit_id: UUID | None
    api_commit_id: UUID | None
    api_head_commit_id: UUID | None
    api_object_instance_graph_commit_id: UUID | None
    package_commit_id: UUID | None
    package_head_commit_id: UUID | None
    generated_dto_graph_count: int = 0
    generated_dto_class_config_count: int = 0
    language_code_package_ids: tuple[UUID, ...] = ()
    language_code_package_refs: tuple[dict[str, object], ...] = ()
    product_runtime_compile_result: object | None = None
    dart_public_package_compile_result: object | None = None
    language_post_step_receipts: tuple[dict[str, object], ...] = ()


@dataclass(frozen=True, slots=True)
class ApiCompilePlanPackageMaterializationResult:
    compile_plan_path: Path | None
    workspace_root: Path
    package_name: str
    fqn_prefix: str
    api_source_path: str
    api: Api
    api_package: ApiPackage
    source_files: tuple[str, ...]
    phase_timings_s: Mapping[str, float]
    api_endpoint_catalog: ApiEndpointCatalog
    generated_dto_graph_count: int
    generated_dto_class_config_count: int
    api_commit_id: UUID | None
    api_head_commit_id: UUID | None
    api_object_instance_graph_commit_id: UUID | None
    package_commit_id: UUID | None
    package_head_commit_id: UUID | None


def _round_duration_s(duration_s: float) -> float:
    return round(max(duration_s, 0.0), 6)


def _dedupe_accessible_graphs(
    graphs: Sequence[ObjectConfigGraph],
) -> tuple[ObjectConfigGraph, ...]:
    graphs_by_id: dict[UUID, ObjectConfigGraph] = {}
    for graph in graphs:
        graphs_by_id[graph.id] = graph
    return tuple(
        sorted(
            graphs_by_id.values(),
            key=lambda graph: (
                (graph.fqn_prefix or "").casefold(),
                (graph.name or "").casefold(),
                str(graph.id),
            ),
        )
    )


def _api_dependency_graph_context_reusable_graphs_for_materialization(
    *,
    snapshot: APIWorkspaceSnapshot,
    accessible_graphs: Sequence[ObjectConfigGraph],
    source: str,
    dependency_repo_roots: Sequence[str | Path],
) -> tuple[ObjectConfigGraph, ...] | None:
    if not accessible_graphs:
        return None
    if source.startswith("runtime_accessible_dependency_graphs_artifact"):
        return tuple(accessible_graphs)
    if source != "workspace_semantic_context":
        return None

    context_graphs = _complete_dependency_context_graphs_from_accessible_graphs(
        snapshot=snapshot,
        accessible_graphs=accessible_graphs,
        dependency_repo_roots=dependency_repo_roots,
    )
    if context_graphs is None:
        return None
    if not _dependency_graphs_cover_current_endpoint_refs(
        snapshot=snapshot,
        accessible_graphs=context_graphs,
        source=source,
    ):
        return None

    dependency_packages = _resolve_api_dependency_packages(
        snapshot=snapshot,
        dependency_repo_roots=dependency_repo_roots,
    )
    graphs_by_package_name = _accessible_graphs_by_dependency_package_name(
        dependency_packages=dependency_packages,
        accessible_graphs=context_graphs,
    )
    source_owned_api_dto_exports = set(
        _source_owned_api_dto_export_package_names(snapshot=snapshot)
    )
    ordered_context_graphs: list[ObjectConfigGraph] = []
    for package in dependency_packages:
        graph = graphs_by_package_name.get(package.package_name)
        if graph is None:
            return None
        if (
            package.package_name in source_owned_api_dto_exports
            and not _source_owned_api_dto_graph_preserves_source_layouts(
                package=package,
                graph=graph,
            )
        ):
            return None
        graph = _ensure_dependency_object_projection_graphs(
            package=package,
            graph=graph,
            graphs_by_package_name=graphs_by_package_name,
        )
        graphs_by_package_name[package.package_name] = graph
        ordered_context_graphs.append(graph)
    return _dedupe_accessible_graphs((*ordered_context_graphs, *accessible_graphs))


def _object_config_graph_package_name(graph: ObjectConfigGraph) -> str:
    return (graph.name or "").strip()


def _object_config_graph_fqn_prefix(graph: ObjectConfigGraph) -> str:
    return (graph.fqn_prefix or "").strip()


def _accessible_graphs_by_dependency_package_name(
    *,
    dependency_packages: Sequence[object],
    accessible_graphs: Sequence[ObjectConfigGraph],
) -> dict[str, ObjectConfigGraph]:
    graphs_by_package_name: dict[str, ObjectConfigGraph] = {}
    for package in dependency_packages:
        package_name = str(getattr(package, "package_name", "") or "").strip()
        if not package_name:
            continue
        matches = tuple(
            graph
            for graph in accessible_graphs
            if _accessible_graph_matches_dependency_package(
                package=package,
                graph=graph,
            )
        )
        matches_by_id = {graph.id: graph for graph in matches}
        if not matches_by_id:
            continue
        if len(matches_by_id) > 1:
            raise RuntimeError(
                "Ambiguous API dependency graph semantic context: "
                + f"package={package_name!r} matches="
                + repr(
                    [
                        {
                            "id": str(graph.id),
                            "name": graph.name,
                            "fqn_prefix": graph.fqn_prefix,
                        }
                        for graph in sorted(
                            matches_by_id.values(),
                            key=lambda item: str(item.id),
                        )
                    ]
                )
            )
        graphs_by_package_name[package_name] = next(iter(matches_by_id.values()))
    return graphs_by_package_name


def _complete_dependency_context_graphs_from_accessible_graphs(
    *,
    snapshot: APIWorkspaceSnapshot,
    accessible_graphs: Sequence[ObjectConfigGraph],
    dependency_repo_roots: Sequence[str | Path] = (),
) -> tuple[ObjectConfigGraph, ...] | None:
    if not snapshot.spec.dependencies or not accessible_graphs:
        return None
    dependency_packages = _resolve_api_dependency_packages(
        snapshot=snapshot,
        dependency_repo_roots=dependency_repo_roots,
    )
    graphs_by_package_name = _accessible_graphs_by_dependency_package_name(
        dependency_packages=dependency_packages,
        accessible_graphs=accessible_graphs,
    )
    missing_package_names = tuple(
        package.package_name
        for package in dependency_packages
        if package.package_name not in graphs_by_package_name
    )
    if missing_package_names:
        return None
    return tuple(
        graphs_by_package_name[package.package_name] for package in dependency_packages
    )


def _available_dependency_context_graphs_from_runtime_artifacts(
    *,
    snapshot: APIWorkspaceSnapshot,
    phase_timings_s: dict[str, float],
    dependency_repo_roots: Sequence[str | Path] = (),
) -> tuple[ObjectConfigGraph, ...]:
    dependency_packages = _resolve_api_dependency_packages(
        snapshot=snapshot,
        dependency_repo_roots=dependency_repo_roots,
    )
    graphs_by_package_name: dict[str, ObjectConfigGraph] = {}
    ordered_graphs: list[ObjectConfigGraph] = []
    for package in dependency_packages:
        with _record_phase(
            phase_timings_s,
            "resolve_api_package_materialization_spec."
            f"load_available_dependency_runtime_artifact.{package.package_name}",
        ):
            graph = _load_existing_runtime_dependency_object_config_graph(
                package=package,
            )
            if graph is None:
                continue
            graph = _ensure_runtime_dependency_object_projection_graphs(
                package=package,
                graph=graph,
                graphs_by_package_name=graphs_by_package_name,
            )
        graphs_by_package_name[package.package_name] = graph
        ordered_graphs.append(graph)
    return canonicalize_api_accessible_dependency_graphs(
        accessible_graphs=_dedupe_accessible_graphs(ordered_graphs)
    )


def _api_dependency_graph_context(
    *,
    snapshot: APIWorkspaceSnapshot,
    accessible_graphs: Sequence[ObjectConfigGraph],
    phase_timings_s: dict[str, float],
    dependency_repo_roots: Sequence[str | Path] = (),
) -> _ApiDependencyGraphContext:
    if not snapshot.spec.dependencies:
        return _ApiDependencyGraphContext(
            class_config_ids={},
            accessible_graphs=(),
            source="no_dependencies",
        )

    context_graphs = _complete_dependency_context_graphs_from_accessible_graphs(
        snapshot=snapshot,
        accessible_graphs=accessible_graphs,
        dependency_repo_roots=dependency_repo_roots,
    )
    if context_graphs is not None and _dependency_graphs_cover_current_endpoint_refs(
        snapshot=snapshot,
        accessible_graphs=context_graphs,
        source="workspace_semantic_context",
    ):
        return _ApiDependencyGraphContext(
            class_config_ids=collect_api_dependency_class_config_ids_from_graphs(
                accessible_graphs=context_graphs,
            ),
            accessible_graphs=context_graphs,
            source="workspace_semantic_context",
        )

    with _record_phase(
        phase_timings_s,
        "resolve_api_package_materialization_spec.load_accessible_dependency_graphs_runtime_artifact",
    ):
        artifact_graphs = _complete_dependency_context_graphs_from_runtime_artifact(
            snapshot=snapshot,
            dependency_repo_roots=dependency_repo_roots,
        )
    if artifact_graphs is not None and _dependency_graphs_cover_current_endpoint_refs(
        snapshot=snapshot,
        accessible_graphs=artifact_graphs,
        source="runtime_accessible_dependency_graphs_artifact",
    ):
        artifact_graphs, refreshed_package_names = (
            _refresh_stale_source_owned_api_dto_export_graphs(
                snapshot=snapshot,
                accessible_graphs=artifact_graphs,
                phase_timings_s=phase_timings_s,
                dependency_repo_roots=dependency_repo_roots,
            )
        )
        source = "runtime_accessible_dependency_graphs_artifact"
        if refreshed_package_names:
            source = (
                "runtime_accessible_dependency_graphs_artifact"
                "_with_source_owned_api_dto_refresh"
            )
        return _ApiDependencyGraphContext(
            class_config_ids=collect_api_dependency_class_config_ids_from_graphs(
                accessible_graphs=artifact_graphs,
            ),
            accessible_graphs=artifact_graphs,
            source=source,
        )

    with _record_phase(
        phase_timings_s,
        "resolve_api_package_materialization_spec.load_accessible_dependency_graphs_from_dependency_artifacts",
    ):
        artifact_graphs = load_api_accessible_dependency_graphs(
            snapshot=snapshot,
            dependency_repo_roots=dependency_repo_roots,
        )
    return _ApiDependencyGraphContext(
        class_config_ids=collect_api_dependency_class_config_ids_from_graphs(
            accessible_graphs=artifact_graphs,
        ),
        accessible_graphs=artifact_graphs,
        source="dependency_runtime_artifacts",
    )


def _source_owned_api_dto_export_package_names(
    *,
    snapshot: APIWorkspaceSnapshot,
) -> tuple[str, ...]:
    package_names: list[str] = []
    for export in snapshot.spec.semantic_package_exports:
        if export.kind is not AwareApiSemanticPackageExportKind.api_dto:
            continue
        package_name = export.package_name.strip()
        if package_name:
            package_names.append(package_name)
    return tuple(dict.fromkeys(package_names))


def _refresh_stale_source_owned_api_dto_export_graphs(
    *,
    snapshot: APIWorkspaceSnapshot,
    accessible_graphs: Sequence[ObjectConfigGraph],
    phase_timings_s: dict[str, float],
    dependency_repo_roots: Sequence[str | Path],
) -> tuple[tuple[ObjectConfigGraph, ...], tuple[str, ...]]:
    source_owned_api_dto_exports = _source_owned_api_dto_export_package_names(
        snapshot=snapshot,
    )
    if not source_owned_api_dto_exports:
        return tuple(accessible_graphs), ()

    from ..compile import resolve_api_runtime_package_dir  # noqa: WPS433

    runtime_package_dir = resolve_api_runtime_package_dir(snapshot=snapshot)
    recorded_source_digests = load_api_accessible_dependency_graph_source_digests(
        runtime_package_dir=runtime_package_dir,
    )
    artifact_path = runtime_package_dir / API_ACCESSIBLE_DEPENDENCY_GRAPHS_FILENAME
    dependency_packages = _resolve_api_dependency_packages(
        snapshot=snapshot,
        dependency_repo_roots=dependency_repo_roots,
    )
    package_by_name = {package.package_name: package for package in dependency_packages}
    graphs_by_package_name = _accessible_graphs_by_dependency_package_name(
        dependency_packages=dependency_packages,
        accessible_graphs=accessible_graphs,
    )
    refreshed_package_names: list[str] = []

    for package_name in source_owned_api_dto_exports:
        package = package_by_name.get(package_name)
        if package is None:
            continue
        expected_digest = _compute_runtime_dependency_source_digest(package=package)
        current_graph = graphs_by_package_name.get(package_name)
        if (
            recorded_source_digests.get(package_name) == expected_digest
            and current_graph is not None
            and _source_owned_api_dto_graph_preserves_source_layouts(
                package=package,
                graph=current_graph,
            )
        ):
            continue
        if (
            current_graph is not None
            and _source_owned_api_dto_graph_preserves_source_layouts(
                package=package,
                graph=current_graph,
            )
            and _source_owned_api_dto_graph_cache_is_fresh_for_inputs(
                package=package,
                artifact_path=artifact_path,
            )
        ):
            continue
        phase_name = (
            "resolve_api_package_materialization_spec."
            f"refresh_source_owned_api_dto_export_graph.{package_name}"
        )
        with _record_phase(phase_timings_s, phase_name):
            graph = _load_existing_runtime_dependency_object_config_graph(
                package=package,
            )
            if graph is None:
                graph = _load_required_runtime_dependency_object_config_graph(
                    package=package,
                )
            graph = _ensure_runtime_dependency_object_projection_graphs(
                package=package,
                graph=graph,
                graphs_by_package_name=graphs_by_package_name,
            )
        graphs_by_package_name[package_name] = graph
        refreshed_package_names.append(package_name)
        logger.info(
            "API dependency graph context refreshed source-owned API DTO export "
            "graph: api_package=%s export_package=%s recorded_digest_present=%s",
            snapshot.spec.api.package_name,
            package_name,
            package_name in recorded_source_digests,
        )

    if not refreshed_package_names:
        return tuple(accessible_graphs), ()

    return (
        tuple(
            graphs_by_package_name[package.package_name]
            for package in dependency_packages
            if package.package_name in graphs_by_package_name
        ),
        tuple(refreshed_package_names),
    )


def _source_owned_api_dto_export_graph_refresh_package_names(
    *,
    snapshot: APIWorkspaceSnapshot,
    accessible_graphs: Sequence[ObjectConfigGraph],
    dependency_repo_roots: Sequence[str | Path],
) -> tuple[str, ...]:
    source_owned_api_dto_exports = _source_owned_api_dto_export_package_names(
        snapshot=snapshot,
    )
    if not source_owned_api_dto_exports:
        return ()

    from ..compile import resolve_api_runtime_package_dir  # noqa: WPS433

    runtime_package_dir = resolve_api_runtime_package_dir(snapshot=snapshot)
    artifact_path = runtime_package_dir / API_ACCESSIBLE_DEPENDENCY_GRAPHS_FILENAME
    recorded_source_digests = load_api_accessible_dependency_graph_source_digests(
        runtime_package_dir=runtime_package_dir,
    )
    dependency_packages = _resolve_api_dependency_packages(
        snapshot=snapshot,
        dependency_repo_roots=dependency_repo_roots,
    )
    package_by_name = {package.package_name: package for package in dependency_packages}
    graphs_by_package_name = _accessible_graphs_by_dependency_package_name(
        dependency_packages=dependency_packages,
        accessible_graphs=accessible_graphs,
    )
    refresh_package_names: list[str] = []
    for package_name in source_owned_api_dto_exports:
        package = package_by_name.get(package_name)
        if package is None:
            continue
        current_graph = graphs_by_package_name.get(package_name)
        if current_graph is None:
            refresh_package_names.append(package_name)
            continue
        if not _source_owned_api_dto_graph_preserves_source_layouts(
            package=package,
            graph=current_graph,
        ):
            refresh_package_names.append(package_name)
            continue
        expected_digest = _compute_runtime_dependency_source_digest(package=package)
        if recorded_source_digests.get(package_name) == expected_digest:
            continue
        if _source_owned_api_dto_graph_cache_is_fresh_for_inputs(
            package=package,
            artifact_path=artifact_path,
        ):
            continue
        refresh_package_names.append(package_name)
    return tuple(dict.fromkeys(refresh_package_names))


def _source_owned_api_dto_graph_cache_is_fresh_for_inputs(
    *,
    package: object,
    artifact_path: Path,
) -> bool:
    if not artifact_path.is_file():
        return False
    return (
        artifact_path.stat().st_mtime_ns
        >= _runtime_dependency_latest_input_mtime_ns(
            package=package,
        )
    )


def _source_owned_api_dto_graph_preserves_source_layouts(
    *,
    package: object,
    graph: ObjectConfigGraph,
) -> bool:
    spec = getattr(package, "spec", None)
    package_spec = getattr(spec, "package", None)
    fqn_prefix = str(getattr(package_spec, "fqn_prefix", "") or "").strip()
    if not fqn_prefix:
        return True

    local_nodes = tuple(
        node
        for node in graph.object_config_graph_nodes
        if _source_owned_api_dto_node_fqn(node=node).startswith(f"{fqn_prefix}.")
    )
    if not local_nodes:
        return True
    return all(_node_has_aware_source_layout(node=node) for node in local_nodes)


def _source_owned_api_dto_node_fqn(*, node: object) -> str:
    class_config = getattr(node, "class_config", None)
    class_fqn = str(getattr(class_config, "class_fqn", "") or "").strip()
    if class_fqn:
        return class_fqn
    enum_config = getattr(node, "enum_config", None)
    enum_fqn = str(getattr(enum_config, "enum_fqn", "") or "").strip()
    if enum_fqn:
        return enum_fqn
    return str(getattr(node, "node_key", "") or "").strip()


def _node_has_aware_source_layout(*, node: object) -> bool:
    for layout in getattr(node, "layouts", ()) or ():
        layout_kind = str(getattr(layout, "layout_kind", "") or "").strip()
        relative_path = str(getattr(layout, "relative_path", "") or "").strip()
        if relative_path and (not layout_kind or layout_kind == "aware"):
            return True
    return False


def _dependency_graphs_cover_current_endpoint_refs(
    *,
    snapshot: APIWorkspaceSnapshot,
    accessible_graphs: Sequence[ObjectConfigGraph],
    source: str,
) -> bool:
    class_config_ids = collect_api_dependency_class_config_ids_from_graphs(
        accessible_graphs=tuple(accessible_graphs),
    )
    required_refs = _current_api_endpoint_class_refs(snapshot=snapshot)
    missing_refs = tuple(ref for ref in required_refs if ref not in class_config_ids)
    if not missing_refs:
        return True
    logger.info(
        "API dependency graph context missing current endpoint class refs; "
        "falling back to source graph resolution: api_package=%s source=%s missing=%s",
        snapshot.spec.api.package_name,
        source,
        missing_refs,
    )
    return False


def _current_api_endpoint_class_refs(
    *, snapshot: APIWorkspaceSnapshot
) -> tuple[str, ...]:
    analysis = analyze_api_sources(
        package_root=snapshot.package_root,
        source_files=snapshot.source_files,
        binding_truth_by_ref={},
    )
    refs: list[str] = []
    for api in analysis.api_ownership:
        for capability in api.capabilities:
            for endpoint in capability.endpoints:
                request_config = endpoint.request_config
                refs.append(request_config.class_ref.strip())
                response_config = request_config.response_config
                if response_config is not None:
                    refs.append(response_config.class_ref.strip())
                stream_config = request_config.stream_config
                if stream_config is not None:
                    refs.extend(
                        event_config.class_ref.strip()
                        for event_config in stream_config.event_configs
                    )
    return tuple(dict.fromkeys(ref for ref in refs if ref))


def _complete_dependency_context_graphs_from_runtime_artifact(
    *,
    snapshot: APIWorkspaceSnapshot,
    dependency_repo_roots: Sequence[str | Path],
) -> tuple[ObjectConfigGraph, ...] | None:
    from ..compile import resolve_api_runtime_package_dir  # noqa: WPS433

    runtime_package_dir = resolve_api_runtime_package_dir(snapshot=snapshot)
    dependency_packages = _resolve_api_dependency_packages(
        snapshot=snapshot,
        dependency_repo_roots=dependency_repo_roots,
    )
    if not _api_accessible_dependency_graph_source_digests_are_current(
        runtime_package_dir=runtime_package_dir,
        dependency_packages=dependency_packages,
    ):
        return None
    try:
        artifact_graphs = load_api_accessible_dependency_graphs_from_runtime_artifact(
            runtime_package_dir=runtime_package_dir,
        )
    except FileNotFoundError:
        return None
    except Exception as exc:
        logger.info(
            "API dependency graph runtime artifact could not be reused; falling back: "
            "api_package=%s runtime_package_dir=%s error=%s",
            snapshot.spec.api.package_name,
            runtime_package_dir,
            exc,
        )
        return None
    return _complete_dependency_context_graphs_from_accessible_graphs(
        snapshot=snapshot,
        accessible_graphs=artifact_graphs,
        dependency_repo_roots=dependency_repo_roots,
    )


def _api_accessible_dependency_graph_source_digests_are_current(
    *,
    runtime_package_dir: Path,
    dependency_packages: Sequence[object],
) -> bool:
    if not dependency_packages:
        return True
    recorded_digests = load_api_accessible_dependency_graph_source_digests(
        runtime_package_dir=runtime_package_dir,
    )
    for package in dependency_packages:
        package_name = str(getattr(package, "package_name", "") or "").strip()
        if not package_name:
            continue
        try:
            expected_digest = _compute_runtime_dependency_source_digest(
                package=package,
            )
        except Exception as exc:
            logger.info(
                "API dependency graph runtime artifact source digest check failed; "
                "falling back: package=%s error=%s",
                package_name,
                exc,
            )
            return False
        recorded_digest = recorded_digests.get(package_name)
        if recorded_digest != expected_digest:
            logger.info(
                "API dependency graph runtime artifact is stale; falling back: "
                "package=%s recorded_digest_present=%s",
                package_name,
                recorded_digest is not None,
            )
            return False
    return True


def _accessible_graph_matches_dependency_package(
    *,
    package: object,
    graph: ObjectConfigGraph,
) -> bool:
    spec = getattr(package, "spec", None)
    package_spec = getattr(spec, "package", None)
    package_name = str(getattr(package, "package_name", "") or "").strip()
    fqn_prefix = str(getattr(package_spec, "fqn_prefix", "") or "").strip()
    graph_name = _object_config_graph_package_name(graph)
    graph_fqn_prefix = _object_config_graph_fqn_prefix(graph)
    return bool(
        (package_name and graph_name == package_name)
        or (fqn_prefix and graph_name == fqn_prefix)
        or (fqn_prefix and graph_fqn_prefix == fqn_prefix)
    )


async def build_api_accessible_dependency_graphs_via_meta_runtime(
    *,
    snapshot: APIWorkspaceSnapshot,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    branch_id: UUID,
    target_projection_hash: str,
    object_config_graph_projection_hash: str,
    include_object_config_graph: bool = True,
    accessible_graphs: Sequence[ObjectConfigGraph] = (),
    dependency_repo_roots: Sequence[str | Path] = (),
) -> tuple[ObjectConfigGraph, ...]:
    """Resolve API dependency OCGs through direct Meta ontology/runtime materialization."""

    dependency_packages = _resolve_api_dependency_packages(
        snapshot=snapshot,
        dependency_repo_roots=dependency_repo_roots,
    )
    source_owned_api_dto_exports = set(
        _source_owned_api_dto_export_package_names(snapshot=snapshot)
    )
    graphs_by_package_name = _accessible_graphs_by_dependency_package_name(
        dependency_packages=dependency_packages,
        accessible_graphs=accessible_graphs,
    )
    missing_accessible_package_names = [
        package.package_name
        for package in dependency_packages
        if package.package_name not in graphs_by_package_name
        or (
            package.package_name in source_owned_api_dto_exports
            and not _source_owned_api_dto_graph_preserves_source_layouts(
                package=package,
                graph=graphs_by_package_name[package.package_name],
            )
        )
    ]
    if dependency_packages and not missing_accessible_package_names:
        logger.info(
            "API dependency graph resolution reused Workspace semantic context: "
            "api_package=%s dependency_packages=%d",
            snapshot.spec.api.package_name,
            len(dependency_packages),
        )
        ordered_context_graphs: list[ObjectConfigGraph] = []
        for package in dependency_packages:
            graph = graphs_by_package_name[package.package_name]
            graph = _ensure_dependency_object_projection_graphs(
                package=package,
                graph=graph,
                graphs_by_package_name=graphs_by_package_name,
            )
            graphs_by_package_name[package.package_name] = graph
            ordered_context_graphs.append(graph)
        return canonicalize_api_accessible_dependency_graphs(
            accessible_graphs=_dedupe_accessible_graphs(
                (*ordered_context_graphs, *accessible_graphs)
            )
        )
    ordered_graphs: list[ObjectConfigGraph] = []
    logger.info(
        "API Meta dependency graph direct materialization started: api_package=%s dependency_packages=%d "
        "include_object_config_graph=%s",
        snapshot.spec.api.package_name,
        len(dependency_packages),
        include_object_config_graph,
    )

    for package_index, package in enumerate(dependency_packages, start=1):
        package_started_at = perf_counter()
        existing_graph = graphs_by_package_name.get(package.package_name)
        if existing_graph is not None and (
            package.package_name not in source_owned_api_dto_exports
            or _source_owned_api_dto_graph_preserves_source_layouts(
                package=package,
                graph=existing_graph,
            )
        ):
            existing_graph = _ensure_dependency_object_projection_graphs(
                package=package,
                graph=existing_graph,
                graphs_by_package_name=graphs_by_package_name,
            )
            graphs_by_package_name[package.package_name] = existing_graph
            ordered_graphs.append(existing_graph)
            logger.info(
                "API Meta dependency package ensure reused accessible graph: "
                "package=%s position=%d/%d nodes=%d duration=%.3fs",
                package.package_name,
                package_index,
                len(dependency_packages),
                len(existing_graph.object_config_graph_nodes),
                perf_counter() - package_started_at,
            )
            continue

        graphs_by_package_name.pop(package.package_name, None)
        dependency_graphs: list[ObjectConfigGraph] = []
        for dependency in package.spec.dependencies:
            dependency_graph = graphs_by_package_name.get(dependency.package_name)
            if dependency_graph is None:
                raise RuntimeError(
                    "API Meta package compile dependency graph is unavailable: "
                    f"package={package.package_name!r} dependency={dependency.package_name!r}"
                )
            dependency_graphs.append(dependency_graph)

        logger.info(
            "API Meta dependency package direct materialization started: package=%s position=%d/%d "
            "direct_dependencies=%d",
            package.package_name,
            package_index,
            len(dependency_packages),
            len(dependency_graphs),
        )
        package_workspace_root = _resolve_dependency_package_workspace_root(
            aware_toml_path=package.aware_toml_path,
            default_workspace_root=snapshot.repo_root,
            dependency_repo_roots=dependency_repo_roots,
        )
        package_branch_id = stable_object_config_graph_package_branch_id(
            workspace_root=package_workspace_root,
            aware_toml_path=package.aware_toml_path,
            package_name=package.package_name,
            fqn_prefix=package.spec.package.fqn_prefix,
        )
        try:
            result = await materialize_object_config_graph_package_leaf_from_manifest(
                runtime=runtime,
                index=index,
                actor_id=actor_id,
                branch_id=branch_id,
                workspace_root=package_workspace_root,
                aware_toml_path=package.aware_toml_path,
                package_branch_id=package_branch_id,
                external_graphs=dependency_graphs,
                collect_telemetry=False,
            )
        except Exception as exc:
            raise RuntimeError(
                "Direct Meta runtime package OCG materialization failed for API dependency: "
                f"package_name={package.package_name!r} "
                f"aware_toml_path={package.aware_toml_path.as_posix()!r} "
                f"package_branch_id={package_branch_id!s} "
                f"error_type={type(exc).__name__!r} "
                f"error={str(exc)!r}"
            ) from exc
        graph = result.object_config_graph
        if graph.id is None:
            raise RuntimeError(
                "Direct Meta runtime package OCG materialization returned an ObjectConfigGraph without id "
                f"for API dependency package={package.package_name!r}"
            )
        if (
            include_object_config_graph
            and not _accessible_graph_matches_dependency_package(
                package=package,
                graph=graph,
            )
        ):
            raise RuntimeError(
                "Direct Meta runtime package OCG materialization returned mismatched package graph "
                "for API dependency: "
                f"expected_package={package.package_name!r} "
                f"expected_fqn_prefix={(package.spec.package.fqn_prefix or '').strip()!r} "
                f"got_name={_object_config_graph_package_name(graph)!r} "
                f"got_fqn_prefix={_object_config_graph_fqn_prefix(graph)!r}"
            )
        if (
            _object_config_graph_fqn_prefix(graph)
            != (package.spec.package.fqn_prefix or "").strip()
        ):
            raise RuntimeError(
                "Direct Meta runtime package OCG materialization returned mismatched fqn_prefix "
                "for API dependency: "
                f"package={package.package_name!r} "
                f"expected={(package.spec.package.fqn_prefix or '').strip()!r} "
                f"got={_object_config_graph_fqn_prefix(graph)!r}"
            )
        graph = _ensure_dependency_object_projection_graphs(
            package=package,
            graph=graph,
            graphs_by_package_name=graphs_by_package_name,
        )
        graphs_by_package_name[package.package_name] = graph
        ordered_graphs.append(graph)
        logger.info(
            "API Meta dependency package direct materialization finished: package=%s position=%d/%d "
            "nodes=%d duration=%.3fs",
            package.package_name,
            package_index,
            len(dependency_packages),
            len(graph.object_config_graph_nodes),
            perf_counter() - package_started_at,
        )

    return canonicalize_api_accessible_dependency_graphs(
        accessible_graphs=_dedupe_accessible_graphs(
            (
                *ordered_graphs,
                *_unconsumed_accessible_graphs(
                    dependency_packages=dependency_packages,
                    accessible_graphs=accessible_graphs,
                ),
            )
        )
    )


def _unconsumed_accessible_graphs(
    *,
    dependency_packages: Sequence[object],
    accessible_graphs: Sequence[ObjectConfigGraph],
) -> tuple[ObjectConfigGraph, ...]:
    return tuple(
        graph
        for graph in accessible_graphs
        if not any(
            _accessible_graph_matches_dependency_package(package=package, graph=graph)
            for package in dependency_packages
        )
    )


async def resolve_source_owned_api_dto_export_accessible_graphs(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    branch_id: UUID,
    workspace_root: Path,
    api_toml_path: Path,
    accessible_graphs: Sequence[ObjectConfigGraph] = (),
    dependency_repo_roots: Sequence[str | Path] = (),
    phase_timings_s: dict[str, float] | None = None,
) -> tuple[ObjectConfigGraph, ...]:
    timings = phase_timings_s if phase_timings_s is not None else {}
    resolved_input_accessible_graphs = tuple(accessible_graphs)
    with _record_phase(
        timings,
        "pre_resolve_api_package_dependency_context.workspace_snapshot",
    ):
        snapshot = APIWorkspace.from_toml(
            toml_path=api_toml_path.resolve(),
            repo_root=workspace_root.resolve(),
        ).build_snapshot()
    if not _source_owned_api_dto_export_package_names(snapshot=snapshot):
        return resolved_input_accessible_graphs
    with _record_phase(
        timings,
        "pre_resolve_api_package_dependency_context."
        "load_complete_accessible_dependency_graphs_runtime_artifact",
    ):
        complete_artifact_graphs = (
            _complete_dependency_context_graphs_from_runtime_artifact(
                snapshot=snapshot,
                dependency_repo_roots=dependency_repo_roots,
            )
        )
    if complete_artifact_graphs is not None:
        refresh_package_names = (
            _source_owned_api_dto_export_graph_refresh_package_names(
                snapshot=snapshot,
                accessible_graphs=complete_artifact_graphs,
                dependency_repo_roots=dependency_repo_roots,
            )
        )
        if not refresh_package_names:
            return _dedupe_accessible_graphs(
                (*resolved_input_accessible_graphs, *complete_artifact_graphs)
            )
        refresh_input_graphs = _drop_accessible_dependency_package_graphs(
            dependency_packages=_resolve_api_dependency_packages(
                snapshot=snapshot,
                dependency_repo_roots=dependency_repo_roots,
            ),
            accessible_graphs=complete_artifact_graphs,
            package_names=refresh_package_names,
        )
        with _record_phase(
            timings,
            "pre_resolve_api_package_dependency_context."
            "refresh_stale_source_owned_api_dto_export_graphs",
        ):
            refreshed_graphs = (
                await build_api_accessible_dependency_graphs_via_meta_runtime(
                    snapshot=snapshot,
                    runtime=runtime,
                    index=index,
                    actor_id=actor_id,
                    branch_id=branch_id,
                    target_projection_hash=find_meta_graph_projection_hash_by_name(
                        index=index,
                        projection_name="ObjectConfigGraphPackage",
                    ),
                    object_config_graph_projection_hash=(
                        find_meta_graph_projection_hash_by_name(
                            index=index,
                            projection_name="ObjectConfigGraph",
                        )
                    ),
                    accessible_graphs=refresh_input_graphs,
                    dependency_repo_roots=dependency_repo_roots,
                )
            )
        return _dedupe_accessible_graphs(
            (*resolved_input_accessible_graphs, *refreshed_graphs)
        )
    with _record_phase(
        timings,
        "pre_resolve_api_package_dependency_context."
        "load_available_runtime_dependency_graphs",
    ):
        available_runtime_graphs = (
            _available_dependency_context_graphs_from_runtime_artifacts(
                snapshot=snapshot,
                phase_timings_s=timings,
                dependency_repo_roots=dependency_repo_roots,
            )
        )
    resolved_input_accessible_graphs = _dedupe_accessible_graphs(
        (*resolved_input_accessible_graphs, *available_runtime_graphs)
    )
    with _record_phase(
        timings,
        "pre_resolve_api_package_dependency_context.projection_hashes",
    ):
        object_config_graph_projection_hash = find_meta_graph_projection_hash_by_name(
            index=index,
            projection_name="ObjectConfigGraph",
        )
        object_config_graph_package_projection_hash = (
            find_meta_graph_projection_hash_by_name(
                index=index,
                projection_name="ObjectConfigGraphPackage",
            )
        )
    with _record_phase(
        timings,
        "pre_resolve_api_package_dependency_context."
        "compile_source_owned_api_dto_export_graphs",
    ):
        source_owned_accessible_graphs = (
            await build_api_accessible_dependency_graphs_via_meta_runtime(
                snapshot=snapshot,
                runtime=runtime,
                index=index,
                actor_id=actor_id,
                branch_id=branch_id,
                target_projection_hash=object_config_graph_package_projection_hash,
                object_config_graph_projection_hash=(
                    object_config_graph_projection_hash
                ),
                accessible_graphs=resolved_input_accessible_graphs,
                dependency_repo_roots=dependency_repo_roots,
            )
        )
    return _dedupe_accessible_graphs(
        (*resolved_input_accessible_graphs, *source_owned_accessible_graphs)
    )


def _drop_accessible_dependency_package_graphs(
    *,
    dependency_packages: Sequence[object],
    accessible_graphs: Sequence[ObjectConfigGraph],
    package_names: Sequence[str],
) -> tuple[ObjectConfigGraph, ...]:
    package_name_set = {package_name for package_name in package_names if package_name}
    if not package_name_set:
        return tuple(accessible_graphs)
    graphs_by_package_name = _accessible_graphs_by_dependency_package_name(
        dependency_packages=dependency_packages,
        accessible_graphs=accessible_graphs,
    )
    excluded_graph_ids = {
        graph.id
        for package_name, graph in graphs_by_package_name.items()
        if package_name in package_name_set
    }
    return tuple(
        graph for graph in accessible_graphs if graph.id not in excluded_graph_ids
    )


def _resolve_dependency_package_workspace_root(
    *,
    aware_toml_path: Path,
    default_workspace_root: Path,
    dependency_repo_roots: Sequence[str | Path] = (),
) -> Path:
    resolved_toml_path = aware_toml_path.expanduser().resolve()
    for candidate_root in _candidate_dependency_package_workspace_roots(
        default_workspace_root=default_workspace_root,
        dependency_repo_roots=dependency_repo_roots,
    ):
        if _is_relative_to(resolved_toml_path, candidate_root):
            return candidate_root
    return default_workspace_root.resolve()


def _candidate_dependency_package_workspace_roots(
    *,
    default_workspace_root: Path,
    dependency_repo_roots: Sequence[str | Path] = (),
) -> tuple[Path, ...]:
    roots: list[Path] = []
    seen: set[Path] = set()

    def add(path: Path) -> None:
        resolved = path.expanduser().resolve()
        if resolved in seen:
            return
        if not resolved.exists() or not resolved.is_dir():
            return
        roots.append(resolved)
        seen.add(resolved)

    add(default_workspace_root)
    for root in dependency_repo_roots:
        add(Path(root))
    for key in ("AWARE_KERNEL_REPO_ROOT", "AWARE_REPOSITORY_ROOT"):
        raw = (os.getenv(key) or "").strip()
        if raw:
            add(Path(raw))
    return tuple(roots)


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _ensure_dependency_object_projection_graphs(
    *,
    package: object,
    graph: ObjectConfigGraph,
    graphs_by_package_name: Mapping[str, ObjectConfigGraph],
) -> ObjectConfigGraph:
    if graph.object_projection_graphs or not graph.object_projection_graph_declarations:
        return graph
    dependencies = getattr(getattr(package, "spec", None), "dependencies", ())
    external_graphs = [
        graphs_by_package_name[dependency.package_name]
        for dependency in dependencies
        if dependency.package_name in graphs_by_package_name
    ]
    graph.object_projection_graphs = build_object_projection_graphs(
        graph,
        external_graphs=external_graphs,
        provision_portals=False,
    )
    return graph


def _json_equivalent(left: object, right: object) -> bool:
    return json.dumps(left, sort_keys=True, default=str) == json.dumps(
        right,
        sort_keys=True,
        default=str,
    )


def _api_package_manifest_truth_is_current(
    *,
    api_package: ApiPackage,
    api_id: UUID,
    api_object_instance_graph_commit_id: UUID | None,
    source_code_package_id: UUID | None,
    fqn_prefix: str | None,
    version_number: int,
    title: str | None,
    description: str | None,
    aware_api_version: int,
    manifest_relative_path: str | None,
    package_root: str,
    sources_root: str,
    include_paths: JsonArray,
    exclude_paths: JsonArray,
    force_fresh_scan: bool,
    compilation_mode: str,
    dependencies: JsonArray,
    targets: JsonObject,
    language_package_refs: Sequence[ApiPackageLanguagePackageSnapshotRef] | None = (),
) -> bool:
    return not _api_package_manifest_truth_mismatch_keys(
        api_package=api_package,
        api_id=api_id,
        api_object_instance_graph_commit_id=api_object_instance_graph_commit_id,
        source_code_package_id=source_code_package_id,
        fqn_prefix=fqn_prefix,
        version_number=version_number,
        title=title,
        description=description,
        aware_api_version=aware_api_version,
        manifest_relative_path=manifest_relative_path,
        package_root=package_root,
        sources_root=sources_root,
        include_paths=include_paths,
        exclude_paths=exclude_paths,
        force_fresh_scan=force_fresh_scan,
        compilation_mode=compilation_mode,
        dependencies=dependencies,
        targets=targets,
        language_package_refs=language_package_refs,
    )


def _api_package_manifest_truth_mismatch_keys(
    *,
    api_package: ApiPackage,
    api_id: UUID,
    api_object_instance_graph_commit_id: UUID | None,
    source_code_package_id: UUID | None,
    fqn_prefix: str | None,
    version_number: int,
    title: str | None,
    description: str | None,
    aware_api_version: int,
    manifest_relative_path: str | None,
    package_root: str,
    sources_root: str,
    include_paths: JsonArray,
    exclude_paths: JsonArray,
    force_fresh_scan: bool,
    compilation_mode: str,
    dependencies: JsonArray,
    targets: JsonObject,
    language_package_refs: Sequence[ApiPackageLanguagePackageSnapshotRef] | None = (),
) -> tuple[str, ...]:
    mismatch_keys: list[str] = []
    if api_package.api_id != api_id:
        mismatch_keys.append("api_id")
    if (
        api_object_instance_graph_commit_id is not None
        and api_package.api_object_instance_graph_commit_id
        != api_object_instance_graph_commit_id
    ):
        mismatch_keys.append("api_object_instance_graph_commit_id")
    if (
        source_code_package_id is not None
        and api_package.source_code_package_id != source_code_package_id
    ):
        mismatch_keys.append("source_code_package_id")
    if api_package.fqn_prefix != fqn_prefix:
        mismatch_keys.append("fqn_prefix")
    if api_package.version_number != version_number:
        mismatch_keys.append("version_number")
    if api_package.title != title:
        mismatch_keys.append("title")
    if api_package.description != description:
        mismatch_keys.append("description")
    if api_package.aware_api_version != aware_api_version:
        mismatch_keys.append("aware_api_version")
    if api_package.manifest_relative_path != manifest_relative_path:
        mismatch_keys.append("manifest_relative_path")
    if api_package.package_root != package_root:
        mismatch_keys.append("package_root")
    if api_package.sources_root != sources_root:
        mismatch_keys.append("sources_root")
    if not _json_equivalent(api_package.include_paths, include_paths):
        mismatch_keys.append("include_paths")
    if not _json_equivalent(api_package.exclude_paths, exclude_paths):
        mismatch_keys.append("exclude_paths")
    if api_package.force_fresh_scan is not force_fresh_scan:
        mismatch_keys.append("force_fresh_scan")
    if api_package.compilation_mode != compilation_mode:
        mismatch_keys.append("compilation_mode")
    if not _json_equivalent(api_package.dependencies, dependencies):
        mismatch_keys.append("dependencies")
    if not _json_equivalent(api_package.targets, targets):
        mismatch_keys.append("targets")
    if language_package_refs is not None and (
        _api_language_package_signature(api_package.language_packages)
        != _api_language_package_ref_signature(language_package_refs)
    ):
        mismatch_keys.append("language_packages")
    return tuple(mismatch_keys)


def _api_language_package_signature(
    language_packages: Sequence[object],
) -> tuple[tuple[object, ...], ...]:
    return tuple(
        sorted(
            (
                getattr(item, "code_package_id", None),
                (getattr(item, "package_name", "") or "").strip(),
                _enum_value(getattr(item, "language", "")),
                (getattr(item, "import_root", "") or "").strip(),
                (getattr(item, "manifest_relative_path", "") or "").strip(),
                (getattr(item, "package_root", "") or "").strip() or ".",
                (getattr(item, "role", "") or "").strip() or "public_package",
                (
                    (getattr(item, "output_key", "") or "").strip()
                    or "python.public_package"
                ),
                tuple(getattr(item, "include_paths", ()) or ()),
                tuple(getattr(item, "exclude_paths", ()) or ()),
            )
            for item in language_packages
        )
    )


def _api_language_package_ref_signature(
    language_package_refs: Sequence[ApiPackageLanguagePackageSnapshotRef],
) -> tuple[tuple[object, ...], ...]:
    return tuple(
        sorted(
            (
                item.code_package_id,
                (item.package_name or "").strip(),
                item.language.value,
                (item.import_root or "").strip(),
                (item.manifest_relative_path or "").strip(),
                (item.package_root or "").strip() or ".",
                (item.role or "").strip() or "public_package",
                (item.output_key or "").strip() or "python.public_package",
                tuple(item.include_paths or ()),
                tuple(item.exclude_paths or ()),
            )
            for item in language_package_refs
        )
    )


@contextmanager
def _record_phase(
    phase_timings_s: dict[str, float],
    phase_name: str,
) -> Iterator[None]:
    started_at = perf_counter()
    logger.info("API package materialization phase started: %s", phase_name)
    _emit_api_materialization_subphase_progress(
        subphase_name=phase_name,
        status="running",
    )
    try:
        yield
    except Exception as exc:
        duration_s = _round_duration_s(perf_counter() - started_at)
        phase_timings_s[phase_name] = duration_s
        _emit_api_materialization_subphase_progress(
            subphase_name=phase_name,
            status="failed",
            duration_s=duration_s,
            error=str(exc),
            detail_payload={"error_type": type(exc).__name__},
        )
        logger.info(
            "API package materialization phase failed: %s (%.6fs)",
            phase_name,
            duration_s,
        )
        raise
    else:
        duration_s = _round_duration_s(perf_counter() - started_at)
        phase_timings_s[phase_name] = duration_s
        _emit_api_materialization_subphase_progress(
            subphase_name=phase_name,
            status="succeeded",
            duration_s=duration_s,
        )
        logger.info(
            "API package materialization phase finished: %s (%.6fs)",
            phase_name,
            duration_s,
        )


@contextmanager
def _api_materialization_progress_context(
    *,
    progress_callback: ApiMaterializationProgressCallback | None,
    detail_payload: Mapping[str, object],
) -> Iterator[None]:
    callback_token = _API_MATERIALIZATION_PROGRESS_CALLBACK.set(progress_callback)
    detail_token = _API_MATERIALIZATION_PROGRESS_DETAIL.set(dict(detail_payload))
    try:
        yield
    finally:
        _API_MATERIALIZATION_PROGRESS_DETAIL.reset(detail_token)
        _API_MATERIALIZATION_PROGRESS_CALLBACK.reset(callback_token)


def _emit_api_materialization_subphase_progress(
    *,
    subphase_name: str,
    status: str,
    duration_s: float | None = None,
    error: str | None = None,
    detail_payload: Mapping[str, object] | None = None,
) -> None:
    callback = _API_MATERIALIZATION_PROGRESS_CALLBACK.get()
    if callback is None:
        return
    detail = dict(_API_MATERIALIZATION_PROGRESS_DETAIL.get() or {})
    detail["subphase_name"] = subphase_name
    detail.update(dict(detail_payload or {}))
    payload: dict[str, object] = {
        "phase_name": "api.package.subphase",
        "status": status,
        "detail_payload": detail,
    }
    if duration_s is not None and status != "running":
        payload["duration_s"] = _round_duration_s(duration_s)
    if error:
        payload["error"] = error
    try:
        result = callback(payload)
        if isawaitable(result):
            _schedule_api_materialization_progress_awaitable(result)
    except Exception:
        return


def _schedule_api_materialization_progress_awaitable(result: object) -> None:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        close = getattr(result, "close", None)
        if callable(close):
            close()
        return
    task = asyncio.ensure_future(cast(Awaitable[object], result))
    task.add_done_callback(_consume_api_materialization_progress_task)


def _consume_api_materialization_progress_task(task: asyncio.Future[object]) -> None:
    try:
        task.result()
    except Exception:
        return


def resolve_api_package_materialization_spec(
    *,
    api_toml_path: Path,
    workspace_root: Path,
    accessible_graphs: Sequence[ObjectConfigGraph] = (),
    phase_timings_s: dict[str, float] | None = None,
    dependency_repo_roots: Sequence[str | Path] = (),
) -> ApiPackageMaterializationSpec:
    timings = phase_timings_s if phase_timings_s is not None else {}
    with _record_phase(
        timings, "resolve_api_package_materialization_spec.resolve_paths"
    ):
        resolved_api_toml_path = api_toml_path.resolve()
        resolved_workspace_root = workspace_root.resolve()
    with _record_phase(
        timings, "resolve_api_package_materialization_spec.workspace_from_toml"
    ):
        workspace = APIWorkspace.from_toml(
            toml_path=resolved_api_toml_path,
            repo_root=resolved_workspace_root,
        )
    with _record_phase(
        timings, "resolve_api_package_materialization_spec.build_snapshot"
    ):
        snapshot = workspace.build_snapshot()
    with _record_phase(
        timings,
        "resolve_api_package_materialization_spec.context_dependency_class_config_ids",
    ):
        dependency_graph_context = _api_dependency_graph_context(
            snapshot=snapshot,
            accessible_graphs=accessible_graphs,
            phase_timings_s=timings,
            dependency_repo_roots=dependency_repo_roots,
        )
    with _record_phase(
        timings, "resolve_api_package_materialization_spec.build_api_compile_plan"
    ):
        from ..ir import (
            api_compile_plan_artifact_hash,
            build_api_compile_plan,
            encode_api_compile_plan_payload as encode_api_runtime_compile_plan_payload,
        )

        compile_plan = build_api_compile_plan(
            snapshot=snapshot,
            dependency_class_config_ids=dependency_graph_context.class_config_ids,
            phase_timings_s=timings,
            dependency_repo_roots=dependency_repo_roots,
        )
        runtime_compile_plan_hash = api_compile_plan_artifact_hash(
            plan=compile_plan,
        )
    with _record_phase(
        timings, "resolve_api_package_materialization_spec.validate_api_ownership"
    ):
        api_ownership = compile_plan.api_ownership
        if len(api_ownership) != 1:
            discovered_api_names = sorted(item.name for item in api_ownership)
            raise RuntimeError(
                "API package materialization v0 requires exactly one canonical `api` declaration per aware.api.toml "
                + f"package: api_toml_path={resolved_api_toml_path} discovered={discovered_api_names!r}"
            )
        canonical_api = api_ownership[0]
    with _record_phase(
        timings, "resolve_api_package_materialization_spec.validate_package_fields"
    ):
        package_name = (snapshot.spec.api.package_name or "").strip()
        if not package_name:
            raise RuntimeError(
                "API package materialization requires non-empty [api].package_name in aware.api.toml: "
                + str(resolved_api_toml_path)
            )
        package_fqn_prefix = (snapshot.spec.api.fqn_prefix or "").strip()
        if not package_fqn_prefix:
            raise RuntimeError(
                "API package materialization requires non-empty [api].fqn_prefix in aware.api.toml: "
                + str(resolved_api_toml_path)
            )
    with _record_phase(
        timings, "resolve_api_package_materialization_spec.build_api_endpoint_catalog"
    ):
        api_endpoint_catalog = _build_api_endpoint_catalog(plan=compile_plan)
    with _record_phase(
        timings,
        "resolve_api_package_materialization_spec.encode_api_compile_plan_payload",
    ):
        compile_plan_payload = _encode_api_compile_plan_payload(plan=compile_plan)
        runtime_compile_plan_payload = encode_api_runtime_compile_plan_payload(
            plan=compile_plan,
        )
    with _record_phase(
        timings, "resolve_api_package_materialization_spec.assemble_result"
    ):
        return ApiPackageMaterializationSpec(
            api_toml_path=resolved_api_toml_path,
            workspace_root=resolved_workspace_root,
            manifest_spec=snapshot.spec,
            package_name=package_name,
            package_fqn_prefix=package_fqn_prefix,
            api_name=canonical_api.name,
            api_source_path=canonical_api.source_path,
            source_files=tuple(path.as_posix() for path in snapshot.source_files),
            api_endpoint_catalog=api_endpoint_catalog,
            compile_plan_payload=compile_plan_payload,
            runtime_compile_plan_payload=runtime_compile_plan_payload,
            dependency_accessible_graphs=dependency_graph_context.accessible_graphs,
            dependency_graph_context_source=dependency_graph_context.source,
            runtime_compile_plan_hash=runtime_compile_plan_hash,
        )


async def materialize_api_package_from_manifest(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    branch_id: UUID,
    workspace_root: Path,
    api_toml_path: Path,
    accessible_graphs: Sequence[ObjectConfigGraph] = (),
    dependency_repo_roots: Sequence[str | Path] = (),
    post_step_tool_env_by_tool_id: Mapping[str, Mapping[str, str]] | None = None,
    post_step_executable_overrides_by_tool_id: (
        Mapping[str, Mapping[str, str]] | None
    ) = None,
    progress_callback: ApiMaterializationProgressCallback | None = None,
) -> ApiPackageMaterializationResult:
    with _api_materialization_progress_context(
        progress_callback=progress_callback,
        detail_payload={
            "materialization_kind": "api_manifest",
            "api_toml_path": api_toml_path.as_posix(),
            "workspace_root": workspace_root.as_posix(),
        },
    ):
        return await _materialize_api_package_from_manifest_impl(
            runtime=runtime,
            index=index,
            actor_id=actor_id,
            branch_id=branch_id,
            workspace_root=workspace_root,
            api_toml_path=api_toml_path,
            accessible_graphs=accessible_graphs,
            dependency_repo_roots=dependency_repo_roots,
            post_step_tool_env_by_tool_id=post_step_tool_env_by_tool_id,
            post_step_executable_overrides_by_tool_id=(
                post_step_executable_overrides_by_tool_id
            ),
        )


async def _materialize_api_package_from_manifest_impl(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    branch_id: UUID,
    workspace_root: Path,
    api_toml_path: Path,
    accessible_graphs: Sequence[ObjectConfigGraph] = (),
    dependency_repo_roots: Sequence[str | Path] = (),
    post_step_tool_env_by_tool_id: Mapping[str, Mapping[str, str]] | None = None,
    post_step_executable_overrides_by_tool_id: (
        Mapping[str, Mapping[str, str]] | None
    ) = None,
) -> ApiPackageMaterializationResult:
    materialization_started_at = perf_counter()
    phase_timings_s: dict[str, float] = {}
    resolved_input_accessible_graphs = (
        await resolve_source_owned_api_dto_export_accessible_graphs(
            runtime=runtime,
            index=index,
            actor_id=actor_id,
            branch_id=branch_id,
            workspace_root=workspace_root,
            api_toml_path=api_toml_path,
            accessible_graphs=accessible_graphs,
            dependency_repo_roots=dependency_repo_roots,
            phase_timings_s=phase_timings_s,
        )
    )
    with _record_phase(phase_timings_s, "resolve_api_package_materialization_spec"):
        spec = resolve_api_package_materialization_spec(
            api_toml_path=api_toml_path,
            workspace_root=workspace_root,
            accessible_graphs=resolved_input_accessible_graphs,
            phase_timings_s=phase_timings_s,
            dependency_repo_roots=dependency_repo_roots,
        )
    with _record_phase(phase_timings_s, "build_api_workspace_snapshot"):
        snapshot = APIWorkspace.from_toml(
            toml_path=spec.api_toml_path,
            repo_root=spec.workspace_root,
        ).build_snapshot()
    sources_root = (snapshot.package_root / snapshot.spec.build.sources_dir).resolve()
    with _record_phase(phase_timings_s, "resolve_stable_ids"):
        source_code_package_config_id = _api_source_code_package_config_id()
        expected_api_id = stable_api_id(name=spec.api_name)
        expected_api_package_id = stable_api_package_id(name=spec.package_name)
        expected_source_code_package_id = stable_code_package_id(
            code_package_config_id=source_code_package_config_id,
            package_name=spec.package_name,
            language=CodeLanguage.aware.value,
        )
    with _record_phase(phase_timings_s, "resolve_projection_hashes"):
        api_projection_hash = find_meta_graph_projection_hash_by_name(
            index=index,
            projection_name="Api",
        )
        api_package_projection_hash = find_meta_graph_projection_hash_by_name(
            index=index,
            projection_name="ApiPackage",
        )
        code_package_projection_hash = find_meta_graph_projection_hash_by_name(
            index=index,
            projection_name="CodePackage",
        )
        object_config_graph_projection_hash = find_meta_graph_projection_hash_by_name(
            index=index,
            projection_name="ObjectConfigGraph",
        )
        object_config_graph_package_projection_hash = (
            find_meta_graph_projection_hash_by_name(
                index=index,
                projection_name="ObjectConfigGraphPackage",
            )
        )
    api_lane_context = MaterializationLaneContext(
        branch_id=branch_id,
        projection_hash=api_projection_hash,
    )
    resolved_accessible_graphs = _dedupe_accessible_graphs(
        (*spec.dependency_accessible_graphs, *resolved_input_accessible_graphs)
    )
    if snapshot.spec.dependencies:
        if (
            resolved_accessible_graphs
            and spec.dependency_graph_context_source
            == "runtime_accessible_dependency_graphs_artifact"
        ):
            graph_phase_name = (
                "resolve_api_accessible_dependency_graphs_reuse_runtime_artifact"
            )
        elif resolved_accessible_graphs:
            graph_phase_name = "resolve_api_accessible_dependency_graphs"
        else:
            graph_phase_name = (
                "resolve_api_accessible_dependency_graphs_from_dependency_artifacts"
            )
        with _record_phase(phase_timings_s, graph_phase_name):
            reusable_accessible_graphs = (
                _api_dependency_graph_context_reusable_graphs_for_materialization(
                    snapshot=snapshot,
                    accessible_graphs=resolved_accessible_graphs,
                    source=spec.dependency_graph_context_source,
                    dependency_repo_roots=dependency_repo_roots,
                )
            )
            if reusable_accessible_graphs is not None:
                logger.info(
                    "API dependency graph resolution reused %s without Meta "
                    "runtime rebuild: api_package=%s dependency_graphs=%d",
                    spec.dependency_graph_context_source,
                    snapshot.spec.api.package_name,
                    len(reusable_accessible_graphs),
                )
                resolved_accessible_graphs = reusable_accessible_graphs
            elif not resolved_accessible_graphs:
                resolved_accessible_graphs = load_api_accessible_dependency_graphs(
                    snapshot=snapshot,
                    dependency_repo_roots=dependency_repo_roots,
                )
            else:
                resolved_accessible_graphs = await build_api_accessible_dependency_graphs_via_meta_runtime(
                    snapshot=snapshot,
                    runtime=runtime,
                    index=index,
                    actor_id=actor_id,
                    branch_id=branch_id,
                    target_projection_hash=object_config_graph_package_projection_hash,
                    object_config_graph_projection_hash=object_config_graph_projection_hash,
                    accessible_graphs=resolved_accessible_graphs,
                    dependency_repo_roots=dependency_repo_roots,
                )
    with _record_phase(phase_timings_s, "hydrate_api_from_head"):
        api = await _hydrate_lane_root_from_head(
            index=index,
            branch_id=branch_id,
            projection_hash=api_projection_hash,
            root_id=expected_api_id,
            root_type=Api,
        )
    if api is not None:
        with _record_phase(phase_timings_s, "validate_api_endpoint_catalog"):
            if not await _api_lane_has_endpoint_catalog(
                index=index,
                branch_id=branch_id,
                projection_hash=api_projection_hash,
                expected_api_id=expected_api_id,
                api_endpoint_catalog=spec.api_endpoint_catalog,
            ):
                _reset_generated_api_lane(
                    aware_root=FSCommitStore().aware_root,
                    branch_id=branch_id,
                    projection_hash=api_projection_hash,
                )
                api = None
    if api is None:
        with _record_phase(phase_timings_s, "reset_invalid_api_lane_if_needed"):
            existing_api_lane_head = await _lane_head_commit_id(
                branch_id=branch_id,
                projection_hash=api_projection_hash,
            )
            if existing_api_lane_head is not None:
                logger.info(
                    "API lane has a HEAD but expected Api root is missing; resetting generated lane "
                    "before provider-owned snapshot materialization (api_name=%s, branch_id=%s)",
                    spec.api_name,
                    branch_id,
                )
                _reset_generated_api_lane(
                    aware_root=FSCommitStore().aware_root,
                    branch_id=branch_id,
                    projection_hash=api_projection_hash,
                )
    api_receipt: MaterializationRunReceipt | None = None
    if api is None:
        with _record_phase(phase_timings_s, "materialize_api_compile_plan_ontology"):
            api_receipt = await materialize_api_compile_plan_ontology(
                runtime=runtime,
                index=index,
                actor_id=actor_id,
                lane=api_lane_context,
                compile_plan_payloads=(spec.compile_plan_payload,),
                accessible_graphs=resolved_accessible_graphs,
                phase_timings_s=phase_timings_s,
            )
        if api_receipt is None or not api_receipt.steps:
            raise RuntimeError(
                "API package materialization requires committed Api definition truth: "
                + str(spec.api_toml_path)
            )
        with _record_phase(phase_timings_s, "rehydrate_api_from_head"):
            api = await _hydrate_lane_root_from_head(
                index=index,
                branch_id=branch_id,
                projection_hash=api_projection_hash,
                root_id=expected_api_id,
                root_type=Api,
            )
    if api is None:
        raise RuntimeError(
            "API package materialization could not hydrate canonical Api after compile-plan materialization: "
            + f"api_name={spec.api_name!r}"
        )
    with _record_phase(phase_timings_s, "resolve_api_semantic_root_commit_id"):
        api_domain_head_commit_id = (
            api_receipt.steps[-1].commit_id
            if api_receipt is not None and api_receipt.steps
            else await _lane_head_commit_id(
                branch_id=branch_id,
                projection_hash=api_projection_hash,
            )
        )
        api_object_instance_graph_commit_id = (
            await _object_instance_graph_commit_id_from_domain_commit(
                branch_id=branch_id,
                projection_hash=api_projection_hash,
                domain_commit_id=api_domain_head_commit_id,
            )
            if api_domain_head_commit_id is not None
            else None
        )
    if api_object_instance_graph_commit_id is None:
        raise RuntimeError(
            "API package materialization requires a committed Api semantic root "
            f"before building ApiPackage: api_name={spec.api_name!r}"
        )

    with _record_phase(
        phase_timings_s,
        "reset_invalid_source_code_package_lane_if_needed",
    ):
        await _reset_code_package_lane_if_root_mismatch(
            branch_id=branch_id,
            projection_hash=code_package_projection_hash,
            expected_code_package_id=expected_source_code_package_id,
            package_name=spec.package_name,
            target_label="api_source",
        )
    with _record_phase(phase_timings_s, "hydrate_code_package_from_head"):
        code_package = await _hydrate_lane_root_from_head(
            index=index,
            branch_id=branch_id,
            projection_hash=code_package_projection_hash,
            root_id=expected_source_code_package_id,
            root_type=CodePackage,
        )
    manifest_relative_path = _relative_to(
        path=spec.api_toml_path,
        root=spec.workspace_root,
        label="aware.api.toml",
    )
    package_root_relative = _relative_to(
        path=snapshot.package_root,
        root=spec.workspace_root,
        label="package_root",
    )
    sources_root_relative = _relative_to(
        path=sources_root,
        root=spec.workspace_root,
        label="sources_root",
    )
    with _record_phase(phase_timings_s, "read_source_texts"):
        source_texts_by_relative_path: dict[str, str] = {}
        for source_file in snapshot.source_files:
            source_path = (snapshot.package_root / source_file).resolve()
            source_texts_by_relative_path[source_file.as_posix()] = (
                source_path.read_text(encoding="utf-8")
            )
    with _record_phase(phase_timings_s, "commit_code_package_text_snapshot"):
        source_snapshot = await commit_code_package_text_snapshot(
            index=index,
            actor_id=actor_id,
            branch_id=branch_id,
            projection_hash=code_package_projection_hash,
            code_package_config_id=source_code_package_config_id,
            package_name=spec.package_name,
            language=CodeLanguage.aware,
            surface="api",
            manifest_kind="aware_api_toml",
            manifest_relative_path=manifest_relative_path,
            package_root=package_root_relative,
            sources_root=sources_root_relative,
            fqn_prefix=spec.package_fqn_prefix,
            source_texts_by_relative_path=source_texts_by_relative_path,
        )
        code_package = source_snapshot.code_package
    with _record_phase(phase_timings_s, "resolve_source_code_package_commit_id"):
        source_object_instance_graph_commit_id = (
            source_snapshot.object_instance_graph_commit_id
        )
    api_package_fqn_prefix = (snapshot.spec.api.fqn_prefix or "").strip() or None
    api_package_include_paths = JsonArray(snapshot.spec.build.include_paths)
    api_package_exclude_paths = JsonArray(snapshot.spec.build.exclude_paths)
    api_package_compilation_mode = cast(
        str, _enum_value(snapshot.spec.build.compilation_mode)
    )
    api_package_dependencies = _api_package_dependencies_payload(snapshot.spec)
    api_package_targets = _api_package_targets_payload(snapshot.spec)
    with _record_phase(phase_timings_s, "materialize_api_product_runtime_artifacts"):
        (
            product_runtime_compile_result,
            dart_public_package_compile_result,
            language_post_step_receipts,
        ) = _materialize_api_product_runtime_artifacts_for_language_packages(
            api_toml_path=spec.api_toml_path,
            workspace_root=spec.workspace_root,
            snapshot=snapshot,
            runtime_compile_plan_payload=spec.runtime_compile_plan_payload,
            accessible_graphs=resolved_accessible_graphs,
            dependency_repo_roots=dependency_repo_roots,
            phase_timings_s=phase_timings_s,
            post_step_tool_env_by_tool_id=post_step_tool_env_by_tool_id,
            post_step_executable_overrides_by_tool_id=(
                post_step_executable_overrides_by_tool_id
            ),
        )
    with _record_phase(phase_timings_s, "materialize_api_language_code_packages"):
        language_code_package_refs = await _materialize_api_language_code_packages(
            index=index,
            actor_id=actor_id,
            code_package_projection_hash=code_package_projection_hash,
            workspace_root=spec.workspace_root,
            snapshot=snapshot,
        )
    language_code_packages = tuple(
        ref.code_package for ref in language_code_package_refs
    )
    language_package_snapshot_refs = _api_package_language_package_snapshots(
        language_code_package_refs=language_code_package_refs,
    )
    with _record_phase(phase_timings_s, "hydrate_api_package_from_head"):
        api_package = await _hydrate_lane_root_from_head(
            index=index,
            branch_id=branch_id,
            projection_hash=api_package_projection_hash,
            root_id=expected_api_package_id,
            root_type=ApiPackage,
        )
    api_package_snapshot = None
    if api_package is None:
        with _record_phase(phase_timings_s, "commit_api_package_manifest_snapshot"):
            api_package_snapshot = await commit_api_package_manifest_snapshot(
                index=index,
                actor_id=actor_id,
                branch_id=branch_id,
                projection_hash=api_package_projection_hash,
                package_name=spec.package_name,
                api_id=api.id,
                api_object_instance_graph_commit_id=api_object_instance_graph_commit_id,
                source_code_package_id=code_package.id,
                fqn_prefix=api_package_fqn_prefix,
                version_number=snapshot.spec.api.version_number,
                title=snapshot.spec.api.title,
                description=snapshot.spec.api.description,
                aware_api_version=snapshot.spec.aware_api,
                manifest_relative_path=manifest_relative_path,
                package_root=package_root_relative,
                sources_root=sources_root_relative,
                include_paths=api_package_include_paths,
                exclude_paths=api_package_exclude_paths,
                force_fresh_scan=snapshot.spec.build.force_fresh_scan,
                compilation_mode=api_package_compilation_mode,
                dependencies=api_package_dependencies,
                targets=api_package_targets,
                language_package_refs=language_package_snapshot_refs,
            )
            api_package = api_package_snapshot.api_package
    else:
        if api_package.api_id != api.id:
            raise RuntimeError(
                "API package materialization resolved committed ApiPackage with unexpected api_id: "
                + f"package_name={spec.package_name!r} expected={api.id} actual={api_package.api_id}"
            )
        with _record_phase(phase_timings_s, "check_api_package_manifest_truth"):
            package_manifest_truth_mismatches = _api_package_manifest_truth_mismatch_keys(
                api_package=api_package,
                api_id=api.id,
                api_object_instance_graph_commit_id=api_object_instance_graph_commit_id,
                source_code_package_id=code_package.id,
                fqn_prefix=api_package_fqn_prefix,
                version_number=snapshot.spec.api.version_number,
                title=snapshot.spec.api.title,
                description=snapshot.spec.api.description,
                aware_api_version=snapshot.spec.aware_api,
                manifest_relative_path=manifest_relative_path,
                package_root=package_root_relative,
                sources_root=sources_root_relative,
                include_paths=api_package_include_paths,
                exclude_paths=api_package_exclude_paths,
                force_fresh_scan=snapshot.spec.build.force_fresh_scan,
                compilation_mode=api_package_compilation_mode,
                dependencies=api_package_dependencies,
                targets=api_package_targets,
                language_package_refs=language_package_snapshot_refs,
            )
            package_manifest_truth_current = not package_manifest_truth_mismatches
            package_manifest_field_mismatches = (
                _api_package_manifest_truth_mismatch_keys(
                    api_package=api_package,
                    api_id=api.id,
                    api_object_instance_graph_commit_id=None,
                    source_code_package_id=code_package.id,
                    fqn_prefix=api_package_fqn_prefix,
                    version_number=snapshot.spec.api.version_number,
                    title=snapshot.spec.api.title,
                    description=snapshot.spec.api.description,
                    aware_api_version=snapshot.spec.aware_api,
                    manifest_relative_path=manifest_relative_path,
                    package_root=package_root_relative,
                    sources_root=sources_root_relative,
                    include_paths=api_package_include_paths,
                    exclude_paths=api_package_exclude_paths,
                    force_fresh_scan=snapshot.spec.build.force_fresh_scan,
                    compilation_mode=api_package_compilation_mode,
                    dependencies=api_package_dependencies,
                    targets=api_package_targets,
                    language_package_refs=None,
                )
            )
            package_manifest_fields_current = (
                package_manifest_truth_current or not package_manifest_field_mismatches
            )
            package_api_root_commit_id_only_mismatch = (
                not package_manifest_truth_current
                and package_manifest_fields_current
                and package_manifest_truth_mismatches
                == ("api_object_instance_graph_commit_id",)
            )
            package_api_root_equivalence_checked = False
            package_api_root_equivalence: bool | None = None
            if (
                not package_manifest_truth_current
                and package_manifest_fields_current
                and package_api_root_commit_id_only_mismatch
                and api_package.api_object_instance_graph_commit_id is not None
            ):
                package_api_root_equivalence_checked = True
                package_api_root_equivalence = (
                    await _api_roots_are_semantically_equivalent(
                        index=index,
                        branch_id=branch_id,
                        projection_hash=api_projection_hash,
                        api_id=api.id,
                        left_object_instance_graph_commit_id=(
                            api_package.api_object_instance_graph_commit_id
                        ),
                        right_object_instance_graph_commit_id=(
                            api_object_instance_graph_commit_id
                        ),
                    )
                )
        if package_manifest_truth_current:
            phase_timings_s["sync_api_package_manifest_truth_skipped_current"] = 0.0
        elif (
            package_api_root_commit_id_only_mismatch
            and package_api_root_equivalence is True
        ):
            phase_timings_s[
                "sync_api_package_manifest_truth_skipped_equivalent_api_root"
            ] = 0.0
        elif (
            package_api_root_commit_id_only_mismatch
            and package_api_root_equivalence_checked
            and package_api_root_equivalence is None
        ):
            phase_timings_s[
                "sync_api_package_manifest_truth_skipped_unresolved_api_commit_id_only"
            ] = 0.0
        else:
            logger.info(
                "API package manifest truth stale; syncing package=%s "
                "mismatches=%s field_mismatches=%s",
                spec.package_name,
                ",".join(package_manifest_truth_mismatches) or "(none)",
                ",".join(package_manifest_field_mismatches) or "(none)",
            )
            with _record_phase(phase_timings_s, "commit_api_package_manifest_snapshot"):
                api_package_snapshot = await commit_api_package_manifest_snapshot(
                    index=index,
                    actor_id=actor_id,
                    branch_id=branch_id,
                    projection_hash=api_package_projection_hash,
                    package_name=spec.package_name,
                    api_id=api.id,
                    api_object_instance_graph_commit_id=api_object_instance_graph_commit_id,
                    source_code_package_id=code_package.id,
                    fqn_prefix=api_package_fqn_prefix,
                    version_number=snapshot.spec.api.version_number,
                    title=snapshot.spec.api.title,
                    description=snapshot.spec.api.description,
                    aware_api_version=snapshot.spec.aware_api,
                    manifest_relative_path=manifest_relative_path,
                    package_root=package_root_relative,
                    sources_root=sources_root_relative,
                    include_paths=api_package_include_paths,
                    exclude_paths=api_package_exclude_paths,
                    force_fresh_scan=snapshot.spec.build.force_fresh_scan,
                    compilation_mode=api_package_compilation_mode,
                    dependencies=api_package_dependencies,
                    targets=api_package_targets,
                    language_package_refs=language_package_snapshot_refs,
                )
                api_package = api_package_snapshot.api_package
    if api_package.api_id != api.id:
        raise RuntimeError(
            "API package materialization resolved ApiPackage with unexpected api_id: "
            + f"package_name={spec.package_name!r} expected={api.id} actual={api_package.api_id}"
        )
    with _record_phase(phase_timings_s, "validate_api_language_packages"):
        _validate_api_language_package_bridges(
            api_package=api_package,
            language_code_packages=language_code_packages,
        )
    with _record_phase(phase_timings_s, "resolve_api_package_semantic_root_commit_id"):
        api_package_domain_commit_id = (
            api_package_snapshot.commit_id
            if api_package_snapshot is not None
            else await _lane_head_commit_id(
                branch_id=branch_id,
                projection_hash=api_package_projection_hash,
            )
        )
        api_package_object_instance_graph_commit_id = (
            await _object_instance_graph_commit_id_from_domain_commit(
                branch_id=branch_id,
                projection_hash=api_package_projection_hash,
                domain_commit_id=api_package_domain_commit_id,
            )
            if api_package_domain_commit_id is not None
            else None
        )

    phase_timings_s["total"] = _round_duration_s(
        perf_counter() - materialization_started_at
    )

    return ApiPackageMaterializationResult(
        api_toml_path=spec.api_toml_path,
        workspace_root=spec.workspace_root,
        manifest_spec=spec.manifest_spec,
        api=api,
        api_package=api_package,
        api_source_path=spec.api_source_path,
        source_files=spec.source_files,
        phase_timings_s=dict(sorted(phase_timings_s.items())),
        runtime_compile_plan_hash=spec.runtime_compile_plan_hash,
        api_endpoint_catalog=spec.api_endpoint_catalog,
        source_code_package_id=api_package.source_code_package_id,
        source_object_instance_graph_commit_id=source_object_instance_graph_commit_id,
        api_commit_id=(
            api_receipt.steps[-1].commit_id if api_receipt is not None else None
        ),
        api_head_commit_id=api_object_instance_graph_commit_id,
        api_object_instance_graph_commit_id=api_object_instance_graph_commit_id,
        package_commit_id=(
            api_package_snapshot.commit_id if api_package_snapshot is not None else None
        ),
        package_head_commit_id=api_package_object_instance_graph_commit_id,
        generated_dto_graph_count=0,
        generated_dto_class_config_count=0,
        language_code_package_ids=tuple(
            ref.code_package.id
            for ref in language_code_package_refs
            if ref.code_package.id is not None
        ),
        language_code_package_refs=tuple(
            ref.to_payload() for ref in language_code_package_refs
        ),
        product_runtime_compile_result=product_runtime_compile_result,
        dart_public_package_compile_result=dart_public_package_compile_result,
        language_post_step_receipts=language_post_step_receipts,
    )


def _materialize_api_product_runtime_artifacts_for_language_packages(
    *,
    api_toml_path: Path,
    workspace_root: Path,
    snapshot: APIWorkspaceSnapshot,
    runtime_compile_plan_payload: Mapping[str, object],
    accessible_graphs: Sequence[ObjectConfigGraph],
    dependency_repo_roots: Sequence[str | Path],
    phase_timings_s: dict[str, float],
    post_step_tool_env_by_tool_id: Mapping[str, Mapping[str, str]] | None,
    post_step_executable_overrides_by_tool_id: Mapping[str, Mapping[str, str]] | None,
) -> tuple[object, object | None, tuple[dict[str, object], ...]]:
    from aware_api_runtime.compile import (  # noqa: WPS433
        compile_api_workspace,
        compile_api_product_runtime_from_compile_plan_payload,
        refresh_api_workspace_from_runtime_artifacts,
    )

    use_compile_plan_product_runtime = bool(accessible_graphs)
    product_runtime_accessible_graphs: tuple[ObjectConfigGraph, ...] = ()
    if use_compile_plan_product_runtime:
        product_runtime_accessible_graphs = (
            build_generated_api_compile_plan_accessible_graphs(
                compile_plan_payload=runtime_compile_plan_payload,
                accessible_graphs=accessible_graphs,
            )
        )
        with _record_phase(
            phase_timings_s,
            "materialize_api_product_runtime_artifacts.python_service_protocol_from_compile_plan",
        ):
            compile_result = compile_api_product_runtime_from_compile_plan_payload(
                compile_plan_payload=runtime_compile_plan_payload,
                repo_root=workspace_root,
                source_api_toml_path=api_toml_path,
                accessible_graphs=product_runtime_accessible_graphs,
                dependency_repo_roots=dependency_repo_roots,
            )
    else:
        with _record_phase(
            phase_timings_s,
            "materialize_api_product_runtime_artifacts.python_service_protocol_from_manifest",
        ):
            compile_result = compile_api_workspace(
                toml_path=api_toml_path,
                repo_root=workspace_root,
                materialize_service_protocol=True,
                public_package_target_language=CodeLanguage.python,
                dependency_repo_roots=dependency_repo_roots,
            )
    dart_result = None
    post_step_receipts: tuple[dict[str, object], ...] = ()
    if snapshot.spec.targets.dart is not None:
        with _record_phase(
            phase_timings_s,
            "materialize_api_product_runtime_artifacts.dart_public_package_refresh_from_runtime_artifacts",
        ):
            dart_result = refresh_api_workspace_from_runtime_artifacts(
                toml_path=api_toml_path,
                repo_root=workspace_root,
                refresh_public_package=True,
                public_package_target_language=CodeLanguage.dart,
                accessible_graphs=(
                    product_runtime_accessible_graphs
                    if use_compile_plan_product_runtime
                    else None
                ),
                dependency_repo_roots=dependency_repo_roots,
                execute_language_post_steps=True,
                post_step_tool_env_by_tool_id=post_step_tool_env_by_tool_id,
                post_step_executable_overrides_by_tool_id=(
                    post_step_executable_overrides_by_tool_id
                ),
            )
        public_package_materialization = getattr(
            dart_result,
            "public_package_materialization",
            None,
        )
        materialization_result = getattr(
            public_package_materialization,
            "materialization_result",
            None,
        )
        post_step_receipts = tuple(
            dict(receipt)
            for receipt in getattr(materialization_result, "post_step_receipts", ())
            or ()
        )
    return compile_result, dart_result, post_step_receipts


async def materialize_api_package_from_compile_plan_input(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    branch_id: UUID,
    workspace_root: Path,
    compile_plan_payload: Mapping[str, object],
    compile_plan_path: Path | None = None,
    provider_payload: Mapping[str, object] | None = None,
    accessible_graphs: Sequence[ObjectConfigGraph] = (),
    progress_callback: ApiMaterializationProgressCallback | None = None,
) -> ApiCompilePlanPackageMaterializationResult:
    with _api_materialization_progress_context(
        progress_callback=progress_callback,
        detail_payload={
            "materialization_kind": "api_compile_plan_input",
            "compile_plan_path": (
                compile_plan_path.as_posix() if compile_plan_path is not None else None
            ),
            "workspace_root": workspace_root.as_posix(),
        },
    ):
        return await _materialize_api_package_from_compile_plan_input_impl(
            runtime=runtime,
            index=index,
            actor_id=actor_id,
            branch_id=branch_id,
            workspace_root=workspace_root,
            compile_plan_payload=compile_plan_payload,
            compile_plan_path=compile_plan_path,
            provider_payload=provider_payload,
            accessible_graphs=accessible_graphs,
        )


async def _materialize_api_package_from_compile_plan_input_impl(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    branch_id: UUID,
    workspace_root: Path,
    compile_plan_payload: Mapping[str, object],
    compile_plan_path: Path | None = None,
    provider_payload: Mapping[str, object] | None = None,
    accessible_graphs: Sequence[ObjectConfigGraph] = (),
) -> ApiCompilePlanPackageMaterializationResult:
    materialization_started_at = perf_counter()
    phase_timings_s: dict[str, float] = {}
    with _record_phase(phase_timings_s, "resolve_api_compile_plan_input"):
        resolved_workspace_root = workspace_root.resolve()
        payload = dict(
            _expect_mapping(
                compile_plan_payload,
                field_name="compile_plan_payload",
            )
        )
        resolved_compile_plan_path = (
            compile_plan_path.resolve() if compile_plan_path is not None else None
        )
        api_plans = _api_ontology_plans_from_compile_plan_payload(payload=payload)
        if len(api_plans) != 1:
            raise RuntimeError(
                "Generated API compile-plan materialization requires exactly one "
                f"canonical api declaration, got {len(api_plans)}"
            )
        api_plan = api_plans[0]
        package_name = _required_compile_plan_text(
            payload.get("package_name"),
            field_name="package_name",
        )
        fqn_prefix = _required_compile_plan_text(
            payload.get("fqn_prefix"),
            field_name="fqn_prefix",
        )
        source_files = _compile_plan_source_files(payload.get("source_files"))
        api_endpoint_catalog = _build_api_endpoint_catalog_from_ontology_plans(
            plans=api_plans,
        )
        generated_dto_graph = _build_generated_compile_plan_dto_graph(
            package_name=package_name,
            fqn_prefix=fqn_prefix,
            plans=api_plans,
            namespace_roots=_compile_plan_generated_dto_namespace_roots(
                payload=payload,
            ),
        )
        effective_accessible_graphs = (
            (*accessible_graphs, generated_dto_graph)
            if generated_dto_graph is not None
            else tuple(accessible_graphs)
        )
    with _record_phase(phase_timings_s, "resolve_projection_hashes"):
        api_projection_hash = find_meta_graph_projection_hash_by_name(
            index=index,
            projection_name="Api",
        )
        api_package_projection_hash = find_meta_graph_projection_hash_by_name(
            index=index,
            projection_name="ApiPackage",
        )
    with _record_phase(phase_timings_s, "resolve_stable_ids"):
        expected_api_id = stable_api_id(name=api_plan.api.name)
        expected_api_package_id = stable_api_package_id(name=package_name)

    api_lane_context = MaterializationLaneContext(
        branch_id=branch_id,
        projection_hash=api_projection_hash,
    )
    with _record_phase(phase_timings_s, "hydrate_api_from_head"):
        api = await _hydrate_lane_root_from_head(
            index=index,
            branch_id=branch_id,
            projection_hash=api_projection_hash,
            root_id=expected_api_id,
            root_type=Api,
        )
    if api is not None:
        with _record_phase(phase_timings_s, "validate_api_endpoint_catalog"):
            if not await _api_lane_has_endpoint_catalog(
                index=index,
                branch_id=branch_id,
                projection_hash=api_projection_hash,
                expected_api_id=expected_api_id,
                api_endpoint_catalog=api_endpoint_catalog,
            ):
                _reset_generated_api_lane(
                    aware_root=FSCommitStore().aware_root,
                    branch_id=branch_id,
                    projection_hash=api_projection_hash,
                )
                api = None
    api_receipt: MaterializationRunReceipt | None = None
    if api is None:
        with _record_phase(phase_timings_s, "materialize_api_compile_plan_ontology"):
            api_receipt = await materialize_api_compile_plan_ontology(
                runtime=runtime,
                index=index,
                actor_id=actor_id,
                lane=api_lane_context,
                compile_plan_payloads=(payload,),
                accessible_graphs=effective_accessible_graphs,
                phase_timings_s=phase_timings_s,
            )
        if api_receipt is None or not api_receipt.steps:
            raise RuntimeError(
                "Generated API compile-plan materialization requires committed "
                f"Api definition truth: package_name={package_name!r}"
            )
        with _record_phase(phase_timings_s, "rehydrate_api_from_head"):
            api = await _hydrate_lane_root_from_head(
                index=index,
                branch_id=branch_id,
                projection_hash=api_projection_hash,
                root_id=expected_api_id,
                root_type=Api,
            )
    if api is None:
        raise RuntimeError(
            "Generated API compile-plan materialization could not hydrate canonical "
            f"Api: api_name={api_plan.api.name!r}"
        )
    with _record_phase(phase_timings_s, "resolve_api_semantic_root_commit_id"):
        api_domain_head_commit_id = (
            api_receipt.steps[-1].commit_id
            if api_receipt is not None and api_receipt.steps
            else await _lane_head_commit_id(
                branch_id=branch_id,
                projection_hash=api_projection_hash,
            )
        )
        api_object_instance_graph_commit_id = (
            await _object_instance_graph_commit_id_from_domain_commit(
                branch_id=branch_id,
                projection_hash=api_projection_hash,
                domain_commit_id=api_domain_head_commit_id,
            )
            if api_domain_head_commit_id is not None
            else None
        )
    if api_object_instance_graph_commit_id is None:
        raise RuntimeError(
            "Generated API package materialization requires a committed Api root: "
            f"api_name={api.name!r}"
        )

    manifest_relative_path = (
        _relative_to(
            path=resolved_compile_plan_path,
            root=resolved_workspace_root,
            label="api.compile_plan",
        )
        if resolved_compile_plan_path is not None
        else None
    )
    package_root_relative = (
        _relative_to(
            path=resolved_compile_plan_path.parent,
            root=resolved_workspace_root,
            label="package_root",
        )
        if resolved_compile_plan_path is not None
        else f".aware/api/runtime/{package_name}"
    )
    sources_root_relative = package_root_relative
    api_package_include_paths = JsonArray(source_files or ("api.compile_plan.json",))
    api_package_exclude_paths = JsonArray(())
    api_package_dependencies = JsonArray(())
    api_package_targets = JsonObject({})
    api_package_compilation_mode = "compile_plan"
    api_package_version = _compile_plan_package_int(
        (provider_payload or {}).get("version_number"),
        default=1,
    )
    api_package_title = _optional_compile_plan_text(
        (provider_payload or {}).get("title")
    )
    api_package_description = _optional_compile_plan_text(
        (provider_payload or {}).get("description")
    )
    with _record_phase(phase_timings_s, "hydrate_api_package_from_head"):
        api_package = await _hydrate_lane_root_from_head(
            index=index,
            branch_id=branch_id,
            projection_hash=api_package_projection_hash,
            root_id=expected_api_package_id,
            root_type=ApiPackage,
        )
    api_package_snapshot = None
    if api_package is not None and api_package.api_id != api.id:
        raise RuntimeError(
            "Generated API package materialization resolved committed ApiPackage "
            "with unexpected api_id: "
            + f"package_name={package_name!r} expected={api.id} actual={api_package.api_id}"
        )
    if api_package is not None:
        with _record_phase(phase_timings_s, "check_api_package_manifest_truth"):
            package_manifest_truth_mismatches = (
                _api_package_manifest_truth_mismatch_keys(
                    api_package=api_package,
                    api_id=api.id,
                    api_object_instance_graph_commit_id=(
                        api_object_instance_graph_commit_id
                    ),
                    source_code_package_id=None,
                    fqn_prefix=fqn_prefix,
                    version_number=api_package_version,
                    title=api_package_title,
                    description=api_package_description,
                    aware_api_version=1,
                    manifest_relative_path=manifest_relative_path,
                    package_root=package_root_relative,
                    sources_root=sources_root_relative,
                    include_paths=api_package_include_paths,
                    exclude_paths=api_package_exclude_paths,
                    force_fresh_scan=False,
                    compilation_mode=api_package_compilation_mode,
                    dependencies=api_package_dependencies,
                    targets=api_package_targets,
                )
            )
    else:
        package_manifest_truth_mismatches = ("missing",)

    if package_manifest_truth_mismatches:
        with _record_phase(phase_timings_s, "commit_api_package_manifest_snapshot"):
            api_package_snapshot = await commit_api_package_manifest_snapshot(
                index=index,
                actor_id=actor_id,
                branch_id=branch_id,
                projection_hash=api_package_projection_hash,
                package_name=package_name,
                api_id=api.id,
                api_object_instance_graph_commit_id=api_object_instance_graph_commit_id,
                source_code_package_id=None,
                fqn_prefix=fqn_prefix,
                version_number=api_package_version,
                title=api_package_title,
                description=api_package_description,
                aware_api_version=1,
                manifest_relative_path=manifest_relative_path,
                package_root=package_root_relative,
                sources_root=sources_root_relative,
                include_paths=api_package_include_paths,
                exclude_paths=api_package_exclude_paths,
                force_fresh_scan=False,
                compilation_mode=api_package_compilation_mode,
                dependencies=api_package_dependencies,
                targets=api_package_targets,
            )
            api_package = api_package_snapshot.api_package
    if api_package is None:
        raise RuntimeError(
            "Generated API package materialization could not hydrate ApiPackage: "
            f"package_name={package_name!r}"
        )
    with _record_phase(phase_timings_s, "resolve_api_package_semantic_root_commit_id"):
        api_package_domain_commit_id = (
            api_package_snapshot.commit_id
            if api_package_snapshot is not None
            else await _lane_head_commit_id(
                branch_id=branch_id,
                projection_hash=api_package_projection_hash,
            )
        )
        api_package_object_instance_graph_commit_id = (
            await _object_instance_graph_commit_id_from_domain_commit(
                branch_id=branch_id,
                projection_hash=api_package_projection_hash,
                domain_commit_id=api_package_domain_commit_id,
            )
            if api_package_domain_commit_id is not None
            else None
        )

    phase_timings_s["total"] = _round_duration_s(
        perf_counter() - materialization_started_at
    )
    return ApiCompilePlanPackageMaterializationResult(
        compile_plan_path=resolved_compile_plan_path,
        workspace_root=resolved_workspace_root,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        api_source_path=api_plan.api.source_path,
        api=api,
        api_package=api_package,
        source_files=source_files,
        phase_timings_s=dict(sorted(phase_timings_s.items())),
        api_endpoint_catalog=api_endpoint_catalog,
        generated_dto_graph_count=1 if generated_dto_graph is not None else 0,
        generated_dto_class_config_count=(
            len(generated_dto_graph.object_config_graph_nodes)
            if generated_dto_graph is not None
            else 0
        ),
        api_commit_id=(
            api_receipt.steps[-1].commit_id if api_receipt is not None else None
        ),
        api_head_commit_id=api_object_instance_graph_commit_id,
        api_object_instance_graph_commit_id=api_object_instance_graph_commit_id,
        package_commit_id=(
            api_package_snapshot.commit_id if api_package_snapshot is not None else None
        ),
        package_head_commit_id=api_package_object_instance_graph_commit_id,
    )


def load_api_compile_plan_payloads(*, repo_root: Path) -> list[dict[str, object]]:
    runtime_root = (repo_root / ".aware" / "api" / "runtime").resolve()
    if not runtime_root.exists() or not runtime_root.is_dir():
        return []

    payloads: list[dict[str, object]] = []
    for compile_plan_path in sorted(runtime_root.glob("*/api.compile_plan.json")):
        if not compile_plan_path.is_file():
            continue
        try:
            payload_obj = cast(
                object,
                json.loads(compile_plan_path.read_text(encoding="utf-8") or "{}"),
            )
        except Exception as exc:  # pragma: no cover - defensive adapter
            raise RuntimeError(
                f"Invalid API compile plan at {compile_plan_path}: {exc}"
            ) from exc
        payload_map = _expect_mapping(
            payload_obj, field_name=f"{compile_plan_path}:root"
        )
        payloads.append(dict(payload_map))
    return payloads


async def materialize_api_compile_plan_ontology(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    lane: MaterializationLaneContext,
    compile_plan_payloads: Sequence[Mapping[str, object]] | None = None,
    repo_root: Path | None = None,
    accessible_graphs: Sequence[ObjectConfigGraph] = (),
    phase_timings_s: dict[str, float] | None = None,
) -> MaterializationRunReceipt | None:
    payloads: Sequence[Mapping[str, object]]
    if compile_plan_payloads is not None:
        payloads = tuple(
            dict(_expect_mapping(item, field_name="compile_plan_payloads[]"))
            for item in compile_plan_payloads
        )
    else:
        resolved_repo_root = repo_root or _resolve_repo_root_from_aware_repo_toml(
            start=runtime.manifest_path.parent
        )
        payloads = load_api_compile_plan_payloads(repo_root=resolved_repo_root)
    if not payloads:
        return None
    return await materialize_api_graph_ontology(
        index=index,
        actor_id=actor_id,
        lane=lane,
        compile_plan_payloads=payloads,
        extra_accessible_graphs=accessible_graphs,
        phase_timings_s=phase_timings_s,
    )


def _expect_mapping(value: object, *, field_name: str) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return cast(Mapping[str, object], value)
    raise RuntimeError(
        f"Invalid api compile plan payload: {field_name} must be an object"
    )


def _encode_api_compile_plan_payload(*, plan: APICompilePlan) -> dict[str, object]:
    return {
        "schema_version": plan.schema_version,
        "package_name": plan.package_name,
        "fqn_prefix": plan.fqn_prefix,
        "source_files": list(plan.source_files),
        "api_ontology": encode_api_ontology_plan_payload(plans=plan.api_ontology),
    }


def _build_api_endpoint_catalog(*, plan: APICompilePlan) -> ApiEndpointCatalog:
    catalog: ApiEndpointCatalog = {}
    for api in plan.api_ownership:
        api_key = api.name.strip().casefold()
        if not api_key:
            continue
        capability_catalog = catalog.setdefault(api_key, {})
        for capability in api.capabilities:
            capability_key = capability.name.strip().casefold()
            if not capability_key:
                continue
            capability_catalog[capability_key] = tuple(
                endpoint.name
                for endpoint in capability.endpoints
                if endpoint.name.strip()
            )
    return catalog


def _build_api_endpoint_catalog_from_ontology_plans(
    *,
    plans: Sequence[APIOntologyPlan],
) -> ApiEndpointCatalog:
    catalog: ApiEndpointCatalog = {}
    for plan in plans:
        api_key = plan.api.name.strip().casefold()
        if not api_key:
            continue
        capability_catalog = catalog.setdefault(api_key, {})
        endpoints_by_capability: dict[str, list[str]] = {}
        for endpoint in plan.capability_endpoints:
            capability_key = endpoint.capability_name.strip().casefold()
            endpoint_name = endpoint.name.strip()
            if not capability_key or not endpoint_name:
                continue
            endpoints_by_capability.setdefault(capability_key, []).append(
                endpoint_name,
            )
        for capability in plan.capabilities:
            capability_key = capability.name.strip().casefold()
            if not capability_key:
                continue
            capability_catalog[capability_key] = tuple(
                sorted(
                    set(endpoints_by_capability.get(capability_key, ())),
                    key=lambda item: item.casefold(),
                )
            )
    return catalog


def _build_generated_compile_plan_dto_graph(
    *,
    package_name: str,
    fqn_prefix: str,
    plans: Sequence[APIOntologyPlan],
    namespace_roots: Sequence[_GeneratedDtoNamespaceRoot],
) -> ObjectConfigGraph | None:
    class_refs = _generated_compile_plan_dto_class_refs(
        fqn_prefix=fqn_prefix,
        plans=plans,
    )
    if not class_refs:
        return None

    graph_digest = sha256(
        json.dumps(
            {
                "package_name": package_name,
                "fqn_prefix": fqn_prefix,
                "class_refs": list(class_refs),
                "namespace_roots": [
                    {
                        "path": root.path,
                        "namespace": root.namespace,
                    }
                    for root in namespace_roots
                ],
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()
    graph_id = stable_object_config_graph_id(
        fqn_prefix=fqn_prefix,
        language=CodeLanguage.aware.value,
    )
    nodes: list[ObjectConfigGraphNode] = []
    for class_ref in class_refs:
        node_id = stable_object_config_graph_node_id(
            object_config_graph_id=graph_id,
            type=ObjectConfigGraphNodeType.class_.value,
            node_key=class_ref,
        )
        class_config = ClassConfig(
            id=stable_class_config_id(
                object_config_graph_node_id=node_id,
                class_fqn=class_ref,
            ),
            class_fqn=class_ref,
            name=_class_name_from_ref(class_ref),
            description=("Generated API compile-plan DTO owned by " f"{package_name}."),
            object_config_graph_node_id=node_id,
            class_config_attribute_configs=[],
            class_config_function_configs=[],
            class_config_relationships=[],
        )
        nodes.append(
            ObjectConfigGraphNode(
                id=node_id,
                object_config_graph_id=graph_id,
                type=ObjectConfigGraphNodeType.class_,
                node_key=class_ref,
                class_config=class_config,
                layouts=[],
            )
        )

    graph = ObjectConfigGraph(
        id=graph_id,
        name=f"{package_name}_generated_dto",
        description=f"Generated API compile-plan DTO graph for {package_name}.",
        hash=f"sha256:{graph_digest}",
        fqn_prefix=fqn_prefix,
        language=CodeLanguage.aware,
        object_config_graph_nodes=nodes,
    )
    _validate_generated_dto_namespace_roots(
        graph=graph,
        class_refs=class_refs,
        namespace_roots=namespace_roots,
    )
    return graph


def _validate_generated_dto_namespace_roots(
    *,
    graph: ObjectConfigGraph,
    class_refs: Sequence[str],
    namespace_roots: Sequence[_GeneratedDtoNamespaceRoot],
) -> None:
    if not class_refs:
        return
    if not namespace_roots:
        raise RuntimeError(
            "Generated API compile-plan DTO graph requires "
            "generated_dto_namespace_roots when local DTO class refs are present."
        )

    node_by_class_ref = {
        (node.class_config.class_fqn or "").strip(): node
        for node in graph.object_config_graph_nodes
        if node.class_config is not None and (node.class_config.class_fqn or "").strip()
    }

    for class_ref in class_refs:
        node = node_by_class_ref.get(class_ref)
        if node is None:
            raise RuntimeError(
                "Generated API compile-plan DTO graph lost class node for "
                f"class_ref={class_ref!r}"
            )
        root = _namespace_root_for_generated_class_ref(
            class_ref=class_ref,
            fqn_prefix=(graph.fqn_prefix or "").strip(),
            namespace_roots=namespace_roots,
        )
        if not root.namespace.strip():
            raise RuntimeError(
                "Generated API compile-plan DTO namespace root must provide "
                f"a non-empty namespace for class_ref={class_ref!r}"
            )


def _namespace_root_for_generated_class_ref(
    *,
    class_ref: str,
    fqn_prefix: str,
    namespace_roots: Sequence[_GeneratedDtoNamespaceRoot],
) -> _GeneratedDtoNamespaceRoot:
    class_name = _class_name_from_ref(class_ref)
    for root in namespace_roots:
        canonical_ref = ".".join(
            part for part in (fqn_prefix, root.namespace, class_name) if part
        )
        if class_ref == canonical_ref or class_ref == _authored_ref_from_fqn(
            canonical_ref,
        ):
            return root
    raise RuntimeError(
        "Generated API compile-plan DTO class ref is not covered by "
        "generated_dto_namespace_roots: "
        f"class_ref={class_ref!r} fqn_prefix={fqn_prefix!r}"
    )


def build_generated_api_compile_plan_accessible_graphs(
    *,
    compile_plan_payload: Mapping[str, object],
    accessible_graphs: Sequence[ObjectConfigGraph] = (),
) -> tuple[ObjectConfigGraph, ...]:
    payload = dict(
        _expect_mapping(
            compile_plan_payload,
            field_name="compile_plan_payload",
        )
    )
    api_plans = _api_ontology_plans_from_compile_plan_payload(payload=payload)
    package_name = _required_compile_plan_text(
        payload.get("package_name"),
        field_name="package_name",
    )
    fqn_prefix = _required_compile_plan_text(
        payload.get("fqn_prefix"),
        field_name="fqn_prefix",
    )
    generated_dto_graph = _build_generated_compile_plan_dto_graph(
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        plans=api_plans,
        namespace_roots=_compile_plan_generated_dto_namespace_roots(
            payload=payload,
        ),
    )
    if generated_dto_graph is None:
        return tuple(accessible_graphs)
    return (*tuple(accessible_graphs), generated_dto_graph)


def _generated_compile_plan_dto_class_refs(
    *,
    fqn_prefix: str,
    plans: Sequence[APIOntologyPlan],
) -> tuple[str, ...]:
    refs: set[str] = set()
    normalized_prefix = fqn_prefix.strip()
    if not normalized_prefix:
        return ()
    for plan in plans:
        for row in plan.capability_endpoint_request_configs:
            if row.class_config_id is None and _class_ref_is_local_to_prefix(
                class_ref=row.class_ref,
                fqn_prefix=normalized_prefix,
            ):
                refs.add(row.class_ref.strip())
        for row in plan.capability_endpoint_response_configs:
            if row.class_config_id is None and _class_ref_is_local_to_prefix(
                class_ref=row.class_ref,
                fqn_prefix=normalized_prefix,
            ):
                refs.add(row.class_ref.strip())
        for row in plan.capability_endpoint_stream_event_configs:
            if row.class_config_id is None and _class_ref_is_local_to_prefix(
                class_ref=row.class_ref,
                fqn_prefix=normalized_prefix,
            ):
                refs.add(row.class_ref.strip())
    return tuple(sorted(refs, key=str.casefold))


def _class_ref_is_local_to_prefix(*, class_ref: str, fqn_prefix: str) -> bool:
    normalized_ref = class_ref.strip()
    return normalized_ref == fqn_prefix or normalized_ref.startswith(f"{fqn_prefix}.")


def _class_name_from_ref(class_ref: str) -> str:
    leaf = class_ref.rsplit(".", 1)[-1].strip()
    return leaf or class_ref.strip() or "GeneratedDto"


def _api_ontology_plans_from_compile_plan_payload(
    *,
    payload: Mapping[str, object],
) -> tuple[APIOntologyPlan, ...]:
    raw_api_ontology = payload.get("api_ontology")
    if not isinstance(raw_api_ontology, Sequence) or isinstance(
        raw_api_ontology,
        (str, bytes),
    ):
        raise RuntimeError(
            "Generated API compile-plan payload requires api_ontology list"
        )
    plan_payloads = [
        dict(_expect_mapping(item, field_name="api_ontology[]"))
        for item in raw_api_ontology
    ]
    return decode_api_ontology_plan_payload(payload=plan_payloads)


def _compile_plan_source_files(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise RuntimeError(
            "Generated API compile-plan payload field source_files must be a list"
        )
    return tuple(
        sorted(
            {str(item).strip() for item in value if str(item).strip()},
            key=lambda item: item.casefold(),
        )
    )


def _compile_plan_generated_dto_namespace_roots(
    *,
    payload: Mapping[str, object],
) -> tuple[_GeneratedDtoNamespaceRoot, ...]:
    value = payload.get("generated_dto_namespace_roots")
    if value is None:
        return ()
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise RuntimeError(
            "Generated API compile-plan payload field "
            "generated_dto_namespace_roots must be a list"
        )
    roots: list[_GeneratedDtoNamespaceRoot] = []
    for index, item in enumerate(value):
        row = _expect_mapping(
            item,
            field_name=f"generated_dto_namespace_roots[{index}]",
        )
        roots.append(
            _GeneratedDtoNamespaceRoot(
                path=_required_compile_plan_text(
                    row.get("path"),
                    field_name=f"generated_dto_namespace_roots[{index}].path",
                ),
                namespace=_required_compile_plan_text(
                    row.get("namespace"),
                    field_name=f"generated_dto_namespace_roots[{index}].namespace",
                ),
            )
        )
    return tuple(roots)


def _required_compile_plan_text(value: object, *, field_name: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    raise RuntimeError(
        f"Generated API compile-plan payload requires non-empty {field_name}"
    )


def _optional_compile_plan_text(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _compile_plan_package_int(value: object, *, default: int) -> int:
    if isinstance(value, bool):
        return default
    if isinstance(value, int) and value > 0:
        return value
    return default


def _enum_value(value: object) -> object:
    enum_value = getattr(value, "value", None)
    return enum_value if enum_value is not None else value


def _api_package_dependencies_payload(spec: AwareApiTomlSpec) -> JsonArray:
    return JsonArray(
        [
            {
                "package_name": dependency.package_name,
                "version_number": dependency.version_number,
            }
            for dependency in spec.dependencies
        ]
    )


def _api_package_targets_payload(spec: AwareApiTomlSpec) -> JsonObject:
    payload: dict[str, JsonValue] = {}
    python = spec.targets.python
    if python is not None:
        payload["python"] = {
            "root_dir": python.root_dir,
            "public_package": {
                "package_dir": python.public_package.package_dir,
                "root_dir": python.public_package.root_dir,
            },
            "service_protocol": {
                "package_dir": python.service_protocol.package_dir,
                "root_dir": python.service_protocol.root_dir,
            },
        }
    dart = spec.targets.dart
    if dart is not None:
        payload["dart"] = {
            "root_dir": dart.root_dir,
            "public_package": {
                "package_dir": dart.public_package.package_dir,
                "root_dir": dart.public_package.root_dir,
            },
        }
    return JsonObject(payload)


async def _materialize_api_language_code_packages(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    code_package_projection_hash: str,
    workspace_root: Path,
    snapshot: APIWorkspaceSnapshot,
) -> tuple[ApiLanguageCodePackageMaterialization, ...]:
    refs: list[ApiLanguageCodePackageMaterialization] = []
    for target in _api_language_code_package_targets(
        snapshot=snapshot,
        workspace_root=workspace_root,
    ):
        code_package_config_id = _api_language_code_package_config_id(target=target)
        expected_code_package_id = stable_code_package_id(
            code_package_config_id=code_package_config_id,
            package_name=target.package_name,
            language=target.language.value,
        )
        language_branch_id = _api_language_code_package_branch_id(
            code_package_id=expected_code_package_id,
        )
        await _reset_code_package_lane_if_root_mismatch(
            branch_id=language_branch_id,
            projection_hash=code_package_projection_hash,
            expected_code_package_id=expected_code_package_id,
            package_name=target.package_name,
            target_label=f"api_language:{target.language.value}",
        )
        manifest_relative_path = _relative_to(
            path=target.manifest_path,
            root=workspace_root,
            label="api_language_package.manifest_path",
        )
        package_root_relative = _relative_to(
            path=target.package_root,
            root=workspace_root,
            label="api_language_package.package_root",
        )
        sources_root_relative = _relative_to(
            path=target.sources_root,
            root=workspace_root,
            label="api_language_package.sources_root",
        )
        unparsed_texts_by_relative_path: dict[str, str] = {}
        for source_file in _api_language_code_source_files(target=target):
            relative_path = source_file.relative_to(target.package_root).as_posix()
            unparsed_texts_by_relative_path[relative_path] = source_file.read_text(
                encoding="utf-8"
            )
        snapshot_commit = await commit_code_package_text_snapshot(
            index=index,
            actor_id=actor_id,
            branch_id=language_branch_id,
            projection_hash=code_package_projection_hash,
            code_package_config_id=code_package_config_id,
            package_name=target.package_name,
            language=target.language,
            surface="api",
            manifest_kind=target.manifest_kind,
            manifest_relative_path=manifest_relative_path,
            package_root=package_root_relative,
            sources_root=sources_root_relative,
            fqn_prefix=target.import_root,
            source_texts_by_relative_path={},
            unparsed_texts_by_relative_path=unparsed_texts_by_relative_path,
        )
        hydrated_code_package = await _hydrate_lane_root_from_head(
            index=index,
            branch_id=language_branch_id,
            projection_hash=code_package_projection_hash,
            root_id=expected_code_package_id,
            root_type=CodePackage,
        )
        if hydrated_code_package is None:
            raise RuntimeError(
                "API language CodePackage materialization did not hydrate: "
                f"package_name={target.package_name!r} "
                f"language={target.language.value!r} "
                f"code_package_id={expected_code_package_id}"
            )
        refs.append(
            ApiLanguageCodePackageMaterialization(
                code_package=hydrated_code_package,
                branch_id=language_branch_id,
                domain_commit_id=snapshot_commit.commit_id,
                object_instance_graph_commit_id=(
                    snapshot_commit.object_instance_graph_commit_id
                ),
                role=target.role,
                output_key=target.output_key,
                include_paths=target.include_paths,
                exclude_paths=target.exclude_paths,
            )
        )
    return tuple(refs)


def _api_language_code_package_targets(
    *,
    snapshot: APIWorkspaceSnapshot,
    workspace_root: Path,
) -> tuple[ApiLanguageCodePackageTarget, ...]:
    targets: list[ApiLanguageCodePackageTarget] = []
    if snapshot.spec.targets.python is not None:
        targets.extend(
            _python_api_language_code_package_targets(
                snapshot=snapshot,
                target=snapshot.spec.targets.python,
                workspace_root=workspace_root,
            )
        )
    if snapshot.spec.targets.dart is not None:
        dart_target = _dart_api_language_code_package_target(
            snapshot=snapshot,
            target=snapshot.spec.targets.dart,
            workspace_root=workspace_root,
        )
        if dart_target is not None:
            targets.append(dart_target)
    return tuple(targets)


def _api_source_code_package_config_id() -> UUID:
    return source_code_package_config_ref(
        manifest_kind="aware_api_toml",
        surface="api",
    ).config_id


def _api_language_code_package_config_id(
    *,
    target: ApiLanguageCodePackageTarget,
) -> UUID:
    return source_code_package_config_ref(
        manifest_kind=target.manifest_kind,
        surface="api",
    ).config_id


def _python_api_language_code_package_targets(
    *,
    snapshot: APIWorkspaceSnapshot,
    target: AwareApiTomlPythonTargetSpec,
    workspace_root: Path,
) -> tuple[ApiLanguageCodePackageTarget, ...]:
    public_import_root = _python_api_import_root(
        package_dir=target.public_package.package_dir,
        fallback=(
            (snapshot.spec.api.fqn_prefix or snapshot.spec.api.package_name)
            .replace("-", "_")
            .strip("_")
        ),
    )
    protocol_import_root = _python_api_import_root(
        package_dir=target.service_protocol.package_dir,
        fallback=_derive_python_service_protocol_import_root(
            public_import_root=public_import_root
        ),
    )
    return (
        _python_api_product_code_package_target(
            snapshot=snapshot,
            target=target,
            product=target.public_package,
            workspace_root=workspace_root,
            import_root=public_import_root,
            role="public_package",
            output_key="python.public_package",
        ),
        _python_api_product_code_package_target(
            snapshot=snapshot,
            target=target,
            product=target.service_protocol,
            workspace_root=workspace_root,
            import_root=protocol_import_root,
            role="service_protocol",
            output_key="python.service_protocol_package",
        ),
    )


def _python_api_product_code_package_target(
    *,
    snapshot: APIWorkspaceSnapshot,
    target: AwareApiTomlPythonTargetSpec,
    product: AwareApiTomlPythonProductTargetSpec,
    workspace_root: Path,
    import_root: str,
    role: str,
    output_key: str,
) -> ApiLanguageCodePackageTarget:
    language_root = (snapshot.package_root / (target.root_dir or "python")).resolve()
    _assert_existing_dir_within(
        root=snapshot.package_root,
        path=language_root,
        label="targets.python.root_dir",
    )
    if product.root_dir is not None and product.root_dir.strip():
        package_root = (snapshot.package_root / product.root_dir).resolve()
    else:
        package_root = (
            language_root
            / ((product.package_dir or import_root).strip() or import_root)
        ).resolve()
    _assert_existing_dir_within(
        root=snapshot.package_root,
        path=package_root,
        label=f"targets.python.{output_key}.root_dir",
    )
    _assert_path_within(
        base=workspace_root,
        candidate=package_root,
        label=f"targets.python.{output_key}.workspace_root",
    )
    package_dir = (product.package_dir or import_root).strip() or import_root
    sources_root = (package_root / package_dir).resolve()
    _assert_existing_dir_within(
        root=package_root,
        path=sources_root,
        label=f"targets.python.{output_key}.package_dir",
    )
    manifest_path = (package_root / "pyproject.toml").resolve()
    _assert_existing_file_within(
        root=package_root,
        path=manifest_path,
        label=f"targets.python.{output_key}.pyproject_toml",
    )
    package_name = _read_pyproject_package_name(manifest_path)
    return ApiLanguageCodePackageTarget(
        language=CodeLanguage.python,
        package_name=package_name,
        import_root=import_root,
        package_root=package_root,
        manifest_path=manifest_path,
        sources_root=sources_root,
        manifest_kind="pyproject_toml",
        role=role,
        output_key=output_key,
        include_paths=(
            "pyproject.toml",
            "README.md",
            f"{package_dir}/**/*",
            "tests/**/*.py",
        ),
        exclude_paths=(
            "**/__pycache__/**",
            "**/*.pyc",
            ".pytest_cache/**",
            ".venv/**",
            "build/**",
            "dist/**",
        ),
    )


def _dart_api_language_code_package_target(
    *,
    snapshot: APIWorkspaceSnapshot,
    target: AwareApiTomlDartTargetSpec,
    workspace_root: Path,
) -> ApiLanguageCodePackageTarget | None:
    package_name_hint = _dart_api_package_name(
        package_dir=target.public_package.package_dir,
        fallback=(
            (snapshot.spec.api.fqn_prefix or snapshot.spec.api.package_name)
            .replace("-", "_")
            .strip("_")
        ),
    )
    language_root = (snapshot.package_root / (target.root_dir or "dart")).resolve()
    if not language_root.is_dir():
        return None
    _assert_existing_dir_within(
        root=snapshot.package_root,
        path=language_root,
        label="targets.dart.root_dir",
    )
    product = target.public_package
    if product.root_dir is not None and product.root_dir.strip():
        package_root = (snapshot.package_root / product.root_dir).resolve()
    else:
        package_root = (
            language_root
            / ((product.package_dir or package_name_hint).strip() or package_name_hint)
        ).resolve()
    _assert_path_within(
        base=snapshot.package_root,
        candidate=package_root,
        label="targets.dart.public_package.root_dir",
    )
    if not package_root.is_dir():
        if not _has_files_below(language_root):
            return None
        _assert_existing_dir_within(
            root=snapshot.package_root,
            path=package_root,
            label="targets.dart.public_package.root_dir",
        )
    _assert_existing_dir_within(
        root=snapshot.package_root,
        path=package_root,
        label="targets.dart.public_package.root_dir",
    )
    _assert_path_within(
        base=workspace_root,
        candidate=package_root,
        label="targets.dart.public_package.workspace_root",
    )
    manifest_path = (package_root / "pubspec.yaml").resolve()
    if not manifest_path.is_file() and not _has_files_below(package_root):
        return None
    _assert_existing_file_within(
        root=package_root,
        path=manifest_path,
        label="targets.dart.public_package.pubspec_yaml",
    )
    sources_root = (package_root / "lib").resolve()
    _assert_existing_dir_within(
        root=package_root,
        path=sources_root,
        label="targets.dart.public_package.lib",
    )
    package_name = _read_pubspec_package_name(manifest_path)
    return ApiLanguageCodePackageTarget(
        language=CodeLanguage.dart,
        package_name=package_name,
        import_root=package_name,
        package_root=package_root,
        manifest_path=manifest_path,
        sources_root=sources_root,
        manifest_kind="pubspec_yaml",
        role="public_package",
        output_key="dart.public_package",
        include_paths=(
            "pubspec.yaml",
            "pubspec.lock",
            "README.md",
            "analysis_options.yaml",
            "lib/**/*",
            "test/**/*.dart",
        ),
        exclude_paths=(
            ".dart_tool/**",
            "build/**",
            ".pub/**",
        ),
    )


def _has_files_below(root: Path) -> bool:
    return any(path.is_file() for path in root.rglob("*"))


def _python_api_import_root(*, package_dir: str | None, fallback: str) -> str:
    token = (package_dir or fallback or "").strip()
    return token.replace("/", ".").strip(".") or "aware_api_public_package"


def _derive_python_service_protocol_import_root(*, public_import_root: str) -> str:
    token = public_import_root
    if token.endswith("_api"):
        token = token[: -len("_api")]
    token = token.strip("_")
    return f"{token}_protocol" if token else "aware_api_protocol"


def _dart_api_package_name(*, package_dir: str | None, fallback: str) -> str:
    token = (package_dir or fallback or "").strip()
    return token.replace("-", "_").strip("_") or "aware_api_public_package"


def _read_pyproject_package_name(pyproject_path: Path) -> str:
    payload = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    project = payload.get("project")
    if not isinstance(project, dict):
        raise RuntimeError(
            "API Python target pyproject.toml must define [project]: "
            f"{pyproject_path}"
        )
    raw_name = project.get("name")
    if not isinstance(raw_name, str) or not raw_name.strip():
        raise RuntimeError(
            "API Python target pyproject.toml must define [project].name: "
            f"{pyproject_path}"
        )
    return raw_name.strip()


def _read_pubspec_package_name(pubspec_path: Path) -> str:
    for line in pubspec_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped.startswith("name:"):
            continue
        raw_name = stripped.removeprefix("name:").split("#", 1)[0].strip()
        if raw_name:
            return raw_name
    raise RuntimeError(
        "API Dart target pubspec.yaml must define package name: " f"{pubspec_path}"
    )


def _api_language_code_source_files(
    *,
    target: ApiLanguageCodePackageTarget,
) -> tuple[Path, ...]:
    files_by_rel: dict[str, Path] = {}
    for include_path in target.include_paths:
        pattern = (include_path or "").strip()
        if not pattern:
            continue
        for candidate in target.package_root.glob(pattern):
            if not candidate.is_file():
                continue
            resolved = candidate.resolve()
            _assert_existing_file_within(
                root=target.package_root,
                path=resolved,
                label="api_language_package.include_paths",
            )
            rel_path = resolved.relative_to(target.package_root).as_posix()
            if _is_api_language_code_path_excluded(
                rel_path=rel_path,
                exclude_patterns=target.exclude_paths,
            ):
                continue
            files_by_rel[rel_path] = resolved
    return tuple(files_by_rel[key] for key in sorted(files_by_rel))


def _is_api_language_code_path_excluded(
    *,
    rel_path: str,
    exclude_patterns: Sequence[str],
) -> bool:
    token = PurePosixPath(rel_path)
    if any(
        part in _API_LANGUAGE_CODE_PACKAGE_EXCLUDED_PATH_PARTS for part in token.parts
    ):
        return True
    for raw_pattern in exclude_patterns:
        pattern = (raw_pattern or "").strip()
        if pattern and token.match(pattern):
            return True
    return False


def _api_package_language_package_snapshots(
    *,
    language_code_package_refs: tuple[ApiLanguageCodePackageMaterialization, ...],
) -> tuple[ApiPackageLanguagePackageSnapshotRef, ...]:
    refs: list[ApiPackageLanguagePackageSnapshotRef] = []
    for language_ref in language_code_package_refs:
        code_package = language_ref.code_package
        if code_package.id is None:
            raise RuntimeError(
                "API language package bridge requires committed CodePackage id: "
                f"package_name={code_package.package_name!r} "
                f"language={code_package.language.value!r}"
            )
        refs.append(
            ApiPackageLanguagePackageSnapshotRef(
                code_package_id=code_package.id,
                package_name=code_package.package_name,
                language=code_package.language,
                import_root=code_package.fqn_prefix or code_package.package_name,
                manifest_relative_path=code_package.manifest_relative_path,
                package_root=code_package.package_root,
                role=language_ref.role,
                output_key=language_ref.output_key,
                include_paths=JsonArray(language_ref.include_paths),
                exclude_paths=JsonArray(language_ref.exclude_paths),
            )
        )
    return tuple(refs)


def _validate_api_language_package_bridges(
    *,
    api_package: ApiPackage,
    language_code_packages: tuple[CodePackage, ...],
) -> None:
    expected_ids = {
        code_package.id
        for code_package in language_code_packages
        if code_package.id is not None
    }
    attached_ids = {bridge.code_package_id for bridge in api_package.language_packages}
    missing = expected_ids - attached_ids
    if missing:
        raise RuntimeError(
            "ApiPackage language package bridge hydration is incomplete: "
            f"api_package_id={api_package.id} "
            f"missing_code_package_ids={sorted(str(item) for item in missing)}"
        )


def _api_language_code_package_branch_id(
    *,
    code_package_id: UUID,
) -> UUID:
    return uuid5(
        _API_LANGUAGE_CODE_PACKAGE_BRANCH_NAMESPACE,
        str(code_package_id).strip().casefold(),
    )


async def _hydrate_lane_root_from_head(
    *,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    projection_hash: str,
    root_id: UUID | None,
    root_type: type[_TRoot],
) -> _TRoot | None:
    if root_id is None:
        return None

    oig_result = await _hydrate_lane_oig_from_head(
        index=index,
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    if oig_result is None:
        return None
    opg, oig = oig_result

    return reify_oig_root_model(
        index=index,
        opg=opg,
        oig=oig,
        model_type=root_type,
        root_id=root_id,
        branch_id=branch_id,
    )


async def _hydrate_lane_oig_from_head(
    *,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    projection_hash: str,
) -> tuple[ObjectProjectionGraph, ObjectInstanceGraph] | None:
    head = await FSCommitStore().head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    if head is None or head.get("commit_id") is None:
        return None
    return await _materialize_lane_oig_from_commit(
        index=index,
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=None,
    )


async def _hydrate_lane_session_from_head(
    *,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    projection_hash: str,
) -> Session | None:
    oig_result = await _hydrate_lane_oig_from_head(
        index=index,
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    if oig_result is None:
        return None
    opg, oig = oig_result
    return await _hydrate_lane_session_from_oig(
        index=index,
        branch_id=branch_id,
        opg=opg,
        oig=oig,
    )


async def _hydrate_lane_session_from_commit(
    *,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    projection_hash: str,
    commit_id: UUID | None,
) -> Session:
    opg, oig = await _materialize_lane_oig_from_commit(
        index=index,
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
    )
    return await _hydrate_lane_session_from_oig(
        index=index,
        branch_id=branch_id,
        opg=opg,
        oig=oig,
    )


async def _materialize_lane_oig_from_commit(
    *,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    projection_hash: str,
    commit_id: UUID | None,
) -> tuple[ObjectProjectionGraph, ObjectInstanceGraph]:
    opg = index.opg_by_hash.get(projection_hash)
    if opg is None:
        raise RuntimeError(
            f"API package materialization missing projection hash: {projection_hash}"
        )
    oig, _ = await OIGMaterializer().get(
        branch_id=branch_id,
        ocg=index.ocg,
        opg=opg,
        commit_id=commit_id,
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )
    return opg, oig


async def _hydrate_lane_session_from_oig(
    *,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    opg: ObjectProjectionGraph,
    oig: ObjectInstanceGraph,
) -> Session:
    return reify_oig_session(
        index=index,
        opg=opg,
        oig=oig,
        branch_id=branch_id,
    )


async def _api_roots_are_semantically_equivalent(
    *,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    projection_hash: str,
    api_id: UUID,
    left_object_instance_graph_commit_id: UUID | None,
    right_object_instance_graph_commit_id: UUID | None,
) -> bool | None:
    if (
        left_object_instance_graph_commit_id is None
        or right_object_instance_graph_commit_id is None
    ):
        return None
    if left_object_instance_graph_commit_id == right_object_instance_graph_commit_id:
        return True

    store = FSCommitStore()
    left_domain_commit_id = (
        await store.domain_commit_id_for_object_instance_graph_commit_id(
            branch_id=branch_id,
            projection_hash=projection_hash,
            object_instance_graph_commit_id=left_object_instance_graph_commit_id,
        )
    )
    right_domain_commit_id = (
        await store.domain_commit_id_for_object_instance_graph_commit_id(
            branch_id=branch_id,
            projection_hash=projection_hash,
            object_instance_graph_commit_id=right_object_instance_graph_commit_id,
        )
    )
    if left_domain_commit_id is None or right_domain_commit_id is None:
        return None

    left_session = await _hydrate_lane_session_from_commit(
        index=index,
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=left_domain_commit_id,
    )
    right_session = await _hydrate_lane_session_from_commit(
        index=index,
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=right_domain_commit_id,
    )
    return _api_semantic_payload_from_session(
        session=left_session,
        api_id=api_id,
    ) == _api_semantic_payload_from_session(
        session=right_session,
        api_id=api_id,
    )


def _api_semantic_payload_from_session(
    *,
    session: Session,
    api_id: UUID,
) -> tuple[dict[str, object], ...]:
    objects_by_id: dict[UUID, object] = {}
    for obj in session.imap_all_objects():
        obj_id = getattr(obj, "id", None)
        if isinstance(obj_id, UUID):
            objects_by_id[obj_id] = obj
    if api_id not in objects_by_id:
        return ()

    selected_ids: set[UUID] = {api_id}
    changed = True
    while changed:
        changed = False
        for obj_id, obj in objects_by_id.items():
            if obj_id in selected_ids:
                continue
            if _object_references_any_id(obj=obj, ids=selected_ids):
                selected_ids.add(obj_id)
                changed = True

    payloads: list[dict[str, object]] = []
    for obj_id in selected_ids:
        obj = objects_by_id[obj_id]
        model_dump = getattr(obj, "model_dump", None)
        if not callable(model_dump):
            continue
        payloads.append(
            {
                "type": f"{type(obj).__module__}.{type(obj).__name__}",
                "payload": model_dump(mode="json"),
            }
        )
    return tuple(
        sorted(
            payloads,
            key=lambda item: (
                str(item["type"]),
                str(cast(Mapping[str, object], item["payload"]).get("id", "")),
            ),
        )
    )


def _object_references_any_id(*, obj: object, ids: set[UUID]) -> bool:
    model_fields = getattr(type(obj), "model_fields", {})
    if not isinstance(model_fields, Mapping):
        return False
    for field_name in model_fields:
        value = getattr(obj, str(field_name), None)
        if isinstance(value, UUID) and value in ids:
            return True
    return False


async def _api_lane_has_endpoint_catalog(
    *,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    projection_hash: str,
    expected_api_id: UUID,
    api_endpoint_catalog: ApiEndpointCatalog,
) -> bool:
    session = await _hydrate_lane_session_from_head(
        index=index,
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    if session is None:
        return False

    api = session.imap_get(Api, expected_api_id)
    if api is None:
        return False

    return _api_endpoint_catalog_is_satisfied_by_session(
        session=session,
        api_endpoint_catalog=api_endpoint_catalog,
    )


def _api_endpoint_catalog_is_satisfied_by_session(
    *,
    session: Session,
    api_endpoint_catalog: ApiEndpointCatalog,
) -> bool:
    apis_by_name = {
        (obj.name or "").casefold().strip(): obj
        for obj in session.imap_all_objects()
        if isinstance(obj, Api) and obj.id is not None
    }
    capabilities_by_key = {
        (obj.api_id, (obj.name or "").casefold().strip()): obj
        for obj in session.imap_all_objects()
        if isinstance(obj, ApiCapability) and obj.id is not None
    }
    endpoints_by_key = {
        (obj.api_capability_id, (obj.name or "").casefold().strip()): obj
        for obj in session.imap_all_objects()
        if isinstance(obj, ApiCapabilityEndpoint) and obj.id is not None
    }

    for api_name, capability_catalog in api_endpoint_catalog.items():
        api_obj = apis_by_name.get(api_name.casefold().strip())
        if api_obj is None or api_obj.id is None:
            return False
        for capability_name, endpoint_names in capability_catalog.items():
            capability = capabilities_by_key.get(
                (api_obj.id, capability_name.casefold().strip())
            )
            if capability is None or capability.id is None:
                return False
            for endpoint_name in endpoint_names:
                endpoint = endpoints_by_key.get(
                    (capability.id, endpoint_name.casefold().strip())
                )
                if endpoint is None:
                    return False
    return True


def _reset_generated_api_lane(
    *,
    aware_root: Path,
    branch_id: UUID,
    projection_hash: str,
) -> None:
    branch_dir = aware_root / ".aware" / "oig" / str(branch_id)
    lane_dir = branch_dir / projection_hash
    if lane_dir.exists():
        shutil.rmtree(lane_dir)
    get_shared_materialization_cache().invalidate_lane(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    if branch_dir.exists() and not any(branch_dir.iterdir()):
        shutil.rmtree(branch_dir)


async def _reset_code_package_lane_if_root_mismatch(
    *,
    branch_id: UUID,
    projection_hash: str,
    expected_code_package_id: UUID,
    package_name: str,
    target_label: str,
) -> None:
    head = await FSCommitStore().head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    if head is None:
        return
    raw_root_object_id = head.get("root_object_id")
    if raw_root_object_id is None:
        return
    root_object_id = (
        raw_root_object_id
        if isinstance(raw_root_object_id, UUID)
        else UUID(str(raw_root_object_id))
    )
    if root_object_id == expected_code_package_id:
        return
    logger.info(
        "API CodePackage lane root mismatch; resetting generated lane before "
        "provider-owned snapshot materialization "
        "(package_name=%s, target=%s, branch_id=%s, existing_root=%s, expected_root=%s)",
        package_name,
        target_label,
        branch_id,
        root_object_id,
        expected_code_package_id,
    )
    _reset_generated_api_lane(
        aware_root=FSCommitStore().aware_root,
        branch_id=branch_id,
        projection_hash=projection_hash,
    )


async def _lane_head_commit_id(
    *,
    branch_id: UUID,
    projection_hash: str,
) -> UUID | None:
    head = await FSCommitStore().head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    if head is None:
        return None
    raw_commit_id = head.get("commit_id")
    if raw_commit_id is None:
        return None
    if isinstance(raw_commit_id, UUID):
        return raw_commit_id
    return UUID(str(raw_commit_id))


async def _object_instance_graph_commit_id_from_domain_commit(
    *,
    branch_id: UUID,
    projection_hash: str,
    domain_commit_id: UUID,
) -> UUID | None:
    domain_commit = await FSCommitStore().get_commit(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=domain_commit_id,
    )
    if domain_commit is None:
        return None
    return stable_object_instance_graph_commit_id(
        object_instance_graph_identity_id=domain_commit.object_instance_graph_identity_id,
        commit_id=domain_commit_id,
    )


def _assert_existing_file_within(*, root: Path, path: Path, label: str) -> None:
    _assert_path_within(base=root, candidate=path, label=label)
    if not path.resolve().is_file():
        raise FileNotFoundError(f"{label} must resolve to a file: {path.resolve()}")


def _assert_existing_dir_within(*, root: Path, path: Path, label: str) -> None:
    _assert_path_within(base=root, candidate=path, label=label)
    if not path.resolve().is_dir():
        raise NotADirectoryError(
            f"{label} must resolve to a directory: {path.resolve()}"
        )


def _assert_path_within(*, base: Path, candidate: Path, label: str) -> None:
    base_resolved = base.resolve()
    candidate_resolved = candidate.resolve()
    if (
        candidate_resolved == base_resolved
        or base_resolved in candidate_resolved.parents
    ):
        return
    raise RuntimeError(
        "API package materialization path resolved outside boundary: "
        + f"label={label} base={base_resolved} path={candidate_resolved}"
    )


def _relative_to(*, path: Path, root: Path, label: str) -> str:
    resolved_path = path.resolve()
    resolved_root = root.resolve()
    try:
        relative = resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise RuntimeError(
            "API package materialization path resolved outside workspace root: "
            + f"label={label} root={resolved_root} path={resolved_path}"
        ) from exc
    relative_text = relative.as_posix()
    return relative_text or "."


__all__ = [
    "ApiEndpointCatalog",
    "ApiCompilePlanPackageMaterializationResult",
    "ApiPackageMaterializationResult",
    "ApiPackageMaterializationSpec",
    "build_generated_api_compile_plan_accessible_graphs",
    "load_api_compile_plan_payloads",
    "materialize_api_package_from_compile_plan_input",
    "materialize_api_package_from_manifest",
    "materialize_api_compile_plan_ontology",
    "resolve_api_package_materialization_spec",
]
