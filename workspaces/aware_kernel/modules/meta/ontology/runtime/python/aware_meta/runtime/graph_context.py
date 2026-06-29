from __future__ import annotations

from collections import OrderedDict
from collections.abc import Iterable, Mapping
from contextlib import contextmanager
from dataclasses import dataclass, field, replace
import hashlib
from pathlib import Path
from threading import RLock
from time import perf_counter
from typing import TypeVar, cast
from uuid import NAMESPACE_URL, UUID, uuid5

from aware_code.semantic_materialization import (
    SEMANTIC_MATERIALIZATION_RUNTIME_TARGET_MANIFEST_POLICY_ISOLATE_TARGET_MANIFESTS,
    SEMANTIC_MATERIALIZATION_RUNTIME_TARGET_MANIFEST_POLICY_KEY,
    SEMANTIC_MATERIALIZATION_TARGET_MANIFEST_PATHS_CONTEXT_KEY,
    SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_CONTEXT_KEY,
    SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_SCHEMA,
    SemanticPackageMaterializationExecutionContextRequest,
    SemanticPackageMaterializationRuntimeContextRequest,
)
from aware_code.semantic_function_call_execution import (
    SemanticFunctionCallExecutionConfig,
)
from aware_meta.manifest.spec import AwareTomlSpec
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.graph.config.handlers import build_object_projection_graphs
from aware_meta.graph.config.runtime_derivation.service import (
    derive_runtime_object_config_graph,
    derive_runtime_object_config_graphs,
)
from aware_meta.graph.config.namespace.membership import (
    build_namespace_membership_payload_from_ocg_identity,
)
from aware_meta.package_graph_reuse_cache import (
    OBJECT_CONFIG_GRAPH_PACKAGE_CONTEXT_GRAPHS_DERIVATION_SIGNATURE,
    OBJECT_CONFIG_GRAPH_PACKAGE_REUSE_CACHE_KIND_CONTEXT_GRAPHS,
    OBJECT_CONFIG_GRAPH_PACKAGE_REUSE_CACHE_KIND_MATERIALIZED_PACKAGE,
    OBJECT_CONFIG_GRAPH_PACKAGE_REUSE_CACHE_VERSION,
    external_graph_signature,
    object_config_graph_payload_has_materialized_body,
    object_config_graph_payload_has_namespace_evidence,
    read_object_config_graph_package_context_reuse_cache_payload,
    read_object_config_graph_package_reuse_cache_payload,
    source_text_manifest_hash,
    write_object_config_graph_package_context_reuse_cache_payload,
)
from aware_meta.graph.projection.portal_index import (
    ObjectProjectionGraphPortalIndex,
    build_portal_index,
)
from aware_meta.runtime.handler_executor.contracts import MetaGraphRuntimeIndex
from aware_meta.runtime.handler_executor.index import (
    MetaGraphFunctionImplOwnership,
    MetaGraphImplementationPolicy,
)
from aware_meta.runtime.package_index import (
    MetaRuntimePackageIndexEntry,
    build_meta_runtime_package_projection_index,
    stable_meta_runtime_package_branch_id,
)
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_relationship import (
    ClassConfigRelationship,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.config.object_config_graph_identity import (
    ObjectConfigGraphIdentity,
)
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_meta_ontology.stable_ids import (
    stable_object_config_graph_id,
    stable_object_config_graph_package_id,
)
from aware_meta.graph.config.stable_ids import stable_object_config_graph_identity_id


_AWARE_SOURCE_EXTENSION = ".aware"
_IGNORED_SEGMENTS = frozenset(
    {".aware", ".git", "__pycache__", "node_modules", ".venv", "venv"}
)
_PACKAGE_REUSE_CACHE_VERSION = OBJECT_CONFIG_GRAPH_PACKAGE_REUSE_CACHE_VERSION
_RUNTIME_INDEX_SNAPSHOT_CACHE_MAX_ENTRIES = 8
_PACKAGE_GRAPH_SESSION_CACHE_MAX_ENTRIES = 32
_T = TypeVar("_T")
_RuntimeIndexSnapshotCacheKey = tuple[str, tuple[tuple[str, ...], ...]]
_RUNTIME_INDEX_SNAPSHOT_CACHE: OrderedDict[
    _RuntimeIndexSnapshotCacheKey,
    "MetaGraphRuntimeIndexSnapshot",
] = OrderedDict()
_RUNTIME_INDEX_SNAPSHOT_CACHE_LOCK = RLock()


@dataclass(frozen=True, slots=True)
class _PackageGraphCacheIdentity:
    package_name: str
    fqn_prefix: str
    branch_id: UUID
    object_config_graph_id: UUID
    object_config_graph_package_id: UUID
    source_manifest_hash: str
    dependency_signature: str


@dataclass(frozen=True, slots=True)
class _PackageGraphRef:
    package_name: str
    fqn_prefix: str
    object_config_graph_id: UUID
    object_config_graph_hash: str


@dataclass(frozen=True, slots=True)
class _CachedPackageGraphs:
    source_graph: ObjectConfigGraph | None
    runtime_graph: ObjectConfigGraph
    source_graph_ref: _PackageGraphRef
    identity: _PackageGraphCacheIdentity


_PACKAGE_GRAPH_SESSION_CACHE: OrderedDict[
    _PackageGraphCacheIdentity,
    _CachedPackageGraphs,
] = OrderedDict()
_PACKAGE_GRAPH_SESSION_CACHE_LOCK = RLock()


@dataclass(frozen=True, slots=True)
class MetaGraphRuntimePackageTiming:
    package_name: str
    manifest_path: str
    cache_status: str
    cache_source: str | None = None
    cache_miss_reason: str | None = None
    phase_timings_s: Mapping[str, float] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class MetaGraphRuntimeIndexSnapshot:
    """Read-only Meta graph index snapshot built from OCG truth.

    This intentionally satisfies MetaGraphRuntimeIndex without depending on the
    legacy composed runtime index or runtime harness artifacts.
    """

    ocg: ObjectConfigGraph
    class_configs_by_id: Mapping[UUID, ClassConfig]
    attribute_configs_by_id: Mapping[UUID, AttributeConfig]
    relationships_by_id: Mapping[UUID, ClassConfigRelationship]
    opg_by_id: Mapping[UUID, ObjectProjectionGraph]
    opg_by_hash: Mapping[str, ObjectProjectionGraph]
    portal_index: ObjectProjectionGraphPortalIndex
    composition_context_id: UUID | None = None
    runtime_handler_provider_import_roots: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class MetaGraphRuntimeContext:
    """Meta-owned graph context for semantic materialization execution."""

    index: MetaGraphRuntimeIndexSnapshot
    projection_hash_by_name: Mapping[str, str]
    runtime_graph_ids: tuple[UUID, ...]
    source_graph_ids: tuple[UUID, ...] = ()
    runtime_graphs: tuple[ObjectConfigGraph, ...] = ()
    source_graphs: tuple[ObjectConfigGraph, ...] = ()
    runtime_graph_by_package_name: Mapping[str, ObjectConfigGraph] = field(
        default_factory=dict
    )
    source_graph_by_package_name: Mapping[str, ObjectConfigGraph] = field(
        default_factory=dict
    )
    implementation_policy: MetaGraphImplementationPolicy = field(
        default_factory=MetaGraphImplementationPolicy
    )
    composition_context_id: UUID | None = None
    composite: bool = False
    phase_timings_s: Mapping[str, float] = field(default_factory=dict)
    package_timings: tuple[MetaGraphRuntimePackageTiming, ...] = ()
    runtime_index_snapshot_cache_status: str = "unknown"
    runtime_handler_provider_import_roots: tuple[str, ...] = ()

    def projection_hash_for_name(self, projection_name: str) -> str:
        """Resolve an authored projection name exactly."""

        target = projection_name.strip()
        if not target:
            raise ValueError("Projection name is required.")
        projection_hash = self.projection_hash_by_name.get(target)
        if projection_hash is None:
            raise ValueError(
                f"Projection {projection_name!r} was not found in Meta graph context."
            )
        return projection_hash


@dataclass(frozen=True, slots=True)
class MetaWorkspaceMaterializationRuntimeContext:
    """Workspace materialization context backed by Meta-owned graph runtime."""

    meta_context: MetaGraphRuntimeContext
    runtime: object
    actor_id: UUID | None = None

    @property
    def index(self) -> MetaGraphRuntimeIndexSnapshot:
        return self.meta_context.index

    @property
    def phase_timings_s(self) -> Mapping[str, float]:
        return self.meta_context.phase_timings_s

    @property
    def package_timings(self) -> tuple[MetaGraphRuntimePackageTiming, ...]:
        return self.meta_context.package_timings

    @property
    def runtime_object_config_graphs(self) -> tuple[ObjectConfigGraph, ...]:
        return self.meta_context.runtime_graphs

    @property
    def semantic_object_config_graphs(self) -> tuple[ObjectConfigGraph, ...]:
        return self.meta_context.source_graphs

    def projection_hash_for_name(self, projection_name: str) -> str:
        return self.meta_context.projection_hash_for_name(projection_name)

    def bind_lane(
        self,
        *,
        projection: str,
        branch_id: UUID,
    ) -> object:
        bind = getattr(self.runtime, "bind", None)
        if not callable(bind):
            raise RuntimeError(
                "Meta Workspace materialization runtime cannot bind lanes."
            )
        return bind(
            projection=projection,
            branch_id=branch_id,
            actor_id=self.actor_id,
            context=self.meta_context,
        )


def build_meta_graph_runtime_context_for_aware_package_manifests(
    *,
    package_manifest_paths: Iterable[Path],
    workspace_root: Path | None = None,
    composition_context_id: UUID | None = None,
    composite_name: str = "Aware Package Graph Runtime Context",
    strict_package_graph_cache: bool = False,
    package_entries_by_manifest_path: (
        Mapping[
            Path,
            MetaRuntimePackageIndexEntry,
        ]
        | None
    ) = None,
    package_cache_owner_roots_by_manifest_path: Mapping[Path, Path] | None = None,
    source_analysis_allowed_manifest_paths: Iterable[Path] = (),
    package_graph_cache_request_signature: str | None = None,
    load_source_graph_payloads: bool = True,
) -> MetaGraphRuntimeContext:
    """Build a Meta graph runtime context directly from canonical package manifests.

    The caller is responsible for passing manifests in dependency order. Meta owns
    the source-package OCG assembly and derives runtime graphs from that OCG truth;
    no environment runtime manifest or generated package import is required.
    """

    from aware_meta.manifest.loader import load_aware_toml_spec  # noqa: WPS433
    from aware_meta.semantic_analysis import analyze_meta_ocg_sources  # noqa: WPS433

    total_started_at = perf_counter()
    phase_timings_s: dict[str, float] = {}
    package_timings: list[MetaGraphRuntimePackageTiming] = []
    with _record_phase(phase_timings_s, "dedupe_package_manifest_paths"):
        manifest_paths = _dedupe_package_manifest_paths(package_manifest_paths)
    if not manifest_paths:
        raise ValueError(
            "Meta graph runtime context requires at least one package manifest."
        )
    with _record_phase(phase_timings_s, "resolve_workspace_root"):
        resolved_workspace_root = _workspace_root_for_package_manifests(
            workspace_root=workspace_root,
            package_manifest_paths=manifest_paths,
        )
    catalog_entries_by_manifest_path = _catalog_entries_by_resolved_manifest_path(
        package_entries_by_manifest_path
    )
    if not catalog_entries_by_manifest_path:
        catalog_entries_by_manifest_path = (
            _module_catalog_entries_by_resolved_manifest_path(
                repo_root=resolved_workspace_root,
                manifest_paths=manifest_paths,
            )
        )
    with _record_phase(phase_timings_s, "order_package_manifest_paths"):
        manifest_paths = _topologically_order_package_manifest_paths(
            manifest_paths,
            package_entries_by_manifest_path=catalog_entries_by_manifest_path,
        )

    source_graph_by_package_name: dict[str, ObjectConfigGraph] = {}
    source_graph_ref_by_package_name: dict[str, _PackageGraphRef] = {}
    source_graph_cache_identity_by_package_name: dict[
        str,
        _PackageGraphCacheIdentity,
    ] = {}
    source_graph_cache_owner_root_by_package_name: dict[str, Path] = {}
    runtime_graph_by_package_name: dict[str, ObjectConfigGraph] = {}
    function_impl_ownership_by_owner_prefix: dict[
        str,
        MetaGraphFunctionImplOwnership,
    ] = {}
    runtime_handler_provider_import_roots: list[str] = []
    runtime_graphs: list[ObjectConfigGraph] = []
    dependency_closure_by_package_name: dict[str, tuple[str, ...]] = {}
    catalog_cache_owner_roots_by_manifest_path = (
        _path_mapping_by_resolved_manifest_path(
            package_cache_owner_roots_by_manifest_path
        )
    )
    source_analysis_allowed_paths = _resolved_path_set(
        source_analysis_allowed_manifest_paths
    )
    with _record_phase(phase_timings_s, "load_package_graphs"):
        for manifest_path in manifest_paths:
            resolved_manifest_path = manifest_path.expanduser().resolve()
            package_started_at = perf_counter()
            package_phase_timings_s: dict[str, float] = {}
            cache_diagnostics: dict[str, object] = {}
            with _record_phase(package_phase_timings_s, "load_aware_toml_spec"):
                spec = load_aware_toml_spec(toml_path=manifest_path)
            package_name = str(spec.package.package_name)
            catalog_entry = _catalog_entry_for_manifest_path(
                entries_by_manifest_path=catalog_entries_by_manifest_path,
                manifest_path=manifest_path,
            )
            if (
                catalog_entry is not None
                and catalog_entry.runtime_handler_provider_import_root
            ):
                runtime_handler_provider_import_roots.append(
                    catalog_entry.runtime_handler_provider_import_root
                )
            package_cache_owner_root = catalog_cache_owner_roots_by_manifest_path.get(
                resolved_manifest_path,
                resolved_workspace_root,
            )
            strict_cache_required = (
                strict_package_graph_cache
                and resolved_manifest_path not in source_analysis_allowed_paths
            )
            if strict_package_graph_cache:
                if catalog_entry is None:
                    raise RuntimeError(
                        "Strict Meta package graph cache requires an explicit "
                        "catalog entry for manifest: "
                        f"{manifest_path.as_posix()}"
                    )
                _validate_catalog_entry_matches_manifest_spec(
                    catalog_entry=catalog_entry,
                    spec=spec,
                    manifest_path=manifest_path,
                )
            with _record_phase(
                package_phase_timings_s,
                "remember_manifest_implementation_policy",
            ):
                _remember_manifest_implementation_policy(
                    spec=spec,
                    ownership_by_owner_prefix=function_impl_ownership_by_owner_prefix,
                )
            with _record_phase(package_phase_timings_s, "validate_dependency_order"):
                dependency_names = (
                    catalog_entry.dependency_package_names
                    if catalog_entry is not None
                    else tuple(
                        dependency.package_name for dependency in spec.dependencies
                    )
                )
                if strict_package_graph_cache and catalog_entry is not None:
                    _validate_catalog_entry_dependencies_match_manifest_spec(
                        catalog_entry=catalog_entry,
                        spec=spec,
                        manifest_path=manifest_path,
                    )
                missing_dependencies = tuple(
                    dependency_name
                    for dependency_name in dependency_names
                    if dependency_name not in source_graph_ref_by_package_name
                )
                if missing_dependencies:
                    raise ValueError(
                        "Meta graph runtime context package manifests must be "
                        "topologically ordered and dependency-complete. "
                        f"package={spec.package.package_name!r} missing="
                        + ", ".join(missing_dependencies)
                    )
                dependency_closure_names = _dependency_closure_package_names(
                    dependency_names=dependency_names,
                    dependency_closure_by_package_name=(
                        dependency_closure_by_package_name
                    ),
                )
            external_graphs = tuple(
                graph
                for package_name, graph in source_graph_by_package_name.items()
                if package_name in dependency_closure_names
            )
            external_graph_refs = tuple(
                graph_ref
                for package_name, graph_ref in source_graph_ref_by_package_name.items()
                if package_name in dependency_closure_names
            )
            external_runtime_graphs = tuple(
                graph
                for package_name, graph in runtime_graph_by_package_name.items()
                if package_name in dependency_closure_names
            )
            if strict_package_graph_cache and catalog_entry is not None:
                assert catalog_entry is not None
                cached_graphs = _try_load_catalog_cached_package_graphs(
                    cache_owner_root=package_cache_owner_root,
                    catalog_entry=catalog_entry,
                    external_graph_refs=external_graph_refs,
                    load_source_graph=load_source_graph_payloads,
                    phase_timings_s=package_phase_timings_s,
                    diagnostics=cache_diagnostics,
                )
            else:
                cached_graphs = _try_load_cached_package_graphs(
                    workspace_root=package_cache_owner_root,
                    manifest_path=manifest_path,
                    spec=spec,
                    external_graphs=external_graphs,
                    phase_timings_s=package_phase_timings_s,
                    diagnostics=cache_diagnostics,
                )
            cache_status = "hit"
            cache_source = _diagnostic_string(
                cache_diagnostics,
                "cache_source",
            )
            cache_miss_reason: str | None = None
            if cached_graphs is None:
                if strict_cache_required:
                    cache_miss_reason = _diagnostic_string(
                        cache_diagnostics,
                        "cache_miss_reason",
                    )
                    raise RuntimeError(
                        "Strict Meta package graph cache miss for "
                        f"package={package_name!r} manifest="
                        f"{manifest_path.as_posix()!r} reason="
                        f"{cache_miss_reason or 'unknown'!r} request_signature="
                        f"{package_graph_cache_request_signature!r}."
                    )
                if not load_source_graph_payloads:
                    with _record_phase(
                        package_phase_timings_s,
                        "load_dependency_source_graph_payloads_for_analysis",
                    ):
                        external_graphs = _load_missing_source_dependency_graphs(
                            dependency_closure_names=dependency_closure_names,
                            source_graph_by_package_name=source_graph_by_package_name,
                            source_graph_cache_identity_by_package_name=(
                                source_graph_cache_identity_by_package_name
                            ),
                            source_graph_cache_owner_root_by_package_name=(
                                source_graph_cache_owner_root_by_package_name
                            ),
                        )
                cache_status = "analysis_fallback"
                cache_source = "analysis"
                cache_miss_reason = _diagnostic_string(
                    cache_diagnostics,
                    "cache_miss_reason",
                )
                with _record_phase(
                    package_phase_timings_s,
                    "analyze_meta_ocg_sources",
                ):
                    analysis = analyze_meta_ocg_sources(
                        package_root=manifest_path.parent,
                        source_files=(),
                        manifest_path=manifest_path,
                        external_graphs=external_graphs,
                        external_runtime_graphs=external_runtime_graphs,
                        fail_on_error=True,
                    )
                if analysis.source_object_config_graph is None:
                    raise ValueError(
                        "Meta graph runtime context package analysis returned no "
                        f"source ObjectConfigGraph: {manifest_path}"
                    )
                if analysis.object_config_graph is None:
                    raise ValueError(
                        "Meta graph runtime context package analysis returned no "
                        f"runtime ObjectConfigGraph: {manifest_path}"
                    )
                source_graph = analysis.source_object_config_graph
                runtime_graph = analysis.object_config_graph
                with _record_phase(
                    package_phase_timings_s,
                    "write_context_package_graph_cache",
                ):
                    _try_write_context_package_graph_cache(
                        workspace_root=package_cache_owner_root,
                        manifest_path=manifest_path,
                        spec=spec,
                        external_graphs=external_graphs,
                        source_graph=source_graph,
                        runtime_graph=runtime_graph,
                    )
            else:
                source_graph = cached_graphs.source_graph
                runtime_graph = cached_graphs.runtime_graph
                if cache_source is None:
                    cache_source = "durable_reuse_cache"
            source_graph_ref_by_package_name[spec.package.package_name] = (
                cached_graphs.source_graph_ref
                if cached_graphs is not None
                else _package_graph_ref_from_graph(
                    package_name=spec.package.package_name,
                    fqn_prefix=str(runtime_graph.fqn_prefix or ""),
                    graph=source_graph,
                )
            )
            if cached_graphs is not None:
                source_graph_cache_identity_by_package_name[
                    spec.package.package_name
                ] = cached_graphs.identity
                source_graph_cache_owner_root_by_package_name[
                    spec.package.package_name
                ] = package_cache_owner_root
            if source_graph is not None:
                source_graph_by_package_name[spec.package.package_name] = source_graph
            runtime_graph_by_package_name[spec.package.package_name] = runtime_graph
            dependency_closure_by_package_name[spec.package.package_name] = (
                dependency_closure_names
            )
            runtime_graphs.append(runtime_graph)
            package_phase_timings_s["total"] = _round_duration_s(
                perf_counter() - package_started_at
            )
            package_timings.append(
                MetaGraphRuntimePackageTiming(
                    package_name=package_name,
                    manifest_path=manifest_path.as_posix(),
                    cache_status=cache_status,
                    cache_source=cache_source,
                    cache_miss_reason=cache_miss_reason,
                    phase_timings_s=dict(sorted(package_phase_timings_s.items())),
                )
            )

    context = build_meta_graph_runtime_context(
        runtime_graphs=tuple(runtime_graphs),
        source_graphs=tuple(source_graph_by_package_name.values()),
        runtime_graph_by_package_name=runtime_graph_by_package_name,
        source_graph_by_package_name=source_graph_by_package_name,
        composition_context_id=composition_context_id,
        composite_name=composite_name,
        implementation_policy=MetaGraphImplementationPolicy(
            function_impl_ownership_by_owner_prefix=(
                function_impl_ownership_by_owner_prefix
            ),
        ),
        phase_timings_s=phase_timings_s,
        package_timings=tuple(package_timings),
        runtime_handler_provider_import_roots=runtime_handler_provider_import_roots,
    )
    phase_timings_s["total"] = _round_duration_s(perf_counter() - total_started_at)
    return replace(
        context,
        phase_timings_s=dict(sorted(phase_timings_s.items())),
    )


def _remember_manifest_implementation_policy(
    *,
    spec: AwareTomlSpec,
    ownership_by_owner_prefix: dict[str, MetaGraphFunctionImplOwnership],
) -> None:
    package = spec.package
    fqn_prefix = package.fqn_prefix.strip()
    if not fqn_prefix:
        return
    ownership = MetaGraphFunctionImplOwnership(
        package.function_impl_ownership or "authored"
    )
    existing = ownership_by_owner_prefix.get(fqn_prefix)
    if existing is not None and existing is not ownership:
        raise ValueError(
            "Conflicting manifest FunctionImpl ownership policy for "
            f"fqn_prefix={fqn_prefix!r}: {existing.value!r} != {ownership.value!r}"
        )
    ownership_by_owner_prefix[fqn_prefix] = ownership


def _dependency_closure_package_names(
    *,
    dependency_names: tuple[str, ...],
    dependency_closure_by_package_name: Mapping[str, tuple[str, ...]],
) -> tuple[str, ...]:
    names: list[str] = []
    seen: set[str] = set()
    for dependency_name in dependency_names:
        for package_name in (
            *dependency_closure_by_package_name.get(dependency_name, ()),
            dependency_name,
        ):
            if package_name in seen:
                continue
            seen.add(package_name)
            names.append(package_name)
    return tuple(names)


def build_meta_graph_runtime_context(
    *,
    runtime_graphs: Iterable[ObjectConfigGraph] = (),
    source_graphs: Iterable[ObjectConfigGraph] = (),
    runtime_graph_by_package_name: Mapping[str, ObjectConfigGraph] | None = None,
    source_graph_by_package_name: Mapping[str, ObjectConfigGraph] | None = None,
    composition_context_id: UUID | None = None,
    composite_name: str = "Aware Meta Graph Runtime Context",
    implementation_policy: MetaGraphImplementationPolicy | None = None,
    phase_timings_s: dict[str, float] | None = None,
    package_timings: tuple[MetaGraphRuntimePackageTiming, ...] = (),
    runtime_handler_provider_import_roots: Iterable[str] = (),
) -> MetaGraphRuntimeContext:
    """Build a Meta graph context from committed/runtime-derived graph truth."""

    started_at = perf_counter()
    timings = phase_timings_s if phase_timings_s is not None else {}
    with _record_phase(timings, "prepare_runtime_graphs"):
        source_graph_tuple = tuple(source_graphs)
        explicit_runtime_graphs = tuple(runtime_graphs)
        explicit_runtime_graph_ids = {
            graph.id for graph in explicit_runtime_graphs if graph.id is not None
        }
        explicit_runtime_graph_fqn_prefixes = {
            key
            for graph in explicit_runtime_graphs
            if (key := _object_config_graph_fqn_prefix_key(graph)) is not None
        }
        source_graphs_to_derive = tuple(
            graph
            for graph in source_graph_tuple
            if graph.id not in explicit_runtime_graph_ids
            and _object_config_graph_fqn_prefix_key(graph)
            not in explicit_runtime_graph_fqn_prefixes
        )
        derived_runtime_graphs = _derive_runtime_graphs(
            source_graphs_to_derive,
            external_runtime_graphs=explicit_runtime_graphs,
        )
        runtime_graph_tuple = (*explicit_runtime_graphs, *derived_runtime_graphs)
    if not runtime_graph_tuple:
        raise ValueError("Meta graph runtime context requires at least one OCG.")

    with _record_phase(timings, "compose_runtime_graphs"):
        context_graph = _context_graph(
            runtime_graphs=runtime_graph_tuple,
            composite_name=composite_name,
        )
    runtime_index_snapshot_cache_status = "unknown"
    with _record_phase(timings, "build_runtime_index_snapshot"):
        index, runtime_index_snapshot_cache_status = (
            _build_meta_graph_runtime_index_snapshot_cached(
                ocg=context_graph,
                composition_context_id=composition_context_id,
            )
        )
        runtime_handler_provider_roots = _clean_string_tuple(
            runtime_handler_provider_import_roots
        )
        if runtime_handler_provider_roots:
            index = replace(
                index,
                runtime_handler_provider_import_roots=runtime_handler_provider_roots,
            )
    with _record_phase(timings, "projection_hash_by_name"):
        projection_hash_by_name = _projection_hash_by_name(index.ocg)
    timings["total"] = _round_duration_s(perf_counter() - started_at)
    return MetaGraphRuntimeContext(
        index=index,
        projection_hash_by_name=projection_hash_by_name,
        runtime_graph_ids=tuple(graph.id for graph in runtime_graph_tuple),
        source_graph_ids=tuple(graph.id for graph in source_graph_tuple),
        runtime_graphs=runtime_graph_tuple,
        source_graphs=source_graph_tuple,
        runtime_graph_by_package_name=dict(runtime_graph_by_package_name or {}),
        source_graph_by_package_name=dict(source_graph_by_package_name or {}),
        implementation_policy=implementation_policy or MetaGraphImplementationPolicy(),
        composition_context_id=composition_context_id,
        composite=len(runtime_graph_tuple) > 1,
        phase_timings_s=dict(sorted(timings.items())),
        package_timings=package_timings,
        runtime_index_snapshot_cache_status=runtime_index_snapshot_cache_status,
        runtime_handler_provider_import_roots=runtime_handler_provider_roots,
    )


def _object_config_graph_fqn_prefix_key(graph: ObjectConfigGraph) -> str | None:
    fqn_prefix = str(graph.fqn_prefix or "").strip()
    if not fqn_prefix:
        return None
    return fqn_prefix


def build_meta_graph_runtime_context_for_semantic_materialization(
    request: SemanticPackageMaterializationExecutionContextRequest,
) -> MetaGraphRuntimeContext | None:
    """Resolve Meta graph context from semantic materialization graph evidence."""

    if not _semantic_function_call_execution_enabled(request):
        return None
    runtime_graphs = _object_config_graphs_from_context_value(
        request.context.get("runtime_object_config_graphs")
    )
    source_graphs = _object_config_graphs_from_context_value(
        request.context.get("semantic_object_config_graphs")
    )
    runtime_index_ocg = getattr(getattr(request, "index", None), "ocg", None)
    if isinstance(runtime_index_ocg, ObjectConfigGraph):
        runtime_graphs = _prepend_unique_object_config_graph(
            graph=runtime_index_ocg,
            graphs=runtime_graphs,
        )
    projection_identity_ocg = request.context.get("projection_identity_ocg")
    if isinstance(projection_identity_ocg, ObjectConfigGraph):
        runtime_graphs = _prepend_unique_object_config_graph(
            graph=projection_identity_ocg,
            graphs=runtime_graphs,
        )
    if not runtime_graphs and not source_graphs:
        return None
    return build_meta_graph_runtime_context(
        runtime_graphs=runtime_graphs,
        source_graphs=source_graphs,
    )


def _semantic_function_call_execution_enabled(
    request: SemanticPackageMaterializationExecutionContextRequest,
) -> bool:
    return SemanticFunctionCallExecutionConfig.from_materialization_context(
        request.context
    ).enabled


def build_meta_workspace_materialization_runtime_context(
    request: SemanticPackageMaterializationRuntimeContextRequest,
) -> MetaWorkspaceMaterializationRuntimeContext | None:
    """Build Workspace's provider-owned materialization context from Meta truth."""

    provider_started_at = perf_counter()
    provider_phase_timings_s: dict[str, float] = {}
    with _record_phase(
        provider_phase_timings_s,
        "workspace_provider_select_manifest_paths_s",
    ):
        manifest_paths = _workspace_materialization_package_manifest_paths(request)
    if not manifest_paths:
        return None

    with _record_phase(
        provider_phase_timings_s,
        "workspace_provider_package_cache_owner_roots_s",
    ):
        package_cache_owner_roots_by_manifest_path = (
            _package_cache_owner_roots_by_manifest_path_for_runtime_request(
                request=request,
                manifest_paths=manifest_paths,
            )
        )
    with _record_phase(
        provider_phase_timings_s,
        "workspace_provider_package_entries_s",
    ):
        package_entries_by_manifest_path = (
            _package_entries_by_manifest_path_for_runtime_request(
                request=request,
                manifest_paths=manifest_paths,
            )
        )
    with _record_phase(
        provider_phase_timings_s,
        "workspace_provider_source_analysis_allowed_paths_s",
    ):
        source_analysis_allowed_manifest_paths = (
            _workspace_materialization_source_analysis_allowed_manifest_paths(
                request=request,
                manifest_paths=manifest_paths,
            )
        )
    with _record_phase(
        provider_phase_timings_s,
        "workspace_provider_package_graph_cache_request_signature_s",
    ):
        package_graph_cache_request_signature = (
            _workspace_materialization_package_graph_cache_request_signature(
                request=request,
                manifest_paths=manifest_paths,
                package_cache_owner_roots_by_manifest_path=(
                    package_cache_owner_roots_by_manifest_path
                ),
            )
        )
    with _record_phase(
        provider_phase_timings_s,
        "workspace_provider_handler_owner_prefixes_s",
    ):
        handler_owner_prefixes = _runtime_context_handler_owner_prefixes(request)
    with _record_phase(
        provider_phase_timings_s,
        "workspace_provider_import_runtime_support_s",
    ):
        from aware_meta.runtime.factory import (  # noqa: WPS433
            build_meta_graph_runtime_for_aware_package_manifests,
        )

    with _record_phase(
        provider_phase_timings_s,
        "workspace_provider_build_meta_graph_runtime_s",
    ):
        runtime = build_meta_graph_runtime_for_aware_package_manifests(
            package_manifest_paths=manifest_paths,
            workspace_root=request.workspace_root,
            composite_name="Aware Workspace Meta Materialization Context",
            implementation_policy=_workspace_materialization_implementation_policy(),
            strict_package_graph_cache=(
                _has_explicit_semantic_ontology_package_catalog(request.context)
            ),
            package_entries_by_manifest_path=package_entries_by_manifest_path,
            package_cache_owner_roots_by_manifest_path=(
                package_cache_owner_roots_by_manifest_path
            ),
            source_analysis_allowed_manifest_paths=(
                source_analysis_allowed_manifest_paths
            ),
            package_graph_cache_request_signature=(
                package_graph_cache_request_signature
            ),
            handler_owner_prefixes=handler_owner_prefixes,
            load_source_graph_payloads=(
                _runtime_context_load_source_graph_payloads_for_request(request)
            ),
        )
    wrap_started_at = perf_counter()
    meta_context = runtime.context
    if meta_context is None:
        raise RuntimeError("Meta graph runtime did not expose its graph context.")
    provider_phase_timings_s["workspace_provider_wrap_context_s"] = _round_duration_s(
        perf_counter() - wrap_started_at
    )
    provider_phase_timings_s["workspace_provider_total_s"] = _round_duration_s(
        perf_counter() - provider_started_at
    )
    meta_context = _meta_context_with_workspace_provider_phase_timings(
        meta_context=meta_context,
        phase_timings_s=provider_phase_timings_s,
    )
    return MetaWorkspaceMaterializationRuntimeContext(
        meta_context=meta_context,
        runtime=runtime,
        actor_id=request.actor_id,
    )


def _meta_context_with_workspace_provider_phase_timings(
    *,
    meta_context: MetaGraphRuntimeContext,
    phase_timings_s: Mapping[str, float],
) -> MetaGraphRuntimeContext:
    try:
        existing_timings = (
            object.__getattribute__(meta_context, "phase_timings_s") or {}
        )
    except AttributeError:
        existing_timings = {}
    merged_timings = {
        **dict(existing_timings),
        **dict(sorted(phase_timings_s.items())),
    }
    try:
        return replace(meta_context, phase_timings_s=merged_timings)
    except TypeError:
        setattr(meta_context, "phase_timings_s", merged_timings)
        return cast(MetaGraphRuntimeContext, meta_context)


def _workspace_materialization_implementation_policy() -> MetaGraphImplementationPolicy:
    """Keep provider-delta OCG mutations on handler-backed ontology functions."""

    return MetaGraphImplementationPolicy(
        default_function_impl_ownership=MetaGraphFunctionImplOwnership.authored,
    )


def _runtime_context_load_source_graph_payloads_for_request(
    request: SemanticPackageMaterializationRuntimeContextRequest,
) -> bool:
    mode = _clean_string_value(
        request.context.get("runtime_context_graph_publication_mode")
    ) or _clean_string_value(
        request.provider_payload.get("runtime_context_graph_publication_mode")
    )
    return mode != "runtime_only"


def _has_explicit_semantic_ontology_package_catalog(
    context: Mapping[str, object],
) -> bool:
    return SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_CONTEXT_KEY in context


def _package_entries_by_manifest_path_for_runtime_request(
    *,
    request: SemanticPackageMaterializationRuntimeContextRequest,
    manifest_paths: tuple[Path, ...],
) -> dict[Path, MetaRuntimePackageIndexEntry] | None:
    if not _has_explicit_semantic_ontology_package_catalog(request.context):
        return None
    entries_by_package_name, _package_names_by_module_id = (
        _ontology_package_manifest_catalog_for_request(request)
    )
    selected_paths = {path.expanduser().resolve() for path in manifest_paths}
    return {
        entry.manifest_path.expanduser().resolve(): entry
        for entry in entries_by_package_name.values()
        if entry.manifest_path.expanduser().resolve() in selected_paths
    }


def _package_cache_owner_roots_by_manifest_path_for_runtime_request(
    *,
    request: SemanticPackageMaterializationRuntimeContextRequest,
    manifest_paths: tuple[Path, ...],
) -> dict[Path, Path]:
    if not _has_explicit_semantic_ontology_package_catalog(request.context):
        return {}
    catalog = request.context.get(SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_CONTEXT_KEY)
    if not isinstance(catalog, Mapping):
        return {}
    raw_entries = catalog.get("entries")
    if not isinstance(raw_entries, list):
        return {}
    selected_paths = {path.expanduser().resolve() for path in manifest_paths}
    owner_roots: dict[Path, Path] = {}
    for raw_entry in raw_entries:
        if not isinstance(raw_entry, Mapping):
            continue
        manifest_path = _optional_catalog_path(
            value=raw_entry.get("manifest_path"),
            default_root=request.repo_root,
        )
        if manifest_path is None or manifest_path not in selected_paths:
            continue
        owner_root = _optional_catalog_path(
            value=raw_entry.get("owner_root"),
            default_root=request.workspace_root,
        )
        if owner_root is None:
            owner_root = _inferred_catalog_owner_root(
                manifest_path=manifest_path,
                workspace_root=request.workspace_root,
                repo_root=request.repo_root,
            )
        owner_roots[manifest_path] = owner_root
    return owner_roots


def _optional_catalog_path(
    *,
    value: object,
    default_root: Path,
) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    path = Path(value.strip()).expanduser()
    if not path.is_absolute():
        path = default_root / path
    return path.resolve()


def _inferred_catalog_owner_root(
    *,
    manifest_path: Path,
    workspace_root: Path,
    repo_root: Path,
) -> Path:
    resolved_workspace_root = workspace_root.expanduser().resolve()
    resolved_repo_root = repo_root.expanduser().resolve()
    if _is_within(candidate=manifest_path, root=resolved_workspace_root):
        return resolved_workspace_root
    if _is_within(candidate=manifest_path, root=resolved_repo_root):
        return resolved_repo_root
    return resolved_workspace_root


def _workspace_materialization_package_graph_cache_request_signature(
    *,
    request: SemanticPackageMaterializationRuntimeContextRequest,
    manifest_paths: tuple[Path, ...],
    package_cache_owner_roots_by_manifest_path: Mapping[Path, Path] | None = None,
) -> str | None:
    if not _has_explicit_semantic_ontology_package_catalog(request.context):
        return None
    entries_by_package_name, _package_names_by_module_id = (
        _ontology_package_manifest_catalog_for_request(request)
    )
    return _package_graph_cache_request_signature(
        repo_root=request.repo_root,
        catalog_entries=tuple(entries_by_package_name.values()),
        manifest_paths=manifest_paths,
        package_cache_owner_roots_by_manifest_path=(
            package_cache_owner_roots_by_manifest_path
        ),
        runtime_package_names=_runtime_context_ontology_package_names(request),
        required_projection_names=_clean_string_tuple(
            request.context.get("required_projection_names")
        ),
        target_manifest_paths=_target_materialization_manifest_paths(request),
        include_dependency_closure=(
            _runtime_context_include_package_dependency_closure(request)
        ),
    )


def _package_graph_cache_request_signature(
    *,
    repo_root: Path,
    catalog_entries: tuple[MetaRuntimePackageIndexEntry, ...],
    manifest_paths: tuple[Path, ...],
    runtime_package_names: tuple[str, ...],
    required_projection_names: tuple[str, ...],
    target_manifest_paths: tuple[Path, ...],
    include_dependency_closure: bool,
    package_cache_owner_roots_by_manifest_path: Mapping[Path, Path] | None = None,
) -> str:
    root = repo_root.expanduser().resolve()
    owner_roots_by_manifest_path = _path_mapping_by_resolved_manifest_path(
        package_cache_owner_roots_by_manifest_path
    )
    hasher = hashlib.sha256()
    hasher.update(b"aware-meta-runtime-context-package-graph-cache-request-v1\n")
    hasher.update(b"catalog\n")
    for entry in sorted(
        catalog_entries,
        key=lambda item: (
            item.module_id,
            item.package_name,
            item.manifest_path.as_posix(),
        ),
    ):
        owner_root = owner_roots_by_manifest_path.get(
            entry.manifest_path.expanduser().resolve()
        )
        parts = (
            entry.module_id,
            entry.package_name,
            entry.fqn_prefix,
            (
                _path_signature_key(root=root, path=owner_root)
                if owner_root is not None
                else ""
            ),
            _path_signature_key(root=root, path=entry.manifest_path),
            ",".join(entry.dependency_package_names),
            ",".join(entry.projection_names),
        )
        hasher.update("|".join(parts).encode("utf-8"))
        hasher.update(b"\n")
    for section_name, values in (
        ("manifest_paths", tuple(path.as_posix() for path in manifest_paths)),
        (
            "target_manifest_paths",
            tuple(path.as_posix() for path in target_manifest_paths),
        ),
        ("runtime_package_names", runtime_package_names),
        ("required_projection_names", required_projection_names),
        ("include_dependency_closure", (str(include_dependency_closure),)),
    ):
        hasher.update(section_name.encode("utf-8"))
        hasher.update(b"\n")
        for value in values:
            hasher.update(str(value).encode("utf-8"))
            hasher.update(b"\n")
    return hasher.hexdigest()


def _path_signature_key(*, root: Path, path: Path) -> str:
    resolved = path.expanduser().resolve()
    try:
        return resolved.relative_to(root).as_posix()
    except ValueError:
        return resolved.as_posix()


def build_meta_graph_runtime_index_snapshot(
    *,
    ocg: ObjectConfigGraph,
    composition_context_id: UUID | None = None,
) -> MetaGraphRuntimeIndexSnapshot:
    """Build the hot graph lookup maps required by Meta execution code."""

    class_configs_by_id: dict[UUID, ClassConfig] = {}
    attribute_configs_by_id: dict[UUID, AttributeConfig] = {}
    relationships_by_id: dict[UUID, ClassConfigRelationship] = {}

    for node in ocg.object_config_graph_nodes:
        if (
            node.type == ObjectConfigGraphNodeType.class_
            and node.class_config is not None
        ):
            _remember_class_config(
                class_config=node.class_config,
                class_configs_by_id=class_configs_by_id,
                attribute_configs_by_id=attribute_configs_by_id,
                relationships_by_id=relationships_by_id,
            )
        elif (
            node.type == ObjectConfigGraphNodeType.relationship
            and node.class_config_relationship is not None
        ):
            relationships_by_id.setdefault(
                node.class_config_relationship.id,
                node.class_config_relationship,
            )

    for graph_relationship in ocg.object_config_graph_relationships:
        for (
            relationship_class
        ) in graph_relationship.object_config_graph_relationship_classes:
            class_config = relationship_class.class_config
            if class_config is not None:
                _remember_class_config(
                    class_config=class_config,
                    class_configs_by_id=class_configs_by_id,
                    attribute_configs_by_id=attribute_configs_by_id,
                    relationships_by_id=relationships_by_id,
                )
        for relationship in graph_relationship.class_config_relationships:
            relationships_by_id.setdefault(relationship.id, relationship)

    opg_by_id = {opg.id: opg for opg in ocg.object_projection_graphs}
    opg_by_hash = {opg.projection_hash: opg for opg in ocg.object_projection_graphs}
    return MetaGraphRuntimeIndexSnapshot(
        ocg=ocg,
        class_configs_by_id=class_configs_by_id,
        attribute_configs_by_id=attribute_configs_by_id,
        relationships_by_id=relationships_by_id,
        opg_by_id=opg_by_id,
        opg_by_hash=opg_by_hash,
        portal_index=build_portal_index(ocg),
        composition_context_id=composition_context_id,
    )


def _build_meta_graph_runtime_index_snapshot_cached(
    *,
    ocg: ObjectConfigGraph,
    composition_context_id: UUID | None = None,
) -> tuple[MetaGraphRuntimeIndexSnapshot, str]:
    cache_key = _runtime_index_snapshot_cache_key(
        ocg=ocg,
        composition_context_id=composition_context_id,
    )
    with _RUNTIME_INDEX_SNAPSHOT_CACHE_LOCK:
        cached_index = _RUNTIME_INDEX_SNAPSHOT_CACHE.get(cache_key)
        if cached_index is not None:
            _RUNTIME_INDEX_SNAPSHOT_CACHE.move_to_end(cache_key)
            return cached_index, "hit"

    index = build_meta_graph_runtime_index_snapshot(
        ocg=ocg,
        composition_context_id=composition_context_id,
    )
    with _RUNTIME_INDEX_SNAPSHOT_CACHE_LOCK:
        _RUNTIME_INDEX_SNAPSHOT_CACHE[cache_key] = index
        _RUNTIME_INDEX_SNAPSHOT_CACHE.move_to_end(cache_key)
        while len(_RUNTIME_INDEX_SNAPSHOT_CACHE) > (
            _RUNTIME_INDEX_SNAPSHOT_CACHE_MAX_ENTRIES
        ):
            _RUNTIME_INDEX_SNAPSHOT_CACHE.popitem(last=False)
    return index, "miss"


def _runtime_index_snapshot_cache_key(
    *,
    ocg: ObjectConfigGraph,
    composition_context_id: UUID | None,
) -> _RuntimeIndexSnapshotCacheKey:
    return (
        str(composition_context_id) if composition_context_id is not None else "",
        (_runtime_graph_cache_signature(ocg),),
    )


def _runtime_graph_cache_signature(ocg: ObjectConfigGraph) -> tuple[str, ...]:
    projection_hashes = tuple(
        sorted(
            projection.projection_hash
            for projection in ocg.object_projection_graphs
            if projection.projection_hash
        )
    )
    return (
        str(ocg.id) if ocg.id is not None else "",
        str(ocg.hash or ""),
        str(ocg.fqn_prefix or ""),
        str(getattr(ocg.language, "value", ocg.language) or ""),
        str(len(ocg.object_config_graph_nodes)),
        str(len(ocg.object_config_graph_relationships)),
        str(len(ocg.object_projection_graphs)),
        "|".join(projection_hashes),
    )


def _clear_meta_graph_runtime_index_snapshot_cache() -> None:
    with _RUNTIME_INDEX_SNAPSHOT_CACHE_LOCK:
        _RUNTIME_INDEX_SNAPSHOT_CACHE.clear()


def find_meta_graph_projection_hash_by_name(
    *,
    index: MetaGraphRuntimeIndex,
    projection_name: str,
) -> str:
    """Resolve an authored projection name exactly from a Meta graph index."""

    target = projection_name.strip()
    if not target:
        raise ValueError("Projection name is required.")
    projection_hash = _projection_hash_by_name(index.ocg).get(target)
    if projection_hash is None:
        raise ValueError(
            f"Projection {projection_name!r} was not found in Meta graph index."
        )
    return projection_hash


def _derive_runtime_graphs(
    source_graphs: tuple[ObjectConfigGraph, ...],
    *,
    external_runtime_graphs: tuple[ObjectConfigGraph, ...] = (),
) -> tuple[ObjectConfigGraph, ...]:
    if not source_graphs:
        return ()
    return derive_runtime_object_config_graphs(
        source_graphs,
        external_runtime_graphs=external_runtime_graphs,
        include_projection_graphs=True,
    )


def _object_config_graphs_from_context_value(
    value: object,
) -> tuple[ObjectConfigGraph, ...]:
    if isinstance(value, ObjectConfigGraph):
        return (value,)
    if not isinstance(value, Iterable):
        return ()
    return tuple(item for item in value if isinstance(item, ObjectConfigGraph))


def _prepend_unique_object_config_graph(
    *,
    graph: ObjectConfigGraph,
    graphs: tuple[ObjectConfigGraph, ...],
) -> tuple[ObjectConfigGraph, ...]:
    if any(candidate.id == graph.id for candidate in graphs):
        return graphs
    return (graph, *graphs)


def _ensure_runtime_projection_graphs(
    runtime_graphs: tuple[ObjectConfigGraph, ...],
) -> tuple[ObjectConfigGraph, ...]:
    graph_ids_requiring_opgs = {
        graph.id
        for graph in runtime_graphs
        if graph.object_projection_graph_declarations
        and not graph.object_projection_graphs
    }
    if not graph_ids_requiring_opgs:
        return runtime_graphs

    graphs = [graph.model_copy(deep=True) for graph in runtime_graphs]
    for graph in graphs:
        if graph.id not in graph_ids_requiring_opgs:
            continue
        graph.object_projection_graphs = build_object_projection_graphs(
            graph,
            external_graphs=[
                external_graph
                for external_graph in graphs
                if external_graph.id != graph.id
            ],
            provision_portals=False,
        )
    for graph in graphs:
        if graph.id not in graph_ids_requiring_opgs:
            continue
        graph.object_projection_graphs = build_object_projection_graphs(
            graph,
            external_graphs=[
                external_graph
                for external_graph in graphs
                if external_graph.id != graph.id
            ],
        )
    return tuple(graphs)


def _context_graph(
    *,
    runtime_graphs: tuple[ObjectConfigGraph, ...],
    composite_name: str,
) -> ObjectConfigGraph:
    if len(runtime_graphs) == 1:
        return runtime_graphs[0]
    composite_hash = _runtime_graphs_hash(runtime_graphs)
    composite_id = uuid5(
        NAMESPACE_URL,
        "aware://meta/runtime/graph-context/composite/" + composite_hash,
    )
    return _shallow_runtime_context_graph(
        runtime_graphs=runtime_graphs,
        composite_id=composite_id,
        composite_name=composite_name,
        composite_hash=composite_hash,
    )


def _shallow_runtime_context_graph(
    *,
    runtime_graphs: tuple[ObjectConfigGraph, ...],
    composite_id: UUID,
    composite_name: str,
    composite_hash: str,
) -> ObjectConfigGraph:
    """Aggregate runtime graph payloads for read-only context indexing.

    Workspace semantic materialization needs lookup/index truth, not a new canonical
    OCG. Keep source graph object ids intact and avoid the expensive deep-copy/rebind
    path used by durable OCG composition.
    """

    first_graph = runtime_graphs[0]
    object_config_graph_identity_id = stable_object_config_graph_identity_id(
        key="aware.runtime_context",
    )
    return ObjectConfigGraph(
        id=composite_id,
        name=composite_name,
        hash=composite_hash,
        fqn_prefix="aware.runtime_context",
        language=first_graph.language,
        object_config_graph_identity_id=object_config_graph_identity_id,
        object_config_graph_identity=ObjectConfigGraphIdentity(
            id=object_config_graph_identity_id,
            key="aware.runtime_context",
            label="ocg:aware.runtime_context",
        ),
        object_config_graph_annotations=_flatten_graph_sequence(
            graph.object_config_graph_annotations for graph in runtime_graphs
        ),
        object_config_graph_mirrors=_flatten_graph_sequence(
            graph.object_config_graph_mirrors for graph in runtime_graphs
        ),
        object_config_graph_nodes=_flatten_graph_sequence(
            graph.object_config_graph_nodes for graph in runtime_graphs
        ),
        object_config_graph_overlays=_flatten_graph_sequence(
            graph.object_config_graph_overlays for graph in runtime_graphs
        ),
        object_config_graph_bindings=_flatten_graph_sequence(
            graph.object_config_graph_bindings for graph in runtime_graphs
        ),
        object_config_graph_relationships=_flatten_graph_sequence(
            graph.object_config_graph_relationships for graph in runtime_graphs
        ),
        object_projection_graph_declarations=_flatten_graph_sequence(
            graph.object_projection_graph_declarations for graph in runtime_graphs
        ),
        object_projection_graphs=_flatten_unique_graph_sequence_by_id(
            graph.object_projection_graphs for graph in runtime_graphs
        ),
    )


def _flatten_graph_sequence(values: Iterable[Iterable[_T]]) -> list[_T]:
    return [item for sequence in values for item in sequence]


def _flatten_unique_graph_sequence_by_id(values: Iterable[Iterable[_T]]) -> list[_T]:
    flattened: list[_T] = []
    seen_ids: set[object] = set()
    for sequence in values:
        for item in sequence:
            item_id = getattr(item, "id", None)
            if item_id is not None:
                if item_id in seen_ids:
                    continue
                seen_ids.add(item_id)
            flattened.append(item)
    return flattened


def _runtime_graphs_hash(runtime_graphs: tuple[ObjectConfigGraph, ...]) -> str:
    parts = sorted(
        (graph.hash or "").strip() or str(graph.id) for graph in runtime_graphs
    )
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def _workspace_materialization_package_manifest_paths(
    request: SemanticPackageMaterializationRuntimeContextRequest,
) -> tuple[Path, ...]:
    target_manifest_paths = _target_materialization_manifest_paths(request)
    target_meta_manifest_paths = _meta_runtime_context_target_manifest_paths(
        target_manifest_paths
    )
    isolate_target_manifests = _runtime_context_isolates_target_manifests(request)
    runtime_package_names = _runtime_context_ontology_package_names(request)
    required_projection_names = _clean_string_tuple(
        request.context.get("required_projection_names")
    )
    if (
        not runtime_package_names
        and not required_projection_names
        and not target_meta_manifest_paths
    ):
        return target_meta_manifest_paths
    if isolate_target_manifests:
        target_manifest_paths = ()
        target_meta_manifest_paths = ()

    entries_by_package_name, _package_names_by_module_id = (
        _ontology_package_manifest_catalog_for_request(request)
    )
    target_package_names = _package_names_for_manifest_paths(
        entries_by_package_name=entries_by_package_name,
        manifest_paths=target_manifest_paths,
    )
    required_projection_package_names = _required_projection_package_names(
        repo_root=request.repo_root,
        aware_root=request.repo_root,
        entries_by_package_name=entries_by_package_name,
        required_projection_names=required_projection_names,
    )
    if not _runtime_context_include_package_dependency_closure(request):
        required_projection_paths = _topological_package_manifest_closure(
            entries_by_package_name=entries_by_package_name,
            seed_package_names=required_projection_package_names,
        )
        provider_seed_paths = _topological_package_manifest_subset(
            entries_by_package_name=entries_by_package_name,
            seed_package_names=runtime_package_names,
        )
        target_dependency_paths = _topological_package_manifest_closure(
            entries_by_package_name=entries_by_package_name,
            seed_package_names=target_package_names,
        )
        return _dedupe_package_manifest_paths(
            (
                *required_projection_paths,
                *provider_seed_paths,
                *target_dependency_paths,
                *target_meta_manifest_paths,
            )
        )
    seed_package_names = tuple(
        dict.fromkeys(
            (
                *runtime_package_names,
                *target_package_names,
                *required_projection_package_names,
            )
        )
    )
    if not seed_package_names:
        return target_meta_manifest_paths
    context_manifest_paths = _topological_package_manifest_closure(
        entries_by_package_name=entries_by_package_name,
        seed_package_names=seed_package_names,
    )
    return _dedupe_package_manifest_paths(
        (*context_manifest_paths, *target_meta_manifest_paths)
    )


def _meta_runtime_context_target_manifest_paths(
    manifest_paths: tuple[Path, ...],
) -> tuple[Path, ...]:
    """Keep Meta runtime graph context scoped to Meta-owned package manifests."""

    return tuple(path for path in manifest_paths if path.name == "aware.toml")


def _package_names_for_manifest_paths(
    *,
    entries_by_package_name: Mapping[str, MetaRuntimePackageIndexEntry],
    manifest_paths: tuple[Path, ...],
) -> tuple[str, ...]:
    if not manifest_paths:
        return ()
    target_paths = {path.expanduser().resolve() for path in manifest_paths}
    package_names: list[str] = []
    for entry in entries_by_package_name.values():
        if entry.manifest_path.expanduser().resolve() not in target_paths:
            continue
        package_names.append(entry.package_name)
    return tuple(dict.fromkeys(package_names))


def resolve_workspace_required_projection_package_manifest_paths(
    request: SemanticPackageMaterializationRuntimeContextRequest,
) -> tuple[Path, ...]:
    """Resolve package manifests needed to satisfy Workspace-required projections."""

    required_projection_names = _clean_string_tuple(
        request.context.get("required_projection_names")
    )
    if not required_projection_names:
        return ()
    entries_by_package_name, _package_names_by_module_id = (
        _ontology_package_manifest_catalog_for_request(request)
    )
    required_projection_package_names = _required_projection_package_names(
        repo_root=request.repo_root,
        aware_root=request.repo_root,
        entries_by_package_name=entries_by_package_name,
        required_projection_names=required_projection_names,
    )
    if not required_projection_package_names:
        return ()
    return _topological_package_manifest_closure(
        entries_by_package_name=entries_by_package_name,
        seed_package_names=required_projection_package_names,
    )


def build_meta_graph_runtime_context_for_workspace_required_projections(
    *,
    repo_root: Path,
    required_projection_names: Iterable[str],
    required_package_names: Iterable[str] = (),
    aware_root: Path | None = None,
    composition_context_id: UUID | None = None,
    semantic_ontology_package_catalog: Mapping[str, object] | None = None,
    composite_name: str = "Aware Required Projection Runtime Context",
) -> MetaGraphRuntimeContext:
    """Build a Meta-owned runtime context for required projections/packages."""

    projection_names = _clean_string_tuple(required_projection_names)
    package_names = _clean_string_tuple(required_package_names)
    if not projection_names and not package_names:
        raise ValueError(
            "At least one required projection or package name is required."
        )
    resolved_repo_root = repo_root.expanduser().resolve()
    resolved_aware_root = (
        aware_root.expanduser().resolve()
        if aware_root is not None
        else resolved_repo_root
    )
    if semantic_ontology_package_catalog is None:
        entries_by_package_name, _package_names_by_module_id = (
            _ontology_package_manifest_catalog(repo_root=resolved_repo_root)
        )
    else:
        explicit_catalog = _ontology_package_manifest_catalog_from_context(
            context={
                SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_CONTEXT_KEY: (
                    semantic_ontology_package_catalog
                )
            },
            repo_root=resolved_repo_root,
        )
        if explicit_catalog is None:
            raise ValueError("Meta runtime ontology package catalog was not resolved.")
        entries_by_package_name, _package_names_by_module_id = explicit_catalog
    required_projection_package_names = (
        _required_projection_package_names(
            repo_root=resolved_repo_root,
            aware_root=resolved_aware_root,
            entries_by_package_name=entries_by_package_name,
            required_projection_names=projection_names,
        )
        if projection_names
        else ()
    )
    missing_package_names = tuple(
        package_name
        for package_name in package_names
        if package_name not in entries_by_package_name
    )
    if missing_package_names:
        raise ValueError(
            "Required Meta runtime packages were not found in the ontology "
            "package catalog: " + ", ".join(missing_package_names)
        )
    seed_package_names = tuple(
        dict.fromkeys((*required_projection_package_names, *package_names))
    )
    if not seed_package_names:
        raise ValueError(
            "Required Meta runtime projections resolved no owning packages: "
            + ", ".join(projection_names)
        )
    package_manifest_paths = _topological_package_manifest_closure(
        entries_by_package_name=entries_by_package_name,
        seed_package_names=seed_package_names,
    )
    return build_meta_graph_runtime_context_for_aware_package_manifests(
        package_manifest_paths=package_manifest_paths,
        workspace_root=resolved_aware_root,
        composition_context_id=composition_context_id,
        composite_name=composite_name,
        package_entries_by_manifest_path={
            entry.manifest_path: entry for entry in entries_by_package_name.values()
        },
    )


def resolve_meta_runtime_package_manifest_closure_for_workspace_read_model(
    *,
    repo_root: Path,
    required_projection_names: Iterable[str],
    required_package_names: Iterable[str] = (),
    aware_root: Path | None = None,
    semantic_ontology_package_catalog: Mapping[str, object] | None = None,
) -> tuple[Path, ...]:
    """Resolve package manifests needed by a Workspace read-model request."""

    projection_names = _clean_string_tuple(required_projection_names)
    package_names = _clean_string_tuple(required_package_names)
    if not projection_names and not package_names:
        return ()
    resolved_repo_root = repo_root.expanduser().resolve()
    resolved_aware_root = (
        aware_root.expanduser().resolve()
        if aware_root is not None
        else resolved_repo_root
    )
    if semantic_ontology_package_catalog is None:
        entries_by_package_name, _package_names_by_module_id = (
            _ontology_package_manifest_catalog(repo_root=resolved_repo_root)
        )
    else:
        explicit_catalog = _ontology_package_manifest_catalog_from_context(
            context={
                SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_CONTEXT_KEY: (
                    semantic_ontology_package_catalog
                )
            },
            repo_root=resolved_repo_root,
        )
        if explicit_catalog is None:
            raise ValueError("Meta runtime ontology package catalog was not resolved.")
        entries_by_package_name, _package_names_by_module_id = explicit_catalog
    required_projection_package_names = (
        _required_projection_package_names(
            repo_root=resolved_repo_root,
            aware_root=resolved_aware_root,
            entries_by_package_name=entries_by_package_name,
            required_projection_names=projection_names,
        )
        if projection_names
        else ()
    )
    missing_package_names = tuple(
        package_name
        for package_name in package_names
        if package_name not in entries_by_package_name
    )
    if missing_package_names:
        raise ValueError(
            "Required Meta runtime packages were not found in the ontology "
            "package catalog: " + ", ".join(missing_package_names)
        )
    seed_package_names = tuple(
        dict.fromkeys((*required_projection_package_names, *package_names))
    )
    if not seed_package_names:
        return ()
    return _topological_package_manifest_closure(
        entries_by_package_name=entries_by_package_name,
        seed_package_names=seed_package_names,
    )


def resolve_meta_runtime_package_manifest_closure_for_package_names(
    *,
    repo_root: Path,
    package_names: Iterable[str],
    semantic_ontology_package_catalog: Mapping[str, object] | None = None,
) -> tuple[Path, ...]:
    """Resolve dependency-ordered aware.toml paths for ontology packages."""

    seed_package_names = _clean_string_tuple(package_names)
    if not seed_package_names:
        return ()
    resolved_repo_root = repo_root.expanduser().resolve()
    if semantic_ontology_package_catalog is None:
        entries_by_package_name, _package_names_by_module_id = (
            _ontology_package_manifest_catalog(repo_root=resolved_repo_root)
        )
    else:
        explicit_catalog = _ontology_package_manifest_catalog_from_context(
            context={
                SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_CONTEXT_KEY: (
                    semantic_ontology_package_catalog
                )
            },
            repo_root=resolved_repo_root,
        )
        if explicit_catalog is None:
            raise ValueError("Meta runtime ontology package catalog was not resolved.")
        entries_by_package_name, _package_names_by_module_id = explicit_catalog
    return _topological_package_manifest_closure(
        entries_by_package_name=entries_by_package_name,
        seed_package_names=seed_package_names,
    )


def _required_projection_package_names(
    *,
    repo_root: Path,
    aware_root: Path,
    entries_by_package_name: Mapping[str, MetaRuntimePackageIndexEntry],
    required_projection_names: tuple[str, ...],
) -> tuple[str, ...]:
    if not required_projection_names:
        return ()
    catalog_package_names = _required_projection_package_names_from_catalog_entries(
        entries_by_package_name=entries_by_package_name,
        required_projection_names=required_projection_names,
    )
    if catalog_package_names is not None:
        return catalog_package_names
    package_projection_index = build_meta_runtime_package_projection_index(
        repo_root=repo_root,
        aware_root=aware_root,
        package_entries=tuple(entries_by_package_name.values()),
        required_projection_names=required_projection_names,
    )
    missing_projection_names = package_projection_index.missing_projection_names(
        required_projection_names
    )
    if missing_projection_names:
        raise ValueError(
            "Required Meta runtime projections were not found in the package "
            "projection index: " + ", ".join(missing_projection_names)
        )
    return package_projection_index.package_names_for_projection_names(
        required_projection_names
    )


def _required_projection_package_names_from_catalog_entries(
    *,
    entries_by_package_name: Mapping[str, MetaRuntimePackageIndexEntry],
    required_projection_names: tuple[str, ...],
) -> tuple[str, ...] | None:
    package_name_by_projection_name: dict[str, str] = {}
    ambiguous_projection_names: set[str] = set()
    for entry in entries_by_package_name.values():
        for projection_name in entry.projection_names:
            existing_package_name = package_name_by_projection_name.get(projection_name)
            if (
                existing_package_name is not None
                and existing_package_name != entry.package_name
            ):
                ambiguous_projection_names.add(projection_name)
                continue
            package_name_by_projection_name[projection_name] = entry.package_name
    package_names: list[str] = []
    seen_package_names: set[str] = set()
    for projection_name in required_projection_names:
        if projection_name in ambiguous_projection_names:
            return None
        package_name = package_name_by_projection_name.get(projection_name)
        if package_name is None:
            return None
        if package_name in seen_package_names:
            continue
        seen_package_names.add(package_name)
        package_names.append(package_name)
    return tuple(package_names)


def _ontology_package_manifest_catalog(
    *,
    repo_root: Path,
) -> tuple[dict[str, MetaRuntimePackageIndexEntry], dict[str, str]]:
    from aware_grammar.module.loader import load_aware_module_spec  # noqa: WPS433

    resolved_repo_root = repo_root.expanduser().resolve()
    entries_by_package_name: dict[str, MetaRuntimePackageIndexEntry] = {}
    package_names_by_module_id: dict[str, str] = {}
    module_roots = _ontology_catalog_module_roots(repo_root=resolved_repo_root)
    if not module_roots:
        return entries_by_package_name, package_names_by_module_id

    for module_root in module_roots:
        module_toml = module_root / "aware.module.toml"
        if not module_toml.is_file():
            continue
        module_spec = load_aware_module_spec(toml_path=module_toml)
        module_id = _ontology_catalog_module_id(
            repo_root=resolved_repo_root,
            module_root=module_root,
        )
        for package in module_spec.packages:
            package_kind = str(getattr(package.kind, "value", package.kind)).strip()
            if package_kind != "ontology":
                continue
            manifest_path = (module_root / package.manifest).resolve()
            (
                source_manifest_path,
                package_name,
                fqn_prefix,
                dependency_package_names,
            ) = _module_ontology_catalog_manifest_entry(manifest_path=manifest_path)
            if not package_name:
                continue
            entries_by_package_name[package_name] = MetaRuntimePackageIndexEntry(
                module_id=module_id,
                package_name=package_name,
                fqn_prefix=fqn_prefix,
                manifest_path=source_manifest_path,
                dependency_package_names=dependency_package_names,
                runtime_handler_provider_import_root=(
                    _module_runtime_handler_provider_import_root(module_spec)
                ),
            )
            package_names_by_module_id.setdefault(module_id, package_name)
    return entries_by_package_name, package_names_by_module_id


def _ontology_catalog_module_roots(*, repo_root: Path) -> tuple[Path, ...]:
    roots: list[Path] = []
    seen: set[Path] = set()
    for modules_root in (
        repo_root / "modules",
        *(repo_root / "workspaces").glob("*/modules"),
    ):
        if not modules_root.is_dir():
            continue
        for module_root in sorted(
            path for path in modules_root.iterdir() if path.is_dir()
        ):
            resolved = module_root.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            roots.append(resolved)
    return tuple(roots)


def _ontology_catalog_module_id(*, repo_root: Path, module_root: Path) -> str:
    resolved_module_root = module_root.resolve()
    try:
        relative = resolved_module_root.relative_to(repo_root.resolve())
        parts = relative.parts
    except ValueError:
        parts = resolved_module_root.parts
        for index, part in enumerate(parts):
            if part != "workspaces":
                continue
            if index + 3 < len(parts) and parts[index + 2] == "modules":
                return f"{parts[index + 1]}:{parts[index + 3]}"
        return module_root.name
    if len(parts) >= 4 and parts[0] == "workspaces" and parts[2] == "modules":
        return f"{parts[1]}:{parts[3]}"
    return module_root.name


def _module_ontology_catalog_manifest_entry(
    *,
    manifest_path: Path,
) -> tuple[Path, str, str, tuple[str, ...]]:
    from aware_meta.manifest.loader import load_aware_toml_spec  # noqa: WPS433

    if manifest_path.name != "aware.ontology.toml":
        aware_spec = load_aware_toml_spec(toml_path=manifest_path)
        return (
            manifest_path,
            str(aware_spec.package.package_name).strip(),
            str(aware_spec.package.fqn_prefix).strip(),
            _aware_toml_dependency_package_names(aware_spec),
        )

    from aware_ontology.manifest.loader import (  # noqa: WPS433
        load_aware_ontology_toml_spec,
    )

    ontology_spec = load_aware_ontology_toml_spec(toml_path=manifest_path)
    source_manifest_path = _meta_source_manifest_path_for_materialization_target(
        manifest_path=manifest_path,
    )
    aware_spec = load_aware_toml_spec(toml_path=source_manifest_path)
    package_name = str(ontology_spec.ontology.package_name).strip()
    fqn_prefix = str(ontology_spec.ontology.fqn_prefix).strip()
    if str(aware_spec.package.package_name).strip() != package_name:
        raise RuntimeError(
            "aware.ontology.toml package_name does not match source aware.toml "
            "for Meta runtime package catalog: "
            f"ontology={package_name!r} "
            f"source={aware_spec.package.package_name!r}"
        )
    if str(aware_spec.package.fqn_prefix).strip() != fqn_prefix:
        raise RuntimeError(
            "aware.ontology.toml fqn_prefix does not match source aware.toml "
            "for Meta runtime package catalog: "
            f"ontology={fqn_prefix!r} source={aware_spec.package.fqn_prefix!r}"
        )
    return (
        source_manifest_path,
        package_name,
        fqn_prefix,
        tuple(
            dict.fromkeys(
                (
                    *_aware_ontology_dependency_package_names(ontology_spec),
                    *_aware_toml_dependency_package_names(aware_spec),
                )
            )
        ),
    )


def _aware_toml_dependency_package_names(
    aware_spec: AwareTomlSpec,
) -> tuple[str, ...]:
    return tuple(
        str(dependency.package_name).strip()
        for dependency in aware_spec.dependencies
        if str(dependency.package_name).strip()
    )


def _aware_ontology_dependency_package_names(
    ontology_spec: object,
) -> tuple[str, ...]:
    return tuple(
        package_name
        for dependency in getattr(ontology_spec, "dependencies", ())
        for package_name in (str(dependency.package_name).strip(),)
        if package_name
    )


def _ontology_package_manifest_catalog_for_request(
    request: SemanticPackageMaterializationRuntimeContextRequest,
) -> tuple[dict[str, MetaRuntimePackageIndexEntry], dict[str, str]]:
    explicit = _ontology_package_manifest_catalog_from_context(
        context=request.context,
        repo_root=request.repo_root,
    )
    if explicit is not None:
        return explicit
    return _ontology_package_manifest_catalog(repo_root=request.repo_root)


def _ontology_package_manifest_catalog_from_context(
    *,
    context: Mapping[str, object],
    repo_root: Path,
) -> tuple[dict[str, MetaRuntimePackageIndexEntry], dict[str, str]] | None:
    raw_catalog = context.get(SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_CONTEXT_KEY)
    if raw_catalog is None:
        return None
    if not isinstance(raw_catalog, Mapping):
        raise ValueError("Meta runtime ontology package catalog must be a mapping.")
    if raw_catalog.get("schema") != SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_SCHEMA:
        raise ValueError(
            "Meta runtime ontology package catalog has an unsupported schema."
        )
    raw_entries = raw_catalog.get("entries")
    if not isinstance(raw_entries, list):
        raise ValueError(
            "Meta runtime ontology package catalog must include an entries list."
        )
    entries_by_package_name: dict[str, MetaRuntimePackageIndexEntry] = {}
    package_names_by_module_id: dict[str, str] = {}
    for raw_entry in raw_entries:
        if not isinstance(raw_entry, Mapping):
            raise ValueError(
                "Meta runtime ontology package catalog entries must be mappings."
            )
        entry = _ontology_package_manifest_catalog_entry_from_payload(
            payload=raw_entry,
            repo_root=repo_root,
        )
        entries_by_package_name[entry.package_name] = entry
        package_names_by_module_id.setdefault(entry.module_id, entry.package_name)
    return entries_by_package_name, package_names_by_module_id


def _ontology_package_manifest_catalog_entry_from_payload(
    *,
    payload: Mapping[str, object],
    repo_root: Path,
) -> MetaRuntimePackageIndexEntry:
    module_id = _required_string_payload(payload, "module_id")
    package_name = _required_string_payload(payload, "package_name")
    fqn_prefix = _required_string_payload(payload, "fqn_prefix")
    manifest_path_text = _required_string_payload(payload, "manifest_path")
    manifest_path = Path(manifest_path_text).expanduser()
    if not manifest_path.is_absolute():
        manifest_path = repo_root / manifest_path
    return MetaRuntimePackageIndexEntry(
        module_id=module_id,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        manifest_path=manifest_path.resolve(),
        dependency_package_names=_clean_string_tuple(
            payload.get("dependency_package_names")
        ),
        projection_names=_clean_string_tuple(payload.get("projection_names")),
        runtime_handler_provider_import_root=_clean_string_value(
            payload.get("runtime_handler_provider_import_root")
        ),
    )


def _required_string_payload(payload: Mapping[str, object], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f"Meta runtime ontology package catalog entry missing {key!r}."
        )
    return value.strip()


def _topological_package_manifest_closure(
    *,
    entries_by_package_name: Mapping[str, MetaRuntimePackageIndexEntry],
    seed_package_names: tuple[str, ...],
) -> tuple[Path, ...]:
    ordered_paths: list[Path] = []
    visited: set[str] = set()
    visiting: set[str] = set()

    def visit(package_name: str) -> None:
        if package_name in visited:
            return
        if package_name in visiting:
            raise ValueError(
                "Cyclic ObjectConfigGraph package dependency: "
                + " -> ".join((*sorted(visiting), package_name))
            )
        entry = entries_by_package_name.get(package_name)
        if entry is None:
            raise ValueError(
                "Missing ObjectConfigGraph package dependency for Meta runtime "
                f"context: {package_name!r}"
            )
        visiting.add(package_name)
        for dependency_package_name in entry.dependency_package_names:
            visit(dependency_package_name)
        visiting.remove(package_name)
        visited.add(package_name)
        ordered_paths.append(entry.manifest_path)

    for seed_package_name in seed_package_names:
        visit(seed_package_name)
    return tuple(ordered_paths)


def _topological_package_manifest_subset(
    *,
    entries_by_package_name: Mapping[str, MetaRuntimePackageIndexEntry],
    seed_package_names: tuple[str, ...],
) -> tuple[Path, ...]:
    selected_package_names = frozenset(seed_package_names)
    ordered_paths: list[Path] = []
    visited: set[str] = set()
    visiting: set[str] = set()

    def visit(package_name: str) -> None:
        if package_name in visited:
            return
        if package_name in visiting:
            raise ValueError(
                "Cyclic ObjectConfigGraph package dependency: "
                + " -> ".join((*sorted(visiting), package_name))
            )
        entry = entries_by_package_name.get(package_name)
        if entry is None:
            raise ValueError(
                "Missing ObjectConfigGraph package dependency for Meta runtime "
                f"context: {package_name!r}"
            )
        visiting.add(package_name)
        for dependency_package_name in entry.dependency_package_names:
            if dependency_package_name in selected_package_names:
                visit(dependency_package_name)
        visiting.remove(package_name)
        visited.add(package_name)
        ordered_paths.append(entry.manifest_path)

    for seed_package_name in seed_package_names:
        visit(seed_package_name)
    return tuple(ordered_paths)


def _runtime_context_ontology_package_names(
    request: SemanticPackageMaterializationRuntimeContextRequest,
) -> tuple[str, ...]:
    context_package_names = _clean_string_tuple(
        request.context.get("runtime_ontology_package_names")
    )
    provider_package_names = _clean_string_tuple(
        request.provider_payload.get("runtime_ontology_package_names")
    )
    return tuple(dict.fromkeys((*context_package_names, *provider_package_names)))


def _runtime_context_handler_owner_prefixes(
    request: SemanticPackageMaterializationRuntimeContextRequest,
) -> tuple[str, ...] | None:
    prefixes = _clean_string_tuple(
        request.context.get("runtime_handler_owner_prefixes")
    )
    return prefixes or None


def _target_materialization_manifest_paths(
    request: SemanticPackageMaterializationRuntimeContextRequest,
) -> tuple[Path, ...]:
    manifest_paths: list[Path] = []
    if request.manifest_path is not None:
        manifest_paths.append(request.manifest_path)
    for manifest_path_text in _clean_string_tuple(
        request.context.get(SEMANTIC_MATERIALIZATION_TARGET_MANIFEST_PATHS_CONTEXT_KEY)
    ):
        manifest_paths.append(Path(manifest_path_text))
    resolved_paths: list[Path] = []
    seen: set[Path] = set()
    for manifest_path in manifest_paths:
        resolved_manifest_path = manifest_path.expanduser()
        if not resolved_manifest_path.is_absolute():
            resolved_manifest_path = request.workspace_root / resolved_manifest_path
        source_manifest_path = _meta_source_manifest_path_for_materialization_target(
            manifest_path=resolved_manifest_path.resolve(),
        )
        if source_manifest_path in seen:
            continue
        seen.add(source_manifest_path)
        resolved_paths.append(source_manifest_path)
    return tuple(resolved_paths)


def _provider_support_materialization_manifest_paths(
    request: SemanticPackageMaterializationRuntimeContextRequest,
) -> tuple[Path, ...]:
    catalog = request.context.get(SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_CONTEXT_KEY)
    if not isinstance(catalog, Mapping):
        return ()
    raw_entries = catalog.get("entries")
    if not isinstance(raw_entries, list):
        return ()
    manifest_paths: list[Path] = []
    seen: set[Path] = set()
    for raw_entry in raw_entries:
        if not isinstance(raw_entry, Mapping):
            continue
        if raw_entry.get("catalog_provenance") != "provider_support":
            continue
        manifest_path = _optional_catalog_path(
            value=raw_entry.get("manifest_path"),
            default_root=request.repo_root,
        )
        if manifest_path is None:
            continue
        source_manifest_path = _meta_source_manifest_path_for_materialization_target(
            manifest_path=manifest_path,
        )
        if source_manifest_path in seen:
            continue
        seen.add(source_manifest_path)
        manifest_paths.append(source_manifest_path)
    return tuple(manifest_paths)


def _workspace_materialization_source_analysis_allowed_manifest_paths(
    *,
    request: SemanticPackageMaterializationRuntimeContextRequest,
    manifest_paths: tuple[Path, ...],
) -> tuple[Path, ...]:
    """Allow selected Workspace runtime-context packages to refresh stale caches.

    Strict Workspace materialization still requires an explicit semantic package
    catalog. This allowlist only controls whether an explicitly selected package
    may rebuild its Meta graph from local source when the durable graph cache is
    stale or missing.
    """

    return _dedupe_package_manifest_paths(
        (
            *manifest_paths,
            *_provider_support_materialization_manifest_paths(request),
        )
    )


def _runtime_context_isolates_target_manifests(
    request: SemanticPackageMaterializationRuntimeContextRequest,
) -> bool:
    provider_payload = getattr(request, "provider_payload", None)
    context = getattr(request, "context", {})
    policy = None
    if isinstance(provider_payload, Mapping):
        policy = provider_payload.get(
            SEMANTIC_MATERIALIZATION_RUNTIME_TARGET_MANIFEST_POLICY_KEY
        )
    if policy is None and isinstance(context, Mapping):
        policy = context.get(
            SEMANTIC_MATERIALIZATION_RUNTIME_TARGET_MANIFEST_POLICY_KEY
        )
    return isinstance(policy, str) and policy.strip() == (
        SEMANTIC_MATERIALIZATION_RUNTIME_TARGET_MANIFEST_POLICY_ISOLATE_TARGET_MANIFESTS
    )


def _meta_source_manifest_path_for_materialization_target(
    *,
    manifest_path: Path,
) -> Path:
    if manifest_path.name != "aware.ontology.toml":
        return manifest_path

    from aware_ontology.manifest.loader import (  # noqa: WPS433
        load_aware_ontology_toml_spec,
    )

    ontology_spec = load_aware_ontology_toml_spec(toml_path=manifest_path)
    source_manifest_path = (
        manifest_path.parent / ontology_spec.ontology.source_manifest
    ).resolve()
    if not source_manifest_path.is_file():
        raise FileNotFoundError(
            "aware.ontology.toml source_manifest was not found for Meta "
            "runtime context resolution: "
            f"{ontology_spec.ontology.source_manifest!r}"
        )
    return source_manifest_path


def _runtime_context_include_package_dependency_closure(
    request: SemanticPackageMaterializationRuntimeContextRequest,
) -> bool:
    context_value = request.context.get("runtime_include_package_dependency_closure")
    if isinstance(context_value, bool):
        return context_value
    provider_value = request.provider_payload.get(
        "runtime_include_package_dependency_closure"
    )
    if isinstance(provider_value, bool):
        return provider_value
    return True


def _clean_string_tuple(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value.strip(),) if value.strip() else ()
    if not isinstance(value, Iterable):
        return ()
    return tuple(
        dict.fromkeys(
            item for raw_item in value for item in (str(raw_item).strip(),) if item
        )
    )


def _clean_string_value(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _module_runtime_handler_provider_import_root(module_spec: object) -> str | None:
    runtime_spec = getattr(module_spec, "runtime", None)
    if runtime_spec is None:
        return None
    return _clean_string_value(getattr(runtime_spec, "import_root", None))


def _dedupe_package_manifest_paths(
    package_manifest_paths: Iterable[Path],
) -> tuple[Path, ...]:
    paths: list[Path] = []
    seen: set[Path] = set()
    for raw_path in package_manifest_paths:
        path = Path(raw_path).expanduser().resolve()
        if path in seen:
            continue
        seen.add(path)
        paths.append(path)
    return tuple(paths)


def _topologically_order_package_manifest_paths(
    package_manifest_paths: Iterable[Path],
    *,
    package_entries_by_manifest_path: Mapping[Path, MetaRuntimePackageIndexEntry],
) -> tuple[Path, ...]:
    from aware_meta.manifest.loader import load_aware_toml_spec  # noqa: WPS433

    manifest_paths = _dedupe_package_manifest_paths(package_manifest_paths)
    package_name_by_path: dict[Path, str] = {}
    dependency_names_by_path: dict[Path, tuple[str, ...]] = {}
    path_by_package_name: dict[str, Path] = {}
    for manifest_path in manifest_paths:
        catalog_entry = _catalog_entry_for_manifest_path(
            entries_by_manifest_path=package_entries_by_manifest_path,
            manifest_path=manifest_path,
        )
        spec = load_aware_toml_spec(toml_path=manifest_path)
        package_name = str(spec.package.package_name).strip()
        if not package_name:
            raise ValueError(
                "Meta graph runtime context package manifest is missing "
                f"package_name: {manifest_path.as_posix()}"
            )
        existing_path = path_by_package_name.get(package_name)
        if existing_path is not None and existing_path != manifest_path:
            raise ValueError(
                "Meta graph runtime context received duplicate package "
                f"{package_name!r}: {existing_path.as_posix()} and "
                f"{manifest_path.as_posix()}"
            )
        spec_dependency_names = tuple(
            str(dependency.package_name).strip()
            for dependency in spec.dependencies
            if str(dependency.package_name).strip()
        )
        catalog_dependency_names = (
            ()
            if catalog_entry is None
            else tuple(catalog_entry.dependency_package_names)
        )
        package_name_by_path[manifest_path] = package_name
        dependency_names_by_path[manifest_path] = tuple(
            dict.fromkeys((*catalog_dependency_names, *spec_dependency_names))
        )
        path_by_package_name[package_name] = manifest_path

    ordered_paths: list[Path] = []
    visited: set[Path] = set()
    visiting: list[str] = []

    def visit(manifest_path: Path) -> None:
        if manifest_path in visited:
            return
        package_name = package_name_by_path[manifest_path]
        if package_name in visiting:
            raise ValueError(
                "Cyclic ObjectConfigGraph package dependency: "
                + " -> ".join((*visiting, package_name))
            )
        visiting.append(package_name)
        for dependency_name in dependency_names_by_path[manifest_path]:
            dependency_path = path_by_package_name.get(dependency_name)
            if dependency_path is not None:
                visit(dependency_path)
        visiting.pop()
        visited.add(manifest_path)
        ordered_paths.append(manifest_path)

    for manifest_path in manifest_paths:
        visit(manifest_path)
    return tuple(ordered_paths)


def _workspace_root_for_package_manifests(
    *,
    workspace_root: Path | None,
    package_manifest_paths: tuple[Path, ...],
) -> Path:
    if workspace_root is not None:
        return workspace_root.expanduser().resolve()
    for manifest_path in package_manifest_paths:
        for candidate in (manifest_path.parent, *manifest_path.parents):
            if (candidate / ".git").exists() or (
                candidate / "aware.environment.toml"
            ).exists():
                return candidate.resolve()
    return package_manifest_paths[0].parents[-1].resolve()


def _catalog_entries_by_resolved_manifest_path(
    entries_by_manifest_path: Mapping[Path, MetaRuntimePackageIndexEntry] | None,
) -> dict[Path, MetaRuntimePackageIndexEntry]:
    if entries_by_manifest_path is None:
        return {}
    return {
        Path(manifest_path).expanduser().resolve(): entry
        for manifest_path, entry in entries_by_manifest_path.items()
    }


def _module_catalog_entries_by_resolved_manifest_path(
    *,
    repo_root: Path,
    manifest_paths: Iterable[Path],
) -> dict[Path, MetaRuntimePackageIndexEntry]:
    entries_by_package_name, _package_names_by_module_id = (
        _ontology_package_manifest_catalog(repo_root=repo_root)
    )
    selected_paths = {path.expanduser().resolve() for path in manifest_paths}
    return {
        entry.manifest_path.expanduser().resolve(): entry
        for entry in entries_by_package_name.values()
        if entry.manifest_path.expanduser().resolve() in selected_paths
    }


def _path_mapping_by_resolved_manifest_path(
    value: Mapping[Path, Path] | None,
) -> dict[Path, Path]:
    if value is None:
        return {}
    return {
        Path(manifest_path)
        .expanduser()
        .resolve(): Path(owner_root)
        .expanduser()
        .resolve()
        for manifest_path, owner_root in value.items()
    }


def _resolved_path_set(value: Iterable[Path]) -> set[Path]:
    return {Path(path).expanduser().resolve() for path in value}


def _catalog_entry_for_manifest_path(
    *,
    entries_by_manifest_path: Mapping[Path, MetaRuntimePackageIndexEntry],
    manifest_path: Path,
) -> MetaRuntimePackageIndexEntry | None:
    return entries_by_manifest_path.get(manifest_path.expanduser().resolve())


def _validate_catalog_entry_matches_manifest_spec(
    *,
    catalog_entry: MetaRuntimePackageIndexEntry,
    spec: object,
    manifest_path: Path,
) -> None:
    package = getattr(spec, "package", None)
    package_name = str(getattr(package, "package_name", "") or "").strip()
    fqn_prefix = str(getattr(package, "fqn_prefix", "") or "").strip()
    if (
        catalog_entry.package_name != package_name
        or catalog_entry.fqn_prefix != fqn_prefix
    ):
        raise RuntimeError(
            "Strict Meta package graph cache catalog entry drift for manifest "
            f"{manifest_path.as_posix()!r}: catalog="
            f"{catalog_entry.package_name!r}/{catalog_entry.fqn_prefix!r} "
            f"manifest={package_name!r}/{fqn_prefix!r}."
        )


def _validate_catalog_entry_dependencies_match_manifest_spec(
    *,
    catalog_entry: MetaRuntimePackageIndexEntry,
    spec: object,
    manifest_path: Path,
) -> None:
    spec_dependency_names = tuple(
        str(dependency.package_name).strip()
        for dependency in getattr(spec, "dependencies", ())
        if str(dependency.package_name).strip()
    )
    if catalog_entry.dependency_package_names != spec_dependency_names:
        raise RuntimeError(
            "Strict Meta package graph cache catalog dependency drift for "
            f"manifest {manifest_path.as_posix()!r}: catalog="
            f"{catalog_entry.dependency_package_names!r} manifest="
            f"{spec_dependency_names!r}."
        )


def _try_load_catalog_cached_package_graphs(
    *,
    cache_owner_root: Path,
    catalog_entry: MetaRuntimePackageIndexEntry,
    external_graph_refs: tuple[_PackageGraphRef, ...] | None = None,
    external_graphs: tuple[ObjectConfigGraph, ...] = (),
    load_source_graph: bool = True,
    phase_timings_s: dict[str, float] | None = None,
    diagnostics: dict[str, object] | None = None,
) -> _CachedPackageGraphs | None:
    with _record_phase(phase_timings_s, "catalog_cache_identity"):
        object_config_graph_id = stable_object_config_graph_id(
            fqn_prefix=catalog_entry.fqn_prefix,
            language=CodeLanguage.aware.value,
        )
        object_config_graph_package_id = stable_object_config_graph_package_id(
            package_name=catalog_entry.package_name,
            fqn_prefix=catalog_entry.fqn_prefix,
        )
        branch_id = _stable_object_config_graph_package_branch_id(
            workspace_root=cache_owner_root,
            aware_toml_path=catalog_entry.manifest_path,
            package_name=catalog_entry.package_name,
            fqn_prefix=catalog_entry.fqn_prefix,
        )
        signature_external_graphs: tuple[ObjectConfigGraph | _PackageGraphRef, ...]
        signature_external_graphs = (
            external_graphs if external_graph_refs is None else external_graph_refs
        )
        dependency_signature = _external_graph_signature(
            external_graphs=signature_external_graphs,
        )
    with _record_phase(phase_timings_s, "read_catalog_context_cache_payload"):
        context_payload = _read_package_context_reuse_cache_payload(
            workspace_root=cache_owner_root,
            branch_id=branch_id,
            object_config_graph_package_id=object_config_graph_package_id,
        )
    if context_payload is not None:
        cached_graphs = _try_load_catalog_cache_payload_graphs(
            payload=context_payload,
            cache_source="catalog_context_reuse_cache",
            cache_owner_root=cache_owner_root,
            catalog_entry=catalog_entry,
            branch_id=branch_id,
            object_config_graph_id=object_config_graph_id,
            object_config_graph_package_id=object_config_graph_package_id,
            dependency_signature=dependency_signature,
            load_source_graph=load_source_graph,
            phase_timings_s=phase_timings_s,
            diagnostics=diagnostics,
        )
        if cached_graphs is not None:
            return cached_graphs
        if diagnostics is not None:
            diagnostics["catalog_context_cache_miss_reason"] = diagnostics.get(
                "cache_miss_reason"
            )
            diagnostics["catalog_context_cache_status"] = "miss"
    with _record_phase(phase_timings_s, "read_catalog_materialized_cache_payload"):
        materialized_payload = _read_package_materialized_reuse_cache_payload(
            workspace_root=cache_owner_root,
            branch_id=branch_id,
            object_config_graph_package_id=object_config_graph_package_id,
        )
    if materialized_payload is None:
        if context_payload is None:
            _record_cache_miss(diagnostics, "catalog_cache_payload_missing")
        elif diagnostics is not None:
            diagnostics["cache_status"] = "miss"
            diagnostics["catalog_materialized_cache_miss_reason"] = (
                "catalog_cache_payload_missing"
            )
            diagnostics["catalog_materialized_cache_status"] = "miss"
        return None
    cached_graphs = _try_load_catalog_cache_payload_graphs(
        payload=materialized_payload,
        cache_source="catalog_materialized_package_cache",
        cache_owner_root=cache_owner_root,
        catalog_entry=catalog_entry,
        branch_id=branch_id,
        object_config_graph_id=object_config_graph_id,
        object_config_graph_package_id=object_config_graph_package_id,
        dependency_signature=dependency_signature,
        load_source_graph=True,
        phase_timings_s=phase_timings_s,
        diagnostics=diagnostics,
    )
    if cached_graphs is None and diagnostics is not None:
        diagnostics["catalog_materialized_cache_miss_reason"] = diagnostics.get(
            "cache_miss_reason"
        )
        diagnostics["catalog_materialized_cache_status"] = "miss"
    return cached_graphs


def _try_load_catalog_cache_payload_graphs(
    *,
    payload: Mapping[str, object],
    cache_source: str,
    cache_owner_root: Path,
    catalog_entry: MetaRuntimePackageIndexEntry,
    branch_id: UUID,
    object_config_graph_id: UUID,
    object_config_graph_package_id: UUID,
    dependency_signature: str,
    load_source_graph: bool,
    phase_timings_s: dict[str, float] | None,
    diagnostics: dict[str, object] | None,
) -> _CachedPackageGraphs | None:
    source_manifest_hash = _diagnostic_string(payload, "source_manifest_hash")
    if source_manifest_hash is None:
        _record_cache_miss(diagnostics, "source_manifest_hash_missing")
        return None
    identity = _PackageGraphCacheIdentity(
        package_name=catalog_entry.package_name,
        fqn_prefix=catalog_entry.fqn_prefix,
        branch_id=branch_id,
        object_config_graph_id=object_config_graph_id,
        object_config_graph_package_id=object_config_graph_package_id,
        source_manifest_hash=source_manifest_hash,
        dependency_signature=dependency_signature,
    )
    with _record_phase(phase_timings_s, "catalog_package_graph_session_cache_lookup"):
        cached_graphs = _package_graph_session_cache_get(identity=identity)
    if cached_graphs is not None and (
        not load_source_graph or cached_graphs.source_graph is not None
    ):
        _record_cache_hit(diagnostics, source="catalog_session")
        return cached_graphs
    cache_kind = _diagnostic_string(payload, "cache_kind")
    if not _catalog_cache_payload_matches_identity(
        payload=payload,
        identity=identity,
        cache_kind=cache_kind,
        diagnostics=diagnostics,
    ):
        return None
    if cache_kind == OBJECT_CONFIG_GRAPH_PACKAGE_REUSE_CACHE_KIND_CONTEXT_GRAPHS:
        cached_graphs = _load_catalog_context_package_graphs(
            payload=payload,
            identity=identity,
            load_source_graph=load_source_graph,
            phase_timings_s=phase_timings_s,
            diagnostics=diagnostics,
        )
    elif (
        cache_kind == OBJECT_CONFIG_GRAPH_PACKAGE_REUSE_CACHE_KIND_MATERIALIZED_PACKAGE
    ):
        cached_graphs = _load_catalog_materialized_package_graphs(
            payload=payload,
            identity=identity,
            phase_timings_s=phase_timings_s,
            diagnostics=diagnostics,
        )
        if cached_graphs is not None:
            if cached_graphs.source_graph is None:
                _record_cache_miss(diagnostics, "materialized_source_graph_missing")
                return None
            with _record_phase(
                phase_timings_s,
                "write_catalog_context_cache_from_materialized_payload",
            ):
                context_cache_written = _try_write_catalog_context_package_graph_cache(
                    identity=identity,
                    workspace_root=cache_owner_root,
                    source_graph=cached_graphs.source_graph,
                    runtime_graph=cached_graphs.runtime_graph,
                )
            if diagnostics is not None:
                diagnostics["catalog_context_cache_refresh_status"] = (
                    "written" if context_cache_written else "skipped"
                )
    else:
        _record_cache_miss(diagnostics, "catalog_cache_kind_unsupported")
        return None
    if cached_graphs is None:
        return None
    _package_graph_session_cache_put(
        identity=identity,
        cached_graphs=cached_graphs,
    )
    _record_cache_hit(diagnostics, source=cache_source)
    return cached_graphs


def _catalog_cache_payload_matches_identity(
    *,
    payload: Mapping[str, object],
    identity: _PackageGraphCacheIdentity,
    cache_kind: str | None,
    diagnostics: dict[str, object] | None,
) -> bool:
    if payload.get("v") != _PACKAGE_REUSE_CACHE_VERSION:
        _record_cache_miss(diagnostics, "catalog_cache_version_mismatch")
        return False
    if payload.get("package_name") != identity.package_name:
        _record_cache_miss(diagnostics, "catalog_package_name_mismatch")
        return False
    if payload.get("fqn_prefix") != identity.fqn_prefix:
        _record_cache_miss(diagnostics, "catalog_fqn_prefix_mismatch")
        return False
    if payload.get("dependency_signature") != identity.dependency_signature:
        _record_cache_miss(diagnostics, "dependency_signature_mismatch")
        return False
    if (
        _payload_uuid(payload, "object_config_graph_id")
        != identity.object_config_graph_id
    ):
        _record_cache_miss(diagnostics, "object_config_graph_id_mismatch")
        return False
    if (
        _payload_uuid(payload, "object_config_graph_package_id")
        != identity.object_config_graph_package_id
    ):
        _record_cache_miss(diagnostics, "object_config_graph_package_id_mismatch")
        return False
    if cache_kind == OBJECT_CONFIG_GRAPH_PACKAGE_REUSE_CACHE_KIND_CONTEXT_GRAPHS:
        if (
            payload.get("runtime_graph_derivation_signature")
            != OBJECT_CONFIG_GRAPH_PACKAGE_CONTEXT_GRAPHS_DERIVATION_SIGNATURE
        ):
            _record_cache_miss(
                diagnostics,
                "runtime_graph_derivation_signature_mismatch",
            )
            return False
    return True


def _load_catalog_context_package_graphs(
    *,
    payload: Mapping[str, object],
    identity: _PackageGraphCacheIdentity,
    load_source_graph: bool,
    phase_timings_s: dict[str, float] | None,
    diagnostics: dict[str, object] | None,
) -> _CachedPackageGraphs | None:
    source_graph: ObjectConfigGraph | None = None
    source_graph_hash = _diagnostic_string(payload, "source_object_config_graph_hash")
    if not source_graph_hash:
        _record_cache_miss(diagnostics, "source_graph_hash_missing")
        return None
    if load_source_graph:
        with _record_phase(phase_timings_s, "load_catalog_source_graph_payload"):
            source_graph = _load_graph_payload_from_context_cache(
                payload=payload,
                payload_key="source_object_config_graph",
                hash_key="source_object_config_graph_hash",
            )
        if source_graph is None:
            _record_cache_miss(diagnostics, "source_graph_payload_invalid")
            return None
    with _record_phase(phase_timings_s, "load_catalog_runtime_graph_payload"):
        runtime_graph = _load_graph_payload_from_context_cache(
            payload=payload,
            payload_key="runtime_object_config_graph",
            hash_key="runtime_object_config_graph_hash",
        )
    if runtime_graph is None:
        _record_cache_miss(diagnostics, "runtime_graph_payload_invalid")
        return None
    return _validated_catalog_cached_graphs(
        source_graph=source_graph,
        runtime_graph=runtime_graph,
        source_graph_hash=source_graph_hash,
        identity=identity,
        diagnostics=diagnostics,
    )


def _load_catalog_materialized_package_graphs(
    *,
    payload: Mapping[str, object],
    identity: _PackageGraphCacheIdentity,
    phase_timings_s: dict[str, float] | None,
    diagnostics: dict[str, object] | None,
) -> _CachedPackageGraphs | None:
    with _record_phase(phase_timings_s, "load_catalog_materialized_graph_payload"):
        source_graph = _load_graph_payload_from_context_cache(
            payload=payload,
            payload_key="object_config_graph",
            hash_key="object_config_graph_hash",
        )
    if source_graph is None:
        _record_cache_miss(diagnostics, "materialized_graph_payload_invalid")
        return None
    with _record_phase(phase_timings_s, "derive_runtime_graph_from_materialized_cache"):
        runtime_derivation = derive_runtime_object_config_graph(
            source_graph,
            include_projection_graphs=False,
        )
        runtime_graph = _ensure_runtime_projection_graphs(
            (runtime_derivation.runtime_graph,)
        )[0]
    return _validated_catalog_cached_graphs(
        source_graph=source_graph,
        runtime_graph=runtime_graph,
        source_graph_hash=str(source_graph.hash or ""),
        identity=identity,
        diagnostics=diagnostics,
    )


def _validated_catalog_cached_graphs(
    *,
    source_graph: ObjectConfigGraph | None,
    runtime_graph: ObjectConfigGraph,
    source_graph_hash: str,
    identity: _PackageGraphCacheIdentity,
    diagnostics: dict[str, object] | None,
) -> _CachedPackageGraphs | None:
    if source_graph is not None and source_graph.id != identity.object_config_graph_id:
        _record_cache_miss(diagnostics, "source_graph_id_mismatch")
        return None
    if runtime_graph.id != identity.object_config_graph_id:
        _record_cache_miss(diagnostics, "runtime_graph_id_mismatch")
        return None
    if source_graph is not None and source_graph.fqn_prefix != identity.fqn_prefix:
        _record_cache_miss(diagnostics, "source_graph_fqn_prefix_mismatch")
        return None
    if runtime_graph.fqn_prefix != identity.fqn_prefix:
        _record_cache_miss(diagnostics, "runtime_graph_fqn_prefix_mismatch")
        return None
    return _CachedPackageGraphs(
        source_graph=source_graph,
        runtime_graph=runtime_graph,
        source_graph_ref=_PackageGraphRef(
            package_name=identity.package_name,
            fqn_prefix=identity.fqn_prefix,
            object_config_graph_id=identity.object_config_graph_id,
            object_config_graph_hash=source_graph_hash,
        ),
        identity=identity,
    )


def _package_graph_ref_from_graph(
    *,
    package_name: str,
    fqn_prefix: str,
    graph: ObjectConfigGraph,
) -> _PackageGraphRef:
    return _PackageGraphRef(
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        object_config_graph_id=graph.id,
        object_config_graph_hash=str(graph.hash or ""),
    )


def _load_missing_source_dependency_graphs(
    *,
    dependency_closure_names: tuple[str, ...],
    source_graph_by_package_name: dict[str, ObjectConfigGraph],
    source_graph_cache_identity_by_package_name: Mapping[
        str,
        _PackageGraphCacheIdentity,
    ],
    source_graph_cache_owner_root_by_package_name: Mapping[str, Path],
) -> tuple[ObjectConfigGraph, ...]:
    graphs: list[ObjectConfigGraph] = []
    for package_name in dependency_closure_names:
        source_graph = source_graph_by_package_name.get(package_name)
        if source_graph is None:
            identity = source_graph_cache_identity_by_package_name.get(package_name)
            cache_owner_root = source_graph_cache_owner_root_by_package_name.get(
                package_name
            )
            if identity is None or cache_owner_root is None:
                raise RuntimeError(
                    "Runtime-only Meta graph context cannot fall back to source "
                    "analysis because a dependency source graph is unavailable: "
                    f"package={package_name!r}."
                )
            source_graph = _load_source_graph_from_package_graph_cache(
                cache_owner_root=cache_owner_root,
                identity=identity,
            )
            if source_graph is None:
                raise RuntimeError(
                    "Runtime-only Meta graph context could not reload dependency "
                    "source graph payload for source analysis fallback: "
                    f"package={package_name!r}."
                )
            source_graph_by_package_name[package_name] = source_graph
        graphs.append(source_graph)
    return tuple(graphs)


def _load_source_graph_from_package_graph_cache(
    *,
    cache_owner_root: Path,
    identity: _PackageGraphCacheIdentity,
) -> ObjectConfigGraph | None:
    context_payload = _read_package_context_reuse_cache_payload(
        workspace_root=cache_owner_root,
        branch_id=identity.branch_id,
        object_config_graph_package_id=identity.object_config_graph_package_id,
    )
    if context_payload is not None and _catalog_cache_payload_matches_identity(
        payload=context_payload,
        identity=identity,
        cache_kind=_diagnostic_string(context_payload, "cache_kind"),
        diagnostics=None,
    ):
        source_graph = _load_graph_payload_from_context_cache(
            payload=context_payload,
            payload_key="source_object_config_graph",
            hash_key="source_object_config_graph_hash",
        )
        if _source_graph_matches_identity(source_graph=source_graph, identity=identity):
            return source_graph
    materialized_payload = _read_package_materialized_reuse_cache_payload(
        workspace_root=cache_owner_root,
        branch_id=identity.branch_id,
        object_config_graph_package_id=identity.object_config_graph_package_id,
    )
    if materialized_payload is not None and _catalog_cache_payload_matches_identity(
        payload=materialized_payload,
        identity=identity,
        cache_kind=_diagnostic_string(materialized_payload, "cache_kind"),
        diagnostics=None,
    ):
        source_graph = _load_graph_payload_from_context_cache(
            payload=materialized_payload,
            payload_key="object_config_graph",
            hash_key="object_config_graph_hash",
        )
        if _source_graph_matches_identity(source_graph=source_graph, identity=identity):
            return source_graph
    return None


def _source_graph_matches_identity(
    *,
    source_graph: ObjectConfigGraph | None,
    identity: _PackageGraphCacheIdentity,
) -> bool:
    return (
        source_graph is not None
        and source_graph.id == identity.object_config_graph_id
        and source_graph.fqn_prefix == identity.fqn_prefix
    )


def _try_load_cached_package_graphs(
    *,
    workspace_root: Path,
    manifest_path: Path,
    spec: object,
    external_graphs: tuple[ObjectConfigGraph, ...],
    phase_timings_s: dict[str, float] | None = None,
    diagnostics: dict[str, object] | None = None,
) -> _CachedPackageGraphs | None:
    with _record_phase(phase_timings_s, "cache_identity"):
        identity = _package_source_graph_cache_identity(
            workspace_root=workspace_root,
            manifest_path=manifest_path,
            spec=spec,
            external_graphs=external_graphs,
            phase_timings_s=phase_timings_s,
        )
    if identity is None:
        _record_cache_miss(diagnostics, "cache_identity_unavailable")
        return None
    with _record_phase(phase_timings_s, "package_graph_session_cache_lookup"):
        cached_graphs = _package_graph_session_cache_get(identity=identity)
    if cached_graphs is not None and cached_graphs.source_graph is not None:
        _record_cache_hit(diagnostics, source="session")
        return cached_graphs
    with _record_phase(phase_timings_s, "read_context_cache_payload"):
        payload = _read_package_context_reuse_cache_payload(
            workspace_root=workspace_root,
            branch_id=identity.branch_id,
            object_config_graph_package_id=identity.object_config_graph_package_id,
        )
    if payload is None:
        return _try_load_materialized_cached_package_graphs_after_context_miss(
            workspace_root=workspace_root,
            identity=identity,
            context_miss_reason="context_cache_payload_missing",
            phase_timings_s=phase_timings_s,
            diagnostics=diagnostics,
        )
    if payload.get("v") != _PACKAGE_REUSE_CACHE_VERSION:
        return _try_load_materialized_cached_package_graphs_after_context_miss(
            workspace_root=workspace_root,
            identity=identity,
            context_miss_reason="context_cache_version_mismatch",
            phase_timings_s=phase_timings_s,
            diagnostics=diagnostics,
        )
    if payload.get("cache_kind") != (
        OBJECT_CONFIG_GRAPH_PACKAGE_REUSE_CACHE_KIND_CONTEXT_GRAPHS
    ):
        return _try_load_materialized_cached_package_graphs_after_context_miss(
            workspace_root=workspace_root,
            identity=identity,
            context_miss_reason="context_cache_kind_mismatch",
            phase_timings_s=phase_timings_s,
            diagnostics=diagnostics,
        )
    if payload.get("source_manifest_hash") != identity.source_manifest_hash:
        return _try_load_materialized_cached_package_graphs_after_context_miss(
            workspace_root=workspace_root,
            identity=identity,
            context_miss_reason="source_manifest_hash_mismatch",
            phase_timings_s=phase_timings_s,
            diagnostics=diagnostics,
        )
    if payload.get("dependency_signature") != identity.dependency_signature:
        return _try_load_materialized_cached_package_graphs_after_context_miss(
            workspace_root=workspace_root,
            identity=identity,
            context_miss_reason="dependency_signature_mismatch",
            phase_timings_s=phase_timings_s,
            diagnostics=diagnostics,
        )
    if (
        payload.get("runtime_graph_derivation_signature")
        != OBJECT_CONFIG_GRAPH_PACKAGE_CONTEXT_GRAPHS_DERIVATION_SIGNATURE
    ):
        return _try_load_materialized_cached_package_graphs_after_context_miss(
            workspace_root=workspace_root,
            identity=identity,
            context_miss_reason="runtime_graph_derivation_signature_mismatch",
            phase_timings_s=phase_timings_s,
            diagnostics=diagnostics,
        )
    if (
        _payload_uuid(payload, "object_config_graph_id")
        != identity.object_config_graph_id
    ):
        return _try_load_materialized_cached_package_graphs_after_context_miss(
            workspace_root=workspace_root,
            identity=identity,
            context_miss_reason="object_config_graph_id_mismatch",
            phase_timings_s=phase_timings_s,
            diagnostics=diagnostics,
        )
    if (
        _payload_uuid(payload, "object_config_graph_package_id")
        != identity.object_config_graph_package_id
    ):
        return _try_load_materialized_cached_package_graphs_after_context_miss(
            workspace_root=workspace_root,
            identity=identity,
            context_miss_reason="object_config_graph_package_id_mismatch",
            phase_timings_s=phase_timings_s,
            diagnostics=diagnostics,
        )

    with _record_phase(phase_timings_s, "load_source_graph_payload"):
        source_graph = _load_graph_payload_from_context_cache(
            payload=payload,
            payload_key="source_object_config_graph",
            hash_key="source_object_config_graph_hash",
        )
    if source_graph is None:
        return _try_load_materialized_cached_package_graphs_after_context_miss(
            workspace_root=workspace_root,
            identity=identity,
            context_miss_reason="source_graph_payload_invalid",
            phase_timings_s=phase_timings_s,
            diagnostics=diagnostics,
        )
    with _record_phase(phase_timings_s, "load_runtime_graph_payload"):
        runtime_graph = _load_graph_payload_from_context_cache(
            payload=payload,
            payload_key="runtime_object_config_graph",
            hash_key="runtime_object_config_graph_hash",
        )
    if runtime_graph is None:
        return _try_load_materialized_cached_package_graphs_after_context_miss(
            workspace_root=workspace_root,
            identity=identity,
            context_miss_reason="runtime_graph_payload_invalid",
            phase_timings_s=phase_timings_s,
            diagnostics=diagnostics,
        )
    if source_graph.id != identity.object_config_graph_id:
        return _try_load_materialized_cached_package_graphs_after_context_miss(
            workspace_root=workspace_root,
            identity=identity,
            context_miss_reason="source_graph_id_mismatch",
            phase_timings_s=phase_timings_s,
            diagnostics=diagnostics,
        )
    if runtime_graph.id != identity.object_config_graph_id:
        return _try_load_materialized_cached_package_graphs_after_context_miss(
            workspace_root=workspace_root,
            identity=identity,
            context_miss_reason="runtime_graph_id_mismatch",
            phase_timings_s=phase_timings_s,
            diagnostics=diagnostics,
        )
    cached_graphs = _CachedPackageGraphs(
        source_graph=source_graph,
        runtime_graph=runtime_graph,
        source_graph_ref=_package_graph_ref_from_graph(
            package_name=identity.package_name,
            fqn_prefix=identity.fqn_prefix,
            graph=source_graph,
        ),
        identity=identity,
    )
    _package_graph_session_cache_put(
        identity=identity,
        cached_graphs=cached_graphs,
    )
    _record_cache_hit(diagnostics, source="durable_reuse_cache")
    return cached_graphs


def _try_load_materialized_cached_package_graphs_after_context_miss(
    *,
    workspace_root: Path,
    identity: _PackageGraphCacheIdentity,
    context_miss_reason: str,
    phase_timings_s: dict[str, float] | None,
    diagnostics: dict[str, object] | None,
) -> _CachedPackageGraphs | None:
    _record_context_cache_miss(diagnostics, context_miss_reason)
    return _try_load_materialized_cached_package_graphs(
        workspace_root=workspace_root,
        identity=identity,
        phase_timings_s=phase_timings_s,
        diagnostics=diagnostics,
    )


def _try_load_materialized_cached_package_graphs(
    *,
    workspace_root: Path,
    identity: _PackageGraphCacheIdentity,
    phase_timings_s: dict[str, float] | None,
    diagnostics: dict[str, object] | None,
) -> _CachedPackageGraphs | None:
    with _record_phase(phase_timings_s, "read_materialized_cache_payload"):
        payload = _read_package_materialized_reuse_cache_payload(
            workspace_root=workspace_root,
            branch_id=identity.branch_id,
            object_config_graph_package_id=identity.object_config_graph_package_id,
        )
    if payload is None:
        _record_materialized_cache_miss(
            diagnostics,
            "materialized_cache_payload_missing",
        )
        return None
    cache_kind = _diagnostic_string(payload, "cache_kind")
    if cache_kind != OBJECT_CONFIG_GRAPH_PACKAGE_REUSE_CACHE_KIND_MATERIALIZED_PACKAGE:
        _record_materialized_cache_miss(
            diagnostics,
            "materialized_cache_kind_mismatch",
        )
        return None
    if payload.get("source_manifest_hash") != identity.source_manifest_hash:
        _record_materialized_cache_miss(
            diagnostics,
            "materialized_source_manifest_hash_mismatch",
        )
        return None
    identity_diagnostics: dict[str, object] = {}
    if not _catalog_cache_payload_matches_identity(
        payload=payload,
        identity=identity,
        cache_kind=cache_kind,
        diagnostics=identity_diagnostics,
    ):
        _record_materialized_cache_miss(
            diagnostics,
            _diagnostic_string(identity_diagnostics, "cache_miss_reason")
            or "materialized_cache_identity_mismatch",
        )
        return None
    load_diagnostics: dict[str, object] = {}
    cached_graphs = _load_materialized_package_graphs(
        payload=payload,
        identity=identity,
        phase_timings_s=phase_timings_s,
        diagnostics=load_diagnostics,
        load_graph_phase_name="load_materialized_graph_payload",
    )
    if cached_graphs is None:
        _record_materialized_cache_miss(
            diagnostics,
            _diagnostic_string(load_diagnostics, "cache_miss_reason")
            or "materialized_graph_payload_invalid",
        )
        return None
    with _record_phase(
        phase_timings_s, "write_context_cache_from_materialized_payload"
    ):
        if cached_graphs.source_graph is None:
            _record_materialized_cache_miss(
                diagnostics,
                "materialized_source_graph_missing",
            )
            return None
        context_cache_written = _try_write_catalog_context_package_graph_cache(
            identity=identity,
            workspace_root=workspace_root,
            source_graph=cached_graphs.source_graph,
            runtime_graph=cached_graphs.runtime_graph,
        )
    _package_graph_session_cache_put(
        identity=identity,
        cached_graphs=cached_graphs,
    )
    if diagnostics is not None:
        diagnostics["materialized_cache_status"] = "hit"
        diagnostics["context_cache_refresh_status"] = (
            "written" if context_cache_written else "skipped"
        )
    _record_cache_hit(diagnostics, source="materialized_package_cache")
    return cached_graphs


def _load_materialized_package_graphs(
    *,
    payload: Mapping[str, object],
    identity: _PackageGraphCacheIdentity,
    phase_timings_s: dict[str, float] | None,
    diagnostics: dict[str, object] | None,
    load_graph_phase_name: str,
) -> _CachedPackageGraphs | None:
    with _record_phase(phase_timings_s, load_graph_phase_name):
        source_graph = _load_graph_payload_from_context_cache(
            payload=payload,
            payload_key="object_config_graph",
            hash_key="object_config_graph_hash",
        )
    if source_graph is None:
        _record_cache_miss(diagnostics, "materialized_graph_payload_invalid")
        return None
    with _record_phase(phase_timings_s, "derive_runtime_graph_from_materialized_cache"):
        runtime_derivation = derive_runtime_object_config_graph(
            source_graph,
            include_projection_graphs=False,
        )
        runtime_graph = _ensure_runtime_projection_graphs(
            (runtime_derivation.runtime_graph,)
        )[0]
    return _validated_catalog_cached_graphs(
        source_graph=source_graph,
        runtime_graph=runtime_graph,
        source_graph_hash=str(source_graph.hash or ""),
        identity=identity,
        diagnostics=diagnostics,
    )


def _try_write_context_package_graph_cache(
    *,
    workspace_root: Path,
    manifest_path: Path,
    spec: object,
    external_graphs: tuple[ObjectConfigGraph, ...],
    source_graph: ObjectConfigGraph,
    runtime_graph: ObjectConfigGraph,
) -> None:
    identity = _package_source_graph_cache_identity(
        workspace_root=workspace_root,
        manifest_path=manifest_path,
        spec=spec,
        external_graphs=external_graphs,
    )
    if identity is None or source_graph.id != identity.object_config_graph_id:
        return
    if runtime_graph.id != identity.object_config_graph_id:
        return
    _package_graph_session_cache_put(
        identity=identity,
        cached_graphs=_CachedPackageGraphs(
            source_graph=source_graph,
            runtime_graph=runtime_graph,
            source_graph_ref=_package_graph_ref_from_graph(
                package_name=identity.package_name,
                fqn_prefix=identity.fqn_prefix,
                graph=source_graph,
            ),
            identity=identity,
        ),
    )
    try:
        write_object_config_graph_package_context_reuse_cache_payload(
            aware_root=workspace_root,
            branch_id=identity.branch_id,
            object_config_graph_package_id=identity.object_config_graph_package_id,
            payload={
                "v": _PACKAGE_REUSE_CACHE_VERSION,
                "cache_kind": (
                    OBJECT_CONFIG_GRAPH_PACKAGE_REUSE_CACHE_KIND_CONTEXT_GRAPHS
                ),
                "source_manifest_hash": identity.source_manifest_hash,
                "dependency_signature": identity.dependency_signature,
                "runtime_graph_derivation_signature": (
                    OBJECT_CONFIG_GRAPH_PACKAGE_CONTEXT_GRAPHS_DERIVATION_SIGNATURE
                ),
                "package_name": identity.package_name,
                "fqn_prefix": identity.fqn_prefix,
                "object_config_graph_id": str(identity.object_config_graph_id),
                "object_config_graph_package_id": str(
                    identity.object_config_graph_package_id
                ),
                "source_object_config_graph_hash": str(source_graph.hash or ""),
                "runtime_object_config_graph_hash": str(runtime_graph.hash or ""),
                "source_object_config_graph": (
                    _object_config_graph_payload_for_context_cache(source_graph)
                ),
                "runtime_object_config_graph": (
                    _object_config_graph_payload_for_context_cache(runtime_graph)
                ),
            },
        )
    except Exception:
        return


def _try_write_catalog_context_package_graph_cache(
    *,
    identity: _PackageGraphCacheIdentity,
    workspace_root: Path,
    source_graph: ObjectConfigGraph,
    runtime_graph: ObjectConfigGraph,
) -> bool:
    try:
        write_object_config_graph_package_context_reuse_cache_payload(
            aware_root=workspace_root,
            branch_id=identity.branch_id,
            object_config_graph_package_id=identity.object_config_graph_package_id,
            payload={
                "v": _PACKAGE_REUSE_CACHE_VERSION,
                "cache_kind": (
                    OBJECT_CONFIG_GRAPH_PACKAGE_REUSE_CACHE_KIND_CONTEXT_GRAPHS
                ),
                "source_manifest_hash": identity.source_manifest_hash,
                "dependency_signature": identity.dependency_signature,
                "runtime_graph_derivation_signature": (
                    OBJECT_CONFIG_GRAPH_PACKAGE_CONTEXT_GRAPHS_DERIVATION_SIGNATURE
                ),
                "package_name": identity.package_name,
                "fqn_prefix": identity.fqn_prefix,
                "object_config_graph_id": str(identity.object_config_graph_id),
                "object_config_graph_package_id": str(
                    identity.object_config_graph_package_id
                ),
                "source_object_config_graph_hash": str(source_graph.hash or ""),
                "runtime_object_config_graph_hash": str(runtime_graph.hash or ""),
                "source_object_config_graph": (
                    _object_config_graph_payload_for_context_cache(source_graph)
                ),
                "runtime_object_config_graph": (
                    _object_config_graph_payload_for_context_cache(runtime_graph)
                ),
            },
        )
    except Exception:
        return False
    return True


def _object_config_graph_payload_for_context_cache(
    graph: ObjectConfigGraph,
) -> dict[str, object]:
    payload = graph.model_dump(mode="json", by_alias=True, exclude_none=True)
    payload["namespace_membership"] = list(
        build_namespace_membership_payload_from_ocg_identity(ocg=graph)
    )
    return payload


def _package_graph_session_cache_get(
    *,
    identity: _PackageGraphCacheIdentity,
) -> _CachedPackageGraphs | None:
    with _PACKAGE_GRAPH_SESSION_CACHE_LOCK:
        cached_graphs = _PACKAGE_GRAPH_SESSION_CACHE.get(identity)
        if cached_graphs is not None:
            _PACKAGE_GRAPH_SESSION_CACHE.move_to_end(identity)
        return cached_graphs


def _package_graph_session_cache_put(
    *,
    identity: _PackageGraphCacheIdentity,
    cached_graphs: _CachedPackageGraphs,
) -> None:
    with _PACKAGE_GRAPH_SESSION_CACHE_LOCK:
        _PACKAGE_GRAPH_SESSION_CACHE[identity] = cached_graphs
        _PACKAGE_GRAPH_SESSION_CACHE.move_to_end(identity)
        while len(_PACKAGE_GRAPH_SESSION_CACHE) > (
            _PACKAGE_GRAPH_SESSION_CACHE_MAX_ENTRIES
        ):
            _PACKAGE_GRAPH_SESSION_CACHE.popitem(last=False)


def _clear_meta_package_graph_session_cache() -> None:
    with _PACKAGE_GRAPH_SESSION_CACHE_LOCK:
        _PACKAGE_GRAPH_SESSION_CACHE.clear()


def _package_source_graph_cache_identity(
    *,
    workspace_root: Path,
    manifest_path: Path,
    spec: object,
    external_graphs: tuple[ObjectConfigGraph, ...],
    phase_timings_s: dict[str, float] | None = None,
) -> _PackageGraphCacheIdentity | None:
    package = getattr(spec, "package", None)
    build = getattr(spec, "build", None)
    package_name = str(getattr(package, "package_name", "") or "").strip()
    fqn_prefix = str(getattr(package, "fqn_prefix", "") or "").strip()
    sources_dir = (
        str(getattr(build, "sources_dir", "aware") or "aware").strip() or "aware"
    )
    package_root = manifest_path.parent.resolve()
    sources_root = (package_root / sources_dir).resolve()
    if not package_name or not fqn_prefix or not sources_root.is_dir():
        return None

    with _record_phase(phase_timings_s, "read_package_source_texts"):
        source_text_by_relative_path = _read_package_source_texts(
            sources_root=sources_root,
            include_paths=_clean_path_patterns(getattr(build, "include_paths", None)),
            exclude_paths=_clean_path_patterns(getattr(build, "exclude_paths", None)),
        )
    if not source_text_by_relative_path:
        return None

    object_config_graph_id = stable_object_config_graph_id(
        fqn_prefix=fqn_prefix,
        language=CodeLanguage.aware.value,
    )
    object_config_graph_package_id = stable_object_config_graph_package_id(
        package_name=package_name,
        fqn_prefix=fqn_prefix,
    )
    package_branch_id = _stable_object_config_graph_package_branch_id(
        workspace_root=workspace_root,
        aware_toml_path=manifest_path,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
    )
    with _record_phase(phase_timings_s, "source_text_manifest_hash"):
        source_manifest_hash = _source_text_manifest_hash(
            source_text_by_relative_path=source_text_by_relative_path,
        )
    with _record_phase(phase_timings_s, "external_graph_signature"):
        dependency_signature = _external_graph_signature(
            external_graphs=external_graphs,
        )
    return _PackageGraphCacheIdentity(
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        branch_id=package_branch_id,
        object_config_graph_id=object_config_graph_id,
        object_config_graph_package_id=object_config_graph_package_id,
        source_manifest_hash=source_manifest_hash,
        dependency_signature=dependency_signature,
    )


def _read_package_source_texts(
    *,
    sources_root: Path,
    include_paths: tuple[str, ...],
    exclude_paths: tuple[str, ...],
) -> dict[str, str]:
    included: set[Path] = set()
    for pattern in include_paths or ("**/*.aware",):
        for candidate in sources_root.glob(pattern):
            if not candidate.is_file() or candidate.suffix != _AWARE_SOURCE_EXTENSION:
                continue
            resolved = candidate.resolve()
            if not _is_within(candidate=resolved, root=sources_root):
                continue
            if _has_ignored_segment(resolved.relative_to(sources_root).parts):
                continue
            included.add(resolved)
    for pattern in exclude_paths:
        for candidate in sources_root.glob(pattern):
            if candidate.is_file():
                included.discard(candidate.resolve())
    return {
        path.relative_to(sources_root).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted(included)
    }


def _clean_path_patterns(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        return ()
    return tuple(
        pattern for pattern in (str(item).strip() for item in value) if pattern
    )


def _source_text_manifest_hash(
    *,
    source_text_by_relative_path: Mapping[str, str],
) -> str:
    return source_text_manifest_hash(
        source_text_by_relative_path=source_text_by_relative_path,
    )


def _external_graph_signature(
    *,
    external_graphs: tuple[ObjectConfigGraph | _PackageGraphRef, ...],
) -> str:
    if not external_graphs or isinstance(external_graphs[0], ObjectConfigGraph):
        return external_graph_signature(
            external_graphs=cast(tuple[ObjectConfigGraph, ...], external_graphs)
        )
    hasher = hashlib.sha256()
    hasher.update(b"aware-meta-package-external-graphs-v1\n")
    for graph_ref in sorted(
        cast(tuple[_PackageGraphRef, ...], external_graphs),
        key=lambda item: str(item.object_config_graph_id),
    ):
        hasher.update(str(graph_ref.object_config_graph_id).encode("ascii"))
        hasher.update(b":")
        hasher.update(str(graph_ref.object_config_graph_hash or "").encode("utf-8"))
        hasher.update(b"\n")
    return hasher.hexdigest()


def _stable_object_config_graph_package_branch_id(
    *,
    workspace_root: Path,
    aware_toml_path: Path,
    package_name: str,
    fqn_prefix: str,
) -> UUID:
    return stable_meta_runtime_package_branch_id(
        workspace_root=workspace_root,
        aware_toml_path=aware_toml_path,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
    )


def _load_graph_payload_from_context_cache(
    *,
    payload: Mapping[str, object],
    payload_key: str,
    hash_key: str,
) -> ObjectConfigGraph | None:
    graph_payload = payload.get(payload_key)
    if not isinstance(graph_payload, Mapping):
        return None
    normalized_payload = {str(key): value for key, value in graph_payload.items()}
    if not _object_config_graph_payload_has_materialized_body(normalized_payload):
        return None
    if not _object_config_graph_payload_has_namespace_evidence(normalized_payload):
        return None
    graph = ObjectConfigGraph.model_validate(normalized_payload)
    if str(graph.hash or "") != str(payload.get(hash_key) or ""):
        return None
    return graph


def _read_package_context_reuse_cache_payload(
    *,
    workspace_root: Path,
    branch_id: UUID,
    object_config_graph_package_id: UUID,
) -> dict[str, object] | None:
    return read_object_config_graph_package_context_reuse_cache_payload(
        aware_root=workspace_root,
        branch_id=branch_id,
        object_config_graph_package_id=object_config_graph_package_id,
    )


def _read_package_materialized_reuse_cache_payload(
    *,
    workspace_root: Path,
    branch_id: UUID,
    object_config_graph_package_id: UUID,
) -> dict[str, object] | None:
    return read_object_config_graph_package_reuse_cache_payload(
        aware_root=workspace_root,
        branch_id=branch_id,
        object_config_graph_package_id=object_config_graph_package_id,
    )


def _payload_uuid(payload: Mapping[str, object], key: str) -> UUID | None:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        return None
    try:
        return UUID(value)
    except Exception:
        return None


def _object_config_graph_payload_has_materialized_body(
    payload: Mapping[str, object],
) -> bool:
    return object_config_graph_payload_has_materialized_body(payload)


def _object_config_graph_payload_has_namespace_evidence(
    payload: Mapping[str, object],
) -> bool:
    return object_config_graph_payload_has_namespace_evidence(payload)


def _is_within(*, candidate: Path, root: Path) -> bool:
    try:
        candidate.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _has_ignored_segment(parts: tuple[str, ...]) -> bool:
    return any(part in _IGNORED_SEGMENTS for part in parts)


def _remember_class_config(
    *,
    class_config: ClassConfig,
    class_configs_by_id: dict[UUID, ClassConfig],
    attribute_configs_by_id: dict[UUID, AttributeConfig],
    relationships_by_id: dict[UUID, ClassConfigRelationship],
) -> None:
    class_configs_by_id.setdefault(class_config.id, class_config)
    for link in class_config.class_config_attribute_configs:
        attribute_config = link.attribute_config
        if attribute_config is not None:
            attribute_configs_by_id.setdefault(attribute_config.id, attribute_config)
    for relationship in class_config.class_config_relationships:
        relationships_by_id.setdefault(relationship.id, relationship)


def _projection_hash_by_name(ocg: ObjectConfigGraph) -> dict[str, str]:
    projection_hash_by_name: dict[str, str] = {}
    for opg in ocg.object_projection_graphs:
        name = opg.name.strip()
        if not name:
            continue
        existing = projection_hash_by_name.get(name)
        if existing is not None and existing != opg.projection_hash:
            raise ValueError(
                "Conflicting projection hashes for authored projection name "
                f"{name!r}: {existing!r} != {opg.projection_hash!r}"
            )
        projection_hash_by_name[name] = opg.projection_hash
    return projection_hash_by_name


@contextmanager
def _record_phase(
    phase_timings_s: dict[str, float] | None,
    phase_name: str,
):
    started_at = perf_counter()
    try:
        yield
    finally:
        if phase_timings_s is not None:
            phase_timings_s[phase_name] = _round_duration_s(perf_counter() - started_at)


def _round_duration_s(duration_s: float) -> float:
    return round(duration_s, 6)


def _record_cache_miss(
    diagnostics: dict[str, object] | None,
    reason: str,
) -> None:
    if diagnostics is None:
        return
    diagnostics["cache_status"] = "miss"
    diagnostics["cache_miss_reason"] = reason


def _record_context_cache_miss(
    diagnostics: dict[str, object] | None,
    reason: str,
) -> None:
    _record_cache_miss(diagnostics, reason)
    if diagnostics is None:
        return
    diagnostics["context_cache_status"] = "miss"
    diagnostics["context_cache_miss_reason"] = reason


def _record_materialized_cache_miss(
    diagnostics: dict[str, object] | None,
    reason: str,
) -> None:
    if diagnostics is None:
        return
    diagnostics["materialized_cache_status"] = "miss"
    diagnostics["materialized_cache_miss_reason"] = reason


def _record_cache_hit(
    diagnostics: dict[str, object] | None,
    *,
    source: str,
) -> None:
    if diagnostics is None:
        return
    diagnostics["cache_status"] = "hit"
    diagnostics["cache_source"] = source
    diagnostics["cache_miss_reason"] = None


def _diagnostic_string(
    diagnostics: Mapping[str, object],
    key: str,
) -> str | None:
    value = diagnostics.get(key)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


__all__ = [
    "build_meta_graph_runtime_context",
    "build_meta_graph_runtime_context_for_aware_package_manifests",
    "build_meta_graph_runtime_context_for_workspace_required_projections",
    "build_meta_graph_runtime_context_for_semantic_materialization",
    "build_meta_workspace_materialization_runtime_context",
    "build_meta_graph_runtime_index_snapshot",
    "find_meta_graph_projection_hash_by_name",
    "resolve_meta_runtime_package_manifest_closure_for_workspace_read_model",
    "resolve_meta_runtime_package_manifest_closure_for_package_names",
    "resolve_workspace_required_projection_package_manifest_paths",
    "MetaGraphRuntimeContext",
    "MetaGraphRuntimeIndexSnapshot",
    "MetaGraphRuntimePackageTiming",
    "MetaWorkspaceMaterializationRuntimeContext",
]
