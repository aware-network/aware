from __future__ import annotations

from collections.abc import AsyncIterator, Callable, Iterable, Iterator, Mapping
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, replace
import hashlib
from inspect import isawaitable
import json
import os
from pathlib import Path
import shutil
from threading import Lock
from time import perf_counter
from typing import Any, TypeAlias, TypeVar, cast
from uuid import NAMESPACE_URL, UUID, uuid5

from aware_code.stable_ids import (
    code_package_generated_config_key,
    code_package_source_config_key,
    stable_code_id,
    stable_code_package_code_id,
    stable_code_package_config_id,
    stable_code_package_id,
)
from aware_code.module_plugin_registry import AwareModulePluginRegistry
from aware_code.package_surface import (
    code_package_surface_from_semantic_manifest_descriptor,
)
from aware_code.setup_language_plugins import setup_code_plugins
from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.code.code_plan import CodePackagePathRole
from aware_code_ontology.class_.code_section_class import CodeSectionClass
from aware_code_ontology.enum.code_section_enum import CodeSectionEnum
from aware_code_ontology.function.code_section_function import CodeSectionFunction
from aware_code_ontology.package.code_package import CodePackage
from aware_code_ontology.package.code_package_code import CodePackageCode
from aware_content_ontology.part.content_part_text import ContentPartText
from aware_meta.manifest.loader import load_aware_toml_spec
from aware_meta.manifest.spec import AwarePackageKind
from aware_meta.graph.config.lane import (
    collect_lane_instance_models,
    ensure_graph_identity_seeded_lane,
    OCGSeedPlan,
    OcgLaneCommitError,
    OcgSeedError,
    commit_ocg_delta_to_lane,
    ensure_ocg_seeded_lane,
    preview_graph_identity_seed_plan,
)
from aware_meta.graph.config.lane.projection import prepare_ocg_seed_projection
from aware_meta.graph.config.node_diff import diff_object_config_graph_nodes
from aware_meta.graph.projection.identity import (
    synthesize_object_projection_graph_identity,
)
from aware_meta.graph.config.builder import build_object_config_graph_from_code
from aware_meta.graph.config.handlers import build_object_projection_graphs
from aware_meta.graph.config.model_bootstrap import get_node_function_config
from aware_meta.graph.instance.builder import build_object_instance_graph
from aware_meta.graph.instance.diff import diff_object_instance_graph_changes
from aware_meta.graph.package.materialization import (
    MetaObjectConfigGraphPackageMaterializationReceipt,
)
from aware_meta_ontology.class_.class_config_relationship import (
    ClassConfigRelationship,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_delta import (
    ObjectConfigGraphDelta,
)
from aware_meta_ontology.graph.config.object_config_graph_package import (
    ObjectConfigGraphPackage,
)
from aware_meta_ontology.graph.config.object_config_graph_package_language_materialization import (
    ObjectConfigGraphPackageLanguageMaterialization,
)
from aware_meta_ontology.graph.config.object_config_graph_package_language_materialization_package import (
    ObjectConfigGraphPackageLanguageMaterializationPackage,
)
from aware_meta_ontology.graph.config.object_config_graph_package_implementation_policy_enums import (
    ObjectConfigGraphPackageFunctionImplOwnership,
    ObjectConfigGraphPackageFunctionImplParityPolicy,
)
from aware_meta_ontology.graph.instance.object_instance_graph import (
    ObjectInstanceGraph,
)
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_meta_ontology.graph.projection.object_projection_graph_declaration import (
    ObjectProjectionGraphDeclaration,
)
from aware_meta_ontology.stable_ids import (
    stable_object_instance_graph_commit_id,
    stable_object_instance_graph_id,
    stable_object_config_graph_id,
    stable_object_config_graph_package_id,
    stable_object_config_graph_package_language_materialization_id,
    stable_object_config_graph_package_language_materialization_package_id,
)
from aware_meta.graph.instance.commit.committer import FSLaneCommitter
from aware_meta.graph.instance.commit.fs_store import (
    CommitActionDescriptor,
    FSCommitStore,
    FSSnapshotStore,
    ObjectInstanceGraphCommitEnvelope,
    object_instance_graph_commit_envelope_from_commit,
)
from aware_meta.graph.instance.commit.materialization_cache import (
    CachedLaneMaterializer,
    get_shared_materialization_cache,
)
from aware_meta.graph.instance.commit.materializer import (
    MaterializerPostHashMismatchError,
)
from aware_meta.graph.config.namespace.membership import (
    build_namespace_membership_payload_from_ocg_identity,
)
from aware_meta.package_graph_reuse_cache import (
    OBJECT_CONFIG_GRAPH_PACKAGE_REUSE_CACHE_KIND_CONTEXT_GRAPHS,
    OBJECT_CONFIG_GRAPH_PACKAGE_REUSE_CACHE_KIND_CONTEXT_SOURCE_GRAPH,
    OBJECT_CONFIG_GRAPH_PACKAGE_REUSE_CACHE_KIND_MATERIALIZED_PACKAGE,
    OBJECT_CONFIG_GRAPH_PACKAGE_REUSE_CACHE_VERSION,
    OBJECT_CONFIG_GRAPH_SOURCE_TO_RUNTIME_LOWERING_SIGNATURE,
    external_graph_signature,
    object_config_graph_package_reuse_cache_path,
    object_config_graph_payload_has_materialized_body,
    object_config_graph_payload_has_namespace_evidence,
    read_object_config_graph_package_reuse_cache_payload,
    source_text_manifest_hash,
    write_object_config_graph_package_reuse_cache_payload,
)
from aware_meta.semantic_contract import META_MANIFEST_RESOLUTION
from aware_meta.graph.instance.validator_opg import (
    OigValidationError,
    validate_object_instance_graph_against_opg,
)
from aware_meta.graph.instance.commit.validator import (
    OigCommitValidationError,
    validate_object_instance_graph_commit,
)
from aware_meta.runtime.author import resolve_meta_author_id
from aware_meta.runtime.graph_context import find_meta_graph_projection_hash_by_name
from aware_meta.runtime.package_index import (
    MetaRuntimePackageIndexEntry,
    record_full_package_materialization_index,
)
from aware_meta.runtime.handler_executor.contracts import MetaGraphRuntimeIndex
from aware_meta.runtime.oig_model_reifier import reify_oig_root_model
from aware_meta.runtime.value_resolvers import default_meta_enum_option_resolver
from aware_meta.language_plugin import MetaLanguagePlugin
from aware_meta.language_plugin_registry import MetaLanguagePluginRegistry
from aware_orm.models.base_model import BaseORMModel
from aware_orm.models.introspection import ModelIntrospection
from aware_orm.session.autobind import disable_autobind
from aware_meta.runtime.commit.required_reactions import (
    RuntimeCommitReactionContext,
    run_required_runtime_commit_reactions,
)
from aware_meta.runtime.commit.identity_lane import (
    ensure_object_instance_graph_identity_lane_head,
    resolve_domain_object_instance_graph_identity_id,
)
from aware_meta.graph.config.cross_ocg import (
    link_cross_ocg_relationships,
)
from aware_utils.logging import logger


_AWARE_SOURCE_EXTENSION = ".aware"
_PACKAGE_REUSE_CACHE_VERSION = OBJECT_CONFIG_GRAPH_PACKAGE_REUSE_CACHE_VERSION
_IGNORED_SEGMENTS = frozenset(
    {".aware", ".git", "__pycache__", "node_modules", ".venv", "venv"}
)
_SOURCE_CONTENT_PART_TEXT_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware://meta/materialization/code-package-source-text/v1",
)
_OBJECT_CONFIG_GRAPH_PACKAGE_SNAPSHOT_COMMIT_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware://meta/materialization/object-config-graph-package-snapshot-commit/v1",
)
_TRoot = TypeVar("_TRoot", CodePackage, ObjectConfigGraph, ObjectConfigGraphPackage)
MetaLeafPackageProgressCallback: TypeAlias = Callable[[Mapping[str, object]], object]


def _setup_meta_materialization_language_plugins() -> None:
    setup_code_plugins()
    for plugin in AwareModulePluginRegistry.get_builtin_meta_language_plugins():
        MetaLanguagePluginRegistry.register(cast(MetaLanguagePlugin, plugin))


def _load_meta_code_package_source_helpers() -> (
    tuple[Callable[..., object], Callable[..., object]]
):
    from aware_meta.materialization.code_package_sources import (
        build_namespace_by_code_id_for_code_package,
        build_parsed_file_codes_for_code_package_sources,
    )

    return (
        build_parsed_file_codes_for_code_package_sources,
        build_namespace_by_code_id_for_code_package,
    )


@dataclass(frozen=True, slots=True)
class _ModelIntrospectionOverlay(ModelIntrospection):
    source: ModelIntrospection
    values_by_name: Mapping[str, object]

    @property
    def id(self) -> UUID:
        return self.source.id

    def field_is_declared(self, name: str) -> bool:
        return name in self.values_by_name or self.source.field_is_declared(name)

    def field_is_set(self, name: str) -> bool:
        return name in self.values_by_name or self.source.field_is_set(name)

    def try_field_value(
        self,
        name: str,
        *,
        include_unset: bool = False,
    ) -> tuple[bool, object]:
        found, value = self.source.try_field_value(
            name,
            include_unset=include_unset,
        )
        if found:
            return True, value
        if name in self.values_by_name:
            return True, self.values_by_name[name]
        return False, None

    def try_virtual_value(self, attribute_config: object) -> tuple[bool, object]:
        return self.source.try_virtual_value(attribute_config)  # type: ignore[arg-type]

    def try_attribute_value(self, attribute_config: object) -> tuple[bool, object]:
        found, value = self.source.try_attribute_value(attribute_config)  # type: ignore[arg-type]
        if found:
            return True, value
        name = getattr(attribute_config, "name", None)
        if name in self.values_by_name:
            return True, self.values_by_name[str(name)]
        return False, None

    def try_class_config_id(self) -> UUID | None:
        return self.source.try_class_config_id()


def _object_config_graph_code_package_surface_for_kind(
    package_kind: AwarePackageKind,
) -> str:
    descriptor = next(
        (
            item
            for item in META_MANIFEST_RESOLUTION
            if item.manifest_kind == "aware_toml"
        ),
        None,
    )
    if descriptor is None:
        raise RuntimeError("Meta semantic contract is missing aware.toml resolution.")
    surface = code_package_surface_from_semantic_manifest_descriptor(
        descriptor,
        package_kind=package_kind.value,
    )
    if surface is None:
        raise RuntimeError(
            "Meta semantic contract does not declare a code package surface for "
            f"aware.toml package kind {package_kind.value!r}."
        )
    return surface


@dataclass(frozen=True, slots=True)
class ObjectConfigGraphPackageLeafMaterializationResult:
    aware_toml_path: Path
    package_branch_id: UUID
    code_package: CodePackage
    object_config_graph_package: ObjectConfigGraphPackage
    object_config_graph: ObjectConfigGraph
    owned_file_paths: tuple[str, ...]
    code_package_commit_id: UUID | None
    code_package_head_commit_id: UUID | None
    code_package_object_instance_graph_commit_id: UUID | None
    object_config_graph_commit_id: UUID | None
    object_config_graph_head_commit_id: UUID | None
    object_config_graph_object_instance_graph_commit_id: UUID | None
    object_config_graph_package_commit_id: UUID | None
    object_config_graph_package_head_commit_id: UUID | None
    object_config_graph_package_object_instance_graph_commit_id: UUID | None
    phase_timings_s: Mapping[str, float]
    code_package_build_runtime_telemetry: Mapping[str, object]
    code_package_build_invoke_perf_ms: Mapping[str, int]
    code_package_upsert_runtime_telemetry: Mapping[str, object]
    code_package_upsert_invoke_perf_ms: Mapping[str, int]
    semantic_commit_strategy: str
    semantic_commit_fallback_reset: bool
    semantic_commit_phase_timings_s: Mapping[str, float]
    object_config_graph_payload: Mapping[str, object] | None = None
    materialization_index_receipt: Mapping[str, object] | None = None


def build_object_config_graph_package_materialization_index_receipt(
    *,
    result: ObjectConfigGraphPackageLeafMaterializationResult,
    source_manifest_hash: str,
    dependency_signature: str,
    cache_status: str,
    code_package_projection_hash: str,
    object_config_graph_projection_hash: str,
    object_config_graph_package_projection_hash: str,
    projection_hashes_by_id: Mapping[UUID, str] | None = None,
    package_materialization_receipt: (
        MetaObjectConfigGraphPackageMaterializationReceipt | None
    ) = None,
) -> dict[str, object]:
    object_config_graph = result.object_config_graph
    object_config_graph_package = result.object_config_graph_package
    object_config_graph_identity = object_config_graph.object_config_graph_identity
    projection_hash_by_id = {
        record.object_projection_graph_id: record.projection_hash
        for record in (
            ()
            if package_materialization_receipt is None
            else package_materialization_receipt.projection_identities
        )
        if record.projection_hash is not None
    }
    projection_hash_by_id.update(dict(projection_hashes_by_id or {}))
    projection_hash_by_id.update(
        {
            opg.id: opg.projection_hash
            for opg in object_config_graph.object_projection_graphs
        }
    )
    projection_identities: list[dict[str, object]] = []
    observables: list[dict[str, object]] = []

    if object_config_graph_identity is not None:
        for opgi in object_config_graph_identity.object_projection_graph_identities:
            projection_hash = projection_hash_by_id.get(opgi.object_projection_graph_id)
            if projection_hash is None and opgi.object_projection_graph is not None:
                projection_hash = opgi.object_projection_graph.projection_hash
            observable_receipts = [
                {
                    "object_projection_graph_observable_id": str(observable.id),
                    "object_projection_graph_identity_id": str(opgi.id),
                    "key": observable.key,
                    "observable_key": observable.observable_key,
                    "kind": observable.kind,
                    "position": observable.position,
                    "is_default": observable.is_default,
                }
                for observable in sorted(
                    opgi.object_projection_graph_observables,
                    key=lambda item: (item.observable_key, item.key),
                )
            ]
            projection_identities.append(
                {
                    "object_projection_graph_identity_id": str(opgi.id),
                    "object_config_graph_identity_id": str(
                        opgi.object_config_graph_identity_id
                    ),
                    "object_projection_graph_id": str(opgi.object_projection_graph_id),
                    "projection_name": opgi.projection_name,
                    "projection_hash": projection_hash,
                    "is_branchable": opgi.is_branchable,
                    "observable_keys": [
                        str(receipt["observable_key"])
                        for receipt in observable_receipts
                    ],
                }
            )
            observables.extend(observable_receipts)

    projection_identities.sort(
        key=lambda item: (
            str(item["projection_name"]),
            str(item["object_projection_graph_id"]),
        )
    )
    observables.sort(
        key=lambda item: (
            str(item["object_projection_graph_identity_id"]),
            str(item["observable_key"]),
            str(item["key"]),
        )
    )
    projection_hashes = [
        str(item["projection_hash"])
        for item in projection_identities
        if item["projection_hash"] is not None
    ]
    projection_hashes_complete = len(projection_hashes) == len(projection_identities)

    return {
        "schema": (
            "aware_meta.object_config_graph_package." "materialization_index_receipt.v1"
        ),
        "provider_key": "aware_meta",
        "receipt_kind": "object_config_graph_package_materialization_index",
        "cache_status": cache_status,
        "semantic_commit_strategy": result.semantic_commit_strategy,
        "semantic_commit_fallback_reset": result.semantic_commit_fallback_reset,
        "cache_key": {
            "package_name": object_config_graph_package.package_name,
            "fqn_prefix": object_config_graph_package.fqn_prefix,
            "source_manifest_hash": source_manifest_hash,
            "dependency_signature": dependency_signature,
            "object_config_graph_hash": object_config_graph.hash,
            "projection_hashes": projection_hashes,
            "projection_hashes_complete": projection_hashes_complete,
        },
        "lane_projection_hashes": {
            "code_package": code_package_projection_hash,
            "object_config_graph": object_config_graph_projection_hash,
            "object_config_graph_package": (
                object_config_graph_package_projection_hash
            ),
        },
        "source": {
            "code_package_id": str(result.code_package.id),
            "code_package_head_commit_id": _uuid_value(
                result.code_package_head_commit_id
            ),
            "code_package_object_instance_graph_commit_id": _uuid_value(
                result.code_package_object_instance_graph_commit_id
            ),
            "owned_file_paths": list(result.owned_file_paths),
        },
        "semantic": {
            "package_branch_id": str(result.package_branch_id),
            "object_config_graph_id": str(object_config_graph.id),
            "object_config_graph_hash": object_config_graph.hash,
            "object_config_graph_head_commit_id": _uuid_value(
                result.object_config_graph_head_commit_id
            ),
            "object_config_graph_object_instance_graph_commit_id": _uuid_value(
                result.object_config_graph_object_instance_graph_commit_id
            ),
            "object_config_graph_package_id": str(object_config_graph_package.id),
            "object_config_graph_package_head_commit_id": _uuid_value(
                result.object_config_graph_package_head_commit_id
            ),
            "object_config_graph_package_object_instance_graph_commit_id": (
                _uuid_value(
                    result.object_config_graph_package_object_instance_graph_commit_id
                )
            ),
        },
        "identity_plane": {
            "object_config_graph_identity_id": (
                None
                if object_config_graph_identity is None
                else str(object_config_graph_identity.id)
            ),
            "object_config_graph_identity_key": (
                None
                if object_config_graph_identity is None
                else object_config_graph_identity.key
            ),
            "projection_identities": projection_identities,
            "observables": observables,
        },
    }


def _with_materialization_index_receipt(
    *,
    result: ObjectConfigGraphPackageLeafMaterializationResult,
    source_manifest_hash: str,
    dependency_signature: str,
    cache_status: str,
    code_package_projection_hash: str,
    object_config_graph_projection_hash: str,
    object_config_graph_package_projection_hash: str,
    projection_hashes_by_id: Mapping[UUID, str] | None = None,
    package_materialization_receipt: (
        MetaObjectConfigGraphPackageMaterializationReceipt | None
    ) = None,
) -> ObjectConfigGraphPackageLeafMaterializationResult:
    return replace(
        result,
        materialization_index_receipt=(
            build_object_config_graph_package_materialization_index_receipt(
                result=result,
                source_manifest_hash=source_manifest_hash,
                dependency_signature=dependency_signature,
                cache_status=cache_status,
                code_package_projection_hash=code_package_projection_hash,
                object_config_graph_projection_hash=(
                    object_config_graph_projection_hash
                ),
                object_config_graph_package_projection_hash=(
                    object_config_graph_package_projection_hash
                ),
                projection_hashes_by_id=projection_hashes_by_id,
                package_materialization_receipt=package_materialization_receipt,
            )
        ),
    )


def _uuid_value(value: UUID | None) -> str | None:
    return None if value is None else str(value)


def _exception_summary(exc: BaseException) -> str:
    message = str(exc).strip()
    if message:
        return f"{exc.__class__.__name__}: {message}"
    return exc.__class__.__name__


def _build_receipt_projection_graphs(
    *,
    graph: ObjectConfigGraph,
    external_graphs: tuple[ObjectConfigGraph, ...],
    cross_relationships_by_target_ocg: dict[UUID, list[ClassConfigRelationship]],
) -> list[ObjectProjectionGraph]:
    runtime_graph = _clone_object_config_graph_public_fields(graph)
    runtime_external_graphs = [
        _clone_object_config_graph_public_fields(external_graph)
        for external_graph in external_graphs
    ]
    if _projection_declarations_have_portal_targets(
        declarations=runtime_graph.object_projection_graph_declarations,
    ):
        graph_closure = [*runtime_external_graphs, runtime_graph]
        graph_ids_requiring_opgs = {
            candidate.id
            for candidate in graph_closure
            if candidate.object_projection_graph_declarations
            and not candidate.object_projection_graphs
        }
        for candidate in graph_closure:
            if candidate.id not in graph_ids_requiring_opgs:
                continue
            candidate.object_projection_graphs = build_object_projection_graphs(
                candidate,
                external_graphs=[
                    external_graph
                    for external_graph in graph_closure
                    if external_graph.id != candidate.id
                ],
                cross_relationships_by_target_ocg=(
                    cross_relationships_by_target_ocg
                    if candidate.id == runtime_graph.id
                    else None
                ),
                provision_portals=False,
            )
        for candidate in graph_closure:
            if candidate.id not in graph_ids_requiring_opgs:
                continue
            candidate.object_projection_graphs = build_object_projection_graphs(
                candidate,
                external_graphs=[
                    external_graph
                    for external_graph in graph_closure
                    if external_graph.id != candidate.id
                ],
                cross_relationships_by_target_ocg=(
                    cross_relationships_by_target_ocg
                    if candidate.id == runtime_graph.id
                    else None
                ),
            )

    return build_object_projection_graphs(
        runtime_graph,
        external_graphs=runtime_external_graphs,
        cross_relationships_by_target_ocg=cross_relationships_by_target_ocg,
    )


def _clone_object_config_graph_public_fields(
    graph: ObjectConfigGraph,
) -> ObjectConfigGraph:
    """Clone OCG public fields without copying runtime private/session state."""

    return ObjectConfigGraph.model_validate(
        graph.model_dump(mode="python", by_alias=False, round_trip=True)
    )


def _projection_declarations_have_portal_targets(
    *, declarations: Iterable[ObjectProjectionGraphDeclaration] | None
) -> bool:
    for declaration in declarations or ():
        for binding in declaration.object_projection_graph_bindings or ():
            if (binding.target_projection_name or "").strip():
                return True
    return False


def _derived_projection_hashes_by_id_for_index_receipt(
    *,
    graph: ObjectConfigGraph,
    external_graphs: tuple[ObjectConfigGraph, ...],
    cross_relationships_by_target_ocg: dict[UUID, list[ClassConfigRelationship]],
) -> dict[UUID, str]:
    if not graph.object_projection_graph_declarations:
        return {}
    try:
        opgs = _build_receipt_projection_graphs(
            graph=graph,
            external_graphs=external_graphs,
            cross_relationships_by_target_ocg=cross_relationships_by_target_ocg,
        )
    except Exception as exc:
        logger.warning(
            "Meta package leaf could not derive projection hashes for materialization index receipt: %s",
            exc,
        )
        return {}
    return {
        opg.id: opg.projection_hash
        for opg in opgs
        if (opg.projection_hash or "").strip()
    }


@dataclass(frozen=True, slots=True)
class _OwnedSourceFile:
    workspace_relative_path: str
    package_relative_path: str
    source_relative_path: str
    absolute_path: Path


@dataclass(frozen=True, slots=True)
class _CodePackageSourceSeedResult:
    code_package: CodePackage
    domain_commit_id: UUID


@dataclass(frozen=True, slots=True)
class _ObjectConfigGraphPackageSnapshotSeedResult:
    object_config_graph_package: ObjectConfigGraphPackage
    domain_commit_id: UUID
    object_instance_graph_commit_id: UUID
    perf_ms: Mapping[str, int]


@dataclass(frozen=True, slots=True)
class _GraphIdentityLaneSeedSpec:
    root_instance: BaseORMModel
    branch_id: UUID
    opg_name: str


@dataclass(frozen=True, slots=True)
class _CurrentIndexIdentitySeedLaneEnsureCacheEntry:
    object_config_graph_id: UUID | None
    object_config_graph_hash: str
    lane_revisions: tuple[tuple[UUID, str, int, str, str], ...]


_CURRENT_INDEX_IDENTITY_SEED_LANE_ENSURE_CACHE: dict[
    int,
    _CurrentIndexIdentitySeedLaneEnsureCacheEntry,
] = {}
_CURRENT_INDEX_IDENTITY_SEED_LANE_ENSURE_CACHE_LOCK = Lock()


@dataclass(frozen=True, slots=True)
class _SemanticLaneCommitSummary:
    commit_id: UUID | None
    head_commit_id: UUID | None
    strategy: str
    fallback_reset: bool
    phase_timings_s: Mapping[str, float]


def _semantic_lane_root_domain_commit_id(
    summary: _SemanticLaneCommitSummary,
) -> UUID | None:
    return summary.head_commit_id or summary.commit_id


def _int_env(name: str, *, default: int) -> int:
    raw = (os.getenv(name) or "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


class _NestedPhaseTimings:
    def __init__(self, target: dict[str, float], *, prefix: str) -> None:
        self._target = target
        self._prefix = prefix.strip(".")

    def add(self, name: str, duration_s: float) -> object:
        key = f"{self._prefix}.{name}" if self._prefix else name
        self._target[key] = _round_duration_s(duration_s)
        return None

    def metric(self, key: str, value: object) -> object:
        if not key:
            return None
        metric_key = f"{self._prefix}.metric.{key}" if self._prefix else f"metric.{key}"
        if isinstance(value, bool):
            self._target[metric_key] = 1.0 if value else 0.0
        elif isinstance(value, (int, float)):
            self._target[metric_key] = float(value)
        return None


def _record_perf_ms_as_phase_timings(
    *,
    phase_timings_s: dict[str, float],
    prefix: str,
    perf_ms: Mapping[str, int],
) -> None:
    normalized_prefix = prefix.strip(".")
    for metric_name, metric_value in sorted(perf_ms.items()):
        if metric_name.endswith("_ms"):
            key = f"{normalized_prefix}.{metric_name[:-3]}_s"
            phase_timings_s[key] = _round_duration_s(float(metric_value) / 1000.0)
        else:
            key = f"{normalized_prefix}.metric.{metric_name}"
            phase_timings_s[key] = float(metric_value)


def _object_instance_graph_snapshot_indexes(
    graph: ObjectInstanceGraph,
) -> dict[str, object]:
    instance_map: dict[str, str] = {}
    class_config_map: dict[str, str] = {}
    for class_instance in graph.class_instances:
        if class_instance.id is None or class_instance.class_config_id is None:
            continue
        instance_map[str(class_instance.id)] = str(class_instance.id)
        class_config_map[str(class_instance.id)] = str(class_instance.class_config_id)
    return {
        "instance_map": instance_map,
        "classcfg_map": class_config_map,
    }


def _build_object_instance_graph_from_meta_index(
    *,
    orm_model: ModelIntrospection,
    index: MetaGraphRuntimeIndex,
    object_projection_graph: ObjectProjectionGraph,
    related_models: Iterable[ModelIntrospection],
    key: str,
    name: str,
    description: str,
    oig_id: UUID,
) -> ObjectInstanceGraph:
    return build_object_instance_graph(
        root_instance=orm_model,
        object_config_graph=index.ocg,
        object_projection_graph=object_projection_graph,
        key=key,
        name=name,
        description=description,
        oig_id=oig_id,
        instance_registry=related_models,
        enum_option_resolver=default_meta_enum_option_resolver,
    )


async def _write_seed_snapshot_from_plan(
    *,
    plan: OCGSeedPlan,
    index: MetaGraphRuntimeIndex,
) -> None:
    after_oig = plan.after_oig
    opg = index.opg_by_hash.get(plan.projection_hash)
    if opg is None:
        raise RuntimeError(
            "Meta package leaf materialization missing OCG seed projection hash: "
            f"{plan.projection_hash}"
        )
    validate_object_instance_graph_against_opg(
        graph=after_oig,
        object_config_graph=index.ocg,
        object_projection_graph=opg,
    )
    snapshot_store = FSSnapshotStore()
    await snapshot_store.put(
        branch_id=plan.branch_id,
        projection_hash=plan.projection_hash,
        commit_id=plan.commit_id,
        oig=after_oig,
        indexes=_object_instance_graph_snapshot_indexes(after_oig),
    )
    snapshot_store.write_snapshot_health_metadata(
        branch_id=plan.branch_id,
        projection_hash=plan.projection_hash,
        commit_id=plan.commit_id,
        oig=after_oig,
    )


def _stable_source_content_part_text_id(
    *,
    code_package_code_id: UUID,
    relative_path: str,
) -> UUID:
    relative_path_norm = (relative_path or "").casefold().strip()
    return uuid5(
        _SOURCE_CONTENT_PART_TEXT_NAMESPACE,
        f"{code_package_code_id}:{relative_path_norm}",
    )


def _build_code_package_source_manifest_root(
    *,
    code_package_id: UUID,
    code_package_config_id: UUID,
    package_name: str,
    surface: str,
    manifest_relative_path: str,
    package_root: str,
    sources_root: str | None,
    fqn_prefix: str | None,
    source_text_by_relative_path: Mapping[str, str],
) -> tuple[CodePackage, list[BaseORMModel]]:
    with disable_autobind():
        code_package = CodePackage(
            id=code_package_id,
            code_package_config_id=code_package_config_id,
            package_name=package_name,
            language=CodeLanguage.aware,
            surface=surface,
            manifest_kind="aware_toml",
            manifest_relative_path=manifest_relative_path,
            package_root=package_root,
            sources_root=sources_root,
            fqn_prefix=fqn_prefix,
        )
        related_models: list[BaseORMModel] = []
        for relative_path, content_text in sorted(source_text_by_relative_path.items()):
            package_code_id = stable_code_package_code_id(
                code_package_id=code_package_id,
                relative_path=relative_path,
            )
            code_id = stable_code_id(
                code_package_code_id=package_code_id,
                relative_path=relative_path,
            )
            content_part_text = ContentPartText(
                id=_stable_source_content_part_text_id(
                    code_package_code_id=package_code_id,
                    relative_path=relative_path,
                ),
                key="default",
                inline_text=content_text,
            )
            code = Code(
                id=code_id,
                code_package_code_id=package_code_id,
                relative_path=relative_path,
                content_part_text=content_part_text,
                content_part_text_id=content_part_text.id,
                language=CodeLanguage.aware,
            )
            package_code = CodePackageCode(
                id=package_code_id,
                code_package_id=code_package_id,
                code=code,
                relative_path=relative_path,
                path_role=CodePackagePathRole.authored_source,
            )
            code_package.code_package_codes.append(package_code)
            related_models.extend([package_code, code, content_part_text])
    return code_package, related_models


async def _seed_code_package_sources_from_manifest(
    *,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    projection_hash: str,
    code_package_id: UUID,
    package_name: str,
    surface: str,
    manifest_relative_path: str,
    package_root: str,
    sources_root: str | None,
    fqn_prefix: str | None,
    source_text_by_relative_path: Mapping[str, str],
    actor_id: UUID | None,
    phase_timings_s: dict[str, float],
) -> _CodePackageSourceSeedResult:
    opg = index.opg_by_hash.get(projection_hash)
    if opg is None:
        raise RuntimeError(
            f"Meta package leaf materialization missing CodePackage projection hash: {projection_hash}"
        )

    with _record_phase(
        phase_timings_s, "seed_code_package_sources_from_manifest.build_root"
    ):
        code_package, related_models = _build_code_package_source_manifest_root(
            code_package_id=code_package_id,
            code_package_config_id=stable_code_package_config_id(
                config_key=code_package_source_config_key(
                    manifest_kind="aware_toml",
                    surface=surface,
                ),
            ),
            package_name=package_name,
            surface=surface,
            manifest_relative_path=manifest_relative_path,
            package_root=package_root,
            sources_root=sources_root,
            fqn_prefix=fqn_prefix,
            source_text_by_relative_path=source_text_by_relative_path,
        )
        root_instance = _ModelIntrospectionOverlay(
            source=code_package,
            values_by_name={
                "code_package_config_id": stable_code_package_config_id(
                    config_key=code_package_source_config_key(
                        manifest_kind="aware_toml",
                        surface=surface,
                    ),
                )
            },
        )

    object_instance_graph_id = stable_object_instance_graph_id(
        object_projection_graph_id=opg.id,
        key=str(branch_id),
    )
    with _record_phase(
        phase_timings_s, "seed_code_package_sources_from_manifest.build_oig"
    ):
        after_oig = _build_object_instance_graph_from_meta_index(
            orm_model=root_instance,
            index=index,
            object_projection_graph=opg,
            related_models=related_models,
            key=str(branch_id),
            name=f"OIG_{branch_id.hex[:8]}",
            description="ROOTED_BASE",
            oig_id=object_instance_graph_id,
        )
    object_instance_graph_identity_id = (
        resolve_domain_object_instance_graph_identity_id(
            index=index,
            object_instance_graph_id=object_instance_graph_id,
            domain_projection_hash=projection_hash,
        )
    )
    committer = FSLaneCommitter()
    with _record_phase(
        phase_timings_s, "seed_code_package_sources_from_manifest.commit"
    ):
        commit = await committer.commit(
            branch_id=branch_id,
            projection_hash=projection_hash,
            object_instance_graph_identity_id=object_instance_graph_identity_id,
            object_instance_graph_id=object_instance_graph_id,
            before_oig=after_oig,
            root_object_id=code_package.id,
            changes=[],
            graph_hash_pre=after_oig.hash,
            graph_hash_post=after_oig.hash,
            author_id=resolve_meta_author_id(actor_id),
            commit_action=CommitActionDescriptor(
                operation_label="CodePackage.seed_sources_from_manifest",
                call_target="meta_materialization",
                object_id=code_package.id,
            ),
        )
    _record_perf_ms_as_phase_timings(
        phase_timings_s=phase_timings_s,
        prefix="seed_code_package_sources_from_manifest.fs_commit",
        perf_ms=committer.last_commit_perf_profile_snapshot(),
    )
    if commit is None:
        raise RuntimeError(
            "Meta package leaf CodePackage source seed expected to append an initial lane commit: "
            f"branch_id={branch_id} projection_hash={projection_hash} code_package_id={code_package_id}"
        )

    with _record_phase(
        phase_timings_s, "seed_code_package_sources_from_manifest.validate_snapshot_opg"
    ):
        validate_object_instance_graph_against_opg(
            graph=after_oig,
            object_config_graph=index.ocg,
            object_projection_graph=opg,
        )
    with _record_phase(
        phase_timings_s, "seed_code_package_sources_from_manifest.write_snapshot"
    ):
        snapshot_store = FSSnapshotStore()
        await snapshot_store.put(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit.commit.id,
            oig=after_oig,
            indexes=_object_instance_graph_snapshot_indexes(after_oig),
        )
        snapshot_store.write_snapshot_health_metadata(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit.commit.id,
            oig=after_oig,
        )
    get_shared_materialization_cache().invalidate_lane(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    return _CodePackageSourceSeedResult(
        code_package=code_package,
        domain_commit_id=commit.commit.id,
    )


def _stable_object_config_graph_package_snapshot_commit_id(
    *,
    branch_id: UUID,
    projection_hash: str,
    object_config_graph_package: ObjectConfigGraphPackage,
) -> UUID:
    language_materialization_signature = (
        _object_config_graph_package_language_materialization_signature(
            object_config_graph_package=object_config_graph_package,
        )
    )
    return uuid5(
        _OBJECT_CONFIG_GRAPH_PACKAGE_SNAPSHOT_COMMIT_NAMESPACE,
        f"{branch_id}:{projection_hash}:"
        + f"{object_config_graph_package.id}:"
        + f"{object_config_graph_package.package_name}:"
        + f"{object_config_graph_package.fqn_prefix}:"
        + f"{object_config_graph_package.source_code_package_id}:"
        + f"{object_config_graph_package.object_config_graph_id}:"
        + f"{object_config_graph_package.object_config_graph_object_instance_graph_commit_id}:"
        + f"{object_config_graph_package.function_impl_ownership.value}:"
        + f"{object_config_graph_package.function_impl_parity_policy.value}:"
        + f"{object_config_graph_package.implementation_policy_source}:"
        + f"{object_config_graph_package.title or ''}:"
        + f"{object_config_graph_package.description or ''}:"
        + language_materialization_signature,
    )


def _object_config_graph_package_language_materialization_signature(
    *,
    object_config_graph_package: ObjectConfigGraphPackage,
) -> str:
    parts: list[str] = []
    for target in sorted(
        object_config_graph_package.language_materializations,
        key=lambda item: (item.target_key, item.role, item.package_name),
    ):
        package_parts = []
        for package in sorted(
            target.materialized_packages,
            key=lambda item: (str(item.code_package_id), item.package_name),
        ):
            package_parts.append(
                "|".join(
                    (
                        str(package.code_package_id),
                        package.package_output_key,
                        package.package_name,
                        package.language.value,
                        package.output_dir,
                        package.package_root,
                        package.sources_root or "",
                        package.import_root or "",
                        package.materialization_source,
                        package.renderer_kind or "",
                        package.renderer_profile or "",
                        str(
                            package.object_config_graph_object_instance_graph_commit_id
                            or ""
                        ),
                        str(package.code_package_object_instance_graph_commit_id or ""),
                        package.status,
                    )
                )
            )
        parts.append(
            "|".join(
                (
                    target.target_key,
                    target.role,
                    target.language.value,
                    target.output_dir,
                    target.import_root,
                    target.package_name,
                    target.materialization_source,
                    target.renderer_kind or "",
                    target.renderer_profile or "",
                    target.stable_ids_import_root or "",
                    str(target.source_is_runtime),
                    ";".join(package_parts),
                )
            )
        )
    return "||".join(parts)


def _object_config_graph_package_language_materialization_manifest_signature(
    *,
    object_config_graph_package: ObjectConfigGraphPackage,
) -> str:
    parts: list[str] = []
    for target in object_config_graph_package.language_materializations:
        parts.append(
            "|".join(
                (
                    target.role,
                    target.language.value,
                    target.output_dir,
                    target.import_root,
                    target.package_name,
                    target.materialization_source,
                    target.renderer_kind or "",
                    target.renderer_profile or "",
                    target.stable_ids_import_root or "",
                    str(target.source_is_runtime),
                )
            )
        )
    return "||".join(sorted(parts))


def _object_config_graph_package_function_impl_ownership(
    value: str,
) -> ObjectConfigGraphPackageFunctionImplOwnership:
    try:
        return ObjectConfigGraphPackageFunctionImplOwnership(value)
    except ValueError as exc:
        raise ValueError(
            f"Unsupported ObjectConfigGraphPackage.function_impl_ownership: {value!r}"
        ) from exc


def _object_config_graph_package_function_impl_parity_policy(
    value: str,
) -> ObjectConfigGraphPackageFunctionImplParityPolicy:
    try:
        return ObjectConfigGraphPackageFunctionImplParityPolicy(value)
    except ValueError as exc:
        raise ValueError(
            f"Unsupported ObjectConfigGraphPackage.function_impl_parity_policy: {value!r}"
        ) from exc


def _build_object_config_graph_package_snapshot_root(
    *,
    object_config_graph_package_id: UUID,
    package_name: str,
    fqn_prefix: str,
    source_code_package_id: UUID,
    object_config_graph_id: UUID,
    object_config_graph_object_instance_graph_commit_id: UUID,
    function_impl_ownership: str,
    function_impl_parity_policy: str,
    implementation_policy_source: str,
    title: str | None,
    description: str | None,
    language_materialization_specs: Iterable[object],
    package_root: Path | None,
    workspace_root: Path | None,
    language_materialization_package_realizations: (
        Mapping[UUID, Mapping[str, object]] | None
    ) = None,
) -> tuple[ObjectConfigGraphPackage, list[BaseORMModel]]:
    object_config_graph_package = ObjectConfigGraphPackage.model_construct(
        id=object_config_graph_package_id,
        source_code_package=None,
        object_config_graph=None,
        object_config_graph_object_instance_graph_commit=None,
        dependencies=[],
        language_materializations=[],
        package_name=(package_name or "").strip(),
        fqn_prefix=(fqn_prefix or "").strip(),
        title=(title or "").strip() or None,
        description=(description or "").strip() or None,
        source_code_package_id=source_code_package_id,
        object_config_graph_id=object_config_graph_id,
        object_config_graph_object_instance_graph_commit_id=(
            object_config_graph_object_instance_graph_commit_id
        ),
        function_impl_ownership=(
            _object_config_graph_package_function_impl_ownership(
                function_impl_ownership,
            )
        ),
        function_impl_parity_policy=(
            _object_config_graph_package_function_impl_parity_policy(
                function_impl_parity_policy,
            )
        ),
        implementation_policy_source=(
            (implementation_policy_source or "").strip() or "aware_toml"
        ),
    )
    related_models = _object_config_graph_package_language_materialization_models(
        object_config_graph_package_id=object_config_graph_package_id,
        package_name=package_name,
        object_config_graph_object_instance_graph_commit_id=(
            object_config_graph_object_instance_graph_commit_id
        ),
        language_materialization_specs=language_materialization_specs,
        package_root=package_root,
        workspace_root=workspace_root,
        language_materialization_package_realizations=(
            language_materialization_package_realizations or {}
        ),
    )
    object_config_graph_package.language_materializations.extend(
        item
        for item in related_models
        if isinstance(item, ObjectConfigGraphPackageLanguageMaterialization)
    )
    return object_config_graph_package, related_models


def _object_config_graph_package_language_materialization_models(
    *,
    object_config_graph_package_id: UUID,
    package_name: str,
    object_config_graph_object_instance_graph_commit_id: UUID,
    language_materialization_specs: Iterable[object],
    package_root: Path | None,
    workspace_root: Path | None,
    language_materialization_package_realizations: Mapping[UUID, Mapping[str, object]],
) -> list[BaseORMModel]:
    related_models: list[BaseORMModel] = []
    for target in language_materialization_specs:
        role = str(getattr(target, "role", "") or "").strip()
        if not role:
            continue
        language = _code_language_from_manifest_value(getattr(target, "language"))
        target_key = _language_materialization_target_key(
            package_name=package_name,
            role=role,
        )
        target_id = stable_object_config_graph_package_language_materialization_id(
            target_key=target_key,
        )
        generated_package_name = str(getattr(target, "package_name")).strip()
        materialization_source = (
            str(getattr(target, "materialization_source", "ontology")).strip()
            or "ontology"
        )
        renderer_kind = _optional_str(getattr(target, "renderer_kind", None))
        generated_manifest_kind = _language_materialization_manifest_kind(
            language=language,
        )
        generated_surface = _language_materialization_code_package_surface(
            materialization_source=materialization_source,
        )
        generated_code_package_config_id = stable_code_package_config_id(
            config_key=code_package_generated_config_key(
                materialization_source=materialization_source,
                renderer_kind=renderer_kind,
                language=language,
                surface=generated_surface,
                manifest_kind=generated_manifest_kind,
            ),
        )
        declared_code_package_id = stable_code_package_id(
            code_package_config_id=generated_code_package_config_id,
            package_name=generated_package_name,
            language=language.value,
        )
        realization = language_materialization_package_realizations.get(
            declared_code_package_id,
            {},
        )
        generated_code_package_id = (
            _payload_uuid(realization, "code_package_id") or declared_code_package_id
        )
        output_dir = str(getattr(target, "output_dir")).strip()
        generated_package_root = _language_materialization_package_root_payload(
            package_root=package_root,
            workspace_root=workspace_root,
            output_dir=output_dir,
        )
        materialization = ObjectConfigGraphPackageLanguageMaterialization(
            id=target_id,
            object_config_graph_package_id=object_config_graph_package_id,
            target_key=target_key,
            role=role,
            language=language,
            output_dir=output_dir,
            import_root=str(getattr(target, "import_root")).strip(),
            package_name=generated_package_name,
            materialization_source=materialization_source,
            renderer_kind=renderer_kind,
            renderer_profile=_optional_str(getattr(target, "renderer_profile", None)),
            stable_ids_import_root=_optional_str(
                getattr(target, "stable_ids_import_root", None)
            ),
            stable_ids_resolution_policy=_optional_str(
                getattr(target, "stable_ids_resolution_policy", None)
            ),
            source_is_runtime=bool(getattr(target, "source_is_runtime", False)),
        )
        materialized_package = ObjectConfigGraphPackageLanguageMaterializationPackage(
            id=stable_object_config_graph_package_language_materialization_package_id(
                code_package_id=generated_code_package_id,
            ),
            object_config_graph_package_language_materialization_id=target_id,
            code_package_id=generated_code_package_id,
            package_output_key="language_package",
            package_name=(
                _payload_string(realization, "package_name") or generated_package_name
            ),
            language=language,
            output_dir=output_dir,
            package_root=(
                _payload_string(realization, "package_root") or generated_package_root
            ),
            sources_root=(
                _payload_string(realization, "sources_root")
                or _language_materialization_sources_root_payload(
                    language=language,
                    import_root=materialization.import_root,
                )
            ),
            import_root=(
                _payload_string(realization, "import_root")
                or materialization.import_root
            ),
            materialization_source=materialization.materialization_source,
            renderer_kind=materialization.renderer_kind,
            renderer_profile=materialization.renderer_profile,
            object_config_graph_object_instance_graph_commit_id=(
                _payload_uuid(
                    realization,
                    "object_config_graph_object_instance_graph_commit_id",
                )
                or object_config_graph_object_instance_graph_commit_id
            ),
            code_package_object_instance_graph_commit_id=(
                _payload_uuid(
                    realization,
                    "code_package_object_instance_graph_commit_id",
                )
            ),
            status=("materialized" if realization else "declared"),
        )
        materialization.materialized_packages.append(materialized_package)
        related_models.extend([materialization, materialized_package])
    return related_models


def _language_materialization_target_key(*, package_name: str, role: str) -> str:
    return f"{package_name}:{role}"


def _language_materialization_code_package_surface(
    *,
    materialization_source: str,
) -> str:
    normalized = (materialization_source or "").casefold().strip()
    if normalized == "api":
        return "api"
    if normalized in {"sdk", "ontology_dto"}:
        return "sdk"
    if normalized == "runtime_handlers":
        return "runtime"
    if normalized in {"ontology", "ontology_orm_models"}:
        return "structure"
    return "runtime"


def _language_materialization_manifest_kind(
    *,
    language: CodeLanguage,
) -> str:
    if language == CodeLanguage.python:
        return "pyproject_toml"
    if language == CodeLanguage.dart:
        return "pubspec_yaml"
    return "generated_materialization"


def _language_materialization_specs_signature(
    *,
    language_materialization_specs: Iterable[object],
) -> str:
    parts: list[str] = []
    for target in language_materialization_specs:
        parts.append(
            "|".join(
                (
                    str(getattr(target, "role", "") or "").strip(),
                    str(getattr(target, "language", "") or "").strip(),
                    str(getattr(target, "output_dir", "") or "").strip(),
                    str(getattr(target, "import_root", "") or "").strip(),
                    str(getattr(target, "package_name", "") or "").strip(),
                    str(
                        getattr(target, "materialization_source", "ontology") or ""
                    ).strip(),
                    str(getattr(target, "renderer_kind", "") or "").strip(),
                    str(getattr(target, "renderer_profile", "") or "").strip(),
                    str(getattr(target, "stable_ids_import_root", "") or "").strip(),
                    str(
                        getattr(target, "stable_ids_resolution_policy", "") or ""
                    ).strip(),
                    str(bool(getattr(target, "source_is_runtime", False))),
                )
            )
        )
    return "||".join(sorted(parts))


def _code_language_from_manifest_value(value: object) -> CodeLanguage:
    raw_value = getattr(value, "value", value)
    return CodeLanguage(str(raw_value))


def _language_materialization_package_root_payload(
    *,
    package_root: Path | None,
    workspace_root: Path | None,
    output_dir: str,
) -> str:
    if package_root is None:
        return output_dir
    output_root = package_root / output_dir
    if workspace_root is not None:
        try:
            return (
                output_root.resolve().relative_to(workspace_root.resolve()).as_posix()
            )
        except ValueError:
            pass
    return output_root.as_posix()


def _language_materialization_sources_root_payload(
    *,
    language: CodeLanguage,
    import_root: str | None,
) -> str | None:
    normalized_import_root = (import_root or "").strip()
    if language is CodeLanguage.python and normalized_import_root:
        return normalized_import_root
    return None


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    stripped = str(value).strip()
    return stripped or None


async def _seed_object_config_graph_package_snapshot(
    *,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    projection_hash: str,
    object_config_graph_package_id: UUID,
    package_name: str,
    fqn_prefix: str,
    source_code_package_id: UUID,
    object_config_graph_id: UUID,
    object_config_graph_object_instance_graph_commit_id: UUID,
    function_impl_ownership: str,
    function_impl_parity_policy: str,
    implementation_policy_source: str,
    title: str | None,
    description: str | None,
    language_materialization_specs: Iterable[object] = (),
    package_root: Path | None = None,
    workspace_root: Path | None = None,
    actor_id: UUID | None,
    phase_timings_s: dict[str, float],
) -> _ObjectConfigGraphPackageSnapshotSeedResult:
    opg = index.opg_by_hash.get(projection_hash)
    if opg is None:
        raise RuntimeError(
            "Meta package leaf materialization missing ObjectConfigGraphPackage "
            f"projection hash: {projection_hash}"
        )

    with _record_phase(
        phase_timings_s,
        "seed_object_config_graph_package_snapshot.build_root",
    ):
        (
            object_config_graph_package,
            related_models,
        ) = _build_object_config_graph_package_snapshot_root(
            object_config_graph_package_id=object_config_graph_package_id,
            package_name=package_name,
            fqn_prefix=fqn_prefix,
            source_code_package_id=source_code_package_id,
            object_config_graph_id=object_config_graph_id,
            object_config_graph_object_instance_graph_commit_id=(
                object_config_graph_object_instance_graph_commit_id
            ),
            function_impl_ownership=function_impl_ownership,
            function_impl_parity_policy=function_impl_parity_policy,
            implementation_policy_source=implementation_policy_source,
            title=title,
            description=description,
            language_materialization_specs=language_materialization_specs,
            package_root=package_root,
            workspace_root=workspace_root,
        )

    object_instance_graph_id = stable_object_instance_graph_id(
        object_projection_graph_id=opg.id,
        key=str(branch_id),
    )
    with _record_phase(
        phase_timings_s,
        "seed_object_config_graph_package_snapshot.build_oig",
    ):
        after_oig = _build_object_instance_graph_from_meta_index(
            orm_model=object_config_graph_package,
            index=index,
            object_projection_graph=opg,
            related_models=related_models,
            key=str(branch_id),
            name=f"OIG_{branch_id.hex[:8]}",
            description="ROOTED_BASE",
            oig_id=object_instance_graph_id,
        )
    object_instance_graph_identity_id = (
        resolve_domain_object_instance_graph_identity_id(
            index=index,
            object_instance_graph_id=object_instance_graph_id,
            domain_projection_hash=projection_hash,
        )
    )
    committer = FSLaneCommitter()
    with _record_phase(
        phase_timings_s,
        "seed_object_config_graph_package_snapshot.commit",
    ):
        commit = await committer.commit(
            branch_id=branch_id,
            projection_hash=projection_hash,
            object_instance_graph_identity_id=object_instance_graph_identity_id,
            object_instance_graph_id=object_instance_graph_id,
            before_oig=after_oig,
            root_object_id=object_config_graph_package.id,
            changes=[],
            graph_hash_pre=after_oig.hash,
            graph_hash_post=after_oig.hash,
            author_id=resolve_meta_author_id(actor_id),
            commit_id=_stable_object_config_graph_package_snapshot_commit_id(
                branch_id=branch_id,
                projection_hash=projection_hash,
                object_config_graph_package=object_config_graph_package,
            ),
            commit_action=CommitActionDescriptor(
                operation_label="ObjectConfigGraphPackage.seed_snapshot",
                call_target="meta_materialization",
                object_id=object_config_graph_package.id,
            ),
        )
    perf_ms = committer.last_commit_perf_profile_snapshot()
    _record_perf_ms_as_phase_timings(
        phase_timings_s=phase_timings_s,
        prefix="seed_object_config_graph_package_snapshot.fs_commit",
        perf_ms=perf_ms,
    )
    if commit is None:
        raise RuntimeError(
            "Meta package leaf ObjectConfigGraphPackage snapshot expected to append "
            "an initial lane commit: "
            f"branch_id={branch_id} projection_hash={projection_hash} "
            f"object_config_graph_package_id={object_config_graph_package_id}"
        )

    with _record_phase(
        phase_timings_s,
        "seed_object_config_graph_package_snapshot.validate_snapshot_opg",
    ):
        validate_object_instance_graph_against_opg(
            graph=after_oig,
            object_config_graph=index.ocg,
            object_projection_graph=opg,
        )
    with _record_phase(
        phase_timings_s,
        "seed_object_config_graph_package_snapshot.write_snapshot",
    ):
        snapshot_store = FSSnapshotStore()
        await snapshot_store.put(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit.commit.id,
            oig=after_oig,
            indexes=_object_instance_graph_snapshot_indexes(after_oig),
        )
        snapshot_store.write_snapshot_health_metadata(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit.commit.id,
            oig=after_oig,
        )
    get_shared_materialization_cache().invalidate_lane(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    return _ObjectConfigGraphPackageSnapshotSeedResult(
        object_config_graph_package=object_config_graph_package,
        domain_commit_id=commit.commit.id,
        object_instance_graph_commit_id=stable_object_instance_graph_commit_id(
            object_instance_graph_identity_id=commit.object_instance_graph_identity_id,
            commit_id=commit.commit.id,
        ),
        perf_ms=perf_ms,
    )


async def realize_object_config_graph_package_language_materialization_packages(
    *,
    result: ObjectConfigGraphPackageLeafMaterializationResult,
    index: MetaGraphRuntimeIndex,
    object_config_graph_package_projection_hash: str,
    generated_code_package_refs: Iterable[Mapping[str, object]],
    workspace_root: Path | None,
    actor_id: UUID | None,
) -> ObjectConfigGraphPackageLeafMaterializationResult:
    """Commit realized generated CodePackage refs back into the Meta package row."""
    realizations = _language_materialization_package_realizations_by_code_package_id(
        generated_code_package_refs=generated_code_package_refs,
        object_config_graph_package_id=result.object_config_graph_package.id,
    )
    if not realizations:
        return result
    realization_count = _language_materialization_package_realization_count(
        realizations
    )

    opg = index.opg_by_hash.get(object_config_graph_package_projection_hash)
    if opg is None:
        raise RuntimeError(
            "Meta package language materialization realization missing "
            "ObjectConfigGraphPackage projection hash: "
            f"{object_config_graph_package_projection_hash}"
        )

    phase_timings_s = dict(result.phase_timings_s)
    started_at = perf_counter()
    with _record_phase(
        phase_timings_s,
        "realize_object_config_graph_package_language_materialization_packages.materialize_head",
    ):
        before_oig, _ = await CachedLaneMaterializer().get(
            branch_id=result.package_branch_id,
            ocg=index.ocg,
            opg=opg,
            commit_id=None,
            attribute_configs_by_id=index.attribute_configs_by_id,
            class_configs_by_id=index.class_configs_by_id,
        )
    object_instance_graph_id = before_oig.id or stable_object_instance_graph_id(
        object_projection_graph_id=opg.id,
        key=str(result.package_branch_id),
    )
    (
        object_config_graph_package,
        related_models,
    ) = _build_object_config_graph_package_snapshot_root(
        object_config_graph_package_id=result.object_config_graph_package.id,
        package_name=result.object_config_graph_package.package_name,
        fqn_prefix=result.object_config_graph_package.fqn_prefix,
        source_code_package_id=result.code_package.id,
        object_config_graph_id=result.object_config_graph.id,
        object_config_graph_object_instance_graph_commit_id=(
            result.object_config_graph_object_instance_graph_commit_id
        ),
        function_impl_ownership=(
            result.object_config_graph_package.function_impl_ownership.value
        ),
        function_impl_parity_policy=(
            result.object_config_graph_package.function_impl_parity_policy.value
        ),
        implementation_policy_source=(
            result.object_config_graph_package.implementation_policy_source
        ),
        title=result.object_config_graph_package.title,
        description=result.object_config_graph_package.description,
        language_materialization_specs=(
            result.object_config_graph_package.language_materializations
        ),
        package_root=result.aware_toml_path.parent,
        workspace_root=workspace_root,
        language_materialization_package_realizations=realizations,
    )
    with _record_phase(
        phase_timings_s,
        "realize_object_config_graph_package_language_materialization_packages.build_oig",
    ):
        after_oig = _build_object_instance_graph_from_meta_index(
            orm_model=object_config_graph_package,
            index=index,
            object_projection_graph=opg,
            related_models=related_models,
            key=str(result.package_branch_id),
            name=f"OIG_{result.package_branch_id.hex[:8]}",
            description="LANGUAGE_MATERIALIZATION_REALIZED",
            oig_id=object_instance_graph_id,
        )
    object_instance_graph_identity_id = (
        resolve_domain_object_instance_graph_identity_id(
            index=index,
            object_instance_graph_id=object_instance_graph_id,
            domain_projection_hash=object_config_graph_package_projection_hash,
        )
    )
    with _record_phase(
        phase_timings_s,
        "realize_object_config_graph_package_language_materialization_packages.diff",
    ):
        changes = diff_object_instance_graph_changes(
            before_oig,
            after_oig,
            object_instance_graph_identity_id=object_instance_graph_identity_id,
        )
    if not changes:
        return result

    committer = FSLaneCommitter()
    with _record_phase(
        phase_timings_s,
        "realize_object_config_graph_package_language_materialization_packages.commit",
    ):
        commit = await committer.commit(
            branch_id=result.package_branch_id,
            projection_hash=object_config_graph_package_projection_hash,
            object_instance_graph_identity_id=object_instance_graph_identity_id,
            object_instance_graph_id=object_instance_graph_id,
            before_oig=before_oig,
            root_object_id=object_config_graph_package.id,
            changes=changes,
            graph_hash_pre=before_oig.hash,
            graph_hash_post=after_oig.hash,
            author_id=resolve_meta_author_id(actor_id),
            commit_id=_stable_object_config_graph_package_snapshot_commit_id(
                branch_id=result.package_branch_id,
                projection_hash=object_config_graph_package_projection_hash,
                object_config_graph_package=object_config_graph_package,
            ),
            commit_action=CommitActionDescriptor(
                operation_label=(
                    "ObjectConfigGraphPackage.language_materialization_package_realize"
                ),
                call_target="meta_materialization",
                object_id=object_config_graph_package.id,
            ),
        )
    perf_ms = committer.last_commit_perf_profile_snapshot()
    _record_perf_ms_as_phase_timings(
        phase_timings_s=phase_timings_s,
        prefix=(
            "realize_object_config_graph_package_language_materialization_packages"
            ".fs_commit"
        ),
        perf_ms=perf_ms,
    )
    if commit is None:
        return result

    with _record_phase(
        phase_timings_s,
        "realize_object_config_graph_package_language_materialization_packages.validate_snapshot_opg",
    ):
        validate_object_instance_graph_against_opg(
            graph=after_oig,
            object_config_graph=index.ocg,
            object_projection_graph=opg,
        )
    with _record_phase(
        phase_timings_s,
        "realize_object_config_graph_package_language_materialization_packages.write_snapshot",
    ):
        snapshot_store = FSSnapshotStore()
        await snapshot_store.put(
            branch_id=result.package_branch_id,
            projection_hash=object_config_graph_package_projection_hash,
            commit_id=commit.commit.id,
            oig=after_oig,
            indexes=_object_instance_graph_snapshot_indexes(after_oig),
        )
        snapshot_store.write_snapshot_health_metadata(
            branch_id=result.package_branch_id,
            projection_hash=object_config_graph_package_projection_hash,
            commit_id=commit.commit.id,
            oig=after_oig,
        )
    get_shared_materialization_cache().invalidate_lane(
        branch_id=result.package_branch_id,
        projection_hash=object_config_graph_package_projection_hash,
    )
    object_config_graph_package.source_code_package = result.code_package
    object_config_graph_package.source_code_package_id = result.code_package.id
    object_config_graph_package.object_config_graph = result.object_config_graph
    object_config_graph_package.object_config_graph_id = result.object_config_graph.id
    object_config_graph_package.object_config_graph_object_instance_graph_commit_id = (
        result.object_config_graph_object_instance_graph_commit_id
    )
    object_config_graph_package_oig_commit_id = stable_object_instance_graph_commit_id(
        object_instance_graph_identity_id=commit.object_instance_graph_identity_id,
        commit_id=commit.commit.id,
    )
    phase_timings_s[
        "realize_object_config_graph_package_language_materialization_packages.total"
    ] = _round_duration_s(perf_counter() - started_at)
    materialization_index_receipt = _materialization_index_receipt_with_realization(
        receipt=result.materialization_index_receipt,
        object_config_graph_package_head_commit_id=commit.commit.id,
        object_config_graph_package_object_instance_graph_commit_id=(
            object_config_graph_package_oig_commit_id
        ),
        realization_count=realization_count,
    )
    return replace(
        result,
        object_config_graph_package=object_config_graph_package,
        object_config_graph_package_commit_id=commit.commit.id,
        object_config_graph_package_head_commit_id=commit.commit.id,
        object_config_graph_package_object_instance_graph_commit_id=(
            object_config_graph_package_oig_commit_id
        ),
        phase_timings_s=dict(sorted(phase_timings_s.items())),
        materialization_index_receipt=materialization_index_receipt,
    )


def _language_materialization_package_realizations_by_code_package_id(
    *,
    generated_code_package_refs: Iterable[Mapping[str, object]],
    object_config_graph_package_id: UUID,
) -> dict[UUID, Mapping[str, object]]:
    realizations: dict[UUID, Mapping[str, object]] = {}
    for ref in generated_code_package_refs:
        if (
            ref.get("schema")
            != "aware.meta.language_materialization.code_package_ref.v1"
        ):
            continue
        if (
            _payload_uuid(ref, "object_config_graph_package_id")
            != object_config_graph_package_id
        ):
            continue
        code_package_id = _payload_uuid(ref, "code_package_id")
        code_package_oig_commit_id = _payload_uuid(
            ref,
            "code_package_object_instance_graph_commit_id",
        )
        if code_package_id is None or code_package_oig_commit_id is None:
            continue
        realization = dict(ref)
        realizations[code_package_id] = realization
        declared_code_package_id = _payload_uuid(ref, "declared_code_package_id")
        if declared_code_package_id is not None:
            realizations[declared_code_package_id] = realization
    return realizations


def _language_materialization_package_realization_count(
    realizations: Mapping[UUID, Mapping[str, object]],
) -> int:
    code_package_ids = {
        code_package_id
        for realization in realizations.values()
        if (code_package_id := _payload_uuid(realization, "code_package_id"))
        is not None
    }
    return len(code_package_ids) if code_package_ids else len(realizations)


def _materialization_index_receipt_with_realization(
    *,
    receipt: Mapping[str, object] | None,
    object_config_graph_package_head_commit_id: UUID,
    object_config_graph_package_object_instance_graph_commit_id: UUID,
    realization_count: int,
) -> Mapping[str, object] | None:
    if receipt is None:
        return None
    payload = dict(receipt)
    semantic = dict(payload.get("semantic") or {})
    semantic["object_config_graph_package_head_commit_id"] = str(
        object_config_graph_package_head_commit_id
    )
    semantic["object_config_graph_package_object_instance_graph_commit_id"] = str(
        object_config_graph_package_object_instance_graph_commit_id
    )
    payload["semantic"] = semantic
    payload["language_materialization_package_realization"] = {
        "schema": (
            "aware.meta.object_config_graph_package."
            "language_materialization_package_realization.v1"
        ),
        "status": "materialized",
        "realization_count": realization_count,
        "object_config_graph_package_head_commit_id": str(
            object_config_graph_package_head_commit_id
        ),
        "object_config_graph_package_object_instance_graph_commit_id": str(
            object_config_graph_package_object_instance_graph_commit_id
        ),
    }
    return payload


def _round_duration_s(duration_s: float) -> float:
    return round(max(duration_s, 0.0), 6)


@contextmanager
def _record_phase(
    phase_timings_s: dict[str, float],
    phase_name: str,
) -> Iterator[None]:
    started_at = perf_counter()
    try:
        yield
    finally:
        phase_timings_s[phase_name] = _round_duration_s(perf_counter() - started_at)


@contextmanager
def _maybe_record_phase(
    phase_timings_s: dict[str, float] | None,
    phase_name: str,
) -> Iterator[None]:
    if phase_timings_s is None:
        yield
        return
    with _record_phase(phase_timings_s, phase_name):
        yield


@asynccontextmanager
async def _record_leaf_package_subphase(
    phase_timings_s: dict[str, float],
    phase_name: str,
    progress_callback: MetaLeafPackageProgressCallback | None,
    *,
    detail_payload: Mapping[str, object] | None = None,
) -> AsyncIterator[None]:
    if progress_callback is None:
        with _record_phase(phase_timings_s, phase_name):
            yield
        return

    started_at = perf_counter()
    await _emit_leaf_package_subphase_progress(
        progress_callback=progress_callback,
        subphase_name=phase_name,
        status="running",
        detail_payload=detail_payload,
    )
    try:
        yield
    except Exception as exc:
        duration_s = _round_duration_s(perf_counter() - started_at)
        phase_timings_s[phase_name] = duration_s
        failed_detail = dict(detail_payload or {})
        failed_detail["error_type"] = type(exc).__name__
        await _emit_leaf_package_subphase_progress(
            progress_callback=progress_callback,
            subphase_name=phase_name,
            status="failed",
            duration_s=duration_s,
            error=str(exc),
            detail_payload=failed_detail,
        )
        raise
    else:
        duration_s = _round_duration_s(perf_counter() - started_at)
        phase_timings_s[phase_name] = duration_s
        await _emit_leaf_package_subphase_progress(
            progress_callback=progress_callback,
            subphase_name=phase_name,
            status="succeeded",
            duration_s=duration_s,
            detail_payload=detail_payload,
        )


async def _emit_leaf_package_subphase_progress(
    *,
    progress_callback: MetaLeafPackageProgressCallback,
    subphase_name: str,
    status: str,
    duration_s: float | None = None,
    error: str | None = None,
    detail_payload: Mapping[str, object] | None = None,
) -> None:
    detail = dict(detail_payload or {})
    detail["subphase_name"] = subphase_name
    payload: dict[str, object] = {
        "phase_name": "meta.leaf_package.subphase",
        "status": status,
        "detail_payload": detail,
    }
    if duration_s is not None and status != "running":
        payload["duration_s"] = _round_duration_s(duration_s)
    if error:
        payload["error"] = error
    try:
        result = progress_callback(payload)
        if isawaitable(result):
            await result
    except Exception:
        return


async def materialize_object_config_graph_package_leaf_from_manifest(
    *,
    runtime: object,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    branch_id: UUID,
    workspace_root: Path,
    aware_toml_path: Path,
    package_branch_id: UUID | None = None,
    external_graphs: list[ObjectConfigGraph] | None = None,
    source_code_package_id: UUID | None = None,
    object_config_graph_package_id: UUID | None = None,
    collect_telemetry: bool = True,
    force_fresh_semantic_materialization: bool = False,
    progress_callback: MetaLeafPackageProgressCallback | None = None,
) -> ObjectConfigGraphPackageLeafMaterializationResult:
    package_started_at = perf_counter()
    phase_timings_s: dict[str, float] = {}
    code_package_build_runtime_telemetry: dict[str, object] = {}
    code_package_build_invoke_perf_ms: dict[str, int] = {}
    code_package_upsert_runtime_telemetry: dict[str, object] = {}
    code_package_upsert_invoke_perf_ms: dict[str, int] = {}
    _setup_meta_materialization_language_plugins()
    workspace_root = workspace_root.resolve()
    aware_toml_path = aware_toml_path.resolve()
    with _record_phase(phase_timings_s, "load_aware_toml_spec"):
        spec = load_aware_toml_spec(toml_path=aware_toml_path)
    external_graphs = [
        graph
        for graph in external_graphs or []
        if graph.fqn_prefix != spec.package.fqn_prefix
    ]

    with _record_phase(phase_timings_s, "resolve_module_root"):
        module_root = _find_module_root(
            aware_toml_path=aware_toml_path,
            workspace_root=workspace_root,
        )
    package_root = aware_toml_path.parent.resolve()
    sources_root = (package_root / spec.build.sources_dir).resolve()

    manifest_relative_path = _relative_to(
        path=aware_toml_path,
        root=workspace_root,
        label="aware.toml",
    )
    package_root_relative = _relative_to(
        path=package_root,
        root=workspace_root,
        label="package_root",
    )
    sources_root_relative = _relative_to(
        path=sources_root,
        root=workspace_root,
        label="sources_root",
    )
    surface = _object_config_graph_code_package_surface_for_kind(spec.package.kind)
    with _record_phase(phase_timings_s, "discover_owned_source_files"):
        owned_source_files = _discover_owned_source_files(
            workspace_root=workspace_root,
            sources_root=sources_root,
            include_paths=tuple(spec.build.include_paths),
            exclude_paths=tuple(spec.build.exclude_paths),
            package_root=package_root,
        )
    if not owned_source_files:
        raise RuntimeError(
            "ObjectConfigGraph package materialization requires at least one owned `.aware` source file: "
            f"aware_toml_path={aware_toml_path}"
        )

    source_code_package_config_id = stable_code_package_config_id(
        config_key=code_package_source_config_key(
            manifest_kind="aware_toml",
            surface=surface,
        ),
    )
    resolved_source_code_package_id = source_code_package_id or stable_code_package_id(
        code_package_config_id=source_code_package_config_id,
        package_name=spec.package.package_name,
        language=CodeLanguage.aware.value,
    )
    resolved_object_config_graph_package_id = (
        object_config_graph_package_id
        or stable_object_config_graph_package_id(
            package_name=spec.package.package_name,
            fqn_prefix=spec.package.fqn_prefix,
        )
    )
    resolved_object_config_graph_id = stable_object_config_graph_id(
        fqn_prefix=spec.package.fqn_prefix,
        language=CodeLanguage.aware.value,
    )
    resolved_package_branch_id = (
        package_branch_id
        or stable_object_config_graph_package_branch_id(
            workspace_root=workspace_root,
            aware_toml_path=aware_toml_path,
            package_name=spec.package.package_name,
            fqn_prefix=spec.package.fqn_prefix,
        )
    )
    if package_branch_id is not None:
        expected_package_branch_id = stable_object_config_graph_package_branch_id(
            workspace_root=workspace_root,
            aware_toml_path=aware_toml_path,
            package_name=spec.package.package_name,
            fqn_prefix=spec.package.fqn_prefix,
        )
        if package_branch_id != expected_package_branch_id:
            raise RuntimeError(
                "Meta ObjectConfigGraph package materialization received an explicit "
                "package branch id that does not match the Meta-owned package lane "
                "identity: "
                f"aware_toml_path={aware_toml_path} package_name={spec.package.package_name!r} "
                f"fqn_prefix={spec.package.fqn_prefix!r} "
                f"received={package_branch_id} expected={expected_package_branch_id}"
            )

    package_branch_id = resolved_package_branch_id

    phase_timings_s["package_branch_resolution"] = 0.0

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
    source_text_by_relative_path: dict[str, str] = {}
    with _record_phase(phase_timings_s, "read_owned_source_texts"):
        for owned_source in owned_source_files:
            relative_path = owned_source.source_relative_path
            content_text = owned_source.absolute_path.read_text(encoding="utf-8")
            source_text_by_relative_path[relative_path] = content_text
    source_manifest_hash = _source_text_manifest_hash(
        source_text_by_relative_path=source_text_by_relative_path,
    )
    dependency_signature = _external_graph_signature(
        external_graphs=tuple(external_graphs or ()),
    )

    leaf_detail = {
        "package_name": spec.package.package_name,
        "fqn_prefix": spec.package.fqn_prefix,
        "aware_toml_path": manifest_relative_path,
        "owned_source_file_count": len(owned_source_files),
    }

    async with _record_leaf_package_subphase(
        phase_timings_s,
        "reset_invalid_package_branch_if_needed",
        progress_callback,
        detail_payload=leaf_detail,
    ):
        await _reset_invalid_package_branch_if_needed(
            index=index,
            branch_id=package_branch_id,
            projection_hashes=(
                code_package_projection_hash,
                object_config_graph_projection_hash,
                object_config_graph_package_projection_hash,
            ),
            phase_timings_s=phase_timings_s,
        )

    async with _record_leaf_package_subphase(
        phase_timings_s,
        "object_config_graph_package_cache_lookup",
        progress_callback,
        detail_payload=leaf_detail,
    ):
        if force_fresh_semantic_materialization:
            cached_result = None
            phase_timings_s["reuse_existing_object_config_graph_package_cache"] = 0.0
            phase_timings_s[
                "reuse_existing_object_config_graph_package_cache.bypass.force_fresh_semantic_materialization"
            ] = 0.0
            logger.info(
                "Meta package leaf ObjectConfigGraphPackage fingerprint cache "
                "bypassed: package=%s reason=force_fresh_semantic_materialization",
                spec.package.package_name,
            )
        else:
            cached_result = await _try_reuse_existing_object_config_graph_package_cache(
                index=index,
                branch_id=package_branch_id,
                code_package_projection_hash=code_package_projection_hash,
                object_config_graph_projection_hash=object_config_graph_projection_hash,
                object_config_graph_package_projection_hash=object_config_graph_package_projection_hash,
                aware_toml_path=aware_toml_path,
                source_manifest_hash=source_manifest_hash,
                dependency_signature=dependency_signature,
                resolved_source_code_package_id=resolved_source_code_package_id,
                resolved_object_config_graph_id=resolved_object_config_graph_id,
                resolved_object_config_graph_package_id=(
                    resolved_object_config_graph_package_id
                ),
                package_name=spec.package.package_name,
                fqn_prefix=spec.package.fqn_prefix,
                function_impl_ownership=spec.package.function_impl_ownership,
                function_impl_parity_policy=spec.package.function_impl_parity_policy,
                implementation_policy_source="aware_toml",
                language_materialization_specs=spec.language_materializations,
                language_materialization_package_root=package_root,
                title=spec.package.title,
                description=spec.package.description,
                surface=surface,
                manifest_relative_path=manifest_relative_path,
                package_root_relative=package_root_relative,
                sources_root_relative=sources_root_relative,
                owned_file_paths=tuple(
                    item.workspace_relative_path for item in owned_source_files
                ),
                phase_timings_s=phase_timings_s,
                package_started_at=package_started_at,
                workspace_root=workspace_root,
                module_root=module_root,
            )
    if cached_result is not None:
        return cached_result

    package_code_edges = []
    seeded_code_package_domain_commit_id: UUID | None = None
    async with _record_leaf_package_subphase(
        phase_timings_s,
        "hydrate_code_package_from_head",
        progress_callback,
        detail_payload=leaf_detail,
    ):
        code_package = await _hydrate_lane_root_from_head(
            index=index,
            branch_id=package_branch_id,
            projection_hash=code_package_projection_hash,
            root_id=resolved_source_code_package_id,
            root_type=CodePackage,
        )
    if _code_package_source_texts_match(
        code_package=code_package,
        package_name=spec.package.package_name,
        language=CodeLanguage.aware.value,
        surface=surface,
        manifest_relative_path=manifest_relative_path,
        package_root=package_root_relative,
        sources_root=sources_root_relative,
        fqn_prefix=spec.package.fqn_prefix,
        source_text_by_relative_path=source_text_by_relative_path,
    ):
        phase_timings_s["reuse_existing_code_package_sources"] = 0.0
        logger.info(
            "Meta package leaf CodePackage source reuse: package=%s files=%d",
            spec.package.package_name,
            len(source_text_by_relative_path),
        )
    else:
        with _record_phase(
            phase_timings_s,
            "reset_package_branch_for_code_package_source_snapshot",
        ):
            _reset_generated_package_branch(
                aware_root=FSCommitStore().aware_root,
                branch_id=package_branch_id,
                projection_hashes=(
                    code_package_projection_hash,
                    object_config_graph_projection_hash,
                    object_config_graph_package_projection_hash,
                ),
            )
        async with _record_leaf_package_subphase(
            phase_timings_s,
            "seed_code_package_sources_from_manifest",
            progress_callback,
            detail_payload=leaf_detail,
        ):
            seed_result = await _seed_code_package_sources_from_manifest(
                index=index,
                branch_id=package_branch_id,
                projection_hash=code_package_projection_hash,
                code_package_id=resolved_source_code_package_id,
                package_name=spec.package.package_name,
                surface=surface,
                manifest_relative_path=manifest_relative_path,
                package_root=package_root_relative,
                sources_root=sources_root_relative,
                fqn_prefix=spec.package.fqn_prefix,
                source_text_by_relative_path=source_text_by_relative_path,
                actor_id=actor_id,
                phase_timings_s=phase_timings_s,
            )
        code_package = seed_result.code_package
        seeded_code_package_domain_commit_id = seed_result.domain_commit_id
    async with _record_leaf_package_subphase(
        phase_timings_s,
        "rehydrate_code_package_from_head",
        progress_callback,
        detail_payload=leaf_detail,
    ):
        code_package = await _hydrate_lane_root_from_head(
            index=index,
            branch_id=package_branch_id,
            projection_hash=code_package_projection_hash,
            root_id=resolved_source_code_package_id,
            root_type=CodePackage,
        )
    if code_package is None:
        raise RuntimeError(
            "Meta package leaf materialization could not rehydrate committed CodePackage after batch upsert: "
            f"package_name={spec.package.package_name!r} aware_toml_path={aware_toml_path}"
        )
    with _record_phase(phase_timings_s, "read_code_package_lane_head"):
        code_package_head = await FSCommitStore().head(
            branch_id=package_branch_id,
            projection_hash=code_package_projection_hash,
        )
    code_package_head_commit_id = _decode_head_commit_id(head=code_package_head)
    code_package_domain_commit_id = (
        seeded_code_package_domain_commit_id or code_package_head_commit_id
    )
    with _record_phase(
        phase_timings_s,
        "resolve_code_package_object_instance_graph_commit_id",
    ):
        code_package_oig_commit_id = (
            await _object_instance_graph_commit_id_from_domain_commit(
                branch_id=package_branch_id,
                projection_hash=code_package_projection_hash,
                domain_commit_id=code_package_domain_commit_id,
            )
            if code_package_domain_commit_id is not None
            else None
        )
    if code_package_oig_commit_id is None:
        raise RuntimeError(
            "Meta package leaf materialization requires a committed CodePackage "
            "OIG before building ObjectConfigGraphPackage: "
            f"aware_toml_path={aware_toml_path}"
        )
    edge_by_relative_path = {
        ((edge.relative_path or "").strip()): edge
        for edge in code_package.code_package_codes
    }
    package_code_edges = []
    for owned_source in owned_source_files:
        edge = edge_by_relative_path.get(owned_source.source_relative_path)
        if edge is None:
            raise RuntimeError(
                "Meta package leaf materialization failed to resolve committed package-owned code edge after batch "
                "CodePackage upsert: "
                f"package_name={spec.package.package_name!r} "
                f"aware_toml_path={aware_toml_path} "
                f"source_relative_path={owned_source.source_relative_path!r} "
                f"workspace_relative_path={owned_source.workspace_relative_path!r}"
            )
        package_code_edges.append(edge)
    (
        build_parsed_file_codes_for_code_package_sources,
        build_namespace_by_code_id_for_code_package,
    ) = _load_meta_code_package_source_helpers()

    async with _record_leaf_package_subphase(
        phase_timings_s,
        "parse_code_package_sources",
        progress_callback,
        detail_payload=leaf_detail,
    ):
        file_codes, parsed_code_package = (
            build_parsed_file_codes_for_code_package_sources(
                code_package=code_package,
                code_package_codes=tuple(package_code_edges),
                sources_root=sources_root,
            )
        )
    if not file_codes:
        raise RuntimeError(
            "Meta package leaf materialization parsed no semantic source files for OCG build: "
            f"aware_toml_path={aware_toml_path}"
        )
    async with _record_leaf_package_subphase(
        phase_timings_s,
        "build_namespace_by_code_id_for_code_package",
        progress_callback,
        detail_payload=leaf_detail,
    ):
        namespace_by_code_id = build_namespace_by_code_id_for_code_package(
            repository_name=spec.package.package_name,
            workspace_root=str(module_root),
            code_package=parsed_code_package,
            fqn_prefix=spec.package.fqn_prefix,
            namespace_mappings=spec.build.namespace.mappings,
        )

    async with _record_leaf_package_subphase(
        phase_timings_s,
        "build_object_config_graph_from_code",
        progress_callback,
        detail_payload=leaf_detail,
    ):
        build_result = build_object_config_graph_from_code(
            name=spec.package.fqn_prefix,
            description=(
                spec.package.description
                or f"ObjectConfigGraph for {spec.package.package_name}"
            ),
            fqn_prefix=spec.package.fqn_prefix,
            file_codes=sorted(file_codes, key=lambda item: item[0]),
            namespace_by_code_id=namespace_by_code_id,
            package_kind=AwarePackageKind(spec.package.kind.value),
            external_graphs=list(external_graphs or ()),
        )
    logger.info(
        "Meta package leaf OCG build finished: package=%s nodes=%d hash=%s",
        spec.package.package_name,
        len(build_result.graph.object_config_graph_nodes),
        build_result.graph.hash,
    )
    logger.info(
        "Meta package leaf cross-OCG link started: package=%s external_graphs=%d",
        spec.package.package_name,
        len(external_graphs or ()),
    )
    async with _record_leaf_package_subphase(
        phase_timings_s,
        "link_cross_ocg_relationships",
        progress_callback,
        detail_payload=leaf_detail,
    ):
        link_cross_ocg_relationships(
            build_results_by_language={CodeLanguage.aware: build_result},
            external_graphs=list(external_graphs or ()),
        )
    with _record_phase(phase_timings_s, "apply_source_to_ocg_lowering_signature"):
        _apply_source_to_ocg_lowering_signature(
            graph=build_result.graph,
            package_name=spec.package.package_name,
            fqn_prefix=spec.package.fqn_prefix,
        )
    logger.info(
        "Meta package leaf cross-OCG link finished: package=%s semantic_hash=%s",
        spec.package.package_name,
        build_result.graph.hash,
    )

    object_config_graph_package: ObjectConfigGraphPackage | None = None
    existing_object_config_graph_id = resolved_object_config_graph_id
    with _record_phase(
        phase_timings_s,
        "load_existing_object_config_graph_head",
    ):
        existing_object_config_graph_head = await FSCommitStore().head(
            branch_id=package_branch_id,
            projection_hash=object_config_graph_projection_hash,
        )
    if (
        existing_object_config_graph_head is not None
        and existing_object_config_graph_head.get("commit_id") is not None
    ):
        with _record_phase(
            phase_timings_s,
            "match_existing_object_config_graph_head_summary",
        ):
            (
                existing_object_config_graph_head_summary_matches,
                existing_object_config_graph_head_summary_reason,
            ) = _existing_object_config_graph_head_summary_matches(
                branch_id=package_branch_id,
                object_config_graph_projection_hash=(
                    object_config_graph_projection_hash
                ),
                object_config_graph_package_id=(
                    resolved_object_config_graph_package_id
                ),
                object_config_graph_id=existing_object_config_graph_id,
                existing_object_config_graph_head=(existing_object_config_graph_head),
                built_object_config_graph=build_result.graph,
            )
        phase_timings_s[
            "match_existing_object_config_graph_head_summary."
            f"{existing_object_config_graph_head_summary_reason}"
        ] = 0.0
    else:
        existing_object_config_graph_head_summary_matches = False
        existing_object_config_graph_head_summary_reason = "head_missing"
    existing_object_config_graph: ObjectConfigGraph | None = None
    if not existing_object_config_graph_head_summary_matches:
        if (
            existing_object_config_graph_head is not None
            and existing_object_config_graph_head.get("commit_id") is not None
        ):
            logger.info(
                "Meta package leaf ensure current index identity seed lanes started: package=%s",
                spec.package.package_name,
            )
            with _record_phase(
                phase_timings_s,
                "ensure_current_index_identity_seed_lanes",
            ):
                await _ensure_current_index_identity_seed_lanes(index=index)
            logger.info(
                "Meta package leaf ensure current index identity seed lanes finished: package=%s",
                spec.package.package_name,
            )
            async with _record_leaf_package_subphase(
                phase_timings_s,
                "hydrate_existing_object_config_graph_from_head",
                progress_callback,
                detail_payload=leaf_detail,
            ):
                logger.info(
                    "Meta package leaf hydrate existing ObjectConfigGraph started: package=%s",
                    spec.package.package_name,
                )
                existing_object_config_graph = await _hydrate_lane_root_from_head(
                    index=index,
                    branch_id=package_branch_id,
                    projection_hash=object_config_graph_projection_hash,
                    root_id=existing_object_config_graph_id,
                    root_type=ObjectConfigGraph,
                )
            logger.info(
                "Meta package leaf hydrate existing ObjectConfigGraph finished: package=%s found=%s hash=%s",
                spec.package.package_name,
                existing_object_config_graph is not None,
                (
                    None
                    if existing_object_config_graph is None
                    else existing_object_config_graph.hash
                ),
            )
    else:
        logger.info(
            "Meta package leaf ensure current index identity seed lanes started: package=%s",
            spec.package.package_name,
        )
        with _record_phase(
            phase_timings_s,
            "ensure_current_index_identity_seed_lanes",
        ):
            await _ensure_current_index_identity_seed_lanes(index=index)
        logger.info(
            "Meta package leaf ensure current index identity seed lanes finished: package=%s",
            spec.package.package_name,
        )
        logger.info(
            "Meta package leaf ObjectConfigGraph head summary reuse matched: package=%s reason=%s",
            spec.package.package_name,
            existing_object_config_graph_head_summary_reason,
        )
    if (
        existing_object_config_graph_head_summary_matches
        or _object_config_graph_hash_matches(
            existing_object_config_graph=existing_object_config_graph,
            built_object_config_graph=build_result.graph,
        )
    ):
        logger.info(
            "Meta package leaf semantic OCG reuse started: package=%s",
            spec.package.package_name,
        )
        async with _record_leaf_package_subphase(
            phase_timings_s,
            "reuse_existing_object_config_graph_semantic_lane",
            progress_callback,
            detail_payload=leaf_detail,
        ):
            semantic_commit_summary = (
                await _reuse_existing_object_config_graph_semantic_lane(
                    branch_id=package_branch_id,
                    projection_hash=object_config_graph_projection_hash,
                    aware_toml_path=aware_toml_path,
                )
            )
        logger.info(
            "Meta package leaf semantic OCG reuse finished: package=%s head_commit_id=%s",
            spec.package.package_name,
            semantic_commit_summary.head_commit_id,
        )
    else:
        logger.info(
            "Meta package leaf semantic OCG commit started: package=%s existing_hash=%s built_hash=%s",
            spec.package.package_name,
            (
                None
                if existing_object_config_graph is None
                else existing_object_config_graph.hash
            ),
            build_result.graph.hash,
        )
        async with _record_leaf_package_subphase(
            phase_timings_s,
            "commit_object_config_graph_to_semantic_lane",
            progress_callback,
            detail_payload=leaf_detail,
        ):
            semantic_commit_summary = (
                await _commit_object_config_graph_to_semantic_lane(
                    built_object_config_graph=build_result.graph,
                    existing_object_config_graph=existing_object_config_graph,
                    branch_id=package_branch_id,
                    projection_hash=object_config_graph_projection_hash,
                    index=index,
                    aware_toml_path=aware_toml_path,
                    external_graphs=tuple(external_graphs or ()),
                    actor_id=actor_id,
                    progress_callback=progress_callback,
                    detail_payload=leaf_detail,
                )
            )
        logger.info(
            "Meta package leaf semantic OCG commit finished: package=%s strategy=%s commit_id=%s head_commit_id=%s",
            spec.package.package_name,
            semantic_commit_summary.strategy,
            semantic_commit_summary.commit_id,
            semantic_commit_summary.head_commit_id,
        )
    semantic_root_domain_commit_id = _semantic_lane_root_domain_commit_id(
        semantic_commit_summary
    )
    logger.info(
        "Meta package leaf semantic OIG id resolution started: package=%s domain_commit_id=%s",
        spec.package.package_name,
        semantic_root_domain_commit_id,
    )
    async with _record_leaf_package_subphase(
        phase_timings_s,
        "resolve_object_config_graph_semantic_root_commit_id",
        progress_callback,
        detail_payload=leaf_detail,
    ):
        object_config_graph_oig_commit_id = (
            await _object_instance_graph_commit_id_from_domain_commit(
                branch_id=package_branch_id,
                projection_hash=object_config_graph_projection_hash,
                domain_commit_id=semantic_root_domain_commit_id,
            )
            if semantic_root_domain_commit_id is not None
            else None
        )
    logger.info(
        "Meta package leaf semantic OIG id resolution finished: package=%s oig_commit_id=%s",
        spec.package.package_name,
        object_config_graph_oig_commit_id,
    )
    if object_config_graph_oig_commit_id is None:
        raise RuntimeError(
            "Meta package leaf materialization requires a committed ObjectConfigGraph semantic root "
            f"before building ObjectConfigGraphPackage: aware_toml_path={aware_toml_path}"
        )
    logger.info(
        "Meta package leaf ObjectConfigGraphPackage snapshot started: package=%s",
        spec.package.package_name,
    )
    async with _record_leaf_package_subphase(
        phase_timings_s,
        "reset_object_config_graph_package_lane",
        progress_callback,
        detail_payload=leaf_detail,
    ):
        _reset_generated_projection_lanes(
            aware_root=FSCommitStore().aware_root,
            branch_id=package_branch_id,
            projection_hashes=(object_config_graph_package_projection_hash,),
        )
    async with _record_leaf_package_subphase(
        phase_timings_s,
        "seed_object_config_graph_package_snapshot",
        progress_callback,
        detail_payload=leaf_detail,
    ):
        package_snapshot_seed = await _seed_object_config_graph_package_snapshot(
            index=index,
            branch_id=package_branch_id,
            projection_hash=object_config_graph_package_projection_hash,
            object_config_graph_package_id=resolved_object_config_graph_package_id,
            package_name=spec.package.package_name,
            fqn_prefix=spec.package.fqn_prefix,
            source_code_package_id=code_package.id,
            object_config_graph_id=build_result.graph.id,
            object_config_graph_object_instance_graph_commit_id=(
                object_config_graph_oig_commit_id
            ),
            function_impl_ownership=spec.package.function_impl_ownership,
            function_impl_parity_policy=spec.package.function_impl_parity_policy,
            implementation_policy_source="aware_toml",
            title=spec.package.title,
            description=spec.package.description,
            language_materialization_specs=spec.language_materializations,
            package_root=package_root,
            workspace_root=workspace_root,
            actor_id=actor_id,
            phase_timings_s=phase_timings_s,
        )
    object_config_graph_package = package_snapshot_seed.object_config_graph_package
    logger.info(
        "Meta package leaf ObjectConfigGraphPackage snapshot finished: package=%s commit_id=%s",
        spec.package.package_name,
        package_snapshot_seed.domain_commit_id,
    )
    object_config_graph_package.source_code_package = code_package
    object_config_graph_package.source_code_package_id = code_package.id
    object_config_graph_package.object_config_graph = build_result.graph
    object_config_graph_package.object_config_graph_id = build_result.graph.id
    object_config_graph_package.object_config_graph_object_instance_graph_commit_id = (
        object_config_graph_oig_commit_id
    )
    object_config_graph_package.function_impl_ownership = (
        _object_config_graph_package_function_impl_ownership(
            spec.package.function_impl_ownership,
        )
    )
    object_config_graph_package.function_impl_parity_policy = (
        _object_config_graph_package_function_impl_parity_policy(
            spec.package.function_impl_parity_policy,
        )
    )
    object_config_graph_package.implementation_policy_source = "aware_toml"
    async with _record_leaf_package_subphase(
        phase_timings_s,
        "read_object_config_graph_package_lane_head",
        progress_callback,
        detail_payload=leaf_detail,
    ):
        object_config_graph_package_head = await FSCommitStore().head(
            branch_id=package_branch_id,
            projection_hash=object_config_graph_package_projection_hash,
        )
    object_config_graph_package_head_commit_id = _decode_head_commit_id(
        head=object_config_graph_package_head,
    )
    object_config_graph_package_domain_commit_id = (
        package_snapshot_seed.domain_commit_id
        or object_config_graph_package_head_commit_id
    )
    async with _record_leaf_package_subphase(
        phase_timings_s,
        "resolve_object_config_graph_package_oig_commit_id",
        progress_callback,
        detail_payload=leaf_detail,
    ):
        object_config_graph_package_oig_commit_id = (
            package_snapshot_seed.object_instance_graph_commit_id
        )
    if object_config_graph_package_oig_commit_id is None:
        raise RuntimeError(
            "Meta package leaf materialization requires a committed "
            "ObjectConfigGraphPackage OIG: "
            f"aware_toml_path={aware_toml_path}"
        )
    phase_timings_s["total"] = _round_duration_s(perf_counter() - package_started_at)

    result = ObjectConfigGraphPackageLeafMaterializationResult(
        aware_toml_path=aware_toml_path,
        package_branch_id=package_branch_id,
        code_package=code_package,
        object_config_graph_package=object_config_graph_package,
        object_config_graph=build_result.graph,
        owned_file_paths=tuple(
            item.workspace_relative_path for item in owned_source_files
        ),
        code_package_commit_id=(seeded_code_package_domain_commit_id),
        code_package_head_commit_id=code_package_head_commit_id,
        code_package_object_instance_graph_commit_id=code_package_oig_commit_id,
        object_config_graph_commit_id=semantic_commit_summary.commit_id,
        object_config_graph_head_commit_id=semantic_commit_summary.head_commit_id,
        object_config_graph_object_instance_graph_commit_id=object_config_graph_oig_commit_id,
        object_config_graph_package_commit_id=(
            object_config_graph_package_domain_commit_id
        ),
        object_config_graph_package_head_commit_id=(
            object_config_graph_package_head_commit_id
        ),
        object_config_graph_package_object_instance_graph_commit_id=(
            object_config_graph_package_oig_commit_id
        ),
        phase_timings_s=dict(sorted(phase_timings_s.items())),
        code_package_build_runtime_telemetry=code_package_build_runtime_telemetry,
        code_package_build_invoke_perf_ms=code_package_build_invoke_perf_ms,
        code_package_upsert_runtime_telemetry=code_package_upsert_runtime_telemetry,
        code_package_upsert_invoke_perf_ms=code_package_upsert_invoke_perf_ms,
        semantic_commit_strategy=semantic_commit_summary.strategy,
        semantic_commit_fallback_reset=semantic_commit_summary.fallback_reset,
        semantic_commit_phase_timings_s=dict(
            sorted(semantic_commit_summary.phase_timings_s.items())
        ),
    )
    async with _record_leaf_package_subphase(
        phase_timings_s,
        "build_materialization_index_receipt",
        progress_callback,
        detail_payload=leaf_detail,
    ):
        projection_hashes_by_id = _derived_projection_hashes_by_id_for_index_receipt(
            graph=build_result.graph,
            external_graphs=tuple(external_graphs or ()),
            cross_relationships_by_target_ocg=(
                build_result.cross_relationships_by_target_ocg
            ),
        )
        result = _with_materialization_index_receipt(
            result=result,
            source_manifest_hash=source_manifest_hash,
            dependency_signature=dependency_signature,
            cache_status="rebuilt",
            code_package_projection_hash=code_package_projection_hash,
            object_config_graph_projection_hash=object_config_graph_projection_hash,
            object_config_graph_package_projection_hash=(
                object_config_graph_package_projection_hash
            ),
            projection_hashes_by_id=projection_hashes_by_id,
            package_materialization_receipt=build_result.package_materialization_receipt,
        )
    async with _record_leaf_package_subphase(
        phase_timings_s,
        "write_object_config_graph_package_reuse_cache",
        progress_callback,
        detail_payload=leaf_detail,
    ):
        _write_object_config_graph_package_reuse_cache(
            result=result,
            source_manifest_hash=source_manifest_hash,
            dependency_signature=dependency_signature,
        )
    async with _record_leaf_package_subphase(
        phase_timings_s,
        "record_runtime_package_projection_index",
        progress_callback,
        detail_payload=leaf_detail,
    ):
        _record_runtime_package_projection_index(
            result=result,
            workspace_root=workspace_root,
            module_root=module_root,
            source_manifest_hash=source_manifest_hash,
            dependency_signature=dependency_signature,
        )
    return result


def _find_module_root(*, aware_toml_path: Path, workspace_root: Path) -> Path:
    current = aware_toml_path.parent.resolve()
    workspace_root = workspace_root.resolve()
    try:
        aware_toml_path.resolve().relative_to(workspace_root)
    except ValueError as exc:
        raise RuntimeError(
            "Meta package leaf materialization aware.toml is not under workspace_root: "
            f"aware_toml_path={aware_toml_path} workspace_root={workspace_root}"
        ) from exc
    while True:
        module_manifest = current / "aware.module.toml"
        if module_manifest.is_file():
            return current
        if current == workspace_root:
            break
        if current.parent == current:
            break
        current = current.parent
    return workspace_root


def stable_semantic_package_branch_id(
    *,
    parent_branch_id: UUID,
    package_name: str,
    fqn_prefix: str,
) -> UUID:
    """Legacy parent-derived package branch id.

    New package materialization rails should use
    `stable_object_config_graph_package_branch_id` and pass the result explicitly.
    """
    return uuid5(
        NAMESPACE_URL,
        "aware://meta/materialization/package-branch:"
        f"{parent_branch_id}:{(package_name or '').strip().casefold()}:{(fqn_prefix or '').strip().casefold()}",
    )


def stable_object_config_graph_package_branch_id(
    *,
    workspace_root: Path | str,
    aware_toml_path: Path | str,
    package_name: str,
    fqn_prefix: str,
) -> UUID:
    workspace_root_path = Path(workspace_root).expanduser().resolve()
    manifest_path = Path(aware_toml_path).expanduser().resolve()
    try:
        manifest_key = manifest_path.relative_to(workspace_root_path).as_posix()
    except ValueError:
        manifest_key = manifest_path.as_posix()
    return uuid5(
        NAMESPACE_URL,
        "aware://meta/materialization/object-config-graph-package-branch:v1:"
        f"{manifest_key.strip().casefold()}:"
        f"{(package_name or '').strip().casefold()}:"
        f"{(fqn_prefix or '').strip().casefold()}",
    )


def _relative_to(*, path: Path, root: Path, label: str) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise RuntimeError(
            f"Meta package leaf materialization {label} is not within the expected root: "
            f"path={path} root={root}"
        ) from exc


def _discover_owned_source_files(
    *,
    workspace_root: Path,
    sources_root: Path,
    include_paths: tuple[str, ...],
    exclude_paths: tuple[str, ...],
    package_root: Path,
) -> tuple[_OwnedSourceFile, ...]:
    if not sources_root.exists() or not sources_root.is_dir():
        raise RuntimeError(
            f"Meta package leaf materialization sources_dir does not exist: {sources_root}"
        )

    included: set[Path] = set()
    for pattern in include_paths:
        raw_pattern = pattern.strip()
        if not raw_pattern:
            continue
        for candidate in sources_root.glob(raw_pattern):
            if not candidate.is_file() or candidate.suffix != _AWARE_SOURCE_EXTENSION:
                continue
            resolved = candidate.resolve()
            if not _is_within(candidate=resolved, root=sources_root):
                continue
            if _has_ignored_segment(resolved.relative_to(sources_root).parts):
                continue
            included.add(resolved)

    for pattern in exclude_paths:
        raw_pattern = pattern.strip()
        if not raw_pattern:
            continue
        for candidate in sources_root.glob(raw_pattern):
            if candidate.is_file():
                included.discard(candidate.resolve())

    owned_files: list[_OwnedSourceFile] = []
    for candidate in sorted(included):
        owned_files.append(
            _OwnedSourceFile(
                workspace_relative_path=_relative_to(
                    path=candidate, root=workspace_root, label="owned source"
                ),
                package_relative_path=_relative_to(
                    path=candidate, root=package_root, label="owned source"
                ),
                source_relative_path=_relative_to(
                    path=candidate, root=sources_root, label="owned source"
                ),
                absolute_path=candidate,
            )
        )
    return tuple(owned_files)


def _code_package_source_texts_match(
    *,
    code_package: CodePackage | None,
    package_name: str,
    language: str,
    surface: str,
    manifest_relative_path: str,
    package_root: str,
    sources_root: str,
    fqn_prefix: str,
    source_text_by_relative_path: Mapping[str, str],
) -> bool:
    if code_package is None:
        return False
    if (
        code_package.package_name != package_name
        or _enum_text(code_package.language) != language
        or _enum_text(code_package.surface) != surface
        or (code_package.manifest_relative_path or "") != manifest_relative_path
        or (code_package.package_root or "") != package_root
        or (code_package.sources_root or "") != sources_root
        or (code_package.fqn_prefix or "") != fqn_prefix
    ):
        return False

    edge_by_relative_path = {
        str(edge.relative_path or "").strip(): edge
        for edge in code_package.code_package_codes
        if str(edge.relative_path or "").strip()
    }
    if set(edge_by_relative_path) != set(source_text_by_relative_path):
        return False

    for relative_path, expected_text in source_text_by_relative_path.items():
        edge = edge_by_relative_path.get(relative_path)
        if edge is None or edge.code is None:
            return False
        content_part_text = getattr(edge.code, "content_part_text", None)
        if content_part_text is None:
            return False
        if (content_part_text.inline_text or "") != expected_text:
            return False
    return True


def _enum_text(value: object) -> str:
    raw_value = getattr(value, "value", value)
    return str(raw_value or "").strip()


def _source_text_manifest_hash(
    *,
    source_text_by_relative_path: Mapping[str, str],
) -> str:
    return source_text_manifest_hash(
        source_text_by_relative_path=source_text_by_relative_path,
    )


def _external_graph_signature(
    *,
    external_graphs: tuple[ObjectConfigGraph, ...],
) -> str:
    return external_graph_signature(external_graphs=external_graphs)


def _object_config_graph_package_reuse_cache_path(
    *,
    branch_id: UUID,
    object_config_graph_package_id: UUID,
) -> Path:
    return object_config_graph_package_reuse_cache_path(
        aware_root=FSCommitStore().aware_root,
        branch_id=branch_id,
        object_config_graph_package_id=object_config_graph_package_id,
    )


def _read_reuse_cache_payload(
    *,
    branch_id: UUID,
    object_config_graph_package_id: UUID,
) -> dict[str, object] | None:
    payload = read_object_config_graph_package_reuse_cache_payload(
        aware_root=FSCommitStore().aware_root,
        branch_id=branch_id,
        object_config_graph_package_id=object_config_graph_package_id,
    )
    if payload is None:
        return None
    if payload.get("cache_kind") in {
        OBJECT_CONFIG_GRAPH_PACKAGE_REUSE_CACHE_KIND_CONTEXT_GRAPHS,
        OBJECT_CONFIG_GRAPH_PACKAGE_REUSE_CACHE_KIND_CONTEXT_SOURCE_GRAPH,
    }:
        return None
    return payload


def _write_reuse_cache_payload(
    *,
    branch_id: UUID,
    object_config_graph_package_id: UUID,
    payload: Mapping[str, object],
) -> None:
    write_object_config_graph_package_reuse_cache_payload(
        aware_root=FSCommitStore().aware_root,
        branch_id=branch_id,
        object_config_graph_package_id=object_config_graph_package_id,
        payload=payload,
    )


def _payload_string(payload: Mapping[str, object], key: str) -> str | None:
    value = payload.get(key)
    if isinstance(value, str) and value:
        return value
    return None


def _payload_uuid(payload: Mapping[str, object], key: str) -> UUID | None:
    value = _payload_string(payload, key)
    if value is None:
        return None
    try:
        return UUID(value)
    except Exception:
        return None


def _apply_source_to_ocg_lowering_signature(
    *,
    graph: ObjectConfigGraph,
    package_name: str,
    fqn_prefix: str,
) -> None:
    raw_hash = str(graph.hash or "").strip()
    if not raw_hash:
        return
    hasher = hashlib.sha256()
    hasher.update(b"aware-meta-object-config-graph-semantic-hash-v1\n")
    for value in (
        raw_hash,
        package_name,
        fqn_prefix,
        OBJECT_CONFIG_GRAPH_SOURCE_TO_RUNTIME_LOWERING_SIGNATURE,
    ):
        encoded = value.encode("utf-8")
        hasher.update(str(len(encoded)).encode("ascii"))
        hasher.update(b":")
        hasher.update(encoded)
        hasher.update(b"\n")
    graph.hash = hasher.hexdigest()


def _object_config_graph_payload_from_reuse_cache(
    payload: Mapping[str, object],
) -> dict[str, object] | None:
    graph_payload = payload.get("object_config_graph")
    if not isinstance(graph_payload, dict):
        return None
    normalized_payload = {str(key): value for key, value in graph_payload.items()}
    if not _object_config_graph_payload_has_materialized_body(normalized_payload):
        return None
    return normalized_payload


_OBJECT_CONFIG_GRAPH_SOURCE_SECTIONS_CACHE_KEY = "object_config_graph_source_sections"


def _object_config_graph_source_sections_payload(
    graph: ObjectConfigGraph,
) -> dict[str, object]:
    classes: dict[str, object] = {}
    enums: dict[str, object] = {}
    functions: dict[str, object] = {}

    for class_config in _iter_object_config_graph_class_configs(graph):
        source = class_config.code_section_class
        if source is not None:
            classes[str(class_config.id)] = source.model_dump(
                mode="json",
                by_alias=True,
                exclude_none=True,
            )
        for link in class_config.class_config_function_configs:
            function_config = link.function_config
            if function_config is None:
                continue
            source_function = function_config.code_section_function
            if source_function is None:
                continue
            functions[str(function_config.id)] = source_function.model_dump(
                mode="json",
                by_alias=True,
                exclude_none=True,
            )

    for node in graph.object_config_graph_nodes:
        enum_config = node.enum_config
        if enum_config is not None and enum_config.code_section_enum is not None:
            enums[str(enum_config.id)] = enum_config.code_section_enum.model_dump(
                mode="json",
                by_alias=True,
                exclude_none=True,
            )
        function_config = get_node_function_config(node)
        if function_config is None or function_config.code_section_function is None:
            continue
        functions[str(function_config.id)] = (
            function_config.code_section_function.model_dump(
                mode="json",
                by_alias=True,
                exclude_none=True,
            )
        )

    return {
        "classes": dict(sorted(classes.items())),
        "enums": dict(sorted(enums.items())),
        "functions": dict(sorted(functions.items())),
    }


def _attach_object_config_graph_source_sections_from_reuse_cache(
    *,
    graph: ObjectConfigGraph,
    payload: Mapping[str, object],
) -> None:
    raw_sections = payload.get(_OBJECT_CONFIG_GRAPH_SOURCE_SECTIONS_CACHE_KEY)
    if not isinstance(raw_sections, Mapping):
        return
    raw_classes = raw_sections.get("classes")
    raw_enums = raw_sections.get("enums")
    raw_functions = raw_sections.get("functions")
    class_payloads = raw_classes if isinstance(raw_classes, Mapping) else {}
    enum_payloads = raw_enums if isinstance(raw_enums, Mapping) else {}
    function_payloads = raw_functions if isinstance(raw_functions, Mapping) else {}

    for class_config in _iter_object_config_graph_class_configs(graph):
        source_payload = class_payloads.get(str(class_config.id))
        if isinstance(source_payload, Mapping):
            class_config.code_section_class = CodeSectionClass.model_validate(
                source_payload
            )
        for link in class_config.class_config_function_configs:
            function_config = link.function_config
            if function_config is None:
                continue
            source_function_payload = function_payloads.get(str(function_config.id))
            if isinstance(source_function_payload, Mapping):
                function_config.code_section_function = (
                    CodeSectionFunction.model_validate(source_function_payload)
                )

    for node in graph.object_config_graph_nodes:
        enum_config = node.enum_config
        if enum_config is not None:
            source_payload = enum_payloads.get(str(enum_config.id))
            if isinstance(source_payload, Mapping):
                enum_config.code_section_enum = CodeSectionEnum.model_validate(
                    source_payload
                )
        function_config = get_node_function_config(node)
        if function_config is None:
            continue
        source_function_payload = function_payloads.get(str(function_config.id))
        if isinstance(source_function_payload, Mapping):
            function_config.code_section_function = CodeSectionFunction.model_validate(
                source_function_payload
            )


def _object_config_graph_has_unhydrated_function_source_refs(
    graph: ObjectConfigGraph,
) -> bool:
    for class_config in _iter_object_config_graph_class_configs(graph):
        for link in class_config.class_config_function_configs:
            function_config = link.function_config
            if (
                function_config is not None
                and function_config.code_section_function_id is not None
                and function_config.code_section_function is None
            ):
                return True
    for node in graph.object_config_graph_nodes:
        function_config = get_node_function_config(node)
        if (
            function_config is not None
            and function_config.code_section_function_id is not None
            and function_config.code_section_function is None
        ):
            return True
    return False


def _rehydrate_object_config_graph_source_relationship_refs(
    graph: ObjectConfigGraph,
) -> None:
    class_by_id = {
        class_config.id: class_config
        for class_config in _iter_object_config_graph_class_configs(graph)
    }
    attribute_by_id = {
        link.attribute_config_id: link.attribute_config
        for class_config in class_by_id.values()
        for link in class_config.class_config_attribute_configs
        if link.attribute_config is not None
    }

    def rehydrate_relationship(relationship: ClassConfigRelationship) -> None:
        if relationship.target_class_config is None:
            relationship.target_class_config = class_by_id.get(
                relationship.target_class_config_id
            )
        for rel_attr in relationship.class_config_relationship_attributes:
            if rel_attr.attribute_config is None:
                rel_attr.attribute_config = attribute_by_id.get(
                    rel_attr.attribute_config_id
                )
        association = relationship.class_config_relationship_association_edge
        if association is not None and association.class_config is None:
            association.class_config = class_by_id.get(association.class_config_id)

    for class_config in class_by_id.values():
        for relationship in class_config.class_config_relationships:
            rehydrate_relationship(relationship)
    for node in graph.object_config_graph_nodes:
        relationship = node.class_config_relationship
        if relationship is not None:
            rehydrate_relationship(relationship)
    for graph_relationship in graph.object_config_graph_relationships:
        for relationship in graph_relationship.class_config_relationships:
            rehydrate_relationship(relationship)


def _iter_object_config_graph_class_configs(
    graph: ObjectConfigGraph,
) -> Iterator[ClassConfig]:
    seen: set[UUID] = set()
    for node in graph.object_config_graph_nodes:
        class_config = node.class_config
        if class_config is not None and class_config.id not in seen:
            seen.add(class_config.id)
            yield class_config
        relationship = node.class_config_relationship
        if (
            relationship is not None
            and relationship.target_class_config is not None
            and relationship.target_class_config.id not in seen
        ):
            seen.add(relationship.target_class_config.id)
            yield relationship.target_class_config
    for graph_relationship in graph.object_config_graph_relationships:
        for relationship in graph_relationship.class_config_relationships:
            if (
                relationship.target_class_config is not None
                and relationship.target_class_config.id not in seen
            ):
                seen.add(relationship.target_class_config.id)
                yield relationship.target_class_config


def _materialization_index_receipt_from_reuse_cache(
    payload: Mapping[str, object],
) -> dict[str, object] | None:
    raw_receipt = payload.get("materialization_index_receipt")
    if not isinstance(raw_receipt, dict):
        return None
    receipt = {str(key): value for key, value in raw_receipt.items()}
    if (
        receipt.get("receipt_kind")
        != "object_config_graph_package_materialization_index"
    ):
        return None
    receipt["cache_status"] = "fingerprint_reuse"
    receipt["semantic_commit_strategy"] = "fingerprint_reuse"
    return receipt


def _object_config_graph_payload_has_materialized_body(
    payload: Mapping[str, object],
) -> bool:
    return object_config_graph_payload_has_materialized_body(payload)


def _object_config_graph_payload_has_namespace_evidence(
    payload: Mapping[str, object],
) -> bool:
    return object_config_graph_payload_has_namespace_evidence(payload)


async def _try_reuse_existing_object_config_graph_package_cache(
    *,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    code_package_projection_hash: str,
    object_config_graph_projection_hash: str,
    object_config_graph_package_projection_hash: str,
    aware_toml_path: Path,
    source_manifest_hash: str,
    dependency_signature: str,
    resolved_source_code_package_id: UUID,
    resolved_object_config_graph_id: UUID,
    resolved_object_config_graph_package_id: UUID,
    package_name: str,
    fqn_prefix: str,
    function_impl_ownership: str,
    function_impl_parity_policy: str,
    implementation_policy_source: str,
    language_materialization_specs: Iterable[object],
    language_materialization_package_root: Path,
    title: str | None,
    description: str | None,
    surface: str,
    manifest_relative_path: str,
    package_root_relative: str,
    sources_root_relative: str,
    owned_file_paths: tuple[str, ...],
    phase_timings_s: dict[str, float],
    package_started_at: float,
    workspace_root: Path | None = None,
    module_root: Path | None = None,
) -> ObjectConfigGraphPackageLeafMaterializationResult | None:
    started_at = perf_counter()

    def miss(reason: str) -> None:
        phase_timings_s["reuse_existing_object_config_graph_package_cache"] = (
            _round_duration_s(perf_counter() - started_at)
        )
        phase_timings_s[
            f"reuse_existing_object_config_graph_package_cache.miss.{reason}"
        ] = 0.0
        logger.info(
            "Meta package leaf ObjectConfigGraphPackage fingerprint cache miss: package=%s reason=%s",
            package_name,
            reason,
        )

    payload = _read_reuse_cache_payload(
        branch_id=branch_id,
        object_config_graph_package_id=resolved_object_config_graph_package_id,
    )
    if payload is None:
        miss("payload_missing")
        return None
    if payload.get("v") != _PACKAGE_REUSE_CACHE_VERSION:
        miss("version_mismatch")
        return None
    if _payload_string(payload, "source_manifest_hash") != source_manifest_hash:
        miss("source_manifest_hash_mismatch")
        return None
    if _payload_string(payload, "dependency_signature") != dependency_signature:
        miss("dependency_signature_mismatch")
        return None
    if (
        _payload_uuid(payload, "source_code_package_id")
        != resolved_source_code_package_id
    ):
        miss("source_code_package_id_mismatch")
        return None
    if (
        _payload_uuid(payload, "object_config_graph_id")
        != resolved_object_config_graph_id
    ):
        miss("object_config_graph_id_mismatch")
        return None
    if (
        _payload_uuid(payload, "object_config_graph_package_id")
        != resolved_object_config_graph_package_id
    ):
        miss("object_config_graph_package_id_mismatch")
        return None
    if _payload_string(payload, "function_impl_ownership") != function_impl_ownership:
        miss("function_impl_ownership_mismatch")
        return None
    if (
        _payload_string(payload, "function_impl_parity_policy")
        != function_impl_parity_policy
    ):
        miss("function_impl_parity_policy_mismatch")
        return None
    if (
        _payload_string(payload, "implementation_policy_source")
        != implementation_policy_source
    ):
        miss("implementation_policy_source_mismatch")
        return None
    if (
        _payload_string(payload, "source_to_ocg_lowering_signature")
        != OBJECT_CONFIG_GRAPH_SOURCE_TO_RUNTIME_LOWERING_SIGNATURE
    ):
        miss("source_to_ocg_lowering_signature_mismatch")
        return None
    if str(payload.get("language_materialization_signature") or "") != (
        _language_materialization_specs_signature(
            language_materialization_specs=language_materialization_specs,
        )
    ):
        miss("language_materialization_signature_mismatch")
        return None
    expected_code_package_fields = {
        "code_package_package_name": package_name,
        "code_package_language": CodeLanguage.aware.value,
        "code_package_surface": surface,
        "code_package_manifest_kind": "aware_toml",
        "code_package_manifest_relative_path": manifest_relative_path,
        "code_package_package_root": package_root_relative,
        "code_package_sources_root": sources_root_relative,
        "code_package_fqn_prefix": fqn_prefix,
    }
    for key, expected_value in expected_code_package_fields.items():
        if _payload_string(payload, key) != expected_value:
            miss(f"{key}_mismatch")
            return None

    store = FSCommitStore()
    code_package_head_commit_id = _decode_head_commit_id(
        head=await store.head(
            branch_id=branch_id,
            projection_hash=code_package_projection_hash,
        )
    )
    object_config_graph_head_commit_id = _decode_head_commit_id(
        head=await store.head(
            branch_id=branch_id,
            projection_hash=object_config_graph_projection_hash,
        )
    )
    object_config_graph_package_head_commit_id = _decode_head_commit_id(
        head=await store.head(
            branch_id=branch_id,
            projection_hash=object_config_graph_package_projection_hash,
        )
    )
    if code_package_head_commit_id != _payload_uuid(
        payload, "code_package_head_commit_id"
    ):
        miss("code_package_head_commit_id_mismatch")
        return None
    if object_config_graph_head_commit_id != _payload_uuid(
        payload, "object_config_graph_head_commit_id"
    ):
        miss("object_config_graph_head_commit_id_mismatch")
        return None
    if object_config_graph_package_head_commit_id != _payload_uuid(
        payload, "object_config_graph_package_head_commit_id"
    ):
        miss("object_config_graph_package_head_commit_id_mismatch")
        return None

    object_config_graph_payload = _object_config_graph_payload_from_reuse_cache(payload)
    if (
        object_config_graph_payload is not None
        and not _object_config_graph_payload_has_namespace_evidence(
            object_config_graph_payload
        )
    ):
        miss("object_config_graph_payload_missing_namespace_evidence")
        return None
    if object_config_graph_payload is None:
        object_config_graph = await _hydrate_lane_root_from_head(
            index=index,
            branch_id=branch_id,
            projection_hash=object_config_graph_projection_hash,
            root_id=resolved_object_config_graph_id,
            root_type=ObjectConfigGraph,
        )
        if object_config_graph is not None:
            object_config_graph_payload = object_config_graph.model_dump(
                mode="json",
                exclude_none=True,
            )
    else:
        try:
            object_config_graph = ObjectConfigGraph.model_validate(
                object_config_graph_payload
            )
        except Exception:
            miss("object_config_graph_payload_invalid")
            return None
    if object_config_graph is None:
        miss("object_config_graph_unavailable")
        return None
    _attach_object_config_graph_source_sections_from_reuse_cache(
        graph=object_config_graph,
        payload=payload,
    )
    _rehydrate_object_config_graph_source_relationship_refs(object_config_graph)
    if _object_config_graph_has_unhydrated_function_source_refs(object_config_graph):
        miss("object_config_graph_source_sections_missing")
        return None
    if _payload_string(payload, "object_config_graph_hash") != str(
        object_config_graph.hash or ""
    ):
        miss("object_config_graph_hash_mismatch")
        return None
    if object_config_graph_payload is None:
        miss("object_config_graph_payload_missing")
        return None

    object_config_graph_oig_commit_id = _payload_uuid(
        payload,
        "object_config_graph_object_instance_graph_commit_id",
    )
    object_config_graph_package_oig_commit_id = _payload_uuid(
        payload,
        "object_config_graph_package_object_instance_graph_commit_id",
    )
    code_package_oig_commit_id = _payload_uuid(
        payload,
        "code_package_object_instance_graph_commit_id",
    )
    if (
        object_config_graph_oig_commit_id is None
        or object_config_graph_package_oig_commit_id is None
        or code_package_oig_commit_id is None
    ):
        miss("object_instance_graph_commit_id_missing")
        return None
    if object_config_graph_head_commit_id is not None:
        with _record_phase(
            phase_timings_s,
            "ensure_current_index_identity_seed_lanes_for_cache_reuse",
        ):
            await _ensure_current_index_identity_seed_lanes(index=index)

    code_package = CodePackage(
        id=resolved_source_code_package_id,
        code_package_config_id=stable_code_package_config_id(
            config_key=code_package_source_config_key(
                manifest_kind="aware_toml",
                surface=surface,
            ),
        ),
        package_name=package_name,
        language=CodeLanguage.aware,
        surface=surface,
        manifest_kind="aware_toml",
        manifest_relative_path=manifest_relative_path,
        package_root=package_root_relative,
        sources_root=sources_root_relative,
        fqn_prefix=fqn_prefix,
    )
    (
        object_config_graph_package,
        _language_materialization_related_models,
    ) = _build_object_config_graph_package_snapshot_root(
        object_config_graph_package_id=resolved_object_config_graph_package_id,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        source_code_package_id=resolved_source_code_package_id,
        object_config_graph_id=resolved_object_config_graph_id,
        object_config_graph_object_instance_graph_commit_id=(
            object_config_graph_oig_commit_id
        ),
        function_impl_ownership=function_impl_ownership,
        function_impl_parity_policy=function_impl_parity_policy,
        implementation_policy_source=implementation_policy_source,
        title=title,
        description=description,
        language_materialization_specs=language_materialization_specs,
        package_root=language_materialization_package_root,
        workspace_root=workspace_root,
    )
    object_config_graph_package.source_code_package = code_package
    object_config_graph_package.object_config_graph = object_config_graph
    phase_timings_s["reuse_existing_object_config_graph_package_cache"] = (
        _round_duration_s(perf_counter() - started_at)
    )
    phase_timings_s["total"] = _round_duration_s(perf_counter() - package_started_at)
    logger.info(
        "Meta package leaf ObjectConfigGraphPackage fingerprint reuse: package=%s",
        package_name,
    )
    result = ObjectConfigGraphPackageLeafMaterializationResult(
        aware_toml_path=aware_toml_path,
        package_branch_id=branch_id,
        code_package=code_package,
        object_config_graph_package=object_config_graph_package,
        object_config_graph=object_config_graph,
        owned_file_paths=owned_file_paths,
        code_package_commit_id=None,
        code_package_head_commit_id=code_package_head_commit_id,
        code_package_object_instance_graph_commit_id=code_package_oig_commit_id,
        object_config_graph_commit_id=None,
        object_config_graph_head_commit_id=object_config_graph_head_commit_id,
        object_config_graph_object_instance_graph_commit_id=(
            object_config_graph_oig_commit_id
        ),
        object_config_graph_package_commit_id=None,
        object_config_graph_package_head_commit_id=(
            object_config_graph_package_head_commit_id
        ),
        object_config_graph_package_object_instance_graph_commit_id=(
            object_config_graph_package_oig_commit_id
        ),
        phase_timings_s=dict(sorted(phase_timings_s.items())),
        code_package_build_runtime_telemetry={},
        code_package_build_invoke_perf_ms={},
        code_package_upsert_runtime_telemetry={},
        code_package_upsert_invoke_perf_ms={},
        semantic_commit_strategy="fingerprint_reuse",
        semantic_commit_fallback_reset=False,
        semantic_commit_phase_timings_s={},
        object_config_graph_payload=object_config_graph_payload,
    )
    cached_index_receipt = _materialization_index_receipt_from_reuse_cache(payload)
    if cached_index_receipt is None:
        result = _with_materialization_index_receipt(
            result=result,
            source_manifest_hash=source_manifest_hash,
            dependency_signature=dependency_signature,
            cache_status="fingerprint_reuse",
            code_package_projection_hash=code_package_projection_hash,
            object_config_graph_projection_hash=object_config_graph_projection_hash,
            object_config_graph_package_projection_hash=(
                object_config_graph_package_projection_hash
            ),
        )
    else:
        result = replace(
            result,
            materialization_index_receipt=cached_index_receipt,
        )
    _write_object_config_graph_package_reuse_cache(
        result=result,
        source_manifest_hash=source_manifest_hash,
        dependency_signature=dependency_signature,
    )
    if workspace_root is not None and module_root is not None:
        _record_runtime_package_projection_index(
            result=result,
            workspace_root=workspace_root,
            module_root=module_root,
            source_manifest_hash=source_manifest_hash,
            dependency_signature=dependency_signature,
        )
    return result


def _write_object_config_graph_package_reuse_cache(
    *,
    result: ObjectConfigGraphPackageLeafMaterializationResult,
    source_manifest_hash: str,
    dependency_signature: str,
) -> None:
    try:
        object_config_graph = result.object_config_graph
        payload = {
            "v": _PACKAGE_REUSE_CACHE_VERSION,
            "cache_kind": (
                OBJECT_CONFIG_GRAPH_PACKAGE_REUSE_CACHE_KIND_MATERIALIZED_PACKAGE
            ),
            "source_manifest_hash": source_manifest_hash,
            "dependency_signature": dependency_signature,
            "package_name": result.object_config_graph_package.package_name,
            "fqn_prefix": result.object_config_graph_package.fqn_prefix,
            "function_impl_ownership": (
                result.object_config_graph_package.function_impl_ownership.value
            ),
            "function_impl_parity_policy": (
                result.object_config_graph_package.function_impl_parity_policy.value
            ),
            "implementation_policy_source": (
                result.object_config_graph_package.implementation_policy_source
            ),
            "source_to_ocg_lowering_signature": (
                OBJECT_CONFIG_GRAPH_SOURCE_TO_RUNTIME_LOWERING_SIGNATURE
            ),
            "language_materialization_signature": (
                _object_config_graph_package_language_materialization_manifest_signature(
                    object_config_graph_package=result.object_config_graph_package,
                )
            ),
            "source_code_package_id": str(result.code_package.id),
            "code_package_package_name": result.code_package.package_name,
            "code_package_language": _enum_text(result.code_package.language),
            "code_package_surface": _enum_text(result.code_package.surface),
            "code_package_manifest_kind": "aware_toml",
            "code_package_manifest_relative_path": (
                result.code_package.manifest_relative_path
            ),
            "code_package_package_root": result.code_package.package_root,
            "code_package_sources_root": result.code_package.sources_root,
            "code_package_fqn_prefix": result.code_package.fqn_prefix,
            "object_config_graph_id": str(object_config_graph.id),
            "object_config_graph_hash": str(object_config_graph.hash or ""),
            "object_config_graph_package_id": str(
                result.object_config_graph_package.id
            ),
            "code_package_head_commit_id": (
                None
                if result.code_package_head_commit_id is None
                else str(result.code_package_head_commit_id)
            ),
            "code_package_object_instance_graph_commit_id": (
                None
                if result.code_package_object_instance_graph_commit_id is None
                else str(result.code_package_object_instance_graph_commit_id)
            ),
            "object_config_graph_head_commit_id": (
                None
                if result.object_config_graph_head_commit_id is None
                else str(result.object_config_graph_head_commit_id)
            ),
            "object_config_graph_object_instance_graph_commit_id": (
                None
                if result.object_config_graph_object_instance_graph_commit_id is None
                else str(result.object_config_graph_object_instance_graph_commit_id)
            ),
            "object_config_graph_package_head_commit_id": (
                None
                if result.object_config_graph_package_head_commit_id is None
                else str(result.object_config_graph_package_head_commit_id)
            ),
            "object_config_graph_package_object_instance_graph_commit_id": (
                None
                if result.object_config_graph_package_object_instance_graph_commit_id
                is None
                else str(
                    result.object_config_graph_package_object_instance_graph_commit_id
                )
            ),
            "owned_file_paths": list(result.owned_file_paths),
            "materialization_index_receipt": result.materialization_index_receipt,
            "object_config_graph": _object_config_graph_payload_for_reuse_cache_write(
                result=result,
            ),
            _OBJECT_CONFIG_GRAPH_SOURCE_SECTIONS_CACHE_KEY: (
                _object_config_graph_source_sections_payload(result.object_config_graph)
            ),
        }
        _write_reuse_cache_payload(
            branch_id=result.package_branch_id,
            object_config_graph_package_id=result.object_config_graph_package.id,
            payload=payload,
        )
    except Exception as exc:
        logger.warning(
            "Meta package leaf failed to write ObjectConfigGraphPackage reuse cache: %s",
            exc,
        )


def _record_runtime_package_projection_index(
    *,
    result: ObjectConfigGraphPackageLeafMaterializationResult,
    workspace_root: Path,
    module_root: Path,
    source_manifest_hash: str,
    dependency_signature: str,
) -> None:
    try:
        package = result.object_config_graph_package
        record_full_package_materialization_index(
            repo_root=workspace_root,
            aware_root=workspace_root,
            materialized_package_name=package.package_name,
            package_entries=(
                MetaRuntimePackageIndexEntry(
                    module_id=module_root.name,
                    package_name=package.package_name,
                    fqn_prefix=package.fqn_prefix,
                    manifest_path=result.aware_toml_path,
                    projection_names=tuple(
                        sorted(
                            {
                                projection.name
                                for projection in result.object_config_graph.object_projection_graphs
                                if projection.name
                            }
                        )
                    ),
                ),
            ),
            object_config_graph_payload=(
                _object_config_graph_payload_for_reuse_cache_write(result=result)
            ),
            materialization_index_receipt=result.materialization_index_receipt,
            source_manifest_hash=source_manifest_hash,
            dependency_signature=dependency_signature,
        )
    except Exception as exc:
        logger.warning(
            "Meta package leaf failed to write runtime package projection index: %s",
            exc,
        )


def _object_config_graph_payload_for_reuse_cache_write(
    *,
    result: ObjectConfigGraphPackageLeafMaterializationResult,
) -> dict[str, object]:
    if result.object_config_graph_payload is not None:
        payload = dict(result.object_config_graph_payload)
    else:
        payload = result.object_config_graph.model_dump(
            mode="json",
            by_alias=True,
            exclude_none=True,
        )
    payload["namespace_membership"] = list(
        build_namespace_membership_payload_from_ocg_identity(
            ocg=result.object_config_graph,
        )
    )
    return payload


def _is_within(*, candidate: Path, root: Path) -> bool:
    try:
        candidate.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _has_ignored_segment(parts: tuple[str, ...]) -> bool:
    return any(part in _IGNORED_SEGMENTS for part in parts)


def _read_single_root_runtime_lane_head(
    *,
    aware_root: Path,
    branch_id: UUID,
    projection_hash: str,
) -> dict[str, str] | None:
    lane_dir = aware_root / ".aware" / "oig" / str(branch_id) / projection_hash
    head_path = lane_dir / "HEAD.json"
    commits_dir = lane_dir / "commits"
    if not head_path.exists() or not commits_dir.is_dir():
        return None

    try:
        loaded = cast(object, json.loads(head_path.read_text(encoding="utf-8")))
    except Exception:
        return None
    if not isinstance(loaded, dict):
        return None
    head_payload = cast(dict[object, object], loaded)
    head_commit_id = head_payload.get("commit_id")
    head_graph_hash_post = head_payload.get("graph_hash_post")
    if not isinstance(head_commit_id, str) or not head_commit_id.strip():
        return None
    if not isinstance(head_graph_hash_post, str) or not head_graph_hash_post.strip():
        return None

    commit_path = commits_dir / f"{head_commit_id}.json"
    if not commit_path.exists():
        return None
    try:
        commit_loaded = cast(
            object, json.loads(commit_path.read_text(encoding="utf-8"))
        )
    except Exception:
        return None
    if not isinstance(commit_loaded, dict):
        return None
    commit_payload = cast(dict[object, object], commit_loaded)
    commit_obj = commit_payload.get("commit")
    if not isinstance(commit_obj, dict):
        return None
    parents = commit_obj.get("commit_parents")
    if not isinstance(parents, list) or parents:
        return None

    return {
        "commit_id": head_commit_id.strip(),
        "graph_hash_post": head_graph_hash_post.strip(),
    }


def _iter_graph_identity_lane_seed_specs(
    *,
    graph: ObjectConfigGraph,
) -> tuple[_GraphIdentityLaneSeedSpec, ...]:
    ocgi = graph.object_config_graph_identity
    if ocgi is None:
        raise RuntimeError(
            "Meta package leaf materialization requires ObjectConfigGraphIdentity on the runtime index graph"
        )

    specs: list[_GraphIdentityLaneSeedSpec] = [
        _GraphIdentityLaneSeedSpec(
            root_instance=ocgi,
            branch_id=ocgi.id,
            opg_name="ObjectConfigGraphIdentity",
        )
    ]

    for opg in graph.object_projection_graphs:
        if not (opg.name or "").strip():
            continue
        opgi = synthesize_object_projection_graph_identity(
            object_config_graph_identity=ocgi,
            object_projection_graph=opg,
        )
        specs.append(
            _GraphIdentityLaneSeedSpec(
                root_instance=opgi,
                branch_id=opgi.id,
                opg_name="ObjectProjectionGraphIdentity",
            )
        )

    return tuple(specs)


async def _ensure_current_index_identity_seed_lanes(
    *,
    index: MetaGraphRuntimeIndex,
) -> None:
    store = FSCommitStore()
    aware_root = store.aware_root
    cache = get_shared_materialization_cache()
    if _current_index_identity_seed_lane_ensure_cache_hit(index=index, cache=cache):
        return

    ensured_lane_keys: list[tuple[UUID, str, str, str]] = []
    for spec in _iter_graph_identity_lane_seed_specs(graph=index.ocg):
        expected_plan = await preview_graph_identity_seed_plan(
            root_instance=spec.root_instance,
            ocg=index.ocg,
            branch_id=spec.branch_id,
            opg_name=spec.opg_name,
            external_graphs=(),
        )
        expected_commit_id = expected_plan.commit_id
        expected_graph_hash_post = str(expected_plan.graph_hash_post or "").strip()
        expected_projection_hash = str(expected_plan.projection_hash or "").strip()
        if (
            expected_commit_id is None
            or not expected_graph_hash_post
            or not expected_projection_hash
        ):
            raise RuntimeError(
                "Meta package leaf materialization could not derive deterministic identity seed truth: "
                f"branch_id={spec.branch_id} opg_name={spec.opg_name!r}"
            )

        lane_sample = _read_single_root_runtime_lane_head(
            aware_root=aware_root,
            branch_id=spec.branch_id,
            projection_hash=expected_projection_hash,
        )
        if lane_sample is not None and (
            lane_sample["commit_id"] != str(expected_commit_id)
            or lane_sample["graph_hash_post"] != expected_graph_hash_post
        ):
            _reset_generated_projection_lanes(
                aware_root=aware_root,
                branch_id=spec.branch_id,
                projection_hashes=(expected_projection_hash,),
            )
            cache.invalidate_lane(
                branch_id=spec.branch_id,
                projection_hash=expected_projection_hash,
            )

        await ensure_graph_identity_seeded_lane(
            root_instance=spec.root_instance,
            ocg=index.ocg,
            branch_id=spec.branch_id,
            opg_name=spec.opg_name,
            external_graphs=(),
            store=store,
            allow_append=True,
        )
        ensured_lane_keys.append(
            (
                spec.branch_id,
                expected_projection_hash,
                str(expected_commit_id),
                expected_graph_hash_post,
            )
        )
    _remember_current_index_identity_seed_lane_ensure(
        index=index,
        cache=cache,
        lane_keys=tuple(ensured_lane_keys),
    )


def _current_index_identity_seed_lane_ensure_cache_hit(
    *,
    index: MetaGraphRuntimeIndex,
    cache: Any,
) -> bool:
    index_cache_key = id(index)
    with _CURRENT_INDEX_IDENTITY_SEED_LANE_ENSURE_CACHE_LOCK:
        entry = _CURRENT_INDEX_IDENTITY_SEED_LANE_ENSURE_CACHE.get(index_cache_key)
    if entry is None:
        return False

    object_config_graph_id = getattr(index.ocg, "id", None)
    object_config_graph_hash = str(getattr(index.ocg, "hash", "") or "").strip()
    if (
        entry.object_config_graph_id != object_config_graph_id
        or entry.object_config_graph_hash != object_config_graph_hash
    ):
        with _CURRENT_INDEX_IDENTITY_SEED_LANE_ENSURE_CACHE_LOCK:
            _CURRENT_INDEX_IDENTITY_SEED_LANE_ENSURE_CACHE.pop(index_cache_key, None)
        return False

    aware_root = FSCommitStore().aware_root
    for (
        branch_id,
        projection_hash,
        revision,
        expected_commit_id,
        expected_graph_hash_post,
    ) in entry.lane_revisions:
        current_revision = cache.current_lane_revision(
            branch_id=branch_id,
            projection_hash=projection_hash,
        )
        if int(current_revision) != int(revision):
            with _CURRENT_INDEX_IDENTITY_SEED_LANE_ENSURE_CACHE_LOCK:
                _CURRENT_INDEX_IDENTITY_SEED_LANE_ENSURE_CACHE.pop(
                    index_cache_key,
                    None,
                )
            return False
        lane_sample = _read_single_root_runtime_lane_head(
            aware_root=aware_root,
            branch_id=branch_id,
            projection_hash=projection_hash,
        )
        if lane_sample is None or (
            lane_sample["commit_id"] != expected_commit_id
            or lane_sample["graph_hash_post"] != expected_graph_hash_post
        ):
            with _CURRENT_INDEX_IDENTITY_SEED_LANE_ENSURE_CACHE_LOCK:
                _CURRENT_INDEX_IDENTITY_SEED_LANE_ENSURE_CACHE.pop(
                    index_cache_key,
                    None,
                )
            return False
    return True


def _remember_current_index_identity_seed_lane_ensure(
    *,
    index: MetaGraphRuntimeIndex,
    cache: Any,
    lane_keys: tuple[tuple[UUID, str, str, str], ...],
) -> None:
    lane_revisions = tuple(
        (
            branch_id,
            projection_hash,
            int(
                cache.current_lane_revision(
                    branch_id=branch_id,
                    projection_hash=projection_hash,
                )
            ),
            expected_commit_id,
            expected_graph_hash_post,
        )
        for (
            branch_id,
            projection_hash,
            expected_commit_id,
            expected_graph_hash_post,
        ) in lane_keys
    )
    entry = _CurrentIndexIdentitySeedLaneEnsureCacheEntry(
        object_config_graph_id=getattr(index.ocg, "id", None),
        object_config_graph_hash=str(getattr(index.ocg, "hash", "") or "").strip(),
        lane_revisions=lane_revisions,
    )
    with _CURRENT_INDEX_IDENTITY_SEED_LANE_ENSURE_CACHE_LOCK:
        _CURRENT_INDEX_IDENTITY_SEED_LANE_ENSURE_CACHE[id(index)] = entry


async def _reset_invalid_package_branch_if_needed(
    *,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    projection_hashes: tuple[str, ...],
    phase_timings_s: dict[str, float] | None = None,
) -> bool:
    store = FSCommitStore()
    normalized_projection_hashes = tuple(
        dict.fromkeys(
            str(projection_hash or "").strip()
            for projection_hash in projection_hashes
            if projection_hash
        )
    )
    if not normalized_projection_hashes:
        return False

    for projection_hash in normalized_projection_hashes:
        projection_phase_key = _projection_phase_key(projection_hash=projection_hash)
        with _maybe_record_phase(
            phase_timings_s,
            f"reset_invalid_package_branch_if_needed.{projection_phase_key}.read_head",
        ):
            head = await store.head(
                branch_id=branch_id, projection_hash=projection_hash
            )
        if head is None or head.get("commit_id") is None:
            continue

        opg = index.opg_by_hash.get(projection_hash)
        if opg is None:
            raise RuntimeError(
                f"Meta package leaf materialization missing projection hash: {projection_hash}"
            )
        projection_phase_key = _projection_phase_key(
            projection_hash=projection_hash,
            opg=opg,
        )

        valid, reason = await _projection_lane_head_is_structurally_healthy(
            index=index,
            opg=opg,
            store=store,
            branch_id=branch_id,
            projection_hash=projection_hash,
            head=head,
            phase_timings_s=phase_timings_s,
            phase_prefix=f"reset_invalid_package_branch_if_needed.{projection_phase_key}",
        )
        if not valid:
            logger.info(
                "Meta package leaf invalid projection lane detected: branch_id=%s projection_hash=%s reason=%s",
                branch_id,
                projection_hash,
                reason,
            )
            _reset_generated_package_branch(
                aware_root=store.aware_root,
                branch_id=branch_id,
                projection_hashes=normalized_projection_hashes,
            )
            return True

    return False


def _projection_phase_key(
    *,
    projection_hash: str,
    opg: ObjectProjectionGraph | None = None,
) -> str:
    raw_name = ""
    if opg is not None:
        raw_name = str(
            getattr(opg, "name", "") or getattr(opg, "projection_name", "") or ""
        )
    raw_name = raw_name.strip() or projection_hash[:12]
    normalized = "".join(
        char.lower() if char.isalnum() else "_" for char in raw_name
    ).strip("_")
    return normalized or "projection"


async def _projection_lane_head_is_structurally_healthy(
    *,
    index: MetaGraphRuntimeIndex,
    opg: ObjectProjectionGraph,
    store: FSCommitStore,
    branch_id: UUID,
    projection_hash: str,
    head: object,
    phase_timings_s: dict[str, float] | None = None,
    phase_prefix: str = "projection_lane_head_is_structurally_healthy",
) -> tuple[bool, str]:
    if not isinstance(head, Mapping):
        return False, "head_not_object"
    head_payload = cast(Mapping[str, object], head)
    head_commit_id = _payload_uuid(head_payload, "commit_id")
    if head_commit_id is None:
        return False, "head_missing_commit_id"
    head_graph_hash_post = _payload_string(head_payload, "graph_hash_post")
    if head_graph_hash_post is None:
        return False, "head_missing_graph_hash_post"
    head_oig_id = _payload_uuid(head_payload, "object_instance_graph_id")

    with _maybe_record_phase(phase_timings_s, f"{phase_prefix}.read_commit_health"):
        commit_health = await store.get_commit_health_metadata(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=head_commit_id,
        )
    commit_oig_id: UUID
    commit_graph_hash_post: str
    if commit_health is not None:
        if commit_health.parent_count > 1:
            return False, "commit_payload_invalid:non_linear_history"
        if commit_health.graph_hash_post != head_graph_hash_post:
            return False, "head_graph_hash_post_mismatch"
        if (
            head_oig_id is not None
            and commit_health.object_instance_graph_id != head_oig_id
        ):
            return False, "head_object_instance_graph_id_mismatch"
        commit_oig_id = commit_health.object_instance_graph_id
        commit_graph_hash_post = commit_health.graph_hash_post
    else:
        with _maybe_record_phase(phase_timings_s, f"{phase_prefix}.read_commit"):
            commit = await store.get_commit(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=head_commit_id,
            )
        if commit is None:
            return False, "head_commit_missing"
        if commit.commit.id != head_commit_id:
            return False, "commit_id_mismatch"
        if commit.graph_hash_post != head_graph_hash_post:
            return False, "head_graph_hash_post_mismatch"
        if head_oig_id is not None and commit.object_instance_graph_id != head_oig_id:
            return False, "head_object_instance_graph_id_mismatch"

        with _maybe_record_phase(phase_timings_s, f"{phase_prefix}.validate_commit"):
            try:
                validate_object_instance_graph_commit(
                    commit=commit,
                    expected_object_instance_graph_id=head_oig_id,
                    expected_projection_hash=projection_hash,
                    require_linear_history=True,
                )
            except OigCommitValidationError as exc:
                return False, f"commit_payload_invalid:{exc}"
        store.write_commit_health_metadata(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit=commit,
        )
        commit_oig_id = commit.object_instance_graph_id
        commit_graph_hash_post = commit.graph_hash_post

    snapshot_store = FSSnapshotStore(root_dir=store.aware_root)
    with _maybe_record_phase(phase_timings_s, f"{phase_prefix}.read_snapshot_health"):
        snapshot_health = await snapshot_store.get_snapshot_health_metadata(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=head_commit_id,
        )
    if snapshot_health is not None:
        if snapshot_health.object_instance_graph_id != commit_oig_id:
            return False, "snapshot_object_instance_graph_id_mismatch"
        if (
            snapshot_health.graph_hash
            and snapshot_health.graph_hash != commit_graph_hash_post
        ):
            return False, "snapshot_graph_hash_mismatch"
        return True, "ok"

    with _maybe_record_phase(phase_timings_s, f"{phase_prefix}.check_snapshot_exists"):
        snapshot_exists = snapshot_store.has_snapshot(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=head_commit_id,
        )
    if not snapshot_exists:
        return True, "ok"

    with _maybe_record_phase(phase_timings_s, f"{phase_prefix}.read_snapshot"):
        snapshot = await snapshot_store.get(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=head_commit_id,
        )
    if snapshot is not None:
        graph_snapshot, _indexes = snapshot
        if graph_snapshot.id != commit_oig_id:
            return False, "snapshot_object_instance_graph_id_mismatch"
        snapshot_hash = str(graph_snapshot.hash or "").strip()
        if snapshot_hash and snapshot_hash != commit_graph_hash_post:
            return False, "snapshot_graph_hash_mismatch"
        with _maybe_record_phase(
            phase_timings_s, f"{phase_prefix}.validate_snapshot_opg"
        ):
            try:
                validate_object_instance_graph_against_opg(
                    graph=graph_snapshot,
                    object_config_graph=index.ocg,
                    object_projection_graph=opg,
                )
            except OigValidationError as exc:
                return False, f"snapshot_opg_invalid:{exc}"
        snapshot_store.write_snapshot_health_metadata(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=head_commit_id,
            oig=graph_snapshot,
        )

    return True, "ok"


def _reset_generated_package_branch(
    *,
    aware_root: Path,
    branch_id: UUID,
    projection_hashes: tuple[str, ...],
) -> None:
    branch_dir = aware_root / ".aware" / "oig" / str(branch_id)
    if branch_dir.exists():
        shutil.rmtree(branch_dir)

    _reset_generated_projection_lanes(
        aware_root=aware_root,
        branch_id=branch_id,
        projection_hashes=projection_hashes,
    )


def _reset_generated_projection_lanes(
    *,
    aware_root: Path,
    branch_id: UUID,
    projection_hashes: tuple[str, ...],
) -> None:
    branch_dir = aware_root / ".aware" / "oig" / str(branch_id)
    cache = get_shared_materialization_cache()
    for projection_hash in projection_hashes:
        lane_dir = branch_dir / projection_hash
        if lane_dir.exists():
            shutil.rmtree(lane_dir)
        cache.invalidate_lane(branch_id=branch_id, projection_hash=projection_hash)
    if branch_dir.exists() and not any(branch_dir.iterdir()):
        shutil.rmtree(branch_dir)


def _object_config_graph_semantic_delta(
    *,
    previous_graph: ObjectConfigGraph,
    current_graph: ObjectConfigGraph,
) -> ObjectConfigGraphDelta:
    return ObjectConfigGraphDelta(
        object_config_graph_id=current_graph.id,
        language=current_graph.language or CodeLanguage.aware,
        graph_hash_pre=str(previous_graph.hash or "").strip() or None,
        graph_hash_post=str(current_graph.hash or "").strip() or None,
        node_deltas=diff_object_config_graph_nodes(
            before=previous_graph,
            after=current_graph,
        ),
        warnings=[],
    )


def _instance_external_graphs_for_semantic_delta_commit(
    *,
    index: MetaGraphRuntimeIndex,
    lane_external_graphs: tuple[ObjectConfigGraph, ...],
) -> tuple[ObjectConfigGraph, ...]:
    schema_graph_id = index.ocg.id
    return tuple(graph for graph in lane_external_graphs if graph.id != schema_graph_id)


def _semantic_delta_commit_instance_model_guard_reason(
    *,
    previous_graph: ObjectConfigGraph,
    current_graph: ObjectConfigGraph,
    instance_external_graphs: tuple[ObjectConfigGraph, ...],
    phase_timings_s: dict[str, float],
) -> str | None:
    max_instance_models = _int_env(
        "AWARE_META_SEMANTIC_DELTA_COMMIT_MAX_INSTANCE_MODELS",
        default=25_000,
    )
    phase_timings_s["semantic_delta_commit_preflight.metric.max_instance_models"] = (
        float(max_instance_models)
    )
    if max_instance_models <= 0:
        phase_timings_s["semantic_delta_commit_preflight.metric.guard_disabled"] = 1.0
        return None

    previous_model_count = len(
        collect_lane_instance_models(
            ocg=previous_graph,
            external_graphs=instance_external_graphs,
        )
    )
    current_model_count = len(
        collect_lane_instance_models(
            ocg=current_graph,
            external_graphs=instance_external_graphs,
        )
    )
    max_model_count = max(previous_model_count, current_model_count)
    phase_timings_s["semantic_delta_commit_preflight.metric.instance_models_pre"] = (
        float(previous_model_count)
    )
    phase_timings_s["semantic_delta_commit_preflight.metric.instance_models_post"] = (
        float(current_model_count)
    )
    if max_model_count <= max_instance_models:
        return None
    return (
        "semantic_delta_commit_instance_model_guard:"
        f"max={max_model_count} limit={max_instance_models}"
    )


async def _canonicalize_semantic_domain_commit_identity(
    *,
    store: FSCommitStore,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    projection_hash: str,
    domain_commit: ObjectInstanceGraphCommit,
) -> ObjectInstanceGraphCommit:
    expected_oigi_id = resolve_domain_object_instance_graph_identity_id(
        index=index,
        object_instance_graph_id=domain_commit.object_instance_graph_id,
        domain_projection_hash=projection_hash,
    )
    if domain_commit.object_instance_graph_identity_id == expected_oigi_id:
        return domain_commit

    canonical_commit = domain_commit.model_copy(
        update={
            "id": stable_object_instance_graph_commit_id(
                object_instance_graph_identity_id=expected_oigi_id,
                commit_id=domain_commit.commit.id,
            ),
            "object_instance_graph_identity_id": expected_oigi_id,
        }
    )
    _ = await store.put_commit_file(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit=canonical_commit,
    )
    return canonical_commit


async def _canonicalize_semantic_domain_commit_envelope(
    *,
    store: FSCommitStore,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    projection_hash: str,
    domain_commit_envelope: ObjectInstanceGraphCommitEnvelope,
) -> ObjectInstanceGraphCommitEnvelope:
    expected_oigi_id = resolve_domain_object_instance_graph_identity_id(
        index=index,
        object_instance_graph_id=domain_commit_envelope.object_instance_graph_id,
        domain_projection_hash=projection_hash,
    )
    if domain_commit_envelope.object_instance_graph_identity_id == expected_oigi_id:
        return domain_commit_envelope

    domain_commit = await store.get_commit(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=domain_commit_envelope.commit_id,
    )
    if domain_commit is None:
        raise RuntimeError(
            "Meta package leaf materialization emitted a stale semantic OCG commit envelope "
            "but the full commit payload was unavailable for identity repair: "
            f"branch_id={branch_id} commit_id={domain_commit_envelope.commit_id}"
        )
    canonical_commit = await _canonicalize_semantic_domain_commit_identity(
        store=store,
        index=index,
        branch_id=branch_id,
        projection_hash=projection_hash,
        domain_commit=domain_commit,
    )
    return object_instance_graph_commit_envelope_from_commit(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit=canonical_commit,
    )


async def _commit_object_config_graph_to_semantic_lane(
    *,
    built_object_config_graph: ObjectConfigGraph,
    existing_object_config_graph: ObjectConfigGraph | None,
    branch_id: UUID,
    projection_hash: str,
    index: MetaGraphRuntimeIndex,
    aware_toml_path: Path,
    external_graphs: tuple[ObjectConfigGraph, ...],
    actor_id: UUID | None,
    progress_callback: MetaLeafPackageProgressCallback | None = None,
    detail_payload: Mapping[str, object] | None = None,
) -> _SemanticLaneCommitSummary:
    commit_started_at = perf_counter()
    phase_timings_s: dict[str, float] = {}
    strategy = "seed" if existing_object_config_graph is None else "delta"
    fallback_reset = False
    trusted_seed_snapshot_written = False
    lane_external_graphs = _resolve_lane_external_graphs(
        index=index,
        external_graphs=external_graphs,
    )
    if (
        existing_object_config_graph is not None
        and existing_object_config_graph.id != built_object_config_graph.id
    ):
        raise RuntimeError(
            "Meta package leaf materialization resolved ObjectConfigGraph with unexpected stable id on the "
            "semantic branch: "
            f"existing={existing_object_config_graph.id} expected={built_object_config_graph.id} "
            f"aware_toml_path={aware_toml_path}"
        )

    try:
        if existing_object_config_graph is None:
            plan, trusted_seed_snapshot_written, recovered_missing_seed = (
                await _ensure_ocg_seeded_lane_with_missing_seed_recovery(
                    ocg=built_object_config_graph,
                    branch_id=branch_id,
                    ocg_hash=str(built_object_config_graph.hash or "").strip(),
                    external_graphs=lane_external_graphs,
                    projection_hash=projection_hash,
                    index=index,
                    aware_toml_path=aware_toml_path,
                    phase_timings_s=phase_timings_s,
                    progress_callback=progress_callback,
                    detail_payload=detail_payload,
                )
            )
            commit_id = plan.commit_id
            if recovered_missing_seed:
                strategy = "seed_after_reset"
                fallback_reset = True
        else:
            async with _record_leaf_package_subphase(
                phase_timings_s,
                "derive_object_config_graph_semantic_delta",
                progress_callback,
                detail_payload=detail_payload,
            ):
                object_config_graph_delta = _object_config_graph_semantic_delta(
                    previous_graph=existing_object_config_graph,
                    current_graph=built_object_config_graph,
                )
                phase_timings_s[
                    "derive_object_config_graph_semantic_delta.metric.node_delta_count"
                ] = float(len(object_config_graph_delta.node_deltas))
            if not object_config_graph_delta.node_deltas:
                raise OcgLaneCommitError(
                    "Meta package semantic OCG graph hash changed, but the source-side "
                    "ObjectConfigGraph node delta was empty. Refusing the legacy full OIG "
                    "snapshot diff and rebuilding the semantic lane from a fresh seed. "
                    f"aware_toml_path={aware_toml_path} branch_id={branch_id}"
                )
            async with _record_leaf_package_subphase(
                phase_timings_s,
                "semantic_delta_commit_preflight",
                progress_callback,
                detail_payload=detail_payload,
            ):
                instance_external_graphs = (
                    _instance_external_graphs_for_semantic_delta_commit(
                        index=index,
                        lane_external_graphs=lane_external_graphs,
                    )
                )
                guard_reason = _semantic_delta_commit_instance_model_guard_reason(
                    previous_graph=existing_object_config_graph,
                    current_graph=built_object_config_graph,
                    instance_external_graphs=instance_external_graphs,
                    phase_timings_s=phase_timings_s,
                )
            if guard_reason is not None:
                raise OcgLaneCommitError(
                    "Meta package semantic OCG delta commit preflight refused the "
                    "legacy OCG-to-OIG diff path before OIG construction. "
                    f"{guard_reason} aware_toml_path={aware_toml_path} branch_id={branch_id}"
                )
            async with _record_leaf_package_subphase(
                phase_timings_s,
                "commit_ocg_delta_to_lane.prepare_projection",
                progress_callback,
                detail_payload=detail_payload,
            ):
                prepared_projection = prepare_ocg_seed_projection(
                    ocg=built_object_config_graph,
                    external_graphs=lane_external_graphs,
                    opg_name="ObjectConfigGraph",
                    timings=_NestedPhaseTimings(
                        phase_timings_s,
                        prefix="commit_ocg_delta_to_lane.prepare_projection",
                    ),
                )
            async with _record_leaf_package_subphase(
                phase_timings_s,
                "commit_ocg_delta_to_lane",
                progress_callback,
                detail_payload=detail_payload,
            ):
                plan = await commit_ocg_delta_to_lane(
                    previous_ocg=existing_object_config_graph,
                    ocg=built_object_config_graph,
                    delta=object_config_graph_delta,
                    branch_id=branch_id,
                    external_graphs=lane_external_graphs,
                    prepared_projection=prepared_projection,
                    projection_hash_override=projection_hash,
                    timings=_NestedPhaseTimings(
                        phase_timings_s,
                        prefix="commit_ocg_delta_to_lane",
                    ),
                )
            commit_id = plan.commit_id
    except (
        MaterializerPostHashMismatchError,
        OcgSeedError,
        OcgLaneCommitError,
        ValueError,
    ) as exc:
        if existing_object_config_graph is not None:
            fallback_reset = True
            strategy = "seed_after_reset"
            async with _record_leaf_package_subphase(
                phase_timings_s,
                "reset_generated_projection_lane",
                progress_callback,
                detail_payload=detail_payload,
            ):
                _reset_generated_projection_lanes(
                    aware_root=FSCommitStore().aware_root,
                    branch_id=branch_id,
                    projection_hashes=(projection_hash,),
                )
            try:
                async with _record_leaf_package_subphase(
                    phase_timings_s,
                    "ensure_ocg_seeded_lane_after_reset",
                    progress_callback,
                    detail_payload=detail_payload,
                ):
                    plan = await ensure_ocg_seeded_lane(
                        ocg=built_object_config_graph,
                        branch_id=branch_id,
                        ocg_hash=str(built_object_config_graph.hash or "").strip(),
                        external_graphs=lane_external_graphs,
                        projection_hash_override=projection_hash,
                        timings=_NestedPhaseTimings(
                            phase_timings_s,
                            prefix="ensure_ocg_seeded_lane_after_reset",
                        ),
                    )
                commit_id = plan.commit_id
                if plan.seeded:
                    async with _record_leaf_package_subphase(
                        phase_timings_s,
                        "write_seed_snapshot_from_plan_after_reset",
                        progress_callback,
                        detail_payload=detail_payload,
                    ):
                        await _write_seed_snapshot_from_plan(
                            plan=plan,
                            index=index,
                        )
                    trusted_seed_snapshot_written = True
            except (
                MaterializerPostHashMismatchError,
                OcgSeedError,
                OcgLaneCommitError,
                ValueError,
            ) as retry_exc:
                retry_summary = _exception_summary(retry_exc)
                logger.exception(
                    "Meta package leaf materialization failed while rebuilding ObjectConfigGraph topology "
                    "after resetting an invalid semantic OCG lane: aware_toml_path=%s branch_id=%s cause=%s",
                    aware_toml_path,
                    branch_id,
                    retry_summary,
                )
                raise RuntimeError(
                    "Meta package leaf materialization failed while rebuilding ObjectConfigGraph topology "
                    f"after resetting an invalid semantic OCG lane: aware_toml_path={aware_toml_path} "
                    f"branch_id={branch_id} cause={retry_summary}"
                ) from retry_exc
        else:
            summary = _exception_summary(exc)
            logger.exception(
                "Meta package leaf materialization failed while committing ObjectConfigGraph topology "
                "to the semantic branch: aware_toml_path=%s branch_id=%s cause=%s",
                aware_toml_path,
                branch_id,
                summary,
            )
            raise RuntimeError(
                "Meta package leaf materialization failed while committing ObjectConfigGraph topology "
                f"to the semantic branch: aware_toml_path={aware_toml_path} branch_id={branch_id} "
                f"cause={summary}"
            ) from exc

    validated_head_commit_id: UUID | None = None
    if trusted_seed_snapshot_written:
        phase_timings_s["validate_projection_lane_head.skipped_trusted_seed"] = 0.0
    else:
        async with _record_leaf_package_subphase(
            phase_timings_s,
            "validate_projection_lane_head",
            progress_callback,
            detail_payload=detail_payload,
        ):
            await _validate_projection_lane_head(
                index=index,
                branch_id=branch_id,
                projection_hash=projection_hash,
            )
    with _record_phase(phase_timings_s, "read_validated_projection_lane_head"):
        validated_head = await FSCommitStore().head(
            branch_id=branch_id,
            projection_hash=projection_hash,
        )
        validated_head_commit_id = _decode_head_commit_id(head=validated_head)

    if commit_id is not None:
        reaction_perf_ms: dict[str, int] = {}
        async with _record_leaf_package_subphase(
            phase_timings_s,
            "run_required_runtime_commit_reactions",
            progress_callback,
            detail_payload=detail_payload,
        ):
            async with _record_leaf_package_subphase(
                phase_timings_s,
                "run_required_runtime_commit_reactions.resolve_author",
                progress_callback,
                detail_payload=detail_payload,
            ):
                author_id = resolve_meta_author_id(actor_id)
            async with _record_leaf_package_subphase(
                phase_timings_s,
                "run_required_runtime_commit_reactions.open_commit_store",
                progress_callback,
                detail_payload=detail_payload,
            ):
                store = FSCommitStore()
            async with _record_leaf_package_subphase(
                phase_timings_s,
                "run_required_runtime_commit_reactions.read_domain_commit",
                progress_callback,
                detail_payload=detail_payload,
            ):
                domain_commit_envelope = await store.get_commit_envelope(
                    branch_id=branch_id,
                    projection_hash=projection_hash,
                    commit_id=commit_id,
                )
            if domain_commit_envelope is None:
                raise RuntimeError(
                    "Meta package leaf materialization emitted a missing semantic OCG commit envelope: "
                    f"aware_toml_path={aware_toml_path} branch_id={branch_id} commit_id={commit_id}"
                )
            async with _record_leaf_package_subphase(
                phase_timings_s,
                "run_required_runtime_commit_reactions.canonicalize_domain_commit_identity",
                progress_callback,
                detail_payload=detail_payload,
            ):
                domain_commit_envelope = (
                    await _canonicalize_semantic_domain_commit_envelope(
                        store=store,
                        index=index,
                        branch_id=branch_id,
                        projection_hash=projection_hash,
                        domain_commit_envelope=domain_commit_envelope,
                    )
                )
            async with _record_leaf_package_subphase(
                phase_timings_s,
                "run_required_runtime_commit_reactions.ensure_oigi_lane_head",
                progress_callback,
                detail_payload=detail_payload,
            ):
                await ensure_object_instance_graph_identity_lane_head(
                    index=index,
                    object_instance_graph_id=(
                        domain_commit_envelope.object_instance_graph_id
                    ),
                    domain_projection_hash=projection_hash,
                    author_id=author_id,
                    perf_ms=reaction_perf_ms,
                    perf_metric_prefix="ensure_object_instance_graph_identity_lane_head",
                )
            async with _record_leaf_package_subphase(
                phase_timings_s,
                "run_required_runtime_commit_reactions.dispatch_required_reactions",
                progress_callback,
                detail_payload=detail_payload,
            ):
                _ = await run_required_runtime_commit_reactions(
                    RuntimeCommitReactionContext(
                        index=index,
                        actor_id=author_id,
                        domain_branch_id=branch_id,
                        domain_projection_hash=projection_hash,
                        domain_commit_envelope=domain_commit_envelope,
                        perf_ms=reaction_perf_ms,
                        oigi_history_projector_mode="direct",
                    )
                )
        _record_perf_ms_as_phase_timings(
            phase_timings_s=phase_timings_s,
            prefix="run_required_runtime_commit_reactions",
            perf_ms=reaction_perf_ms,
        )

    with _record_phase(phase_timings_s, "read_projection_lane_head"):
        head = await FSCommitStore().head(
            branch_id=branch_id,
            projection_hash=projection_hash,
        )
    head_commit_id = _decode_head_commit_id(head=head)
    if head_commit_id is None and validated_head_commit_id is not None:
        phase_timings_s["read_projection_lane_head.recovered_from_validated_head"] = 0.0
        head_commit_id = validated_head_commit_id
    phase_timings_s["total"] = _round_duration_s(perf_counter() - commit_started_at)
    return _SemanticLaneCommitSummary(
        commit_id=commit_id,
        head_commit_id=head_commit_id,
        strategy=strategy,
        fallback_reset=fallback_reset,
        phase_timings_s=dict(sorted(phase_timings_s.items())),
    )


async def _ensure_ocg_seeded_lane_with_missing_seed_recovery(
    *,
    ocg: ObjectConfigGraph,
    branch_id: UUID,
    ocg_hash: str,
    external_graphs: tuple[ObjectConfigGraph, ...],
    projection_hash: str,
    index: MetaGraphRuntimeIndex,
    aware_toml_path: Path,
    phase_timings_s: dict[str, float],
    store: FSCommitStore | None = None,
    progress_callback: MetaLeafPackageProgressCallback | None = None,
    detail_payload: Mapping[str, object] | None = None,
) -> tuple[OCGSeedPlan, bool, bool]:
    store = store or FSCommitStore()
    async with _record_leaf_package_subphase(
        phase_timings_s,
        "ensure_ocg_seeded_lane",
        progress_callback,
        detail_payload=detail_payload,
    ):
        plan = await ensure_ocg_seeded_lane(
            ocg=ocg,
            branch_id=branch_id,
            ocg_hash=ocg_hash,
            external_graphs=external_graphs,
            store=store,
            projection_hash_override=projection_hash,
            timings=_NestedPhaseTimings(
                phase_timings_s,
                prefix="ensure_ocg_seeded_lane",
            ),
        )
    if plan.seeded:
        async with _record_leaf_package_subphase(
            phase_timings_s,
            "write_seed_snapshot_from_plan",
            progress_callback,
            detail_payload=detail_payload,
        ):
            await _write_seed_snapshot_from_plan(
                plan=plan,
                index=index,
            )
        return plan, True, False

    existing_seed_commit = await store.get_commit(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=plan.commit_id,
    )
    if existing_seed_commit is not None:
        return plan, False, False

    logger.warning(
        "Meta package leaf OCG seed lane is non-empty but missing deterministic seed commit; "
        "resetting generated projection lane: aware_toml_path=%s branch_id=%s projection_hash=%s commit_id=%s",
        aware_toml_path,
        branch_id,
        projection_hash,
        plan.commit_id,
    )
    async with _record_leaf_package_subphase(
        phase_timings_s,
        "reset_nonempty_missing_seed_projection_lane",
        progress_callback,
        detail_payload=detail_payload,
    ):
        _reset_generated_projection_lanes(
            aware_root=store.aware_root,
            branch_id=branch_id,
            projection_hashes=(projection_hash,),
        )
    async with _record_leaf_package_subphase(
        phase_timings_s,
        "ensure_ocg_seeded_lane_after_missing_seed_reset",
        progress_callback,
        detail_payload=detail_payload,
    ):
        recovered_plan = await ensure_ocg_seeded_lane(
            ocg=ocg,
            branch_id=branch_id,
            ocg_hash=ocg_hash,
            external_graphs=external_graphs,
            store=store,
            projection_hash_override=projection_hash,
            timings=_NestedPhaseTimings(
                phase_timings_s,
                prefix="ensure_ocg_seeded_lane_after_missing_seed_reset",
            ),
        )
    if recovered_plan.seeded:
        async with _record_leaf_package_subphase(
            phase_timings_s,
            "write_seed_snapshot_from_plan_after_missing_seed_reset",
            progress_callback,
            detail_payload=detail_payload,
        ):
            await _write_seed_snapshot_from_plan(
                plan=recovered_plan,
                index=index,
            )
        return recovered_plan, True, True

    recovered_seed_commit = await store.get_commit(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=recovered_plan.commit_id,
    )
    if recovered_seed_commit is None:
        raise RuntimeError(
            "Meta package leaf materialization could not recover a missing deterministic OCG seed commit "
            "after resetting the generated semantic lane: "
            f"aware_toml_path={aware_toml_path} branch_id={branch_id} "
            f"projection_hash={projection_hash} commit_id={recovered_plan.commit_id}"
        )
    return recovered_plan, False, True


def _decode_head_commit_id(*, head: object) -> UUID | None:
    if not isinstance(head, dict):
        return None
    raw_commit_id = head.get("commit_id")
    if not isinstance(raw_commit_id, str) or not raw_commit_id.strip():
        return None
    try:
        return UUID(raw_commit_id)
    except ValueError:
        return None


async def _object_instance_graph_commit_id_from_domain_commit(
    *,
    branch_id: UUID,
    projection_hash: str,
    domain_commit_id: UUID,
) -> UUID | None:
    commit_store = FSCommitStore()
    identity_metadata = await commit_store.get_commit_identity_metadata(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=domain_commit_id,
    )
    if identity_metadata is not None:
        return stable_object_instance_graph_commit_id(
            object_instance_graph_identity_id=identity_metadata.object_instance_graph_identity_id,
            commit_id=domain_commit_id,
        )
    domain_commit = await commit_store.get_commit(
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


def _resolve_lane_external_graphs(
    *,
    index: MetaGraphRuntimeIndex,
    external_graphs: tuple[ObjectConfigGraph, ...],
) -> tuple[ObjectConfigGraph, ...]:
    graphs_by_id: dict[UUID, ObjectConfigGraph] = {}
    graphs_by_id[index.ocg.id] = index.ocg
    for graph in external_graphs:
        graphs_by_id[graph.id] = graph
    return tuple(graphs_by_id.values())


def _existing_object_config_graph_head_summary_matches(
    *,
    branch_id: UUID,
    object_config_graph_projection_hash: str,
    object_config_graph_package_id: UUID,
    object_config_graph_id: UUID,
    existing_object_config_graph_head: Mapping[str, object] | None,
    built_object_config_graph: ObjectConfigGraph,
) -> tuple[bool, str]:
    """Use Meta package cache as a semantic OCG head summary.

    `HEAD.graph_hash_post` is the OIG lane hash, not the root ObjectConfigGraph
    semantic hash. The package reuse cache stores the root OCG hash plus the
    OCG lane head commit id, so it is the cheap proof we can compare against a
    freshly built OCG without hydrating the full OIG.
    """

    if existing_object_config_graph_head is None:
        return False, "head_missing"
    head_commit_id = _decode_head_commit_id(head=existing_object_config_graph_head)
    if head_commit_id is None:
        return False, "head_commit_id_missing"
    head_root_id = _payload_uuid(existing_object_config_graph_head, "root_object_id")
    if head_root_id is not None and head_root_id != object_config_graph_id:
        return False, "head_root_object_id_mismatch"
    head_projection_hash = _payload_string(
        existing_object_config_graph_head,
        "projection_hash",
    )
    if (
        head_projection_hash is not None
        and head_projection_hash != object_config_graph_projection_hash
    ):
        return False, "head_projection_hash_mismatch"

    payload = _read_reuse_cache_payload(
        branch_id=branch_id,
        object_config_graph_package_id=object_config_graph_package_id,
    )
    if payload is None:
        return False, "cache_payload_missing"
    if payload.get("v") != _PACKAGE_REUSE_CACHE_VERSION:
        return False, "cache_version_mismatch"
    if (
        payload.get("cache_kind")
        != OBJECT_CONFIG_GRAPH_PACKAGE_REUSE_CACHE_KIND_MATERIALIZED_PACKAGE
    ):
        return False, "cache_kind_mismatch"
    if _payload_uuid(payload, "object_config_graph_id") != object_config_graph_id:
        return False, "cache_object_config_graph_id_mismatch"
    if (
        _payload_uuid(payload, "object_config_graph_package_id")
        != object_config_graph_package_id
    ):
        return False, "cache_object_config_graph_package_id_mismatch"
    if _payload_uuid(payload, "object_config_graph_head_commit_id") != head_commit_id:
        return False, "cache_head_commit_id_mismatch"
    if (
        _payload_string(payload, "source_to_ocg_lowering_signature")
        != OBJECT_CONFIG_GRAPH_SOURCE_TO_RUNTIME_LOWERING_SIGNATURE
    ):
        return False, "cache_source_to_ocg_lowering_signature_mismatch"

    cached_graph_hash = _payload_string(payload, "object_config_graph_hash")
    built_graph_hash = str(built_object_config_graph.hash or "").strip()
    if not cached_graph_hash:
        return False, "cache_object_config_graph_hash_missing"
    if not built_graph_hash:
        return False, "built_object_config_graph_hash_missing"
    if cached_graph_hash != built_graph_hash:
        return False, "object_config_graph_hash_mismatch"
    return True, "ok"


def _object_config_graph_hash_matches(
    *,
    existing_object_config_graph: ObjectConfigGraph | None,
    built_object_config_graph: ObjectConfigGraph,
) -> bool:
    if existing_object_config_graph is None:
        return False
    existing_hash = str(existing_object_config_graph.hash or "").strip()
    built_hash = str(built_object_config_graph.hash or "").strip()
    return bool(existing_hash and built_hash and existing_hash == built_hash)


def _object_config_graph_package_matches(
    *,
    object_config_graph_package: ObjectConfigGraphPackage | None,
    code_package: CodePackage,
    object_config_graph: ObjectConfigGraph,
    object_config_graph_oig_commit_id: UUID,
) -> bool:
    if object_config_graph_package is None:
        return False
    return (
        object_config_graph_package.source_code_package_id == code_package.id
        and object_config_graph_package.object_config_graph_id == object_config_graph.id
        and object_config_graph_package.object_config_graph_object_instance_graph_commit_id
        == object_config_graph_oig_commit_id
    )


async def _reuse_existing_object_config_graph_semantic_lane(
    *,
    branch_id: UUID,
    projection_hash: str,
    aware_toml_path: Path,
) -> _SemanticLaneCommitSummary:
    started_at = perf_counter()
    phase_timings_s: dict[str, float] = {}
    read_started_at = perf_counter()
    head = await FSCommitStore().head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    phase_timings_s["read_projection_lane_head"] = _round_duration_s(
        perf_counter() - read_started_at
    )
    head_commit_id = _decode_head_commit_id(head=head)
    if head_commit_id is None:
        raise RuntimeError(
            "Meta package leaf materialization cannot reuse unchanged ObjectConfigGraph "
            "without a committed semantic lane head: "
            f"aware_toml_path={aware_toml_path} branch_id={branch_id}"
        )
    return _SemanticLaneCommitSummary(
        commit_id=None,
        head_commit_id=head_commit_id,
        strategy="unchanged",
        fallback_reset=False,
        phase_timings_s={
            **phase_timings_s,
            "total": _round_duration_s(perf_counter() - started_at),
        },
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

    opg = index.opg_by_hash.get(projection_hash)
    if opg is None:
        raise RuntimeError(
            f"Meta package leaf materialization missing projection hash: {projection_hash}"
        )

    head = await FSCommitStore().head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    if head is None or head.get("commit_id") is None:
        return None

    oig, _ = await CachedLaneMaterializer().get(
        branch_id=branch_id,
        ocg=index.ocg,
        opg=opg,
        commit_id=None,
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )
    return reify_oig_root_model(
        index=index,
        opg=opg,
        oig=oig,
        model_type=root_type,
        root_id=root_id,
        branch_id=branch_id,
    )


async def _validate_projection_lane_head(
    *,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    projection_hash: str,
) -> None:
    opg = index.opg_by_hash.get(projection_hash)
    if opg is None:
        raise RuntimeError(
            f"Meta package leaf materialization missing projection hash: {projection_hash}"
        )

    head = await FSCommitStore().head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    if head is None or head.get("commit_id") is None:
        raise RuntimeError(
            "Meta package leaf materialization expected a committed lane head after semantic projection commit: "
            f"branch_id={branch_id} projection_hash={projection_hash}"
        )

    _oig, _ = await CachedLaneMaterializer().get(
        branch_id=branch_id,
        ocg=index.ocg,
        opg=opg,
        commit_id=None,
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )
