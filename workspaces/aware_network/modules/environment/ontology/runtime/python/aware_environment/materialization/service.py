from __future__ import annotations

from collections.abc import Awaitable, Callable, Iterable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from fnmatch import fnmatch
from pathlib import Path
import shutil
import tomllib
from time import perf_counter
from typing import TypeVar, cast
from uuid import UUID, uuid5

from aware_code.types import JsonObject
from aware_code.semantic_materialization import (
    SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_SCHEMA,
)
from aware_code.package_surface import (
    code_package_surface_from_semantic_manifest_descriptor,
)
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_grammar.code_language_plugin import AWARE_CODE_PLUGIN
from aware_code.module_manifest.loader import load_aware_module_spec
from aware_meta.manifest.loader import load_aware_toml_spec
from aware_ontology.manifest.loader import load_aware_ontology_toml_spec
from aware_orm.models.base_model import BaseORMModel
from aware_meta_service.api_service_protocol import (
    MetaCommitEventStore,
    build_aware_meta_service_protocol_handler,
)
from aware_meta_service_dto.graph.config.package_compile import (
    MetaObjectConfigGraphPackageDependencyRef,
    MetaObjectConfigGraphPackageEnsureRequest,
    MetaObjectConfigGraphPackageEnsureResponse,
)
from aware_meta_service_protocol.protocols import (
    invoke_meta__package__ensure_object_config_graph_package,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.stable_ids import (
    stable_object_config_graph_package_id,
    stable_object_instance_graph_id,
    stable_object_instance_graph_commit_id,
)
from aware_meta.materialization import (
    MaterializationLaneContext,
    stable_object_config_graph_package_branch_id,
)
from aware_meta.graph.instance.builder import build_rooted_object_instance_graph_base
from aware_meta.graph.instance.commit.committer import (
    FSLaneCommitter,
    LaneHeadPreHashMismatchError,
)
from aware_meta.graph.instance.commit.materialization_cache import (
    get_shared_materialization_cache,
)
from aware_meta.graph.instance.commit.contract import CommitActionDescriptor
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
from aware_meta.graph.instance.diff_orm import (
    build_object_instance_graph_changes_from_orm_change_set,
)
from aware_meta_ontology.stable_ids import stable_object_instance_graph_identity_id
from aware_meta.runtime.author import resolve_author_id
from aware_meta.runtime.graph_identity import (
    resolve_meta_graph_ocgi_opgi as resolve_ocgi_opgi,
)
from aware_meta.runtime.handler_executor.contracts import MetaGraphRuntimeIndex
from aware_meta.runtime.commit.identity_lane import (
    ensure_object_instance_graph_identity_lane_head,
)
from aware_meta.runtime.oig_model_reifier import reify_oig_root_model
from aware_meta.runtime.oig_post import materialize_meta_oig_post
from aware_meta.runtime.portal_lane_resolution import (
    attach_portal_target_branch_relationship_for_object,
    resolve_portal_target_branch_ref_for_object,
)
from aware_meta.runtime.value_resolvers import default_meta_enum_option_resolver
from aware_meta.semantic_contract import META_MANIFEST_RESOLUTION
from aware_orm.session.change_collector import ORMChangeSet
from aware_service_runtime.api_ingress.host_context import (
    ServiceApiMaterializationContext,
    service_api_host_context,
)
from aware_service_runtime.contracts import ServiceOperationContext
from aware_environment.environment_config.stable_ids import (
    stable_environment_config_id,
    stable_environment_config_ontology_config_id,
)
from aware_environment.materialization.projection_catalog import (
    EnvironmentMetaProjectionCatalog,
    require_environment_meta_projection_catalog,
)
from aware_environment.materialization.environment_source import (
    EnvironmentSourceBundle,
    EnvironmentSourceError,
    merge_environment_source_bundles,
    parse_environment_source_text,
)
from aware_environment.setup_language_plugins import setup_language_plugins
from aware_environment_ontology.environment.environment_config import EnvironmentConfig
from aware_environment_ontology.environment.environment_config_package import (
    EnvironmentConfigPackage,
)
from aware_environment_ontology.environment.environment_config_package_dependency import (
    EnvironmentConfigPackageDependency,
)
from aware_environment_ontology.environment.environment_config_package_ontology_package import (
    EnvironmentConfigPackageOntologyPackage,
)
from aware_environment_ontology.stable_ids import (
    NS_ENVIRONMENT,
    stable_environment_profile_config_id,
    stable_environment_session_config_id,
    stable_environment_config_package_dependency_id,
    stable_environment_config_package_id,
    stable_environment_config_package_ontology_package_id,
    stable_process_config_id,
    stable_thread_config_id,
)
from aware_identity_ontology.stable_ids import stable_session_config_id
from aware_environment.manifest import (
    AwareEnvironmentSpec,
    load_aware_environment_spec,
)
from aware_utils.logging import logger

_TRoot = TypeVar("_TRoot", bound=BaseORMModel)


def _environment_semantic_code_package_surface_for_kind(
    package_kind: object,
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
    package_kind_value = getattr(package_kind, "value", package_kind)
    surface = code_package_surface_from_semantic_manifest_descriptor(
        descriptor,
        package_kind=(
            package_kind_value if isinstance(package_kind_value, str) else None
        ),
    )
    if surface is None:
        raise RuntimeError(
            "Meta semantic contract does not declare a code package surface for "
            f"aware.toml package kind {package_kind_value!r}."
        )
    return str(surface)


@dataclass(frozen=True, slots=True)
class EnvironmentSemanticPackageMaterializationRef:
    module_name: str
    aware_toml_path: Path
    ontology_manifest_path: str | None
    source_manifest_path: str
    manifest_relative_path: str
    package_root: str
    workspace_package_root: str
    sources_root: str | None
    package_name: str
    fqn_prefix: str
    semantic_branch_id: UUID
    code_package_id: UUID
    code_package_object_instance_graph_commit_id: UUID | None
    object_config_graph_package_id: UUID
    object_config_graph_id: UUID
    object_config_graph_hash: str | None
    object_config_graph_head_commit_id: UUID | None
    object_config_graph_package_object_instance_graph_commit_id: UUID | None
    object_config_graph_package_head_commit_id: UUID | None
    object_config_graph_object_instance_graph_commit_id: UUID | None
    phase_timings_s: Mapping[str, float]
    code_package_build_runtime_telemetry: Mapping[str, object]
    code_package_build_invoke_perf_ms: Mapping[str, int]
    code_package_upsert_runtime_telemetry: Mapping[str, object]
    code_package_upsert_invoke_perf_ms: Mapping[str, int]
    semantic_commit_strategy: str
    semantic_commit_fallback_reset: bool
    semantic_commit_phase_timings_s: Mapping[str, float]
    artifact_ownership_receipts: tuple[Mapping[str, object], ...] = ()
    code_package_head_commit_id: UUID | None = None
    ontology_config_id: UUID | None = None
    ontology_config_commit_id: UUID | None = None
    ontology_config_head_commit_id: UUID | None = None
    ontology_config_object_instance_graph_commit_id: UUID | None = None
    ontology_package_id: UUID | None = None
    ontology_package_commit_id: UUID | None = None
    ontology_package_head_commit_id: UUID | None = None
    ontology_package_object_instance_graph_commit_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class EnvironmentConfigPackageDependencyMaterializationRef:
    dependency_role: str
    dependency_index: int
    target_handle: str
    target_environment_config_package_id: UUID
    target_environment_config_package_object_instance_graph_commit_id: UUID
    manifest_path: Path
    manifest_toml_path: Path


@dataclass(frozen=True, slots=True)
class EnvironmentPackageMaterializationResult:
    environment_toml_path: Path
    environment_spec: AwareEnvironmentSpec
    environment_config: EnvironmentConfig
    environment_package: EnvironmentConfigPackage
    semantic_package_names: tuple[str, ...]
    code_module_names: tuple[str, ...]
    semantic_packages: tuple[EnvironmentSemanticPackageMaterializationRef, ...]
    environment_package_dependencies: tuple[
        EnvironmentConfigPackageDependencyMaterializationRef, ...
    ]
    semantic_object_config_graphs: tuple[ObjectConfigGraph, ...]
    environment_config_ontology_membership_ids: tuple[UUID, ...]
    environment_package_ontology_membership_ids: tuple[UUID, ...]
    environment_commit_id: UUID | None
    environment_head_commit_id: UUID | None
    environment_config_object_instance_graph_commit_id: UUID | None
    code_package_commit_id: UUID | None
    code_package_head_commit_id: UUID | None
    object_config_graph_commit_id: UUID | None
    object_config_graph_head_commit_id: UUID | None
    object_config_graph_package_commit_id: UUID | None
    object_config_graph_package_head_commit_id: UUID | None
    package_commit_id: UUID | None
    package_head_commit_id: UUID | None
    package_object_instance_graph_commit_id: UUID | None
    phase_timings_s: Mapping[str, float]
    environment_profile_config_portal_target_branch_ids: tuple[UUID, ...] = ()
    environment_profile_config_object_instance_graph_commit_ids: tuple[UUID, ...] = ()
    environment_session_config_portal_target_branch_ids: tuple[UUID, ...] = ()
    environment_session_config_object_instance_graph_commit_ids: tuple[UUID, ...] = ()


@dataclass(frozen=True, slots=True)
class EnvironmentSemanticPackageMaterializationProgress:
    event_key: str
    status: str
    generated_at_utc: str
    environment_handle: str
    environment_toml_path: Path
    package_name: str
    module_name: str
    manifest_relative_path: str
    package_index: int
    package_count: int
    fqn_prefix: str
    duration_s: float | None = None
    error: str | None = None
    phase_timings_s: Mapping[str, float] | None = None
    code_package_build_runtime_telemetry: Mapping[str, object] | None = None
    code_package_build_invoke_perf_ms: Mapping[str, int] | None = None
    code_package_upsert_runtime_telemetry: Mapping[str, object] | None = None
    code_package_upsert_invoke_perf_ms: Mapping[str, int] | None = None
    semantic_commit_strategy: str | None = None
    semantic_commit_fallback_reset: bool | None = None
    semantic_commit_phase_timings_s: Mapping[str, float] | None = None


EnvironmentSemanticPackageProgressCallback = Callable[
    [EnvironmentSemanticPackageMaterializationProgress],
    Awaitable[None] | None,
]


@dataclass(frozen=True, slots=True)
class _MetaServicePackageMaterializationResult:
    aware_toml_path: Path
    package_branch_id: UUID
    code_package_id: UUID
    object_config_graph_package_id: UUID
    object_config_graph: ObjectConfigGraph
    object_config_graph_payload: Mapping[str, object] | None
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
    artifact_ownership_receipts: tuple[Mapping[str, object], ...] = ()


@dataclass(frozen=True, slots=True)
class _EnvironmentConfigSnapshotCommitResult:
    environment_config: EnvironmentConfig
    environment_config_commit_id: UUID
    environment_config_head_commit_id: UUID
    environment_config_object_instance_graph_commit_id: UUID
    environment_config_object_instance_graph_id: UUID
    environment_config_object_instance_graph_identity_id: UUID
    commit_perf_ms: Mapping[str, int]


@dataclass(frozen=True, slots=True)
class _EnvironmentPortalTargetSnapshotCommitResult:
    root_object_id: UUID
    branch_id: UUID
    projection_hash: str
    commit_id: UUID
    head_commit_id: UUID
    object_instance_graph_commit_id: UUID
    object_instance_graph_id: UUID
    object_instance_graph_identity_id: UUID
    commit_perf_ms: Mapping[str, int]


@dataclass(frozen=True, slots=True)
class _EnvironmentPackageSnapshotCommitResult:
    package: EnvironmentConfigPackage
    ontology_membership_ids: tuple[UUID, ...]
    package_commit_id: UUID
    package_head_commit_id: UUID
    package_object_instance_graph_commit_id: UUID
    commit_perf_ms: Mapping[str, int]


@dataclass(frozen=True, slots=True)
class _OntologyPackageSnapshotCommitResult:
    ontology_package_id: UUID
    package_commit_id: UUID
    package_head_commit_id: UUID
    package_object_instance_graph_commit_id: UUID
    commit_perf_ms: Mapping[str, int]


@dataclass(frozen=True, slots=True)
class _OntologyConfigSnapshotCommitResult:
    ontology_config_id: UUID
    config_commit_id: UUID
    config_head_commit_id: UUID
    config_object_instance_graph_commit_id: UUID
    commit_perf_ms: Mapping[str, int]


def _round_duration_s(duration_s: float) -> float:
    return round(max(duration_s, 0.0), 6)


def _uuid_from_head(head: Mapping[str, object], key: str) -> UUID | None:
    raw = head.get(key)
    if isinstance(raw, UUID):
        return raw
    if isinstance(raw, str) and raw.strip():
        return UUID(raw)
    return None


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


def _reset_generated_projection_lane(
    *,
    store: FSCommitStore,
    branch_id: UUID,
    projection_hash: str,
) -> None:
    branch_dir = store.aware_root / ".aware" / "oig" / str(branch_id)
    lane_dir = branch_dir / projection_hash
    if lane_dir.exists():
        shutil.rmtree(lane_dir)
    get_shared_materialization_cache().invalidate_lane(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    if branch_dir.exists() and not any(branch_dir.iterdir()):
        shutil.rmtree(branch_dir)


def _reset_generated_projection_lane_with_identity(
    *,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    projection_hash: str,
    object_instance_graph_id: UUID | None,
    error_context: str,
    stale_reason: str,
    projection_catalog: EnvironmentMetaProjectionCatalog | None = None,
) -> None:
    store = FSCommitStore()
    _reset_generated_projection_lane(
        store=store,
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    if object_instance_graph_id is not None:
        try:
            resolved_projection_catalog = require_environment_meta_projection_catalog(
                projection_catalog or index,
                required_projection_names=("ObjectInstanceGraphIdentity",),
                source="_reset_generated_projection_lane_with_identity",
            )
            oigi_projection_hash = resolved_projection_catalog.projection_hash_for_name(
                "ObjectInstanceGraphIdentity"
            )
        except Exception:
            oigi_projection_hash = None
        if oigi_projection_hash:
            _reset_generated_projection_lane(
                store=store,
                branch_id=object_instance_graph_id,
                projection_hash=oigi_projection_hash,
            )
    logger.warning(
        "%s reset stale generated projection lane: branch_id=%s projection_hash=%s reason=%s",
        error_context,
        branch_id,
        projection_hash,
        stale_reason,
    )


def _build_environment_config_snapshot(
    *,
    environment_config_id: UUID,
    handle: str,
    title: str,
    canonical_language: CodeLanguage,
    languages: Iterable[CodeLanguage],
    semantic_packages: Iterable[EnvironmentSemanticPackageMaterializationRef],
    environment_sources: EnvironmentSourceBundle | None = None,
    description: str | None,
    is_kernel: bool,
) -> EnvironmentConfig:
    ontology_configs = [
        _build_environment_config_ontology_membership(
            environment_config_id=environment_config_id,
            semantic_package=semantic_package,
        )
        for semantic_package in semantic_packages
    ]
    profile_configs, session_configs = _build_environment_config_topology(
        environment_config_id=environment_config_id,
        environment_sources=environment_sources or EnvironmentSourceBundle(),
    )
    return EnvironmentConfig.model_construct(
        id=environment_config_id,
        ontology_configs=ontology_configs,
        profile_configs=profile_configs,
        session_configs=session_configs,
        canonical_language=canonical_language,
        description=description,
        handle=handle,
        is_kernel=is_kernel,
        languages=list(languages),
        title=title,
    )


def _build_environment_config_topology(
    *,
    environment_config_id: UUID,
    environment_sources: EnvironmentSourceBundle,
) -> tuple[list[object], list[object]]:
    from aware_environment_ontology.environment.environment_profile_config import (  # noqa: WPS433
        EnvironmentProfileConfig,
    )
    from aware_environment_ontology.environment.environment_session_config import (  # noqa: WPS433
        EnvironmentSessionConfig,
    )
    from aware_environment_ontology.process.process_config import (  # noqa: WPS433
        ProcessConfig,
    )
    from aware_environment_ontology.thread.thread_config import (  # noqa: WPS433
        ThreadConfig,
    )

    profile_configs: list[object] = []
    session_configs: list[object] = []
    profile_ids_by_key: dict[str, UUID] = {}
    process_ids_by_profile_and_key: dict[tuple[str, str], UUID] = {}
    thread_ids_by_profile_process_and_key: dict[tuple[str, str, str], UUID] = {}

    for profile_source in environment_sources.profiles:
        profile_id = stable_environment_profile_config_id(
            environment_config_id=environment_config_id,
            key=profile_source.key,
        )
        profile_ids_by_key[_source_key(profile_source.key)] = profile_id
        process_configs: list[object] = []
        for process_source in profile_source.processes:
            process_id = stable_process_config_id(
                environment_profile_config_id=profile_id,
                key=process_source.key,
            )
            process_ids_by_profile_and_key[
                (_source_key(profile_source.key), _source_key(process_source.key))
            ] = process_id
            thread_configs: list[object] = []
            for thread_source in process_source.threads:
                thread_id = stable_thread_config_id(
                    process_config_id=process_id,
                    key=thread_source.key,
                )
                thread_ids_by_profile_process_and_key[
                    (
                        _source_key(profile_source.key),
                        _source_key(process_source.key),
                        _source_key(thread_source.key),
                    )
                ] = thread_id
                thread_configs.append(
                    ThreadConfig.model_construct(
                        id=thread_id,
                        process_config_id=process_id,
                        key=thread_source.key,
                        title=thread_source.title,
                        description=thread_source.description,
                        narrative=thread_source.narrative,
                        intent=thread_source.intent,
                        workspace_view_key=thread_source.workspace_view_key,
                        position=None,
                        is_default=thread_source.is_default,
                        state_prompt_template=None,
                        object_projection_graphs=[],
                        layout_configs=[],
                    )
                )
            process_configs.append(
                ProcessConfig.model_construct(
                    id=process_id,
                    environment_profile_config_id=profile_id,
                    type=process_source.type,
                    key=process_source.key,
                    title=process_source.title,
                    description=process_source.description,
                    narrative=process_source.narrative,
                    intent=process_source.intent,
                    shape=None,
                    position=None,
                    is_default=process_source.is_default,
                    thread_configs=thread_configs,
                )
            )
        profile_configs.append(
            EnvironmentProfileConfig.model_construct(
                id=profile_id,
                environment_config_id=environment_config_id,
                key=profile_source.key,
                title=profile_source.title,
                description=profile_source.description,
                narrative=profile_source.narrative,
                process_configs=process_configs,
                providers=[],
                actor_configs=[],
            )
        )

    for profile_source in environment_sources.profiles:
        for session_source in profile_source.sessions:
            profile_key = _source_key(
                session_source.default_profile_key or profile_source.key
            )
            profile_id = profile_ids_by_key.get(profile_key)
            if profile_id is None:
                raise EnvironmentSourceError(
                    "Environment session references unknown default profile "
                    f"{session_source.default_profile_key!r}"
                )
            process_id = None
            thread_id = None
            if session_source.default_process_key is not None:
                process_id = process_ids_by_profile_and_key.get(
                    (profile_key, _source_key(session_source.default_process_key))
                )
                if process_id is None:
                    raise EnvironmentSourceError(
                        "Environment session references unknown default process "
                        f"{session_source.default_process_key!r}"
                    )
            if (
                session_source.default_process_key is not None
                and session_source.default_thread_key is not None
            ):
                thread_id = thread_ids_by_profile_process_and_key.get(
                    (
                        profile_key,
                        _source_key(session_source.default_process_key),
                        _source_key(session_source.default_thread_key),
                    )
                )
                if thread_id is None:
                    raise EnvironmentSourceError(
                        "Environment session references unknown default thread "
                        f"{session_source.default_thread_key!r}"
                    )
            session_configs.append(
                EnvironmentSessionConfig.model_construct(
                    id=stable_environment_session_config_id(
                        environment_config_id=environment_config_id,
                        key=session_source.key,
                    ),
                    environment_config_id=environment_config_id,
                    key=session_source.key,
                    identity_session_config_id=stable_session_config_id(
                        key=session_source.key,
                    ),
                    default_profile_config_id=profile_id,
                    default_process_config_id=process_id,
                    default_thread_config_id=thread_id,
                    title=session_source.title,
                    description=session_source.description,
                    purpose=session_source.purpose,
                    status=session_source.status,
                    source_kind="aware.environment.source",
                    source_ref=profile_source.source_path,
                    metadata_json=JsonObject({"profile_key": profile_source.key}),
                )
            )

    return profile_configs, session_configs


def _source_key(value: str) -> str:
    return (value or "").casefold().strip()


def _environment_config_snapshot_commit_id(
    *,
    branch_id: UUID,
    projection_hash: str,
    environment_config: EnvironmentConfig,
) -> UUID:
    language_key = ",".join(
        sorted(
            getattr(language, "value", str(language))
            for language in environment_config.languages
        )
    )
    ontology_configs_key = ",".join(
        sorted(
            f"{membership.id}:{membership.name}:{membership.fqn_prefix}:"
            f"{membership.ontology_config_id}:"
            f"{membership.ontology_config_object_instance_graph_commit_id}"
            for membership in environment_config.ontology_configs
        )
    )
    profile_configs_key = ",".join(
        sorted(
            _environment_profile_config_snapshot_key(profile_config)
            for profile_config in environment_config.profile_configs
        )
    )
    session_configs_key = ",".join(
        sorted(
            f"{session_config.id}:{session_config.key}:"
            f"{session_config.identity_session_config_id}:"
            f"{session_config.default_profile_config_id}:"
            f"{session_config.default_process_config_id}:"
            f"{session_config.default_thread_config_id}:"
            f"{session_config.title or ''}:{session_config.description or ''}:"
            f"{session_config.purpose or ''}:{session_config.status}:"
            f"{session_config.source_kind or ''}:{session_config.source_ref or ''}"
            for session_config in environment_config.session_configs
        )
    )
    return uuid5(
        NS_ENVIRONMENT,
        "aware:environment_config_snapshot_commit:"
        + f"{branch_id}:{projection_hash}:{environment_config.id}:"
        + f"{environment_config.handle}:{environment_config.title}:"
        + f"{getattr(environment_config.canonical_language, 'value', environment_config.canonical_language)}:"
        + f"{language_key}:{int(bool(environment_config.is_kernel))}:"
        + f"{ontology_configs_key}:{profile_configs_key}:{session_configs_key}",
    )


def _environment_profile_config_snapshot_key(profile_config: object) -> str:
    process_keys: list[str] = []
    for process_config in getattr(profile_config, "process_configs", []):
        thread_keys = ",".join(
            sorted(
                f"{thread_config.id}:{thread_config.key}:{thread_config.title or ''}:"
                f"{thread_config.description or ''}:{thread_config.workspace_view_key or ''}:"
                f"{thread_config.narrative or ''}:{thread_config.intent or ''}:"
                f"{int(bool(thread_config.is_default))}"
                for thread_config in getattr(process_config, "thread_configs", [])
            )
        )
        process_keys.append(
            f"{process_config.id}:{process_config.key}:{process_config.type}:"
            f"{process_config.title or ''}:{process_config.description or ''}:"
            f"{process_config.narrative or ''}:{process_config.intent or ''}:"
            f"{int(bool(process_config.is_default))}:{thread_keys}"
        )
    return (
        f"{profile_config.id}:{profile_config.key}:{profile_config.title or ''}:"
        f"{profile_config.description or ''}:{profile_config.narrative or ''}:"
        + ",".join(sorted(process_keys))
    )


def _environment_session_config_snapshot_key(session_config: object) -> str:
    return (
        f"{session_config.id}:{session_config.key}:"
        f"{session_config.identity_session_config_id}:"
        f"{session_config.default_profile_config_id}:"
        f"{session_config.default_process_config_id}:"
        f"{session_config.default_thread_config_id}:"
        f"{session_config.title or ''}:{session_config.description or ''}:"
        f"{session_config.purpose or ''}:{session_config.status}:"
        f"{session_config.source_kind or ''}:{session_config.source_ref or ''}"
    )


def _environment_portal_target_snapshot_commit_id(
    *,
    branch_id: UUID,
    projection_hash: str,
    root_object: object,
    snapshot_key: str,
    target_kind: str,
) -> UUID:
    root_object_id = _required_model_id(
        root_object,
        context=f"{target_kind} portal target snapshot commit",
    )
    return uuid5(
        NS_ENVIRONMENT,
        f"aware:{target_kind}_portal_target_snapshot_commit:"
        + f"{branch_id}:{projection_hash}:{root_object_id}:{snapshot_key}",
    )


_ENVIRONMENT_PROFILE_TARGET_COLLECTION_FIELDS = (
    "process_configs",
    "thread_configs",
    "providers",
    "grants",
    "actor_configs",
    "object_projection_graphs",
    "layout_configs",
    "sections",
)


def _required_model_id(instance: object, *, context: str) -> UUID:
    instance_id = getattr(instance, "id", None)
    if not isinstance(instance_id, UUID):
        raise RuntimeError(f"{context} requires a UUID id")
    return instance_id


def _environment_profile_config_target_objects_by_id(
    profile_config: object,
) -> dict[UUID, object]:
    objects_by_id: dict[UUID, object] = {}

    def append_tree(instance: object) -> None:
        instance_id = _required_model_id(
            instance,
            context="EnvironmentProfileConfig portal target object",
        )
        if instance_id in objects_by_id:
            return
        objects_by_id[instance_id] = instance
        for field_name in _ENVIRONMENT_PROFILE_TARGET_COLLECTION_FIELDS:
            children = getattr(instance, field_name, None) or ()
            for child in children:
                append_tree(child)

    append_tree(profile_config)
    return objects_by_id


async def _commit_environment_portal_target_snapshot(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    branch_id: UUID,
    projection_hash: str,
    root_object: object,
    objects_by_id: Mapping[UUID, object],
    commit_id: UUID,
    operation_label: str,
) -> _EnvironmentPortalTargetSnapshotCommitResult:
    opg = index.opg_by_hash.get(projection_hash)
    if opg is None:
        raise RuntimeError(
            "Environment portal target snapshot commit missing projection hash: "
            f"{projection_hash}"
        )

    root_object_id = _required_model_id(
        root_object,
        context=f"{operation_label} root object",
    )
    domain_oig_id = stable_object_instance_graph_id(
        object_projection_graph_id=opg.id,
        key=str(branch_id),
    )
    _ocgi, opgi = resolve_ocgi_opgi(index=index, projection_hash=projection_hash)
    if opgi is None:
        raise RuntimeError(
            "Environment portal target snapshot commit missing ObjectProjectionGraphIdentity: "
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
        root_source_object_id=root_object_id,
        oig_id=domain_oig_id,
    )
    created_ids = frozenset(objects_by_id)
    change_set = ORMChangeSet(
        collected_at=datetime.now(UTC),
        created_ids=created_ids,
        touched_ids=created_ids,
        deleted_ids=frozenset(),
        objects_by_id=dict(objects_by_id),
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
        enum_option_resolver=default_meta_enum_option_resolver,
        class_instance_resolver=None,
        union_selections=None,
    )
    if not changes:
        raise RuntimeError(
            "Environment portal target snapshot commit produced no OIG changes: "
            f"operation_label={operation_label!r} root_object_id={root_object_id}"
        )
    after_oig = materialize_meta_oig_post(
        before_oig=before_oig,
        changes=changes,
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )
    committer = FSLaneCommitter()
    try:
        commit = await committer.commit(
            branch_id=branch_id,
            projection_hash=projection_hash,
            object_instance_graph_identity_id=oigi_id,
            object_instance_graph_id=domain_oig_id,
            before_oig=before_oig,
            root_object_id=root_object_id,
            changes=changes,
            graph_hash_pre=before_oig.hash,
            graph_hash_post=after_oig.hash,
            author_id=resolve_author_id(actor_id),
            commit_id=commit_id,
            commit_action=CommitActionDescriptor(
                operation_label=operation_label,
                call_target="generated_materialization",
                object_id=root_object_id,
            ),
        )
    except LaneHeadPreHashMismatchError as exc:
        if (
            exc.details.branch_id != branch_id
            or exc.details.projection_hash != projection_hash
            or exc.details.object_instance_graph_id != domain_oig_id
        ):
            raise
        _reset_generated_projection_lane_with_identity(
            index=index,
            branch_id=branch_id,
            projection_hash=projection_hash,
            object_instance_graph_id=domain_oig_id,
            error_context="Environment portal target deterministic snapshot migration",
            stale_reason=(
                "generated portal target lane head predates deterministic snapshot "
                + f"commit id: head_commit_id={exc.details.head_commit_id} "
                + f"expected_commit_id={commit_id}"
            ),
        )
        committer = FSLaneCommitter()
        commit = await committer.commit(
            branch_id=branch_id,
            projection_hash=projection_hash,
            object_instance_graph_identity_id=oigi_id,
            object_instance_graph_id=domain_oig_id,
            before_oig=before_oig,
            root_object_id=root_object_id,
            changes=changes,
            graph_hash_pre=before_oig.hash,
            graph_hash_post=after_oig.hash,
            author_id=resolve_author_id(actor_id),
            commit_id=commit_id,
            commit_action=CommitActionDescriptor(
                operation_label=operation_label,
                call_target="generated_materialization",
                object_id=root_object_id,
            ),
        )
    if commit is None or commit.commit is None:
        raise RuntimeError(
            "Environment portal target snapshot commit did not append a lane commit: "
            f"operation_label={operation_label!r} root_object_id={root_object_id}"
        )
    identity_perf_ms: dict[str, int] = {}
    await ensure_object_instance_graph_identity_lane_head(
        index=index,
        object_instance_graph_id=domain_oig_id,
        domain_projection_hash=projection_hash,
        author_id=resolve_author_id(actor_id),
        label=f"environment_portal_target:{root_object_id}",
        perf_ms=identity_perf_ms,
        perf_metric_prefix="ensure_environment_portal_target_oigi_lane",
    )
    commit_perf_ms = committer.last_commit_perf_profile_snapshot()
    commit_perf_ms.update(identity_perf_ms)

    object_instance_graph_commit_id = stable_object_instance_graph_commit_id(
        object_instance_graph_identity_id=commit.object_instance_graph_identity_id,
        commit_id=commit.commit.id,
    )
    return _EnvironmentPortalTargetSnapshotCommitResult(
        root_object_id=root_object_id,
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit.commit.id,
        head_commit_id=object_instance_graph_commit_id,
        object_instance_graph_commit_id=object_instance_graph_commit_id,
        object_instance_graph_id=domain_oig_id,
        object_instance_graph_identity_id=oigi_id,
        commit_perf_ms=commit_perf_ms,
    )


async def _commit_environment_config_portal_target_snapshots(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    source_branch_id: UUID,
    source_projection_hash: str,
    source_object_instance_graph_id: UUID,
    environment_profile_projection_hash: str,
    environment_session_projection_hash: str,
    environment_config: EnvironmentConfig,
) -> tuple[
    tuple[_EnvironmentPortalTargetSnapshotCommitResult, ...],
    tuple[_EnvironmentPortalTargetSnapshotCommitResult, ...],
]:
    store = FSCommitStore()
    author_id = resolve_author_id(actor_id)

    profile_results: list[_EnvironmentPortalTargetSnapshotCommitResult] = []
    for profile_config in environment_config.profile_configs:
        profile_config_id = _required_model_id(
            profile_config,
            context="EnvironmentProfileConfig portal target",
        )
        target_branch = await resolve_portal_target_branch_ref_for_object(
            index=index,
            source_domain_branch_id=source_branch_id,
            source_projection_hash=source_projection_hash,
            source_object_instance_graph_id=source_object_instance_graph_id,
            target_projection_hash=environment_profile_projection_hash,
            target_object_id=profile_config_id,
        )
        target_branch_id = target_branch.target_branch_id
        _reset_generated_projection_lane(
            store=store,
            branch_id=target_branch_id,
            projection_hash=environment_profile_projection_hash,
        )
        result = await _commit_environment_portal_target_snapshot(
            index=index,
            actor_id=actor_id,
            branch_id=target_branch_id,
            projection_hash=environment_profile_projection_hash,
            root_object=profile_config,
            objects_by_id=_environment_profile_config_target_objects_by_id(
                profile_config
            ),
            commit_id=_environment_portal_target_snapshot_commit_id(
                branch_id=target_branch_id,
                projection_hash=environment_profile_projection_hash,
                root_object=profile_config,
                snapshot_key=_environment_profile_config_snapshot_key(profile_config),
                target_kind="environment_profile_config",
            ),
            operation_label="EnvironmentProfileConfig.materialize_portal_target",
        )
        await attach_portal_target_branch_relationship_for_object(
            index=index,
            author_id=author_id,
            source_domain_branch_id=source_branch_id,
            source_projection_hash=source_projection_hash,
            target_projection_hash=environment_profile_projection_hash,
            target_object_id=profile_config_id,
            source_object_instance_graph_id=source_object_instance_graph_id,
            target_domain_branch_id=target_branch_id,
        )
        profile_results.append(result)

    session_results: list[_EnvironmentPortalTargetSnapshotCommitResult] = []
    for session_config in environment_config.session_configs:
        session_config_id = _required_model_id(
            session_config,
            context="EnvironmentSessionConfig portal target",
        )
        target_branch = await resolve_portal_target_branch_ref_for_object(
            index=index,
            source_domain_branch_id=source_branch_id,
            source_projection_hash=source_projection_hash,
            source_object_instance_graph_id=source_object_instance_graph_id,
            target_projection_hash=environment_session_projection_hash,
            target_object_id=session_config_id,
        )
        target_branch_id = target_branch.target_branch_id
        _reset_generated_projection_lane(
            store=store,
            branch_id=target_branch_id,
            projection_hash=environment_session_projection_hash,
        )
        result = await _commit_environment_portal_target_snapshot(
            index=index,
            actor_id=actor_id,
            branch_id=target_branch_id,
            projection_hash=environment_session_projection_hash,
            root_object=session_config,
            objects_by_id={session_config_id: session_config},
            commit_id=_environment_portal_target_snapshot_commit_id(
                branch_id=target_branch_id,
                projection_hash=environment_session_projection_hash,
                root_object=session_config,
                snapshot_key=_environment_session_config_snapshot_key(session_config),
                target_kind="environment_session_config",
            ),
            operation_label="EnvironmentSessionConfig.materialize_portal_target",
        )
        await attach_portal_target_branch_relationship_for_object(
            index=index,
            author_id=author_id,
            source_domain_branch_id=source_branch_id,
            source_projection_hash=source_projection_hash,
            target_projection_hash=environment_session_projection_hash,
            target_object_id=session_config_id,
            source_object_instance_graph_id=source_object_instance_graph_id,
            target_domain_branch_id=target_branch_id,
        )
        session_results.append(result)

    return tuple(profile_results), tuple(session_results)


def _ontology_package_snapshot_commit_id(
    *,
    branch_id: UUID,
    projection_hash: str,
    semantic_package: EnvironmentSemanticPackageMaterializationRef,
    ontology_package_id: UUID,
    ontology_config_commit: _OntologyConfigSnapshotCommitResult,
) -> UUID:
    return uuid5(
        NS_ENVIRONMENT,
        "aware:ontology_package_snapshot_commit:"
        + f"{branch_id}:{projection_hash}:{ontology_package_id}:"
        + f"{semantic_package.package_name}:{semantic_package.fqn_prefix}:"
        + f"{semantic_package.code_package_id}:"
        + f"{ontology_config_commit.ontology_config_id}:"
        + f"{ontology_config_commit.config_object_instance_graph_commit_id}:"
        + f"{semantic_package.object_config_graph_package_id}:"
        + f"{semantic_package.object_config_graph_id}:"
        + f"{semantic_package.object_config_graph_package_object_instance_graph_commit_id}:"
        + f"{semantic_package.object_config_graph_object_instance_graph_commit_id}:"
        + f"{semantic_package.manifest_relative_path}:"
        + f"{semantic_package.package_root}:"
        + f"{semantic_package.sources_root or ''}",
    )


def _ontology_config_snapshot_commit_id(
    *,
    branch_id: UUID,
    projection_hash: str,
    semantic_package: EnvironmentSemanticPackageMaterializationRef,
    ontology_config_id: UUID,
) -> UUID:
    return uuid5(
        NS_ENVIRONMENT,
        "aware:ontology_config_snapshot_commit:"
        + f"{branch_id}:{projection_hash}:{ontology_config_id}:"
        + f"{semantic_package.package_name}:{semantic_package.fqn_prefix}:"
        + f"{semantic_package.object_config_graph_id}:"
        + f"{semantic_package.object_config_graph_hash or ''}:"
        + f"{semantic_package.object_config_graph_object_instance_graph_commit_id}:"
        + f"{semantic_package.manifest_relative_path}:"
        + f"{semantic_package.package_root}:"
        + f"{semantic_package.sources_root or ''}",
    )


async def _commit_environment_config_snapshot(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    branch_id: UUID,
    projection_hash: str,
    environment_config: EnvironmentConfig,
) -> _EnvironmentConfigSnapshotCommitResult:
    opg = index.opg_by_hash.get(projection_hash)
    if opg is None:
        raise RuntimeError(
            "Environment config snapshot commit missing projection hash: "
            f"{projection_hash}"
        )

    domain_oig_id = stable_object_instance_graph_id(
        object_projection_graph_id=opg.id,
        key=str(branch_id),
    )
    _ocgi, opgi = resolve_ocgi_opgi(index=index, projection_hash=projection_hash)
    if opgi is None:
        raise RuntimeError(
            "Environment config snapshot commit missing ObjectProjectionGraphIdentity: "
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
        root_source_object_id=environment_config.id,
        oig_id=domain_oig_id,
    )
    objects_by_id: dict[UUID, object] = {environment_config.id: environment_config}
    for membership in environment_config.ontology_configs:
        objects_by_id[membership.id] = membership
    for profile_config in environment_config.profile_configs:
        objects_by_id[profile_config.id] = profile_config
        for process_config in profile_config.process_configs:
            objects_by_id[process_config.id] = process_config
            for thread_config in process_config.thread_configs:
                objects_by_id[thread_config.id] = thread_config
    for session_config in environment_config.session_configs:
        objects_by_id[session_config.id] = session_config
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
        enum_option_resolver=default_meta_enum_option_resolver,
        class_instance_resolver=None,
        union_selections=None,
    )
    if not changes:
        raise RuntimeError(
            "Environment config snapshot commit produced no OIG changes: "
            f"handle={environment_config.handle!r}"
        )
    after_oig = materialize_meta_oig_post(
        before_oig=before_oig,
        changes=changes,
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )
    committer = FSLaneCommitter()
    commit = await committer.commit(
        branch_id=branch_id,
        projection_hash=projection_hash,
        object_instance_graph_identity_id=oigi_id,
        object_instance_graph_id=domain_oig_id,
        before_oig=before_oig,
        root_object_id=environment_config.id,
        changes=changes,
        graph_hash_pre=before_oig.hash,
        graph_hash_post=after_oig.hash,
        author_id=resolve_author_id(actor_id),
        commit_id=_environment_config_snapshot_commit_id(
            branch_id=branch_id,
            projection_hash=projection_hash,
            environment_config=environment_config,
        ),
        commit_action=CommitActionDescriptor(
            operation_label="EnvironmentConfig.materialize",
            call_target="generated_materialization",
            object_id=environment_config.id,
        ),
    )
    if commit is None or commit.commit is None:
        raise RuntimeError(
            "Environment config snapshot commit did not append a lane commit: "
            f"handle={environment_config.handle!r}"
        )
    identity_perf_ms: dict[str, int] = {}
    await ensure_object_instance_graph_identity_lane_head(
        index=index,
        object_instance_graph_id=domain_oig_id,
        domain_projection_hash=projection_hash,
        author_id=resolve_author_id(actor_id),
        label=f"environment_config:{environment_config.handle}",
        perf_ms=identity_perf_ms,
        perf_metric_prefix="ensure_environment_config_oigi_lane",
    )
    commit_perf_ms = committer.last_commit_perf_profile_snapshot()
    commit_perf_ms.update(identity_perf_ms)

    return _EnvironmentConfigSnapshotCommitResult(
        environment_config=environment_config,
        environment_config_commit_id=commit.commit.id,
        environment_config_head_commit_id=stable_object_instance_graph_commit_id(
            object_instance_graph_identity_id=commit.object_instance_graph_identity_id,
            commit_id=commit.commit.id,
        ),
        environment_config_object_instance_graph_commit_id=(
            stable_object_instance_graph_commit_id(
                object_instance_graph_identity_id=commit.object_instance_graph_identity_id,
                commit_id=commit.commit.id,
            )
        ),
        environment_config_object_instance_graph_id=domain_oig_id,
        environment_config_object_instance_graph_identity_id=oigi_id,
        commit_perf_ms=commit_perf_ms,
    )


def _build_environment_config_ontology_membership(
    *,
    environment_config_id: UUID,
    semantic_package: EnvironmentSemanticPackageMaterializationRef,
) -> object:
    from aware_environment_ontology.environment.environment_config_ontology_config import (  # noqa: WPS433
        EnvironmentConfigOntologyConfig,
    )

    normalized_name = (semantic_package.package_name or "").strip()
    normalized_fqn_prefix = (semantic_package.fqn_prefix or "").strip()
    if not normalized_name:
        raise RuntimeError(
            "Environment config materialization requires non-empty ontology config name"
        )
    if not normalized_fqn_prefix:
        raise RuntimeError(
            "Environment config materialization requires non-empty ontology config fqn_prefix"
        )
    if semantic_package.ontology_config_id is None:
        raise RuntimeError(
            "Environment config materialization requires OntologyConfig id before "
            f"attaching package={normalized_name!r}"
        )

    return EnvironmentConfigOntologyConfig(
        id=stable_environment_config_ontology_config_id(
            environment_config_id=environment_config_id,
            name=normalized_name,
            fqn_prefix=normalized_fqn_prefix,
        ),
        environment_config_id=environment_config_id,
        ontology_config=None,
        ontology_config_id=semantic_package.ontology_config_id,
        ontology_config_object_instance_graph_commit=None,
        ontology_config_object_instance_graph_commit_id=(
            semantic_package.ontology_config_object_instance_graph_commit_id
        ),
        name=normalized_name,
        fqn_prefix=normalized_fqn_prefix,
    )


def _build_environment_package_ontology_membership(
    *,
    environment_config_package_id: UUID,
    name: str,
    fqn_prefix: str,
    ontology_package_object_instance_graph_commit_id: UUID | None,
) -> EnvironmentConfigPackageOntologyPackage:
    from aware_ontology_ontology.stable_ids import (
        stable_ontology_package_id,
    )  # noqa: WPS433

    normalized_name = (name or "").strip()
    normalized_fqn_prefix = (fqn_prefix or "").strip()
    if not normalized_name:
        raise RuntimeError(
            "Environment package materialization requires non-empty ontology package name"
        )
    if not normalized_fqn_prefix:
        raise RuntimeError(
            "Environment package materialization requires non-empty ontology fqn_prefix"
        )

    return EnvironmentConfigPackageOntologyPackage(
        id=stable_environment_config_package_ontology_package_id(
            environment_config_package_id=environment_config_package_id,
            name=normalized_name,
            fqn_prefix=normalized_fqn_prefix,
        ),
        environment_config_package_id=environment_config_package_id,
        ontology_package=None,
        ontology_package_id=stable_ontology_package_id(
            name=normalized_name,
            fqn_prefix=normalized_fqn_prefix,
        ),
        ontology_package_object_instance_graph_commit=None,
        ontology_package_object_instance_graph_commit_id=(
            ontology_package_object_instance_graph_commit_id
        ),
        name=normalized_name,
        fqn_prefix=normalized_fqn_prefix,
    )


def _build_environment_package_dependency(
    *,
    environment_config_package_id: UUID,
    dependency_ref: EnvironmentConfigPackageDependencyMaterializationRef,
) -> EnvironmentConfigPackageDependency:
    normalized_role = (dependency_ref.dependency_role or "").strip()
    normalized_target_handle = (dependency_ref.target_handle or "").strip()
    if not normalized_role:
        raise RuntimeError("Environment package dependency requires dependency_role")
    if not normalized_target_handle:
        raise RuntimeError("Environment package dependency requires target_handle")

    return EnvironmentConfigPackageDependency.model_construct(
        id=stable_environment_config_package_dependency_id(
            environment_config_package_id=environment_config_package_id,
            dependency_role=normalized_role,
            dependency_index=dependency_ref.dependency_index,
            target_handle=normalized_target_handle,
            target_environment_config_package_id=(
                dependency_ref.target_environment_config_package_id
            ),
            target_environment_config_package_object_instance_graph_commit_id=(
                dependency_ref.target_environment_config_package_object_instance_graph_commit_id
            ),
        ),
        environment_config_package_id=environment_config_package_id,
        target_environment_config_package=None,
        target_environment_config_package_id=(
            dependency_ref.target_environment_config_package_id
        ),
        target_environment_config_package_object_instance_graph_commit=None,
        target_environment_config_package_object_instance_graph_commit_id=(
            dependency_ref.target_environment_config_package_object_instance_graph_commit_id
        ),
        dependency_role=normalized_role,
        dependency_index=dependency_ref.dependency_index,
        target_handle=normalized_target_handle,
    )


async def _commit_ontology_config_snapshot(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    branch_id: UUID,
    projection_hash: str,
    semantic_package: EnvironmentSemanticPackageMaterializationRef,
) -> _OntologyConfigSnapshotCommitResult:
    from aware_ontology_ontology.ontology.ontology_config import (  # noqa: WPS433
        OntologyConfig,
    )
    from aware_ontology_ontology.stable_ids import (
        stable_ontology_config_id,
    )  # noqa: WPS433

    opg = index.opg_by_hash.get(projection_hash)
    if opg is None:
        raise RuntimeError(
            "OntologyConfig snapshot commit missing projection hash: "
            f"{projection_hash}"
        )
    if semantic_package.object_config_graph_object_instance_graph_commit_id is None:
        raise RuntimeError(
            "OntologyConfig snapshot commit requires ObjectConfigGraph OIG commit: "
            f"package_name={semantic_package.package_name!r}"
        )

    config_id = stable_ontology_config_id(
        name=semantic_package.package_name,
        fqn_prefix=semantic_package.fqn_prefix,
    )
    config = OntologyConfig.model_construct(
        id=config_id,
        name=semantic_package.package_name,
        fqn_prefix=semantic_package.fqn_prefix,
        object_config_graph=None,
        object_config_graph_id=semantic_package.object_config_graph_id,
        object_config_graph_object_instance_graph_commit=None,
        object_config_graph_object_instance_graph_commit_id=(
            semantic_package.object_config_graph_object_instance_graph_commit_id
        ),
        ontologies=[],
        version_number=1,
        title=None,
        description=None,
        schema_hash=semantic_package.object_config_graph_hash,
    )

    domain_oig_id = stable_object_instance_graph_id(
        object_projection_graph_id=opg.id,
        key=str(branch_id),
    )
    _ocgi, opgi = resolve_ocgi_opgi(index=index, projection_hash=projection_hash)
    if opgi is None:
        raise RuntimeError(
            "OntologyConfig snapshot commit missing ObjectProjectionGraphIdentity: "
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
    objects_by_id: dict[UUID, object] = {config.id: config}
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
            f"name={semantic_package.package_name!r}"
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
        semantic_package=semantic_package,
        ontology_config_id=config.id,
    )
    commit_action = CommitActionDescriptor(
        operation_label="OntologyConfig.materialize",
        call_target="generated_materialization",
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
            author_id=resolve_author_id(actor_id),
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
        _reset_generated_projection_lane_with_identity(
            index=index,
            branch_id=branch_id,
            projection_hash=projection_hash,
            object_instance_graph_id=domain_oig_id,
            error_context="OntologyConfig deterministic snapshot migration",
            stale_reason=(
                "generated lane head predates deterministic snapshot commit id: "
                + f"head_commit_id={exc.details.head_commit_id} "
                + f"expected_commit_id={commit_id}"
            ),
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
            author_id=resolve_author_id(actor_id),
            commit_id=commit_id,
            commit_action=commit_action,
        )
    if commit is None or commit.commit is None:
        raise RuntimeError(
            "OntologyConfig snapshot commit did not append a lane commit: "
            f"name={semantic_package.package_name!r}"
        )
    object_instance_graph_commit_id = stable_object_instance_graph_commit_id(
        object_instance_graph_identity_id=commit.object_instance_graph_identity_id,
        commit_id=commit.commit.id,
    )
    return _OntologyConfigSnapshotCommitResult(
        ontology_config_id=config.id,
        config_commit_id=commit.commit.id,
        config_head_commit_id=object_instance_graph_commit_id,
        config_object_instance_graph_commit_id=object_instance_graph_commit_id,
        commit_perf_ms=committer.last_commit_perf_profile_snapshot(),
    )


async def _commit_ontology_package_snapshot(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    branch_id: UUID,
    projection_hash: str,
    semantic_package: EnvironmentSemanticPackageMaterializationRef,
    ontology_config_commit: _OntologyConfigSnapshotCommitResult,
) -> _OntologyPackageSnapshotCommitResult:
    from aware_ontology_ontology.ontology.ontology_package import (  # noqa: WPS433
        OntologyPackage,
    )
    from aware_ontology_ontology.stable_ids import (
        stable_ontology_package_id,
    )  # noqa: WPS433

    opg = index.opg_by_hash.get(projection_hash)
    if opg is None:
        raise RuntimeError(
            "OntologyPackage snapshot commit missing projection hash: "
            f"{projection_hash}"
        )

    package_id = stable_ontology_package_id(
        name=semantic_package.package_name,
        fqn_prefix=semantic_package.fqn_prefix,
    )
    package = OntologyPackage.model_construct(
        id=package_id,
        name=semantic_package.package_name,
        fqn_prefix=semantic_package.fqn_prefix,
        ontology_config=None,
        ontology_config_id=ontology_config_commit.ontology_config_id,
        ontology_config_object_instance_graph_commit=None,
        ontology_config_object_instance_graph_commit_id=(
            ontology_config_commit.config_object_instance_graph_commit_id
        ),
        source_code_package=None,
        source_code_package_id=semantic_package.code_package_id,
        object_config_graph_package=None,
        object_config_graph_package_id=semantic_package.object_config_graph_package_id,
        object_config_graph_package_object_instance_graph_commit=None,
        object_config_graph_package_object_instance_graph_commit_id=(
            semantic_package.object_config_graph_package_object_instance_graph_commit_id
        ),
        object_config_graph_object_instance_graph_commit=None,
        object_config_graph_object_instance_graph_commit_id=(
            semantic_package.object_config_graph_object_instance_graph_commit_id
        ),
        runtime_code_packages=[],
        dependencies=[],
        version_number=1,
        title=None,
        description=None,
        manifest_relative_path=semantic_package.manifest_relative_path,
        package_root=semantic_package.package_root,
        sources_root=semantic_package.sources_root or "modules",
    )

    domain_oig_id = stable_object_instance_graph_id(
        object_projection_graph_id=opg.id,
        key=str(branch_id),
    )
    _ocgi, opgi = resolve_ocgi_opgi(index=index, projection_hash=projection_hash)
    if opgi is None:
        raise RuntimeError(
            "OntologyPackage snapshot commit missing ObjectProjectionGraphIdentity: "
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
        root_source_object_id=package.id,
        oig_id=domain_oig_id,
    )
    objects_by_id: dict[UUID, object] = {package.id: package}
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
            "OntologyPackage snapshot commit produced no OIG changes: "
            f"name={semantic_package.package_name!r}"
        )
    after_oig = materialize_meta_oig_post(
        before_oig=before_oig,
        changes=changes,
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )
    commit_id = _ontology_package_snapshot_commit_id(
        branch_id=branch_id,
        projection_hash=projection_hash,
        semantic_package=semantic_package,
        ontology_package_id=package.id,
        ontology_config_commit=ontology_config_commit,
    )
    commit_action = CommitActionDescriptor(
        operation_label="OntologyPackage.materialize",
        call_target="generated_materialization",
        object_id=package.id,
    )
    committer = FSLaneCommitter()
    try:
        commit = await committer.commit(
            branch_id=branch_id,
            projection_hash=projection_hash,
            object_instance_graph_identity_id=oigi_id,
            object_instance_graph_id=domain_oig_id,
            before_oig=before_oig,
            root_object_id=package.id,
            changes=changes,
            graph_hash_pre=before_oig.hash,
            graph_hash_post=after_oig.hash,
            author_id=resolve_author_id(actor_id),
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
        _reset_generated_projection_lane_with_identity(
            index=index,
            branch_id=branch_id,
            projection_hash=projection_hash,
            object_instance_graph_id=domain_oig_id,
            error_context="OntologyPackage deterministic snapshot migration",
            stale_reason=(
                "generated lane head predates deterministic snapshot commit id: "
                + f"head_commit_id={exc.details.head_commit_id} "
                + f"expected_commit_id={commit_id}"
            ),
        )
        committer = FSLaneCommitter()
        commit = await committer.commit(
            branch_id=branch_id,
            projection_hash=projection_hash,
            object_instance_graph_identity_id=oigi_id,
            object_instance_graph_id=domain_oig_id,
            before_oig=before_oig,
            root_object_id=package.id,
            changes=changes,
            graph_hash_pre=before_oig.hash,
            graph_hash_post=after_oig.hash,
            author_id=resolve_author_id(actor_id),
            commit_id=commit_id,
            commit_action=commit_action,
        )
    if commit is None or commit.commit is None:
        raise RuntimeError(
            "OntologyPackage snapshot commit did not append a lane commit: "
            f"name={semantic_package.package_name!r}"
        )

    return _OntologyPackageSnapshotCommitResult(
        ontology_package_id=package.id,
        package_commit_id=commit.commit.id,
        package_head_commit_id=stable_object_instance_graph_commit_id(
            object_instance_graph_identity_id=commit.object_instance_graph_identity_id,
            commit_id=commit.commit.id,
        ),
        package_object_instance_graph_commit_id=stable_object_instance_graph_commit_id(
            object_instance_graph_identity_id=commit.object_instance_graph_identity_id,
            commit_id=commit.commit.id,
        ),
        commit_perf_ms=committer.last_commit_perf_profile_snapshot(),
    )


async def _commit_environment_package_snapshot(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    branch_id: UUID,
    projection_hash: str,
    environment_handle: str,
    environment_config: EnvironmentConfig,
    environment_config_oig_commit_id: UUID | None,
    semantic_packages: Iterable[EnvironmentSemanticPackageMaterializationRef],
    environment_package_dependencies: Iterable[
        EnvironmentConfigPackageDependencyMaterializationRef
    ],
) -> _EnvironmentPackageSnapshotCommitResult:
    opg = index.opg_by_hash.get(projection_hash)
    if opg is None:
        raise RuntimeError(
            "Environment package snapshot commit missing projection hash: "
            f"{projection_hash}"
        )

    package_id = stable_environment_config_package_id(handle=environment_handle)
    ontology_memberships = [
        _build_environment_package_ontology_membership(
            environment_config_package_id=package_id,
            name=semantic_package.package_name,
            fqn_prefix=semantic_package.fqn_prefix,
            ontology_package_object_instance_graph_commit_id=(
                semantic_package.ontology_package_object_instance_graph_commit_id
            ),
        )
        for semantic_package in semantic_packages
    ]
    dependencies = [
        _build_environment_package_dependency(
            environment_config_package_id=package_id,
            dependency_ref=dependency_ref,
        )
        for dependency_ref in environment_package_dependencies
    ]
    package = EnvironmentConfigPackage.model_construct(
        id=package_id,
        handle=(environment_handle or "").strip(),
        environment_config=None,
        environment_config_id=environment_config.id,
        environment_config_object_instance_graph_commit=None,
        environment_config_object_instance_graph_commit_id=environment_config_oig_commit_id,
        ontology_packages=ontology_memberships,
        dependencies=dependencies,
    )

    domain_oig_id = stable_object_instance_graph_id(
        object_projection_graph_id=opg.id,
        key=str(branch_id),
    )
    _ocgi, opgi = resolve_ocgi_opgi(index=index, projection_hash=projection_hash)
    if opgi is None:
        raise RuntimeError(
            "Environment package snapshot commit missing ObjectProjectionGraphIdentity: "
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
        root_source_object_id=package.id,
        oig_id=domain_oig_id,
    )
    objects_by_id: dict[UUID, object] = {package.id: package}
    for ontology_membership in ontology_memberships:
        objects_by_id[ontology_membership.id] = ontology_membership
    for dependency in dependencies:
        objects_by_id[dependency.id] = dependency
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
            "Environment package snapshot commit produced no OIG changes: "
            f"handle={environment_handle!r}"
        )
    after_oig = materialize_meta_oig_post(
        before_oig=before_oig,
        changes=changes,
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )
    committer = FSLaneCommitter()
    commit = await committer.commit(
        branch_id=branch_id,
        projection_hash=projection_hash,
        object_instance_graph_identity_id=oigi_id,
        object_instance_graph_id=domain_oig_id,
        before_oig=before_oig,
        root_object_id=package.id,
        changes=changes,
        graph_hash_pre=before_oig.hash,
        graph_hash_post=after_oig.hash,
        author_id=resolve_author_id(actor_id),
        commit_action=CommitActionDescriptor(
            operation_label="EnvironmentConfigPackage.materialize",
            call_target="generated_materialization",
            object_id=package.id,
        ),
    )
    if commit is None or commit.commit is None:
        raise RuntimeError(
            "Environment package snapshot commit did not append a lane commit: "
            f"handle={environment_handle!r}"
        )

    return _EnvironmentPackageSnapshotCommitResult(
        package=package,
        ontology_membership_ids=tuple(
            membership.id for membership in ontology_memberships
        ),
        package_commit_id=commit.commit.id,
        package_head_commit_id=stable_object_instance_graph_commit_id(
            object_instance_graph_identity_id=commit.object_instance_graph_identity_id,
            commit_id=commit.commit.id,
        ),
        package_object_instance_graph_commit_id=stable_object_instance_graph_commit_id(
            object_instance_graph_identity_id=commit.object_instance_graph_identity_id,
            commit_id=commit.commit.id,
        ),
        commit_perf_ms=committer.last_commit_perf_profile_snapshot(),
    )


async def _reset_stale_generated_projection_lane_if_needed(
    *,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    projection_hash: str,
    error_context: str,
    projection_catalog: EnvironmentMetaProjectionCatalog | None = None,
) -> bool:
    """Reset generated materialization lanes whose commit lineage has stale OIGI ids."""
    store = FSCommitStore()
    head = await store.head(branch_id=branch_id, projection_hash=projection_hash)
    if head is None or head.get("commit_id") is None:
        return False

    opg = index.opg_by_hash.get(projection_hash)
    if opg is None:
        raise RuntimeError(
            f"{error_context} missing projection hash: {projection_hash}"
        )

    head_commit_id = _uuid_from_head(head, "commit_id")
    head_oig_id = _uuid_from_head(head, "object_instance_graph_id")
    stale_reason: str | None = None
    if head_commit_id is None:
        stale_reason = "HEAD commit_id is invalid"
    if head_oig_id is None:
        stale_reason = "HEAD object_instance_graph_id is invalid"

    expected_oigi_id: UUID | None = None
    if head_oig_id is not None:
        _ocgi, opgi = resolve_ocgi_opgi(index=index, projection_hash=projection_hash)
        if opgi is None:
            raise RuntimeError(
                f"{error_context} missing ObjectProjectionGraphIdentity: projection_hash={projection_hash}"
            )
        expected_oigi_id = stable_object_instance_graph_identity_id(
            object_projection_graph_identity_id=opgi.id,
            object_instance_graph_id=head_oig_id,
        )

    if stale_reason is None and head_commit_id is not None and head_oig_id is not None:
        health_metadata = await store.get_commit_health_metadata(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=head_commit_id,
        )
        if health_metadata is not None:
            if health_metadata.object_instance_graph_id != head_oig_id:
                stale_reason = (
                    "commit object_instance_graph_id mismatch: "
                    + f"commit_id={head_commit_id} "
                    + f"have={health_metadata.object_instance_graph_id} "
                    + f"expected={head_oig_id}"
                )
            elif (
                expected_oigi_id is not None
                and health_metadata.object_instance_graph_identity_id
                != expected_oigi_id
            ):
                stale_reason = (
                    "commit object_instance_graph_identity_id mismatch: "
                    + f"commit_id={head_commit_id} "
                    + f"have={health_metadata.object_instance_graph_identity_id} "
                    + f"expected={expected_oigi_id}"
                )
            elif health_metadata.projection_hash != projection_hash:
                stale_reason = (
                    "commit projection_hash mismatch: "
                    + f"commit_id={head_commit_id} "
                    + f"have={health_metadata.projection_hash} "
                    + f"expected={projection_hash}"
                )
        else:
            identity_metadata = await store.get_commit_identity_metadata(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=head_commit_id,
            )
            if identity_metadata is None:
                stale_reason = f"missing commit payload: commit_id={head_commit_id}"
            elif identity_metadata.object_instance_graph_id != head_oig_id:
                stale_reason = (
                    "commit object_instance_graph_id mismatch: "
                    + f"commit_id={head_commit_id} "
                    + f"have={identity_metadata.object_instance_graph_id} "
                    + f"expected={head_oig_id}"
                )
            elif (
                expected_oigi_id is not None
                and identity_metadata.object_instance_graph_identity_id
                != expected_oigi_id
            ):
                stale_reason = (
                    "commit object_instance_graph_identity_id mismatch: "
                    + f"commit_id={head_commit_id} "
                    + f"have={identity_metadata.object_instance_graph_identity_id} "
                    + f"expected={expected_oigi_id}"
                )

    if stale_reason is None:
        return False

    _reset_generated_projection_lane_with_identity(
        index=index,
        branch_id=branch_id,
        projection_hash=projection_hash,
        object_instance_graph_id=head_oig_id,
        error_context=error_context,
        stale_reason=stale_reason,
        projection_catalog=projection_catalog,
    )
    return True


async def materialize_environment_package_from_manifest(
    *,
    runtime: object,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    branch_id: UUID,
    workspace_root: Path,
    environment_toml_path: Path,
    semantic_package_progress_callback: (
        EnvironmentSemanticPackageProgressCallback | None
    ) = None,
    collect_leaf_telemetry: bool = True,
    selected_semantic_package_names: Iterable[str] | None = None,
    dependency_object_config_graphs_by_package_name: (
        Mapping[str, ObjectConfigGraph] | None
    ) = None,
    completed_semantic_packages_by_package_name: (
        Mapping[str, EnvironmentSemanticPackageMaterializationRef] | None
    ) = None,
    meta_projection_catalog: object | None = None,
    semantic_ontology_package_catalog: Mapping[str, object] | None = None,
) -> EnvironmentPackageMaterializationResult:
    materialization_started_at = perf_counter()
    phase_timings_s: dict[str, float] = {}
    environment_toml_path = environment_toml_path.resolve()
    workspace_root = workspace_root.resolve()
    with _record_phase(phase_timings_s, "load_aware_environment_spec"):
        spec = load_aware_environment_spec(toml_path=environment_toml_path)
    semantic_package_names = _environment_semantic_package_selector_names(
        workspace_root=workspace_root,
        spec=spec,
    )

    expected_environment_config_id = stable_environment_config_id(
        handle=spec.environment.handle
    )
    declared_environment_config_id = spec.environment.environment_config_id
    if (
        declared_environment_config_id is not None
        and str(expected_environment_config_id) != declared_environment_config_id
    ):
        raise RuntimeError(
            "Declared aware.environment.toml id does not match the canonical EnvironmentConfig stable id "
            + f"for handle={spec.environment.handle!r}: declared={declared_environment_config_id!r} "
            + f"expected={expected_environment_config_id}"
        )

    projection_catalog = require_environment_meta_projection_catalog(
        meta_projection_catalog or index,
        required_projection_names=(
            "EnvironmentConfig",
            "EnvironmentConfigPackage",
            "EnvironmentProfileConfig",
            "EnvironmentSessionConfig",
            "CodePackage",
            "ObjectConfigGraphPackage",
            "OntologyConfig",
            "OntologyPackage",
            "ObjectConfigGraph",
            "ObjectInstanceGraphIdentity",
        ),
        source="materialize_environment_package_from_manifest",
    )
    environment_projection_hash = projection_catalog.projection_hash_for_name(
        "EnvironmentConfig"
    )
    environment_package_projection_hash = projection_catalog.projection_hash_for_name(
        "EnvironmentConfigPackage"
    )
    environment_profile_projection_hash = projection_catalog.projection_hash_for_name(
        "EnvironmentProfileConfig"
    )
    environment_session_projection_hash = projection_catalog.projection_hash_for_name(
        "EnvironmentSessionConfig"
    )
    code_package_projection_hash = projection_catalog.projection_hash_for_name(
        "CodePackage"
    )
    object_config_graph_package_projection_hash = (
        projection_catalog.projection_hash_for_name("ObjectConfigGraphPackage")
    )
    ontology_config_projection_hash = projection_catalog.projection_hash_for_name(
        "OntologyConfig"
    )
    ontology_package_projection_hash = projection_catalog.projection_hash_for_name(
        "OntologyPackage"
    )
    object_config_graph_projection_hash = projection_catalog.projection_hash_for_name(
        "ObjectConfigGraph"
    )

    canonical_language = _decode_code_language(spec.environment.canonical_language)
    environment_title = (
        spec.environment.title or ""
    ).strip() or spec.environment.handle

    with _record_phase(
        phase_timings_s,
        "discover_environment_semantic_package_specs",
    ):
        external_dependency_package_names = (
            _environment_external_dependency_package_names(
                workspace_root=workspace_root,
                semantic_ontology_package_catalog=semantic_ontology_package_catalog,
            )
        )
        semantic_package_specs = _discover_environment_semantic_package_specs(
            workspace_root=workspace_root,
            module_names=semantic_package_names,
            ontology_manifest_paths=tuple(spec.ontologies),
            available_dependency_package_names=external_dependency_package_names,
        )
        semantic_package_specs = _filter_environment_semantic_package_specs(
            semantic_package_specs=semantic_package_specs,
            selected_package_names=selected_semantic_package_names,
            available_dependency_package_names=external_dependency_package_names,
        )
    with _record_phase(phase_timings_s, "load_environment_profile_session_sources"):
        environment_sources = _load_environment_profile_session_sources(
            workspace_root=workspace_root,
            environment_toml_path=environment_toml_path,
            spec=spec,
        )
    semantic_packages: list[EnvironmentSemanticPackageMaterializationRef] = []
    semantic_object_config_graphs: list[ObjectConfigGraph] = []
    object_config_graph_by_package_name: dict[str, ObjectConfigGraph] = {}
    object_config_graph_payload_by_package_name: dict[str, Mapping[str, object]] = {}
    supplied_object_config_graph_by_package_name = {
        str(raw_package_name).strip(): graph
        for raw_package_name, graph in (
            dependency_object_config_graphs_by_package_name or {}
        ).items()
        if str(raw_package_name).strip() and isinstance(graph, ObjectConfigGraph)
    }
    external_object_config_graph_by_package_name = {
        package_name: graph
        for package_name, graph in supplied_object_config_graph_by_package_name.items()
        if package_name in external_dependency_package_names
    }
    meta_service_protocol_handler = build_aware_meta_service_protocol_handler(
        event_store=MetaCommitEventStore(
            root_path=workspace_root / ".aware" / "meta-service-events",
        ),
    )
    code_package_commit_id: UUID | None = None
    code_package_head_commit_id: UUID | None = None
    object_config_graph_commit_id: UUID | None = None
    object_config_graph_head_commit_id: UUID | None = None
    object_config_graph_package_commit_id: UUID | None = None
    object_config_graph_package_head_commit_id: UUID | None = None
    semantic_package_count = len(semantic_package_specs)
    semantic_packages_started_at = perf_counter()
    for package_index, package_spec in enumerate(semantic_package_specs, start=1):
        package_started_at = datetime.now(UTC)
        await _notify_environment_semantic_package_progress(
            callback=semantic_package_progress_callback,
            event=EnvironmentSemanticPackageMaterializationProgress(
                event_key="environment.semantic_package.materialization",
                status="running",
                generated_at_utc=_isoformat_z(package_started_at),
                environment_handle=spec.environment.handle,
                environment_toml_path=environment_toml_path,
                package_name=package_spec.package_name,
                module_name=package_spec.module_name,
                manifest_relative_path=package_spec.manifest_relative_path,
                package_index=package_index,
                package_count=semantic_package_count,
                fqn_prefix=package_spec.fqn_prefix,
            ),
        )
        try:
            dependency_graph_names, dependency_graphs = (
                _dependency_object_config_graphs_for_package_spec(
                    package_spec=package_spec,
                    local_object_config_graphs_by_package_name=(
                        object_config_graph_by_package_name
                    ),
                    external_object_config_graphs_by_package_name=(
                        external_object_config_graph_by_package_name
                    ),
                )
            )
            completed_semantic_package = (
                completed_semantic_packages_by_package_name or {}
            ).get(package_spec.package_name)
            completed_graph = supplied_object_config_graph_by_package_name.get(
                package_spec.package_name
            )
            completed_reuse_currentness_mismatch = None
            if completed_semantic_package is not None and completed_graph is not None:
                completed_reuse_currentness_mismatch = (
                    await _completed_semantic_package_ref_currentness_mismatch(
                        semantic_package=completed_semantic_package,
                        graph=completed_graph,
                        package_spec=package_spec,
                        workspace_root=workspace_root,
                        code_package_projection_hash=code_package_projection_hash,
                        object_config_graph_projection_hash=(
                            object_config_graph_projection_hash
                        ),
                        object_config_graph_package_projection_hash=(
                            object_config_graph_package_projection_hash
                        ),
                        ontology_config_projection_hash=ontology_config_projection_hash,
                        ontology_package_projection_hash=(
                            ontology_package_projection_hash
                        ),
                    )
                )
            completed_semantic_package_is_current = (
                completed_semantic_package is not None
                and completed_graph is not None
                and completed_reuse_currentness_mismatch is None
            )
            if completed_semantic_package is None:
                completed_reuse_rejection_reason = "evidence_missing"
            elif completed_graph is None:
                completed_reuse_rejection_reason = "graph_missing"
            elif not completed_semantic_package_is_current:
                completed_reuse_rejection_reason = (
                    completed_reuse_currentness_mismatch
                    or "durable_currentness_mismatch"
                )
            else:
                completed_reuse_rejection_reason = None
            if completed_reuse_rejection_reason is not None:
                logger.info(
                    "Environment completed semantic package reuse rejected: "
                    "package=%s reason=%s",
                    package_spec.package_name,
                    completed_reuse_rejection_reason,
                )
            if completed_semantic_package_is_current:
                package_result = _meta_service_result_from_completed_semantic_package(
                    semantic_package=cast(
                        EnvironmentSemanticPackageMaterializationRef,
                        completed_semantic_package,
                    ),
                    graph=cast(ObjectConfigGraph, completed_graph),
                )
            else:
                completed_semantic_package = None
                package_result = (
                    await _materialize_environment_semantic_package_via_meta_service(
                        meta_service_protocol_handler=meta_service_protocol_handler,
                        runtime=runtime,
                        index=index,
                        actor_id=actor_id,
                        environment_id=expected_environment_config_id,
                        process_id=None,
                        thread_id=None,
                        branch_id=branch_id,
                        workspace_root=workspace_root,
                        package_spec=package_spec,
                        dependency_graph_names=dependency_graph_names,
                        dependency_graphs=dependency_graphs,
                        dependency_graph_payloads=(
                            object_config_graph_payload_by_package_name
                        ),
                        target_projection_hash=(
                            object_config_graph_package_projection_hash
                        ),
                        object_config_graph_projection_hash=(
                            object_config_graph_projection_hash
                        ),
                        collect_telemetry=collect_leaf_telemetry,
                    )
                )
        except Exception as exc:
            package_finished_at = datetime.now(UTC)
            await _notify_environment_semantic_package_progress(
                callback=semantic_package_progress_callback,
                event=EnvironmentSemanticPackageMaterializationProgress(
                    event_key="environment.semantic_package.materialization",
                    status="failed",
                    generated_at_utc=_isoformat_z(package_finished_at),
                    environment_handle=spec.environment.handle,
                    environment_toml_path=environment_toml_path,
                    package_name=package_spec.package_name,
                    module_name=package_spec.module_name,
                    manifest_relative_path=package_spec.manifest_relative_path,
                    package_index=package_index,
                    package_count=semantic_package_count,
                    fqn_prefix=package_spec.fqn_prefix,
                    duration_s=max(
                        (package_finished_at - package_started_at).total_seconds(), 0.0
                    ),
                    error=str(exc),
                ),
            )
            raise
        code_package_oig_commit_id = (
            package_result.code_package_object_instance_graph_commit_id
        )
        if code_package_oig_commit_id is None:
            code_package_domain_commit_id = (
                package_result.code_package_commit_id
                or await _lane_domain_head_commit_id(
                    workspace_root=workspace_root,
                    branch_id=package_result.package_branch_id,
                    projection_hash=code_package_projection_hash,
                )
            )
            code_package_oig_commit_id = (
                await _object_instance_graph_commit_id_from_domain_commit(
                    workspace_root=workspace_root,
                    branch_id=package_result.package_branch_id,
                    projection_hash=code_package_projection_hash,
                    domain_commit_id=code_package_domain_commit_id,
                )
                if code_package_domain_commit_id is not None
                else None
            )
        object_config_graph_package_oig_commit_id = (
            package_result.object_config_graph_package_object_instance_graph_commit_id
        )
        if object_config_graph_package_oig_commit_id is None:
            object_config_graph_package_domain_commit_id = (
                package_result.object_config_graph_package_commit_id
                or await _lane_domain_head_commit_id(
                    workspace_root=workspace_root,
                    branch_id=package_result.package_branch_id,
                    projection_hash=object_config_graph_package_projection_hash,
                )
            )
            object_config_graph_package_oig_commit_id = (
                await _object_instance_graph_commit_id_from_domain_commit(
                    workspace_root=workspace_root,
                    branch_id=package_result.package_branch_id,
                    projection_hash=object_config_graph_package_projection_hash,
                    domain_commit_id=object_config_graph_package_domain_commit_id,
                )
                if object_config_graph_package_domain_commit_id is not None
                else None
            )
        semantic_package_ref = EnvironmentSemanticPackageMaterializationRef(
            module_name=package_spec.module_name,
            aware_toml_path=package_spec.aware_toml_path,
            ontology_manifest_path=package_spec.ontology_manifest_path,
            source_manifest_path=package_spec.source_manifest_path,
            manifest_relative_path=package_spec.manifest_relative_path,
            package_root=package_spec.package_root,
            workspace_package_root=package_spec.workspace_package_root,
            sources_root=package_spec.sources_root,
            package_name=package_spec.package_name,
            fqn_prefix=package_spec.fqn_prefix,
            semantic_branch_id=package_result.package_branch_id,
            code_package_id=package_result.code_package_id,
            code_package_object_instance_graph_commit_id=(code_package_oig_commit_id),
            object_config_graph_package_id=(
                package_result.object_config_graph_package_id
            ),
            object_config_graph_id=package_result.object_config_graph.id,
            object_config_graph_hash=package_result.object_config_graph.hash,
            object_config_graph_head_commit_id=(
                package_result.object_config_graph_head_commit_id
            ),
            object_config_graph_package_object_instance_graph_commit_id=(
                object_config_graph_package_oig_commit_id
            ),
            object_config_graph_package_head_commit_id=(
                package_result.object_config_graph_package_head_commit_id
            ),
            object_config_graph_object_instance_graph_commit_id=(
                package_result.object_config_graph_object_instance_graph_commit_id
            ),
            phase_timings_s=package_result.phase_timings_s,
            code_package_build_runtime_telemetry=(
                package_result.code_package_build_runtime_telemetry
            ),
            code_package_build_invoke_perf_ms=(
                package_result.code_package_build_invoke_perf_ms
            ),
            code_package_upsert_runtime_telemetry=(
                package_result.code_package_upsert_runtime_telemetry
            ),
            code_package_upsert_invoke_perf_ms=(
                package_result.code_package_upsert_invoke_perf_ms
            ),
            semantic_commit_strategy=package_result.semantic_commit_strategy,
            semantic_commit_fallback_reset=package_result.semantic_commit_fallback_reset,
            semantic_commit_phase_timings_s=package_result.semantic_commit_phase_timings_s,
            artifact_ownership_receipts=(package_result.artifact_ownership_receipts),
            code_package_head_commit_id=package_result.code_package_head_commit_id,
        )
        if completed_semantic_package is not None:
            semantic_package_ref = completed_semantic_package
            phase_timings_s["reuse_completed_semantic_package_count"] = (
                phase_timings_s.get("reuse_completed_semantic_package_count", 0.0) + 1.0
            )
        else:
            with _record_phase(phase_timings_s, "commit_ontology_config_snapshot"):
                ontology_config_commit_result = await _commit_ontology_config_snapshot(
                    index=index,
                    actor_id=actor_id,
                    branch_id=package_result.package_branch_id,
                    projection_hash=ontology_config_projection_hash,
                    semantic_package=semantic_package_ref,
                )
            for (
                metric_name,
                metric_value,
            ) in ontology_config_commit_result.commit_perf_ms.items():
                phase_timings_s[f"commit_ontology_config_snapshot.{metric_name}"] = (
                    _round_duration_s(float(metric_value) / 1000.0)
                )
            semantic_package_ref = replace(
                semantic_package_ref,
                ontology_config_id=ontology_config_commit_result.ontology_config_id,
                ontology_config_commit_id=(
                    ontology_config_commit_result.config_commit_id
                ),
                ontology_config_head_commit_id=(
                    ontology_config_commit_result.config_head_commit_id
                ),
                ontology_config_object_instance_graph_commit_id=(
                    ontology_config_commit_result.config_object_instance_graph_commit_id
                ),
            )
            with _record_phase(phase_timings_s, "commit_ontology_package_snapshot"):
                ontology_package_commit_result = (
                    await _commit_ontology_package_snapshot(
                        index=index,
                        actor_id=actor_id,
                        branch_id=package_result.package_branch_id,
                        projection_hash=ontology_package_projection_hash,
                        semantic_package=semantic_package_ref,
                        ontology_config_commit=ontology_config_commit_result,
                    )
                )
            for (
                metric_name,
                metric_value,
            ) in ontology_package_commit_result.commit_perf_ms.items():
                phase_timings_s[f"commit_ontology_package_snapshot.{metric_name}"] = (
                    _round_duration_s(float(metric_value) / 1000.0)
                )
            semantic_package_ref = replace(
                semantic_package_ref,
                ontology_package_id=(
                    ontology_package_commit_result.ontology_package_id
                ),
                ontology_package_commit_id=(
                    ontology_package_commit_result.package_commit_id
                ),
                ontology_package_head_commit_id=(
                    ontology_package_commit_result.package_head_commit_id
                ),
                ontology_package_object_instance_graph_commit_id=(
                    ontology_package_commit_result.package_object_instance_graph_commit_id
                ),
            )
        semantic_packages.append(semantic_package_ref)
        semantic_object_config_graphs.append(package_result.object_config_graph)
        object_config_graph_by_package_name[package_spec.package_name] = (
            package_result.object_config_graph
        )
        if package_result.object_config_graph_payload is not None:
            object_config_graph_payload_by_package_name[package_spec.package_name] = (
                package_result.object_config_graph_payload
            )
        code_package_commit_id = package_result.code_package_commit_id
        code_package_head_commit_id = package_result.code_package_head_commit_id
        object_config_graph_commit_id = package_result.object_config_graph_commit_id
        object_config_graph_head_commit_id = (
            package_result.object_config_graph_head_commit_id
        )
        object_config_graph_package_commit_id = (
            package_result.object_config_graph_package_commit_id
        )
        object_config_graph_package_head_commit_id = (
            package_result.object_config_graph_package_head_commit_id
        )
        package_finished_at = datetime.now(UTC)
        await _notify_environment_semantic_package_progress(
            callback=semantic_package_progress_callback,
            event=EnvironmentSemanticPackageMaterializationProgress(
                event_key="environment.semantic_package.materialization",
                status="succeeded",
                generated_at_utc=_isoformat_z(package_finished_at),
                environment_handle=spec.environment.handle,
                environment_toml_path=environment_toml_path,
                package_name=package_spec.package_name,
                module_name=package_spec.module_name,
                manifest_relative_path=package_spec.manifest_relative_path,
                package_index=package_index,
                package_count=semantic_package_count,
                fqn_prefix=package_spec.fqn_prefix,
                duration_s=max(
                    (package_finished_at - package_started_at).total_seconds(), 0.0
                ),
                phase_timings_s=package_result.phase_timings_s,
                code_package_build_runtime_telemetry=(
                    package_result.code_package_build_runtime_telemetry
                ),
                code_package_build_invoke_perf_ms=(
                    package_result.code_package_build_invoke_perf_ms
                ),
                code_package_upsert_runtime_telemetry=(
                    package_result.code_package_upsert_runtime_telemetry
                ),
                code_package_upsert_invoke_perf_ms=(
                    package_result.code_package_upsert_invoke_perf_ms
                ),
                semantic_commit_strategy=package_result.semantic_commit_strategy,
                semantic_commit_fallback_reset=package_result.semantic_commit_fallback_reset,
                semantic_commit_phase_timings_s=package_result.semantic_commit_phase_timings_s,
            ),
        )
    phase_timings_s["materialize_semantic_packages"] = _round_duration_s(
        perf_counter() - semantic_packages_started_at
    )

    with _record_phase(phase_timings_s, "resolve_environment_package_dependencies"):
        environment_package_dependencies = (
            await _resolve_environment_config_package_dependencies(
                workspace_root=workspace_root,
                environment_toml_path=environment_toml_path,
                spec=spec,
                environment_package_projection_hash=environment_package_projection_hash,
            )
        )

    with _record_phase(phase_timings_s, "build_environment_config_snapshot"):
        environment_config = _build_environment_config_snapshot(
            environment_config_id=expected_environment_config_id,
            handle=spec.environment.handle,
            title=environment_title,
            canonical_language=canonical_language,
            languages=(canonical_language,),
            semantic_packages=semantic_packages,
            environment_sources=environment_sources,
            description=None,
            is_kernel=spec.environment.handle == "kernel",
        )
    with _record_phase(phase_timings_s, "reset_environment_config_lane"):
        # EnvironmentConfig is generated from the manifest and current ontology
        # config closure. Snapshotting it after semantic package materialization
        # keeps the config-to-ontology bridge in the committed root.
        _reset_generated_projection_lane(
            store=FSCommitStore(),
            branch_id=branch_id,
            projection_hash=environment_projection_hash,
        )
    with _record_phase(phase_timings_s, "commit_environment_config_snapshot"):
        environment_config_commit_result = await _commit_environment_config_snapshot(
            index=index,
            actor_id=actor_id,
            branch_id=branch_id,
            projection_hash=environment_projection_hash,
            environment_config=environment_config,
        )
    for (
        metric_name,
        metric_value,
    ) in environment_config_commit_result.commit_perf_ms.items():
        phase_timings_s[f"commit_environment_config_snapshot.{metric_name}"] = (
            _round_duration_s(float(metric_value) / 1000.0)
        )
    environment_config = environment_config_commit_result.environment_config
    environment_config_oig_commit_id = (
        environment_config_commit_result.environment_config_object_instance_graph_commit_id
    )
    environment_config_ontology_membership_ids = tuple(
        membership.id for membership in environment_config.ontology_configs
    )
    with _record_phase(
        phase_timings_s,
        "commit_environment_config_portal_target_snapshots",
    ):
        (
            environment_profile_target_commit_results,
            environment_session_target_commit_results,
        ) = await _commit_environment_config_portal_target_snapshots(
            index=index,
            actor_id=actor_id,
            source_branch_id=branch_id,
            source_projection_hash=environment_projection_hash,
            source_object_instance_graph_id=(
                environment_config_commit_result.environment_config_object_instance_graph_id
            ),
            environment_profile_projection_hash=environment_profile_projection_hash,
            environment_session_projection_hash=environment_session_projection_hash,
            environment_config=environment_config,
        )
    for index_suffix, target_result in enumerate(
        environment_profile_target_commit_results,
        start=1,
    ):
        for metric_name, metric_value in target_result.commit_perf_ms.items():
            phase_timings_s[
                "commit_environment_profile_config_portal_target_"
                + f"{index_suffix}.{metric_name}"
            ] = _round_duration_s(float(metric_value) / 1000.0)
    for index_suffix, target_result in enumerate(
        environment_session_target_commit_results,
        start=1,
    ):
        for metric_name, metric_value in target_result.commit_perf_ms.items():
            phase_timings_s[
                "commit_environment_session_config_portal_target_"
                + f"{index_suffix}.{metric_name}"
            ] = _round_duration_s(float(metric_value) / 1000.0)

    with _record_phase(phase_timings_s, "reset_environment_package_lane"):
        # EnvironmentConfigPackage is generated from the current environment
        # semantic closure. Rebuilding it avoids replaying stale failed-run
        # package membership history before the final attach.
        _reset_generated_projection_lane(
            store=FSCommitStore(),
            branch_id=branch_id,
            projection_hash=environment_package_projection_hash,
        )
    with _record_phase(phase_timings_s, "commit_environment_package_snapshot"):
        environment_package_commit_result = await _commit_environment_package_snapshot(
            index=index,
            actor_id=actor_id,
            branch_id=branch_id,
            projection_hash=environment_package_projection_hash,
            environment_handle=spec.environment.handle,
            environment_config=environment_config,
            environment_config_oig_commit_id=environment_config_oig_commit_id,
            semantic_packages=semantic_packages,
            environment_package_dependencies=environment_package_dependencies,
        )
    for (
        metric_name,
        metric_value,
    ) in environment_package_commit_result.commit_perf_ms.items():
        phase_timings_s[f"commit_environment_package_snapshot.{metric_name}"] = (
            _round_duration_s(float(metric_value) / 1000.0)
        )
    environment_package = environment_package_commit_result.package
    environment_package_ontology_membership_ids = (
        environment_package_commit_result.ontology_membership_ids
    )
    environment_package_commit_id = environment_package_commit_result.package_commit_id
    environment_package_oig_commit_id = (
        environment_package_commit_result.package_object_instance_graph_commit_id
    )
    environment_package_head_commit_id = (
        environment_package_commit_result.package_head_commit_id
    )
    phase_timings_s["total"] = _round_duration_s(
        perf_counter() - materialization_started_at
    )

    return EnvironmentPackageMaterializationResult(
        environment_toml_path=environment_toml_path,
        environment_spec=spec,
        environment_config=environment_config,
        environment_package=environment_package,
        semantic_package_names=semantic_package_names,
        code_module_names=(),
        semantic_packages=tuple(semantic_packages),
        environment_package_dependencies=tuple(environment_package_dependencies),
        semantic_object_config_graphs=tuple(semantic_object_config_graphs),
        environment_config_ontology_membership_ids=tuple(
            environment_config_ontology_membership_ids
        ),
        environment_package_ontology_membership_ids=tuple(
            environment_package_ontology_membership_ids
        ),
        environment_commit_id=(
            environment_config_commit_result.environment_config_commit_id
        ),
        environment_head_commit_id=(
            environment_config_commit_result.environment_config_head_commit_id
        ),
        environment_config_object_instance_graph_commit_id=environment_config_oig_commit_id,
        code_package_commit_id=code_package_commit_id,
        code_package_head_commit_id=code_package_head_commit_id,
        object_config_graph_commit_id=object_config_graph_commit_id,
        object_config_graph_head_commit_id=object_config_graph_head_commit_id,
        object_config_graph_package_commit_id=object_config_graph_package_commit_id,
        object_config_graph_package_head_commit_id=object_config_graph_package_head_commit_id,
        package_commit_id=environment_package_commit_id,
        package_head_commit_id=environment_package_head_commit_id,
        package_object_instance_graph_commit_id=environment_package_oig_commit_id,
        phase_timings_s=dict(sorted(phase_timings_s.items())),
        environment_profile_config_portal_target_branch_ids=tuple(
            result.branch_id for result in environment_profile_target_commit_results
        ),
        environment_profile_config_object_instance_graph_commit_ids=tuple(
            result.object_instance_graph_commit_id
            for result in environment_profile_target_commit_results
        ),
        environment_session_config_portal_target_branch_ids=tuple(
            result.branch_id for result in environment_session_target_commit_results
        ),
        environment_session_config_object_instance_graph_commit_ids=tuple(
            result.object_instance_graph_commit_id
            for result in environment_session_target_commit_results
        ),
    )


async def _completed_semantic_package_ref_is_current(
    *,
    semantic_package: EnvironmentSemanticPackageMaterializationRef,
    graph: ObjectConfigGraph,
    package_spec: _DiscoveredEnvironmentSemanticPackageSpec,
    workspace_root: Path,
    code_package_projection_hash: str,
    object_config_graph_projection_hash: str,
    object_config_graph_package_projection_hash: str,
    ontology_config_projection_hash: str,
    ontology_package_projection_hash: str,
) -> bool:
    return (
        await _completed_semantic_package_ref_currentness_mismatch(
            semantic_package=semantic_package,
            graph=graph,
            package_spec=package_spec,
            workspace_root=workspace_root,
            code_package_projection_hash=code_package_projection_hash,
            object_config_graph_projection_hash=object_config_graph_projection_hash,
            object_config_graph_package_projection_hash=(
                object_config_graph_package_projection_hash
            ),
            ontology_config_projection_hash=ontology_config_projection_hash,
            ontology_package_projection_hash=ontology_package_projection_hash,
        )
        is None
    )


async def _completed_semantic_package_ref_currentness_mismatch(
    *,
    semantic_package: EnvironmentSemanticPackageMaterializationRef,
    graph: ObjectConfigGraph,
    package_spec: _DiscoveredEnvironmentSemanticPackageSpec,
    workspace_root: Path,
    code_package_projection_hash: str,
    object_config_graph_projection_hash: str,
    object_config_graph_package_projection_hash: str,
    ontology_config_projection_hash: str,
    ontology_package_projection_hash: str,
) -> str | None:
    from aware_ontology_ontology.stable_ids import (
        stable_ontology_config_id,
        stable_ontology_package_id,
    )

    expected_branch_id = stable_object_config_graph_package_branch_id(
        workspace_root=workspace_root,
        aware_toml_path=package_spec.aware_toml_path,
        package_name=package_spec.package_name,
        fqn_prefix=package_spec.fqn_prefix,
    )
    coordinate_checks = (
        (
            "package_name_mismatch",
            semantic_package.package_name == package_spec.package_name,
        ),
        ("fqn_prefix_mismatch", semantic_package.fqn_prefix == package_spec.fqn_prefix),
        (
            "aware_toml_path_mismatch",
            semantic_package.aware_toml_path.resolve()
            == package_spec.aware_toml_path.resolve(),
        ),
        (
            "semantic_branch_id_mismatch",
            semantic_package.semantic_branch_id == expected_branch_id,
        ),
        (
            "object_config_graph_id_mismatch",
            semantic_package.object_config_graph_id == graph.id,
        ),
        (
            "object_config_graph_hash_mismatch",
            semantic_package.object_config_graph_hash == graph.hash,
        ),
        (
            "ontology_config_id_mismatch",
            semantic_package.ontology_config_id
            == stable_ontology_config_id(
                name=package_spec.package_name,
                fqn_prefix=package_spec.fqn_prefix,
            ),
        ),
        (
            "ontology_package_id_mismatch",
            semantic_package.ontology_package_id
            == stable_ontology_package_id(
                name=package_spec.package_name,
                fqn_prefix=package_spec.fqn_prefix,
            ),
        ),
    )
    for mismatch_reason, matches in coordinate_checks:
        if not matches:
            return mismatch_reason
    lane_evidence = (
        (
            "code_package",
            code_package_projection_hash,
            semantic_package.code_package_head_commit_id,
            semantic_package.code_package_object_instance_graph_commit_id,
        ),
        (
            "object_config_graph",
            object_config_graph_projection_hash,
            semantic_package.object_config_graph_head_commit_id,
            semantic_package.object_config_graph_object_instance_graph_commit_id,
        ),
        (
            "object_config_graph_package",
            object_config_graph_package_projection_hash,
            semantic_package.object_config_graph_package_head_commit_id,
            semantic_package.object_config_graph_package_object_instance_graph_commit_id,
        ),
        (
            "ontology_config",
            ontology_config_projection_hash,
            semantic_package.ontology_config_commit_id,
            semantic_package.ontology_config_object_instance_graph_commit_id,
        ),
        (
            "ontology_package",
            ontology_package_projection_hash,
            semantic_package.ontology_package_commit_id,
            semantic_package.ontology_package_object_instance_graph_commit_id,
        ),
    )
    for lane_name, projection_hash, head_commit_id, oig_commit_id in lane_evidence:
        if not await _completed_semantic_package_lane_is_current(
            workspace_root=workspace_root,
            branch_id=expected_branch_id,
            projection_hash=projection_hash,
            expected_head_commit_id=head_commit_id,
            expected_object_instance_graph_commit_id=oig_commit_id,
        ):
            return f"{lane_name}_lane_head_mismatch"
    return None


async def _completed_semantic_package_lane_is_current(
    *,
    workspace_root: Path,
    branch_id: UUID,
    projection_hash: str,
    expected_head_commit_id: UUID | None,
    expected_object_instance_graph_commit_id: UUID | None,
) -> bool:
    if (
        expected_head_commit_id is None
        or expected_object_instance_graph_commit_id is None
    ):
        return False
    head_commit_id = await _lane_domain_head_commit_id(
        workspace_root=workspace_root,
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    if head_commit_id != expected_head_commit_id:
        return False
    current_oig_commit_id = await _object_instance_graph_commit_id_from_domain_commit(
        workspace_root=workspace_root,
        branch_id=branch_id,
        projection_hash=projection_hash,
        domain_commit_id=head_commit_id,
    )
    return current_oig_commit_id == expected_object_instance_graph_commit_id


def _meta_service_result_from_completed_semantic_package(
    *,
    semantic_package: EnvironmentSemanticPackageMaterializationRef,
    graph: ObjectConfigGraph,
) -> _MetaServicePackageMaterializationResult:
    return _MetaServicePackageMaterializationResult(
        aware_toml_path=semantic_package.aware_toml_path,
        package_branch_id=semantic_package.semantic_branch_id,
        code_package_id=semantic_package.code_package_id,
        object_config_graph_package_id=semantic_package.object_config_graph_package_id,
        object_config_graph=graph,
        object_config_graph_payload=None,
        code_package_commit_id=semantic_package.code_package_head_commit_id,
        code_package_head_commit_id=semantic_package.code_package_head_commit_id,
        code_package_object_instance_graph_commit_id=(
            semantic_package.code_package_object_instance_graph_commit_id
        ),
        object_config_graph_commit_id=(
            semantic_package.object_config_graph_head_commit_id
        ),
        object_config_graph_head_commit_id=(
            semantic_package.object_config_graph_head_commit_id
        ),
        object_config_graph_object_instance_graph_commit_id=(
            semantic_package.object_config_graph_object_instance_graph_commit_id
        ),
        object_config_graph_package_commit_id=(
            semantic_package.object_config_graph_package_head_commit_id
        ),
        object_config_graph_package_head_commit_id=(
            semantic_package.object_config_graph_package_head_commit_id
        ),
        object_config_graph_package_object_instance_graph_commit_id=(
            semantic_package.object_config_graph_package_object_instance_graph_commit_id
        ),
        phase_timings_s=semantic_package.phase_timings_s,
        code_package_build_runtime_telemetry={},
        code_package_build_invoke_perf_ms={},
        code_package_upsert_runtime_telemetry={},
        code_package_upsert_invoke_perf_ms={},
        semantic_commit_strategy="completed_semantic_package_reuse",
        semantic_commit_fallback_reset=False,
        semantic_commit_phase_timings_s={},
        artifact_ownership_receipts=semantic_package.artifact_ownership_receipts,
    )


async def _materialize_environment_semantic_package_via_meta_service(
    *,
    meta_service_protocol_handler: object,
    runtime: object,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    environment_id: UUID,
    process_id: UUID | None,
    thread_id: UUID | None,
    branch_id: UUID,
    workspace_root: Path,
    package_spec: _DiscoveredEnvironmentSemanticPackageSpec,
    dependency_graph_names: list[str],
    dependency_graphs: list[ObjectConfigGraph],
    dependency_graph_payloads: Mapping[str, Mapping[str, object]],
    target_projection_hash: str,
    object_config_graph_projection_hash: str,
    collect_telemetry: bool,
) -> _MetaServicePackageMaterializationResult:
    resolved_actor_id = resolve_author_id(actor_id)
    operation_context = ServiceOperationContext(
        actor_id=resolved_actor_id,
        environment_id=environment_id,
        process_id=process_id,
        thread_id=thread_id,
        branch_id=branch_id,
        projection_hash=target_projection_hash,
    )
    package_branch_id = stable_object_config_graph_package_branch_id(
        workspace_root=workspace_root,
        aware_toml_path=package_spec.aware_toml_path,
        package_name=package_spec.package_name,
        fqn_prefix=package_spec.fqn_prefix,
    )
    request = MetaObjectConfigGraphPackageEnsureRequest(
        actor_id=resolved_actor_id,
        workspace_root=workspace_root.as_posix(),
        aware_toml_path=package_spec.aware_toml_path.as_posix(),
        parent_branch_id=branch_id,
        package_branch_id=package_branch_id,
        dependency_refs=[
            _meta_dependency_ref_from_object_config_graph(
                package_name=dependency_package_name,
                graph=dependency_graph,
                graph_payload=dependency_graph_payloads.get(dependency_package_name),
            )
            for dependency_package_name, dependency_graph in zip(
                dependency_graph_names,
                dependency_graphs,
                strict=True,
            )
        ],
        include_object_config_graph=True,
        collect_telemetry=collect_telemetry,
    )
    with service_api_host_context(
        operation_context=operation_context,
        graph_gateway=None,
        service_name="aware_meta",
        materialization=ServiceApiMaterializationContext(
            runtime=runtime,
            graph_context=index,
            target_lane=MaterializationLaneContext(
                branch_id=branch_id,
                projection_hash=target_projection_hash,
            ),
        ),
    ):
        response = await invoke_meta__package__ensure_object_config_graph_package(
            meta_service_protocol_handler,
            request,
        )
    return await _meta_service_package_result_from_response(
        index=index,
        package_spec=package_spec,
        response=response,
        object_config_graph_projection_hash=object_config_graph_projection_hash,
    )


def _meta_dependency_ref_from_object_config_graph(
    *,
    package_name: str,
    graph: ObjectConfigGraph,
    graph_payload: Mapping[str, object] | None = None,
) -> MetaObjectConfigGraphPackageDependencyRef:
    return MetaObjectConfigGraphPackageDependencyRef(
        package_name=package_name,
        fqn_prefix=graph.fqn_prefix,
        object_config_graph_package_id=stable_object_config_graph_package_id(
            package_name=package_name,
            fqn_prefix=graph.fqn_prefix,
        ),
        object_config_graph_id=graph.id,
        object_config_graph=cast(
            JsonObject | None,
            (
                _object_config_graph_payload(graph)
                if graph_payload is None
                else dict(graph_payload)
            ),
        ),
    )


def _object_config_graph_payload(graph: ObjectConfigGraph) -> Mapping[str, object]:
    return cast(Mapping[str, object], graph.model_dump(mode="json"))


def _dependency_object_config_graphs_for_package_spec(
    *,
    package_spec: _DiscoveredEnvironmentSemanticPackageSpec,
    local_object_config_graphs_by_package_name: Mapping[str, ObjectConfigGraph],
    external_object_config_graphs_by_package_name: Mapping[str, ObjectConfigGraph],
) -> tuple[list[str], list[ObjectConfigGraph]]:
    dependency_names = list(package_spec.dependency_package_names)
    dependency_graphs: list[ObjectConfigGraph] = []
    missing_dependency_names: list[str] = []
    for dependency_name in dependency_names:
        graph = local_object_config_graphs_by_package_name.get(dependency_name)
        if graph is None:
            graph = external_object_config_graphs_by_package_name.get(dependency_name)
        if graph is None:
            missing_dependency_names.append(dependency_name)
            continue
        dependency_graphs.append(graph)
    if missing_dependency_names:
        raise RuntimeError(
            "Environment semantic package compile is missing dependency "
            "ObjectConfigGraph evidence: "
            f"{package_spec.package_name} -> "
            + ", ".join(sorted(missing_dependency_names))
        )
    return dependency_names, dependency_graphs


async def _meta_service_package_result_from_response(
    *,
    index: MetaGraphRuntimeIndex,
    package_spec: _DiscoveredEnvironmentSemanticPackageSpec,
    response: MetaObjectConfigGraphPackageEnsureResponse,
    object_config_graph_projection_hash: str,
) -> _MetaServicePackageMaterializationResult:
    if response.status != "succeeded":
        raise RuntimeError(
            "Meta service package OCG compile failed: "
            f"package_name={package_spec.package_name!r} "
            f"aware_toml_path={package_spec.aware_toml_path} "
            f"status={response.status!r} error={response.error!r}"
        )
    package_branch_id = _require_response_uuid(
        response.package_branch_id,
        field_name="package_branch_id",
        package_spec=package_spec,
    )
    object_config_graph_id = _require_response_uuid(
        response.object_config_graph_id,
        field_name="object_config_graph_id",
        package_spec=package_spec,
    )
    object_config_graph = _object_config_graph_from_response(
        response=response,
        package_spec=package_spec,
    )
    if object_config_graph is None:
        object_config_graph = await _hydrate_lane_root_from_head(
            index=index,
            branch_id=package_branch_id,
            projection_hash=object_config_graph_projection_hash,
            root_id=object_config_graph_id,
            root_type=ObjectConfigGraph,
        )
    if object_config_graph is None:
        raise RuntimeError(
            "Meta service package OCG compile response did not provide hydratable ObjectConfigGraph evidence: "
            f"package_name={package_spec.package_name!r}"
        )
    if object_config_graph.id != object_config_graph_id:
        raise RuntimeError(
            "Meta service package OCG compile returned mismatched ObjectConfigGraph id: "
            f"package_name={package_spec.package_name!r} "
            f"response={object_config_graph_id} payload={object_config_graph.id}"
        )
    return _MetaServicePackageMaterializationResult(
        aware_toml_path=Path(response.aware_toml_path or package_spec.aware_toml_path),
        package_branch_id=package_branch_id,
        code_package_id=_require_response_uuid(
            response.source_code_package_id,
            field_name="source_code_package_id",
            package_spec=package_spec,
        ),
        object_config_graph_package_id=_require_response_uuid(
            response.object_config_graph_package_id,
            field_name="object_config_graph_package_id",
            package_spec=package_spec,
        ),
        object_config_graph=object_config_graph,
        object_config_graph_payload=response.object_config_graph,
        code_package_commit_id=response.code_package_commit_id,
        code_package_head_commit_id=response.code_package_head_commit_id,
        code_package_object_instance_graph_commit_id=(
            response.code_package_object_instance_graph_commit_id
        ),
        object_config_graph_commit_id=response.object_config_graph_commit_id,
        object_config_graph_head_commit_id=response.object_config_graph_head_commit_id,
        object_config_graph_object_instance_graph_commit_id=(
            response.object_config_graph_object_instance_graph_commit_id
        ),
        object_config_graph_package_commit_id=(
            response.object_config_graph_package_commit_id
        ),
        object_config_graph_package_head_commit_id=(
            response.object_config_graph_package_head_commit_id
        ),
        object_config_graph_package_object_instance_graph_commit_id=(
            response.object_config_graph_package_object_instance_graph_commit_id
        ),
        phase_timings_s=_float_mapping(response.timings.get("phase_timings_s")),
        code_package_build_runtime_telemetry=_object_mapping(
            response.telemetry.get("code_package_build_runtime_telemetry")
        ),
        code_package_build_invoke_perf_ms=_int_mapping(
            response.telemetry.get("code_package_build_invoke_perf_ms")
        ),
        code_package_upsert_runtime_telemetry=_object_mapping(
            response.telemetry.get("code_package_upsert_runtime_telemetry")
        ),
        code_package_upsert_invoke_perf_ms=_int_mapping(
            response.telemetry.get("code_package_upsert_invoke_perf_ms")
        ),
        semantic_commit_strategy=str(
            response.telemetry.get("semantic_commit_strategy") or "unknown"
        ),
        semantic_commit_fallback_reset=bool(
            response.telemetry.get("semantic_commit_fallback_reset") or False
        ),
        semantic_commit_phase_timings_s=_float_mapping(
            response.timings.get("semantic_commit_phase_timings_s")
        ),
        artifact_ownership_receipts=_mapping_tuple(
            response.telemetry.get("artifact_ownership_receipts")
        ),
    )


def _object_config_graph_from_response(
    *,
    response: MetaObjectConfigGraphPackageEnsureResponse,
    package_spec: _DiscoveredEnvironmentSemanticPackageSpec,
) -> ObjectConfigGraph | None:
    if response.object_config_graph is None:
        return None
    try:
        return _object_config_graph_from_response_payload(response.object_config_graph)
    except Exception as exc:
        logger.warning(
            "Environment environment package could not use inline Meta OCG payload; "
            "falling back to committed lane hydration: package=%s error=%s",
            package_spec.package_name,
            exc,
        )
        return None


def _require_response_uuid(
    value: UUID | None,
    *,
    field_name: str,
    package_spec: _DiscoveredEnvironmentSemanticPackageSpec,
) -> UUID:
    if value is None:
        raise RuntimeError(
            "Meta service package OCG compile response missing required field "
            f"{field_name!r}: package_name={package_spec.package_name!r}"
        )
    return value


def _object_config_graph_from_response_payload(
    payload: JsonObject,
) -> ObjectConfigGraph:
    try:
        return ObjectConfigGraph.model_validate(payload)
    except Exception:
        data: dict[str, object] = dict(payload)
        raw_id = data.get("id")
        if isinstance(raw_id, str) and raw_id.strip():
            data["id"] = UUID(raw_id)
        raw_language = data.get("language")
        if isinstance(raw_language, str) and raw_language.strip():
            data["language"] = CodeLanguage(raw_language)
        for relationship_field in (
            "object_config_graph_annotations",
            "object_config_graph_mirrors",
            "object_config_graph_nodes",
            "object_config_graph_overlays",
            "object_config_graph_bindings",
            "object_config_graph_relationships",
            "object_projection_graph_declarations",
            "object_projection_graphs",
            "domain_relationships",
            "domains",
        ):
            data.setdefault(relationship_field, [])
        return ObjectConfigGraph.model_validate(data)


def _object_mapping(value: object) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        return {}
    return {str(key): item for key, item in value.items()}


def _mapping_tuple(value: object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(
        {str(key): item for key, item in item.items()}
        for item in value
        if isinstance(item, Mapping)
    )


def _int_mapping(value: object) -> Mapping[str, int]:
    if not isinstance(value, Mapping):
        return {}
    return {
        str(key): int(item)
        for key, item in value.items()
        if isinstance(item, int) and not isinstance(item, bool)
    }


def _float_mapping(value: object) -> Mapping[str, float]:
    if not isinstance(value, Mapping):
        return {}
    return {
        str(key): float(item)
        for key, item in value.items()
        if isinstance(item, (int, float)) and not isinstance(item, bool)
    }


async def _notify_environment_semantic_package_progress(
    *,
    callback: EnvironmentSemanticPackageProgressCallback | None,
    event: EnvironmentSemanticPackageMaterializationProgress,
) -> None:
    if callback is None:
        return
    try:
        result = callback(event)
        if result is not None:
            await result
    except Exception:
        return


def _isoformat_z(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _decode_code_language(value: str) -> CodeLanguage:
    normalized = (value or "").strip() or CodeLanguage.aware.value
    try:
        return CodeLanguage(normalized)
    except ValueError as exc:
        raise RuntimeError(
            f"Unsupported aware.environment.toml canonical_language: {normalized!r}"
        ) from exc


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
            "Environment package materialization missing projection hash: "
            + projection_hash
        )

    head = await FSCommitStore().head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    if head is None or head.get("commit_id") is None:
        return None

    oig, _ = await OIGMaterializer().get(
        branch_id=branch_id,
        ocg=index.ocg,
        opg=opg,
        commit_id=None,
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )
    hydrated_root = reify_oig_root_model(
        index=index,
        opg=opg,
        oig=oig,
        model_type=root_type,
        root_id=root_id,
        branch_id=branch_id,
    )
    if hydrated_root is not None:
        return hydrated_root
    return None


async def _lane_domain_head_commit_id(
    *,
    workspace_root: Path,
    branch_id: UUID,
    projection_hash: str,
) -> UUID | None:
    head = await FSCommitStore(root_dir=workspace_root).head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    if head is None or head.get("commit_id") is None:
        return None
    return UUID(str(head["commit_id"]))


async def _object_instance_graph_commit_id_from_domain_commit(
    *,
    workspace_root: Path,
    branch_id: UUID,
    projection_hash: str,
    domain_commit_id: UUID,
) -> UUID | None:
    store = FSCommitStore(root_dir=workspace_root)
    commit_identity = await store.get_commit_identity_metadata(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=domain_commit_id,
    )
    if commit_identity is not None:
        return stable_object_instance_graph_commit_id(
            object_instance_graph_identity_id=(
                commit_identity.object_instance_graph_identity_id
            ),
            commit_id=domain_commit_id,
        )
    domain_commit = await store.get_commit(
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


async def _resolve_environment_config_package_dependencies(
    *,
    workspace_root: Path,
    environment_toml_path: Path,
    spec: AwareEnvironmentSpec,
    environment_package_projection_hash: str,
) -> tuple[EnvironmentConfigPackageDependencyMaterializationRef, ...]:
    refs: list[EnvironmentConfigPackageDependencyMaterializationRef] = []
    store = FSCommitStore()
    seen_targets: set[tuple[UUID, UUID, str]] = set()
    for dependency_index, raw_path in enumerate(
        spec.base_environment_manifest_paths,
    ):
        manifest_path = _resolve_base_environment_manifest_path(
            raw_path=raw_path,
            workspace_root=workspace_root,
            environment_toml_path=environment_toml_path,
        )
        source_toml_path = _base_environment_source_toml_path(
            manifest_path=manifest_path,
        )
        base_spec = load_aware_environment_spec(toml_path=source_toml_path)
        target_handle = (base_spec.environment.handle or "").strip()
        if not target_handle:
            raise RuntimeError(
                "Base environment aware.environment.toml is missing environment.handle: "
                f"{source_toml_path}"
            )
        target_package_id = stable_environment_config_package_id(
            handle=target_handle,
        )
        target_oig_commit_id = (
            await _resolve_environment_config_package_oig_commit_id_by_root(
                store=store,
                projection_hash=environment_package_projection_hash,
                root_id=target_package_id,
                target_handle=target_handle,
            )
        )
        target_key = (target_package_id, target_oig_commit_id, "base")
        if target_key in seen_targets:
            continue
        seen_targets.add(target_key)
        refs.append(
            EnvironmentConfigPackageDependencyMaterializationRef(
                dependency_role="base",
                dependency_index=dependency_index,
                target_handle=target_handle,
                target_environment_config_package_id=target_package_id,
                target_environment_config_package_object_instance_graph_commit_id=(
                    target_oig_commit_id
                ),
                manifest_path=manifest_path,
                manifest_toml_path=source_toml_path,
            )
        )
    return tuple(refs)


def _load_environment_profile_session_sources(
    *,
    workspace_root: Path,
    environment_toml_path: Path,
    spec: AwareEnvironmentSpec,
) -> EnvironmentSourceBundle:
    if spec.build is None:
        return EnvironmentSourceBundle()

    source_root = (environment_toml_path.parent / spec.build.sources_dir).resolve()
    if not _is_relative_to(source_root, workspace_root):
        raise RuntimeError(
            "aware.environment.toml [build].sources_dir must stay inside the "
            f"workspace: {source_root}"
        )
    if not source_root.is_dir():
        raise RuntimeError(
            "aware.environment.toml [build].sources_dir does not exist: "
            f"{source_root}"
        )

    source_paths = _discover_environment_source_paths(
        source_root=source_root,
        include_paths=spec.build.include_paths,
        exclude_paths=spec.build.exclude_paths,
    )
    bundles = [
        parse_environment_source_text(
            source_text=source_path.read_text(encoding="utf-8"),
            source_path=source_path.relative_to(workspace_root).as_posix(),
        )
        for source_path in source_paths
    ]
    return merge_environment_source_bundles(bundles)


def _discover_environment_source_paths(
    *,
    source_root: Path,
    include_paths: Iterable[str],
    exclude_paths: Iterable[str],
) -> tuple[Path, ...]:
    discovered: dict[str, Path] = {}
    exclude_patterns = tuple(exclude_paths)
    for include_path in include_paths:
        for path in source_root.glob(include_path):
            if not path.is_file():
                continue
            rel = path.relative_to(source_root).as_posix()
            if any(fnmatch(rel, pattern) for pattern in exclude_patterns):
                continue
            discovered[rel] = path.resolve()
    return tuple(discovered[key] for key in sorted(discovered))


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _resolve_base_environment_manifest_path(
    *,
    raw_path: str,
    workspace_root: Path,
    environment_toml_path: Path,
) -> Path:
    token = (raw_path or "").strip()
    if not token:
        raise RuntimeError("base_environment_manifest_paths contains an empty path")
    path = Path(token).expanduser()
    if path.is_absolute():
        resolved = path.resolve()
        if resolved.exists():
            return resolved
        raise RuntimeError(f"Base environment manifest not found: {resolved}")

    candidates = (
        (workspace_root / path).resolve(),
        (environment_toml_path.parent / path).resolve(),
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise RuntimeError(f"Base environment manifest not found: {candidates[0]}")


def _base_environment_source_toml_path(*, manifest_path: Path) -> Path:
    if manifest_path.name == "aware.environment.toml":
        return manifest_path
    for ancestor in manifest_path.parents:
        if ancestor.name not in {".aware", "_aware"}:
            continue
        candidate = ancestor.parent / "aware.environment.toml"
        if candidate.is_file():
            return candidate.resolve()
    raise RuntimeError(
        "Base environment manifest must be traceable to an adjacent "
        f"aware.environment.toml source: manifest_path={manifest_path}"
    )


async def _resolve_environment_config_package_oig_commit_id_by_root(
    *,
    store: FSCommitStore,
    projection_hash: str,
    root_id: UUID,
    target_handle: str,
) -> UUID:
    matches: dict[UUID, tuple[UUID, UUID]] = {}
    async for branch_id, head in store.iter_lane_heads_by_projection(
        projection_hash=projection_hash,
    ):
        domain_commit_id = _uuid_from_head(head, "commit_id")
        if domain_commit_id is None:
            continue
        commit = await store.get_commit(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=domain_commit_id,
        )
        if commit is None or commit.root_source_object_id != root_id:
            continue
        oig_commit_id = stable_object_instance_graph_commit_id(
            object_instance_graph_identity_id=commit.object_instance_graph_identity_id,
            commit_id=domain_commit_id,
        )
        matches[oig_commit_id] = (branch_id, domain_commit_id)
    if not matches:
        raise RuntimeError(
            "Base EnvironmentConfigPackage must be materialized and committed "
            "before dependent environment materialization: "
            f"target_handle={target_handle!r} "
            f"target_environment_config_package_id={root_id}"
        )
    if len(matches) > 1:
        raise RuntimeError(
            "Base EnvironmentConfigPackage resolution is ambiguous: "
            f"target_handle={target_handle!r} "
            f"target_environment_config_package_id={root_id} "
            f"commit_ids={', '.join(str(value) for value in sorted(matches, key=str))}"
        )
    return next(iter(matches))


@dataclass(frozen=True, slots=True)
class _DiscoveredEnvironmentSemanticPackageSpec:
    module_name: str
    aware_toml_path: Path
    ontology_manifest_path: str | None
    source_manifest_path: str
    package_name: str
    fqn_prefix: str
    dependency_package_names: tuple[str, ...]
    manifest_relative_path: str
    package_root: str
    workspace_package_root: str
    sources_root: str | None
    surface: str


def _workspace_dependency_semantic_package_names(
    *, workspace_root: Path
) -> tuple[str, ...]:
    workspace_toml_path = workspace_root / "aware.workspace.toml"
    if not workspace_toml_path.is_file():
        return ()
    try:
        raw = tomllib.loads(workspace_toml_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return ()
    if not isinstance(raw, Mapping):
        return ()
    workspace = raw.get("workspace")
    if not isinstance(workspace, Mapping):
        return ()
    dependencies = workspace.get("dependencies")
    if not isinstance(dependencies, list):
        return ()
    names: list[str] = []
    seen: set[str] = set()
    for dependency in dependencies:
        if not isinstance(dependency, Mapping):
            continue
        semantic_packages = dependency.get("semantic_packages")
        if not isinstance(semantic_packages, list):
            continue
        for semantic_package in semantic_packages:
            if not isinstance(semantic_package, Mapping):
                continue
            package_name = str(semantic_package.get("package_name") or "").strip()
            if not package_name or package_name in seen:
                continue
            seen.add(package_name)
            names.append(package_name)
    return tuple(names)


def _environment_external_dependency_package_names(
    *,
    workspace_root: Path,
    semantic_ontology_package_catalog: object | None = None,
) -> tuple[str, ...]:
    return _dedupe_texts(
        (
            *_workspace_dependency_semantic_package_names(
                workspace_root=workspace_root,
            ),
            *_semantic_catalog_external_dependency_package_names(
                workspace_root=workspace_root,
                semantic_ontology_package_catalog=semantic_ontology_package_catalog,
            ),
        )
    )


def _semantic_catalog_external_dependency_package_names(
    *,
    workspace_root: Path,
    semantic_ontology_package_catalog: object | None,
) -> tuple[str, ...]:
    if semantic_ontology_package_catalog is None:
        return ()
    if not isinstance(semantic_ontology_package_catalog, Mapping):
        raise ValueError(
            "Environment semantic materialization requires semantic ontology "
            "package catalog context to be a mapping."
        )
    if (
        semantic_ontology_package_catalog.get("schema")
        != SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_SCHEMA
    ):
        raise ValueError(
            "Environment semantic materialization received an unsupported "
            "semantic ontology package catalog schema."
        )
    entries = semantic_ontology_package_catalog.get("entries")
    if not isinstance(entries, list):
        raise ValueError(
            "Environment semantic materialization requires semantic ontology "
            "package catalog entries to be a list."
        )
    names: list[str] = []
    for entry in entries:
        if not isinstance(entry, Mapping):
            raise ValueError(
                "Environment semantic materialization requires semantic "
                "ontology package catalog entries to be mappings."
            )
        if not _semantic_catalog_entry_is_external_dependency(
            workspace_root=workspace_root,
            entry=entry,
        ):
            continue
        package_name = str(entry.get("package_name") or "").strip()
        if package_name:
            names.append(package_name)
    return _dedupe_texts(names)


def _semantic_catalog_entry_is_external_dependency(
    *,
    workspace_root: Path,
    entry: Mapping[str, object],
) -> bool:
    for key in ("dependency_id", "dependency_workspace_root"):
        value = entry.get(key)
        if isinstance(value, str) and value.strip():
            return True
    provenance = entry.get("catalog_provenance")
    if isinstance(provenance, str) and provenance.strip() in {
        "workspace_dependency",
        "dependency_profile_runtime_import",
        "dependency_import_lock",
    }:
        return True
    owner_root = entry.get("owner_root")
    if not isinstance(owner_root, str) or not owner_root.strip():
        return False
    resolved_owner_root = Path(owner_root).expanduser().resolve()
    resolved_workspace_root = workspace_root.expanduser().resolve()
    try:
        resolved_owner_root.relative_to(resolved_workspace_root)
    except ValueError:
        return True
    return False


def _dedupe_texts(values: Iterable[str]) -> tuple[str, ...]:
    deduped: list[str] = []
    seen: set[str] = set()
    for raw_value in values:
        value = str(raw_value).strip()
        if not value or value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return tuple(deduped)


def _environment_semantic_package_selector_names(
    *,
    workspace_root: Path,
    spec: AwareEnvironmentSpec,
) -> tuple[str, ...]:
    if not spec.ontologies:
        return tuple(spec.modules)
    module_names: list[str] = []
    seen: set[str] = set()
    for raw_path in spec.ontologies:
        ontology_toml_path = _resolve_environment_ontology_manifest_path(
            workspace_root=workspace_root,
            raw_path=raw_path,
        )
        ontology_spec = load_aware_ontology_toml_spec(toml_path=ontology_toml_path)
        module_name = _compatibility_module_name_from_ontology_manifest_path(
            workspace_root=workspace_root,
            ontology_toml_path=ontology_toml_path,
            fallback_name=ontology_spec.ontology.package_name,
        )
        if module_name in seen:
            continue
        seen.add(module_name)
        module_names.append(module_name)
    for module_name in spec.modules:
        if module_name in seen:
            continue
        seen.add(module_name)
        module_names.append(module_name)
    return tuple(module_names)


def _resolve_environment_ontology_manifest_path(
    *,
    workspace_root: Path,
    raw_path: str,
) -> Path:
    path = Path(raw_path)
    resolved = (
        path.resolve() if path.is_absolute() else (workspace_root / path).resolve()
    )
    if not resolved.is_file():
        raise RuntimeError(f"Environment ontology manifest not found: {raw_path}")
    try:
        resolved.relative_to(workspace_root.resolve())
    except ValueError as exc:
        raise RuntimeError(
            "Environment ontology manifest must stay inside workspace root: "
            f"{raw_path}"
        ) from exc
    if resolved.name != "aware.ontology.toml":
        raise RuntimeError(
            "Environment ontology selector must point to aware.ontology.toml: "
            f"{raw_path}"
        )
    return resolved


def _compatibility_module_name_from_ontology_manifest_path(
    *,
    workspace_root: Path,
    ontology_toml_path: Path,
    fallback_name: str,
) -> str:
    try:
        rel = ontology_toml_path.resolve().relative_to(workspace_root.resolve())
    except ValueError as exc:
        raise RuntimeError(
            "Environment ontology manifest must be workspace-relative: "
            f"{ontology_toml_path}"
        ) from exc
    parts = rel.parts
    if len(parts) >= 3 and parts[0] == "modules" and parts[-1] == "aware.ontology.toml":
        return parts[1]
    return (fallback_name or "").strip() or ontology_toml_path.parent.name


def _discover_environment_semantic_package_specs(
    *,
    workspace_root: Path,
    module_names: tuple[str, ...],
    ontology_manifest_paths: tuple[str, ...] = (),
    available_dependency_package_names: Iterable[str] = (),
) -> tuple[_DiscoveredEnvironmentSemanticPackageSpec, ...]:
    external_package_names = _dedupe_texts(
        (
            *_workspace_dependency_semantic_package_names(
                workspace_root=workspace_root,
            ),
            *available_dependency_package_names,
        )
    )
    if ontology_manifest_paths:
        discovered_from_paths = (
            _discover_environment_semantic_package_specs_from_ontology_manifests(
                workspace_root=workspace_root,
                ontology_manifest_paths=ontology_manifest_paths,
            )
        )
        return _topologically_order_environment_semantic_packages(
            discovered_packages=discovered_from_paths,
            available_dependency_package_names=external_package_names,
        )
    direct_specs = _discover_environment_semantic_package_specs_from_module_manifests(
        workspace_root=workspace_root,
        module_names=module_names,
    )
    if direct_specs is not None:
        return _topologically_order_environment_semantic_packages(
            discovered_packages=direct_specs,
            available_dependency_package_names=external_package_names,
        )

    setup_language_plugins()
    discovered_modules = {
        module.name: module
        for module in AWARE_CODE_PLUGIN.discover_modules(
            file_tree={}, workspace_root=workspace_root
        )
    }
    missing_modules = [
        module_name
        for module_name in module_names
        if module_name not in discovered_modules
    ]
    if missing_modules:
        raise RuntimeError(
            "aware.environment.toml references modules that were not discovered from canonical manifests: "
            + ", ".join(sorted(missing_modules))
        )

    discovered_packages: list[_DiscoveredEnvironmentSemanticPackageSpec] = []
    seen_package_keys: set[tuple[str, str]] = set()
    seen_package_names: set[str] = set()
    for module_name in module_names:
        module = discovered_modules[module_name]
        module_root = _resolve_module_root(
            workspace_root=workspace_root,
            module_root=module.root_path,
        )
        raw_packages = _expect_package_metadata_list(
            module.metadata, module_name=module_name
        )
        if not raw_packages:
            raise RuntimeError(
                f"Discovered module {module_name!r} has no canonical package manifests to materialize"
            )

        for raw_package in raw_packages:
            package_manifest_path = _resolve_package_manifest_path(
                workspace_root=workspace_root,
                module_root=module_root,
                raw_package=raw_package,
                module_name=module_name,
            )
            package_paths = _environment_semantic_package_manifest_paths(
                module_name=module_name,
                package_manifest_path=package_manifest_path,
            )
            if package_paths is None:
                continue
            aware_toml_path, ontology_toml_path = package_paths
            package_spec = _environment_semantic_package_spec_from_manifest(
                workspace_root=workspace_root,
                module_root=module_root,
                module_name=module_name,
                aware_toml_path=aware_toml_path,
                ontology_toml_path=ontology_toml_path,
            )
            _append_discovered_environment_semantic_package(
                discovered_packages=discovered_packages,
                seen_package_keys=seen_package_keys,
                seen_package_names=seen_package_names,
                package_spec=package_spec,
            )

    return _topologically_order_environment_semantic_packages(
        discovered_packages=tuple(discovered_packages),
        available_dependency_package_names=external_package_names,
    )


def _discover_environment_semantic_package_specs_from_module_manifests(
    *,
    workspace_root: Path,
    module_names: tuple[str, ...],
) -> tuple[_DiscoveredEnvironmentSemanticPackageSpec, ...] | None:
    module_roots: dict[str, Path] = {}
    module_specs: dict[str, object] = {}
    for module_name in module_names:
        module_root = (workspace_root / "modules" / module_name).resolve()
        module_toml_path = module_root / "aware.module.toml"
        if not module_toml_path.is_file():
            return None
        module_roots[module_name] = module_root
        module_specs[module_name] = load_aware_module_spec(toml_path=module_toml_path)

    discovered_packages: list[_DiscoveredEnvironmentSemanticPackageSpec] = []
    seen_package_keys: set[tuple[str, str]] = set()
    seen_package_names: set[str] = set()
    for module_name in module_names:
        module_root = module_roots[module_name]
        raw_packages = []
        for package in getattr(module_specs[module_name], "packages"):
            if Path(package.manifest).name not in {
                "aware.toml",
                "aware.ontology.toml",
            }:
                continue
            raw_packages.append(package)
        if not raw_packages:
            raise RuntimeError(
                f"Discovered module {module_name!r} has no canonical package manifests to materialize"
            )
        for raw_package in raw_packages:
            package_manifest_path = (module_root / raw_package.manifest).resolve()
            if not package_manifest_path.is_file():
                raise RuntimeError(
                    "Module package manifest declared by aware.module.toml was not found: "
                    + f"module={module_name!r} manifest={raw_package.manifest!r}"
                )
            package_paths = _environment_semantic_package_manifest_paths(
                module_name=module_name,
                package_manifest_path=package_manifest_path,
            )
            if package_paths is None:
                continue
            aware_toml_path, ontology_toml_path = package_paths
            package_spec = _environment_semantic_package_spec_from_manifest(
                workspace_root=workspace_root,
                module_root=module_root,
                module_name=module_name,
                aware_toml_path=aware_toml_path,
                ontology_toml_path=ontology_toml_path,
            )
            _append_discovered_environment_semantic_package(
                discovered_packages=discovered_packages,
                seen_package_keys=seen_package_keys,
                seen_package_names=seen_package_names,
                package_spec=package_spec,
            )

    return tuple(discovered_packages)


def _environment_semantic_package_manifest_paths(
    *,
    module_name: str,
    package_manifest_path: Path,
) -> tuple[Path, Path | None] | None:
    if package_manifest_path.name == "aware.toml":
        return package_manifest_path, None
    if package_manifest_path.name != "aware.ontology.toml":
        return None
    ontology_spec = load_aware_ontology_toml_spec(toml_path=package_manifest_path)
    aware_toml_path = (
        package_manifest_path.parent / ontology_spec.ontology.source_manifest
    ).resolve()
    if not aware_toml_path.is_file():
        raise RuntimeError(
            "aware.ontology.toml source_manifest was not found: "
            + f"module={module_name!r} "
            + f"ontology={package_manifest_path.as_posix()!r} "
            + f"source_manifest={ontology_spec.ontology.source_manifest!r}"
        )
    return aware_toml_path, package_manifest_path


def _discover_environment_semantic_package_specs_from_ontology_manifests(
    *,
    workspace_root: Path,
    ontology_manifest_paths: tuple[str, ...],
) -> tuple[_DiscoveredEnvironmentSemanticPackageSpec, ...]:
    discovered_packages: list[_DiscoveredEnvironmentSemanticPackageSpec] = []
    seen_package_keys: set[tuple[str, str]] = set()
    seen_package_names: set[str] = set()
    for raw_path in ontology_manifest_paths:
        ontology_toml_path = _resolve_environment_ontology_manifest_path(
            workspace_root=workspace_root,
            raw_path=raw_path,
        )
        ontology_spec = load_aware_ontology_toml_spec(toml_path=ontology_toml_path)
        module_root = ontology_toml_path.parent.resolve()
        module_name = _compatibility_module_name_from_ontology_manifest_path(
            workspace_root=workspace_root,
            ontology_toml_path=ontology_toml_path,
            fallback_name=ontology_spec.ontology.package_name,
        )
        aware_toml_path = (
            ontology_toml_path.parent / ontology_spec.ontology.source_manifest
        ).resolve()
        if not aware_toml_path.is_file():
            raise RuntimeError(
                "aware.ontology.toml source_manifest was not found: "
                + f"ontology={raw_path!r} "
                + f"source_manifest={ontology_spec.ontology.source_manifest!r}"
            )
        package_spec = _environment_semantic_package_spec_from_manifest(
            workspace_root=workspace_root,
            module_root=module_root,
            module_name=module_name,
            aware_toml_path=aware_toml_path,
            ontology_toml_path=ontology_toml_path,
        )
        _append_discovered_environment_semantic_package(
            discovered_packages=discovered_packages,
            seen_package_keys=seen_package_keys,
            seen_package_names=seen_package_names,
            package_spec=package_spec,
        )
    return _topologically_order_environment_semantic_packages(
        discovered_packages=tuple(discovered_packages),
    )


def _environment_semantic_package_spec_from_manifest(
    *,
    workspace_root: Path,
    module_root: Path,
    module_name: str,
    aware_toml_path: Path,
    ontology_toml_path: Path | None = None,
) -> _DiscoveredEnvironmentSemanticPackageSpec:
    aware_toml_spec = load_aware_toml_spec(toml_path=aware_toml_path)
    package_root = aware_toml_path.parent.resolve()
    sources_root = (package_root / aware_toml_spec.build.sources_dir).resolve()
    manifest_relative_path = _relative_to_module(
        path=aware_toml_path,
        module_root=module_root,
        module_name=module_name,
        label="aware.toml",
    )
    package_root_relative_path = _relative_to_module(
        path=package_root,
        module_root=module_root,
        module_name=module_name,
        label="package_root",
    )
    sources_root_relative_path = _relative_to_module(
        path=sources_root,
        module_root=module_root,
        module_name=module_name,
        label="sources_root",
    )
    workspace_package_root = _relative_to_workspace(
        path=package_root,
        workspace_root=workspace_root,
        label="package_root",
    )
    source_manifest_path = _relative_to_workspace(
        path=aware_toml_path,
        workspace_root=workspace_root,
        label="source_manifest",
    )
    ontology_manifest_path = (
        _relative_to_workspace(
            path=ontology_toml_path,
            workspace_root=workspace_root,
            label="ontology_manifest",
        )
        if ontology_toml_path is not None
        else None
    )
    return _DiscoveredEnvironmentSemanticPackageSpec(
        module_name=module_name,
        aware_toml_path=aware_toml_path,
        ontology_manifest_path=ontology_manifest_path,
        source_manifest_path=source_manifest_path,
        package_name=aware_toml_spec.package.package_name,
        fqn_prefix=aware_toml_spec.package.fqn_prefix,
        dependency_package_names=tuple(
            dependency.package_name for dependency in aware_toml_spec.dependencies
        ),
        manifest_relative_path=manifest_relative_path,
        package_root=package_root_relative_path,
        workspace_package_root=workspace_package_root,
        sources_root=sources_root_relative_path,
        surface=_environment_semantic_code_package_surface_for_kind(
            aware_toml_spec.package.kind
        ),
    )


def _append_discovered_environment_semantic_package(
    *,
    discovered_packages: list[_DiscoveredEnvironmentSemanticPackageSpec],
    seen_package_keys: set[tuple[str, str]],
    seen_package_names: set[str],
    package_spec: _DiscoveredEnvironmentSemanticPackageSpec,
) -> None:
    package_key = (
        package_spec.package_name,
        package_spec.fqn_prefix,
    )
    if package_key in seen_package_keys:
        raise RuntimeError(
            "Duplicate canonical package identity discovered for environment semantic closure: "
            + f"package_name={package_key[0]!r} fqn_prefix={package_key[1]!r}"
        )
    seen_package_keys.add(package_key)
    if package_spec.package_name in seen_package_names:
        raise RuntimeError(
            "Environment semantic closure discovered duplicate package_name values across canonical "
            + "package manifests, which makes aware.toml dependency resolution ambiguous: "
            + f"package_name={package_spec.package_name!r}"
        )
    seen_package_names.add(package_spec.package_name)
    discovered_packages.append(package_spec)


def _filter_environment_semantic_package_specs(
    *,
    semantic_package_specs: tuple[_DiscoveredEnvironmentSemanticPackageSpec, ...],
    selected_package_names: Iterable[str] | None,
    available_dependency_package_names: Iterable[str] = (),
) -> tuple[_DiscoveredEnvironmentSemanticPackageSpec, ...]:
    selected_names = tuple(
        dict.fromkeys(
            package_name
            for package_name in (
                str(raw_name).strip() for raw_name in (selected_package_names or ())
            )
            if package_name
        )
    )
    if not selected_names:
        return semantic_package_specs

    package_by_name = {
        package_spec.package_name: package_spec
        for package_spec in semantic_package_specs
    }
    external_package_names = frozenset(
        package_name
        for package_name in (
            str(raw_name).strip() for raw_name in available_dependency_package_names
        )
        if package_name
    )
    missing_package_names = sorted(
        package_name
        for package_name in selected_names
        if package_name not in package_by_name
    )
    if missing_package_names:
        raise RuntimeError(
            "Selected environment semantic package seed(s) are not present in "
            "the environment module closure: " + ", ".join(missing_package_names)
        )

    required_package_names: set[str] = set()
    visiting: list[str] = []

    def visit(package_name: str) -> None:
        if package_name in required_package_names:
            return
        if package_name in visiting:
            cycle = " -> ".join([*visiting, package_name])
            raise RuntimeError(
                "Selected environment semantic package closure detected a "
                f"dependency cycle in aware.toml manifests: {cycle}"
            )
        visiting.append(package_name)
        package = package_by_name[package_name]
        for dependency_package_name in package.dependency_package_names:
            if dependency_package_name in external_package_names:
                continue
            if dependency_package_name not in package_by_name:
                raise RuntimeError(
                    "Selected environment semantic package closure is missing "
                    "a dependency declared by aware.toml: "
                    f"{package_name} -> {dependency_package_name}"
                )
            visit(dependency_package_name)
        _ = visiting.pop()
        required_package_names.add(package_name)

    for selected_name in selected_names:
        visit(selected_name)

    return tuple(
        package_spec
        for package_spec in semantic_package_specs
        if package_spec.package_name in required_package_names
    )


def _topologically_order_environment_semantic_packages(
    *,
    discovered_packages: tuple[_DiscoveredEnvironmentSemanticPackageSpec, ...],
    available_dependency_package_names: Iterable[str] = (),
) -> tuple[_DiscoveredEnvironmentSemanticPackageSpec, ...]:
    sorted_packages = tuple(
        sorted(
            discovered_packages,
            key=lambda package: (
                package.module_name.casefold(),
                package.manifest_relative_path,
                package.package_name.casefold(),
            ),
        )
    )
    package_by_name = {package.package_name: package for package in sorted_packages}
    external_package_names = frozenset(
        package_name
        for package_name in (
            str(raw_name).strip() for raw_name in available_dependency_package_names
        )
        if package_name
    )
    missing_dependency_names = sorted(
        {
            dependency_package_name
            for package in sorted_packages
            for dependency_package_name in package.dependency_package_names
            if dependency_package_name not in package_by_name
            and dependency_package_name not in external_package_names
        }
    )
    if missing_dependency_names:
        raise RuntimeError(
            "Environment semantic closure is missing canonical package dependencies declared by aware.toml "
            + "manifests. Add the owning module package(s) to the environment before materialization: "
            + ", ".join(missing_dependency_names)
        )

    ordered_package_names: list[str] = []
    visiting: list[str] = []
    visited: set[str] = set()
    seed_order_index = {
        package.package_name: index for index, package in enumerate(sorted_packages)
    }

    def visit(package_name: str) -> None:
        if package_name in visited:
            return
        if package_name in visiting:
            cycle = " -> ".join([*visiting, package_name])
            raise RuntimeError(
                "Environment semantic closure detected a canonical package dependency cycle in aware.toml "
                + f"manifests: {cycle}"
            )
        visiting.append(package_name)
        package = package_by_name[package_name]
        dependency_package_names = sorted(
            (
                dependency_package_name
                for dependency_package_name in package.dependency_package_names
                if dependency_package_name not in external_package_names
            ),
            key=lambda dependency_package_name: seed_order_index[
                dependency_package_name
            ],
        )
        for dependency_package_name in dependency_package_names:
            visit(dependency_package_name)
        _ = visiting.pop()
        visited.add(package_name)
        ordered_package_names.append(package_name)

    for package in sorted_packages:
        visit(package.package_name)

    return tuple(
        package_by_name[package_name] for package_name in ordered_package_names
    )


def _resolve_module_root(*, workspace_root: Path, module_root: Path) -> Path:
    return (
        (workspace_root / module_root).resolve()
        if not module_root.is_absolute()
        else module_root.resolve()
    )


def _expect_package_metadata_list(
    metadata: Mapping[str, object], *, module_name: str
) -> list[Mapping[str, object]]:
    raw_packages = metadata.get("packages")
    if not isinstance(raw_packages, list):
        raise RuntimeError(
            f"Discovered module {module_name!r} metadata is missing canonical package metadata"
        )
    packages: list[Mapping[str, object]] = []
    for index, raw_package in enumerate(raw_packages):
        if not isinstance(raw_package, Mapping):
            raise RuntimeError(
                f"Discovered module {module_name!r} package metadata at index {index} must be an object"
            )
        packages.append(raw_package)
    return packages


def _resolve_package_manifest_path(
    *,
    workspace_root: Path,
    module_root: Path,
    raw_package: Mapping[str, object],
    module_name: str,
) -> Path:
    module_package_manifest = raw_package.get("module_package_manifest")
    if (
        not isinstance(module_package_manifest, str)
        or not module_package_manifest.strip()
    ):
        raise RuntimeError(
            f"Discovered module {module_name!r} package metadata is missing module_package_manifest"
        )
    manifest_path = Path(module_package_manifest.strip())
    resolved_path = (
        manifest_path.resolve()
        if manifest_path.is_absolute()
        else (module_root / manifest_path).resolve()
    )
    try:
        resolved_path.relative_to(module_root.resolve())
    except ValueError as exc:
        raise RuntimeError(
            "Discovered module package manifest must stay inside the module root: "
            f"module={module_name!r} manifest={module_package_manifest!r}"
        ) from exc
    try:
        resolved_path.relative_to(workspace_root.resolve())
    except ValueError as exc:
        raise RuntimeError(
            "Discovered module package manifest must stay inside the workspace root: "
            f"module={module_name!r} manifest={module_package_manifest!r}"
        ) from exc
    return resolved_path


def _relative_to_module(
    *, path: Path, module_root: Path, module_name: str, label: str
) -> str:
    try:
        return path.resolve().relative_to(module_root).as_posix()
    except ValueError as exc:
        raise RuntimeError(
            f"Discovered module {module_name!r} {label} is not within the module root: {path}"
        ) from exc


def _relative_to_workspace(*, path: Path, workspace_root: Path, label: str) -> str:
    try:
        return path.resolve().relative_to(workspace_root.resolve()).as_posix()
    except ValueError as exc:
        raise RuntimeError(
            f"Discovered environment package {label} is not within the workspace root: {path}"
        ) from exc
