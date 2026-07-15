from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from time import perf_counter
from typing import Any, Protocol, TypeVar
from uuid import UUID

from aware_code.package.snapshot_commit import commit_code_package_text_snapshot
from aware_code.semantic_contract_config import CodePackageConfigRef
from aware_code.semantic_contract_config import source_code_package_config_ref
from aware_code.stable_ids import stable_code_package_id
from aware_code.types import JsonArray
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.package.code_package import CodePackage

from aware_node.manifest.spec import AwareNodeCompilationMode, AwareNodeTomlSpec
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.fs_snapshot_store import FSSnapshotStore
from aware_meta.runtime.graph_context import MetaGraphRuntimeIndexSnapshot
from aware_meta.runtime.oig_hydration import reify_meta_orm_root_from_oig_commit
from aware_meta.runtime.read_model_provider import (
    read_workspace_meta_runtime_read_model,
)
from aware_node.compiler import (
    NodeEnvironmentTargetOwnership,
    NodePackageIncludeOwnership,
    NodeServiceTargetOwnership,
)
from aware_node.compile import compile_node_workspace
from aware_node.materialization.snapshot_commit import (
    NodeConfigEnvironmentProfileMountSnapshot,
    NodeConfigEnvironmentTargetSnapshot,
    NodeConfigServiceCodePackageSnapshot,
    NodeConfigServiceTargetSnapshot,
    NodePackageIncludedNodePackageSnapshot,
    commit_node_config_manifest_snapshot,
    commit_node_package_manifest_snapshot,
)
from aware_node_ontology.node.node_config import NodeConfig
from aware_node_ontology.node.node_config_environment_target import (
    NodeConfigEnvironmentTarget,
)
from aware_node_ontology.node.node_config_interface_target import (
    NodeConfigInterfaceTarget,
)
from aware_node_ontology.node.node_config_ontology_target import (
    NodeConfigOntologyTarget,
)
from aware_node_ontology.node.node_config_service_target import NodeConfigServiceTarget
from aware_node_ontology.node.node_config_service_code_package import (
    NodeConfigServiceCodePackage,
)
from aware_node_ontology.node.node_package import NodePackage
from aware_node_ontology.node.node_package_included_node_package import (
    NodePackageIncludedNodePackage,
)
from aware_node_ontology.stable_ids import (
    stable_node_config_id,
    stable_node_package_included_node_package_id,
    stable_node_package_id,
)
from aware_orm.models.orm_model import ORMModel
from aware_utils.logging import logger

_TRoot = TypeVar("_TRoot", bound=ORMModel)
_NODE_SOURCE_MANIFEST_KIND = "aware_node_toml"
_NODE_SOURCE_SURFACE = "runtime"


class _NodePackageMaterializationReadModel(Protocol):
    @property
    def index(self) -> MetaGraphRuntimeIndexSnapshot: ...

    def projection_hash_for_name(self, projection_name: str) -> str: ...


def _source_code_package_config_ref() -> CodePackageConfigRef:
    return source_code_package_config_ref(
        manifest_kind=_NODE_SOURCE_MANIFEST_KIND,
        surface=_NODE_SOURCE_SURFACE,
    )


def _source_code_package_config_id() -> UUID:
    return _source_code_package_config_ref().config_id


def _round_duration_s(duration_s: float) -> float:
    return round(max(duration_s, 0.0), 6)


@contextmanager
def _record_phase(phase_timings_s: dict[str, float], phase_name: str) -> Iterator[None]:
    started_at = perf_counter()
    logger.info("Node package materialization phase started: %s", phase_name)
    try:
        yield
    finally:
        duration_s = _round_duration_s(perf_counter() - started_at)
        phase_timings_s[phase_name] = duration_s
        logger.info(
            "Node package materialization phase finished: %s (%.6fs)",
            phase_name,
            duration_s,
        )


@dataclass(frozen=True, slots=True)
class NodePackageMaterializationSpec:
    node_toml_path: Path
    workspace_root: Path
    package_root: Path
    sources_root: Path
    manifest_spec: AwareNodeTomlSpec
    package_name: str
    package_fqn_prefix: str
    config_name: str
    config_description: str | None
    included_node_packages: tuple[NodePackageIncludeOwnership, ...]
    environment_targets: tuple[NodeEnvironmentTargetOwnership, ...]
    ontology_package_names: tuple[str, ...]
    service_targets: tuple[NodeServiceTargetOwnership, ...]
    service_names: tuple[str, ...]
    interface_names: tuple[str, ...]
    source_files: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class NodePackageMaterializationResult:
    node_toml_path: Path
    workspace_root: Path
    manifest_spec: AwareNodeTomlSpec
    node_config: NodeConfig
    node_config_environment_targets: tuple[NodeConfigEnvironmentTarget, ...]
    node_config_ontology_targets: tuple[NodeConfigOntologyTarget, ...]
    node_config_service_targets: tuple[NodeConfigServiceTarget, ...]
    node_config_service_code_packages: tuple[NodeConfigServiceCodePackage, ...]
    node_config_interface_targets: tuple[NodeConfigInterfaceTarget, ...]
    node_package_included_node_packages: tuple[NodePackageIncludedNodePackage, ...]
    node_package: NodePackage
    source_files: tuple[str, ...]
    source_code_package_id: UUID | None
    source_code_package_object_instance_graph_commit_id: UUID | None
    node_config_commit_id: UUID | None
    node_config_head_commit_id: UUID | None
    node_config_object_instance_graph_commit_id: UUID | None
    package_commit_id: UUID | None
    package_head_commit_id: UUID | None
    package_object_instance_graph_commit_id: UUID | None
    node_config_projection_hash: str
    node_package_projection_hash: str
    phase_timings_s: Mapping[str, float]


def resolve_node_package_materialization_spec(
    *,
    node_toml_path: Path,
    workspace_root: Path,
) -> NodePackageMaterializationSpec:
    compile_result = compile_node_workspace(
        toml_path=node_toml_path,
        repo_root=workspace_root,
        emit_compile_plan=False,
    )
    snapshot = compile_result.snapshot
    if snapshot.spec.build.compilation_mode != AwareNodeCompilationMode.node_ontology:
        raise RuntimeError(
            'Node package materialization requires [build].compilation_mode = "node_ontology" in aware.node.toml: '
            + str(snapshot.spec_path)
        )
    if compile_result.compile_plan is None:
        raise RuntimeError(
            "Node package materialization expected a compile plan for node_ontology mode: "
            + str(snapshot.spec_path)
        )

    package_name = (snapshot.spec.node.package_name or "").strip()
    if not package_name:
        raise RuntimeError(
            "Node package materialization requires non-empty [node].package_name in aware.node.toml: "
            + str(snapshot.spec_path)
        )
    package_fqn_prefix = (snapshot.spec.node.fqn_prefix or "").strip()
    if not package_fqn_prefix:
        raise RuntimeError(
            "Node package materialization requires non-empty [node].fqn_prefix in aware.node.toml: "
            + str(snapshot.spec_path)
        )

    node_ownership = compile_result.compile_plan.node_ownership
    sources_root = (snapshot.package_root / snapshot.spec.build.sources_dir).resolve()
    _assert_within(
        base=snapshot.package_root, candidate=sources_root, label="[build].sources_dir"
    )

    return NodePackageMaterializationSpec(
        node_toml_path=snapshot.spec_path,
        workspace_root=snapshot.repo_root,
        package_root=snapshot.package_root,
        sources_root=sources_root,
        manifest_spec=snapshot.spec,
        package_name=package_name,
        package_fqn_prefix=package_fqn_prefix,
        config_name=node_ownership.name,
        config_description=_normalize_optional_text(snapshot.spec.node.description),
        included_node_packages=tuple(node_ownership.included_node_packages),
        environment_targets=tuple(node_ownership.environment_targets),
        ontology_package_names=tuple(
            item.package_name for item in node_ownership.ontology_targets
        ),
        service_targets=tuple(node_ownership.service_targets),
        service_names=tuple(
            item.service_name for item in node_ownership.service_targets
        ),
        interface_names=tuple(
            item.interface_name for item in node_ownership.interface_targets
        ),
        source_files=tuple(path.as_posix() for path in snapshot.source_files),
    )


async def materialize_node_package_from_manifest(
    *,
    runtime: object,
    index: object,
    actor_id: UUID | None,
    branch_id: UUID,
    workspace_root: Path,
    node_toml_path: Path,
    repo_root: Path | None = None,
    semantic_ontology_package_catalog: Mapping[str, object] | None = None,
    source_code_package_id: UUID | None = None,
) -> NodePackageMaterializationResult:
    materialization_started_at = perf_counter()
    phase_timings_s: dict[str, float] = {}
    with _record_phase(phase_timings_s, "resolve_node_package_materialization_spec"):
        spec = resolve_node_package_materialization_spec(
            node_toml_path=node_toml_path,
            workspace_root=workspace_root,
        )
    source_code_package_config_ref = _source_code_package_config_ref()
    source_code_package_config_id = source_code_package_config_ref.config_id
    canonical_source_code_package_id = stable_code_package_id(
        code_package_config_id=source_code_package_config_ref.config_id,
        package_name=spec.package_name,
        language=CodeLanguage.aware.value,
    )
    if (
        source_code_package_id is not None
        and source_code_package_id != canonical_source_code_package_id
    ):
        raise RuntimeError(
            "Node package materialization received a source CodePackage id that "
            "does not match the aware_node_toml source package config: "
            f"expected={canonical_source_code_package_id} "
            f"actual={source_code_package_id}"
        )
    expected_source_code_package_id = canonical_source_code_package_id
    expected_node_config_id = stable_node_config_id(name=spec.config_name)
    expected_node_package_id = stable_node_package_id(name=spec.package_name)
    with _record_phase(phase_timings_s, "resolve_meta_runtime_read_model"):
        read_model = _resolve_node_package_materialization_read_model(
            workspace_root=workspace_root,
            repo_root=repo_root,
            semantic_ontology_package_catalog=semantic_ontology_package_catalog,
        )
    meta_index = read_model.index
    snapshot_index = _snapshot_commit_index(meta_index)

    code_package_projection_hash = read_model.projection_hash_for_name("CodePackage")
    node_config_projection_hash = read_model.projection_hash_for_name("NodeConfig")
    node_package_projection_hash = read_model.projection_hash_for_name("NodePackage")

    if index is None:
        logger.debug(
            "Node package materialization received no caller runtime index; "
            "using Meta runtime read model only."
        )
    else:
        logger.debug(
            "Node package materialization ignored caller runtime index in favor of "
            "Meta runtime read model."
        )

    manifest_relative_path = _relative_to(
        path=spec.node_toml_path,
        root=spec.workspace_root,
        label="aware.node.toml",
    )
    package_root_relative = _relative_to(
        path=spec.package_root,
        root=spec.workspace_root,
        label="package_root",
    )
    sources_root_relative = _relative_to(
        path=spec.sources_root,
        root=spec.workspace_root,
        label="sources_root",
    )

    source_texts_by_relative_path: dict[str, str] = {}
    for relative_path, source_path in _code_package_payload_files(spec=spec):
        with _record_phase(phase_timings_s, f"read_source_text:{relative_path}"):
            source_texts_by_relative_path[relative_path] = source_path.read_text(
                encoding="utf-8"
            )
    with _record_phase(phase_timings_s, "upsert_code_package_sources"):
        code_package_snapshot = await commit_code_package_text_snapshot(
            index=snapshot_index,
            actor_id=actor_id,
            branch_id=branch_id,
            projection_hash=code_package_projection_hash,
            code_package_config_id=source_code_package_config_id,
            package_name=spec.package_name,
            language=CodeLanguage.aware,
            surface=source_code_package_config_ref.surface,
            manifest_kind=source_code_package_config_ref.manifest_kind,
            manifest_relative_path=manifest_relative_path,
            package_root=package_root_relative,
            sources_root=sources_root_relative,
            fqn_prefix=spec.package_fqn_prefix,
            source_texts_by_relative_path=source_texts_by_relative_path,
        )
    with _record_phase(phase_timings_s, "hydrate_code_package_from_head"):
        code_package = await _hydrate_lane_root_from_head(
            index=meta_index,
            branch_id=branch_id,
            projection_hash=code_package_projection_hash,
            projection_name="CodePackage",
            root_id=expected_source_code_package_id,
            root_type=CodePackage,
        )
    if code_package is None:
        raise RuntimeError(
            "Node package materialization could not hydrate canonical CodePackage after build: "
            + f"package_name={spec.package_name!r}"
        )
    if code_package.id != code_package_snapshot.code_package.id:
        raise RuntimeError(
            "Node package materialization committed CodePackage with unexpected id: "
            f"expected={code_package_snapshot.code_package.id} actual={code_package.id}"
        )
    _validate_code_package_materialization_result(
        code_package=code_package,
        spec=spec,
        expected_source_code_package_id=expected_source_code_package_id,
        source_code_package_config_ref=source_code_package_config_ref,
    )

    with _record_phase(phase_timings_s, "upsert_node_config_targets"):
        node_config_snapshot = await commit_node_config_manifest_snapshot(
            index=snapshot_index,
            actor_id=actor_id,
            branch_id=branch_id,
            projection_hash=node_config_projection_hash,
            name=spec.config_name,
            description=spec.config_description,
            environment_targets=_node_config_environment_target_snapshots(spec=spec),
            ontology_package_names=spec.ontology_package_names,
            service_targets=_node_config_service_target_snapshots(spec=spec),
            interface_names=spec.interface_names,
        )
    with _record_phase(phase_timings_s, "hydrate_node_config_from_head"):
        node_config = await _hydrate_lane_root_from_head(
            index=meta_index,
            branch_id=branch_id,
            projection_hash=node_config_projection_hash,
            projection_name="NodeConfig",
            root_id=expected_node_config_id,
            root_type=NodeConfig,
        )
    if node_config is None:
        raise RuntimeError(
            "Node package materialization could not hydrate canonical NodeConfig after build: "
            + f"package_name={spec.package_name!r}"
        )
    _validate_node_config_materialization_result(
        node_config=node_config,
        spec=spec,
    )
    node_config_environment_targets = tuple(node_config.environment_targets)
    node_config_ontology_targets = tuple(node_config.ontology_targets)
    node_config_service_targets = tuple(node_config.service_targets)
    node_config_service_code_packages = tuple(
        package
        for target in node_config_service_targets
        for package in target.code_packages
    )
    node_config_interface_targets = tuple(node_config.interface_targets)

    node_package_fqn_prefix = (spec.manifest_spec.node.fqn_prefix or "").strip() or None
    node_package_include_paths = JsonArray(spec.manifest_spec.build.include_paths)
    node_package_exclude_paths = JsonArray(spec.manifest_spec.build.exclude_paths)
    node_package_compilation_mode = str(
        _enum_value(spec.manifest_spec.build.compilation_mode)
    )
    node_package_dependencies = _node_package_dependencies_payload(spec.manifest_spec)
    with _record_phase(phase_timings_s, "commit_node_package_manifest_snapshot"):
        node_package_snapshot = await commit_node_package_manifest_snapshot(
            index=snapshot_index,
            actor_id=actor_id,
            branch_id=branch_id,
            projection_hash=node_package_projection_hash,
            name=spec.package_name,
            node_config_id=node_config.id,
            source_code_package_id=code_package.id,
            fqn_prefix=node_package_fqn_prefix,
            version_number=spec.manifest_spec.node.version_number,
            title=spec.manifest_spec.node.title,
            description=spec.manifest_spec.node.description,
            aware_node_version=spec.manifest_spec.aware_node,
            manifest_relative_path=manifest_relative_path,
            package_root=package_root_relative,
            sources_root=sources_root_relative,
            include_paths=node_package_include_paths,
            exclude_paths=node_package_exclude_paths,
            force_fresh_scan=spec.manifest_spec.build.force_fresh_scan,
            compilation_mode=node_package_compilation_mode,
            dependencies=node_package_dependencies,
            included_node_packages=_node_package_include_snapshots(spec=spec),
        )
    with _record_phase(phase_timings_s, "hydrate_node_package_from_head"):
        node_package = await _hydrate_lane_root_from_head(
            index=meta_index,
            branch_id=branch_id,
            projection_hash=node_package_projection_hash,
            projection_name="NodePackage",
            root_id=expected_node_package_id,
            root_type=NodePackage,
        )
    if node_package is None:
        raise RuntimeError(
            "Node package materialization could not hydrate canonical NodePackage after build: "
            + f"package_name={spec.package_name!r}"
        )
    node_package_included_node_packages = tuple(node_package.included_node_packages)
    with _record_phase(phase_timings_s, "validate_node_package"):
        _validate_node_package_materialization_result(
            node_package=node_package,
            node_config=node_config,
            code_package=code_package,
            spec=spec,
        )
    phase_timings_s["total"] = _round_duration_s(
        perf_counter() - materialization_started_at
    )

    return NodePackageMaterializationResult(
        node_toml_path=spec.node_toml_path,
        workspace_root=spec.workspace_root,
        manifest_spec=spec.manifest_spec,
        node_config=node_config,
        node_config_environment_targets=tuple(node_config_environment_targets),
        node_config_ontology_targets=tuple(node_config_ontology_targets),
        node_config_service_targets=tuple(node_config_service_targets),
        node_config_service_code_packages=tuple(node_config_service_code_packages),
        node_config_interface_targets=tuple(node_config_interface_targets),
        node_package_included_node_packages=tuple(node_package_included_node_packages),
        node_package=node_package,
        source_files=spec.source_files,
        source_code_package_id=node_package.source_code_package_id,
        source_code_package_object_instance_graph_commit_id=(
            code_package_snapshot.object_instance_graph_commit_id
        ),
        node_config_commit_id=node_config_snapshot.commit_id,
        node_config_head_commit_id=node_config_snapshot.head_commit_id,
        node_config_object_instance_graph_commit_id=(
            node_config_snapshot.object_instance_graph_commit_id
        ),
        package_commit_id=node_package_snapshot.commit_id,
        package_head_commit_id=node_package_snapshot.head_commit_id,
        package_object_instance_graph_commit_id=(
            node_package_snapshot.object_instance_graph_commit_id
        ),
        node_config_projection_hash=node_config_projection_hash,
        node_package_projection_hash=node_package_projection_hash,
        phase_timings_s=dict(sorted(phase_timings_s.items())),
    )


def _validate_code_package_materialization_result(
    *,
    code_package: CodePackage,
    spec: NodePackageMaterializationSpec,
    expected_source_code_package_id: UUID,
    source_code_package_config_ref: CodePackageConfigRef,
) -> None:
    if code_package.id != expected_source_code_package_id:
        raise RuntimeError(
            "Node package materialization resolved CodePackage with unexpected id: "
            + f"expected={expected_source_code_package_id} actual={code_package.id}"
        )
    if code_package.surface != source_code_package_config_ref.surface:
        raise RuntimeError(
            "Node package materialization resolved CodePackage with unexpected surface: "
            + f"expected={source_code_package_config_ref.surface!r} "
            + f"actual={code_package.surface!r}"
        )
    if (
        getattr(code_package, "code_package_config_id", None)
        != source_code_package_config_ref.config_id
    ):
        raise RuntimeError(
            "Node package materialization resolved CodePackage with unexpected CodePackageConfig: "
            + f"expected={source_code_package_config_ref.config_id} "
            + f"actual={getattr(code_package, 'code_package_config_id', None)}"
        )


def _validate_node_config_materialization_result(
    *,
    node_config: NodeConfig,
    spec: NodePackageMaterializationSpec,
) -> None:
    expected_node_config_id = stable_node_config_id(name=spec.config_name)
    if node_config.id != expected_node_config_id:
        raise RuntimeError(
            "Node package materialization resolved NodeConfig with unexpected id: "
            + f"expected={expected_node_config_id} actual={node_config.id}"
        )
    if (node_config.name or "").strip() != spec.config_name:
        raise RuntimeError(
            "Node package materialization resolved NodeConfig with unexpected name: "
            + f"expected={spec.config_name!r} actual={node_config.name!r}"
        )
    if _normalize_optional_text(node_config.description) != spec.config_description:
        raise RuntimeError(
            "Node package materialization resolved NodeConfig with unexpected description: "
            + f"expected={spec.config_description!r} actual={node_config.description!r}"
        )
    expected_environment_targets = tuple(
        sorted(
            (
                target.environment_handle,
                tuple(
                    sorted(
                        (
                            mount.package_name,
                            mount.profile_key,
                            mount.mount_key,
                            mount.mode,
                            mount.position,
                        )
                        for mount in target.profile_mounts
                    )
                ),
            )
            for target in spec.environment_targets
        )
    )
    actual_environment_targets = tuple(
        sorted(
            (
                target.environment_handle,
                tuple(
                    sorted(
                        (
                            mount.package_name,
                            mount.profile_key,
                            mount.mount_key,
                            mount.mode,
                            mount.position,
                        )
                        for mount in target.profile_mounts
                    )
                ),
            )
            for target in node_config.environment_targets
        )
    )
    if actual_environment_targets != expected_environment_targets:
        raise RuntimeError(
            "Node package materialization resolved NodeConfig with stale or unexpected "
            "environment targets: "
            f"expected={expected_environment_targets!r} actual={actual_environment_targets!r}"
        )
    expected_service_names = tuple(sorted(spec.service_names))
    actual_service_names = tuple(
        sorted(target.service_name for target in node_config.service_targets)
    )
    if actual_service_names != expected_service_names:
        raise RuntimeError(
            "Node package materialization resolved NodeConfig with stale or unexpected "
            "service targets: "
            f"expected={expected_service_names!r} actual={actual_service_names!r}"
        )
    expected_service_code_packages = tuple(
        sorted(
            (
                target.service_name,
                package.slot_key,
                package.package_name,
                package.language,
            )
            for target in spec.service_targets
            for package in target.code_packages
        )
    )
    actual_service_code_packages = tuple(
        sorted(
            (
                target.service_name,
                package.slot_key,
                package.package_name,
                getattr(package.language, "value", package.language),
            )
            for target in node_config.service_targets
            for package in target.code_packages
        )
    )
    if actual_service_code_packages != expected_service_code_packages:
        raise RuntimeError(
            "Node package materialization resolved NodeConfig with stale or unexpected "
            "service code package activations: "
            f"expected={expected_service_code_packages!r} "
            f"actual={actual_service_code_packages!r}"
        )
    expected_ontology_package_names = tuple(sorted(spec.ontology_package_names))
    actual_ontology_package_names = tuple(
        sorted(target.package_name for target in node_config.ontology_targets)
    )
    if actual_ontology_package_names != expected_ontology_package_names:
        raise RuntimeError(
            "Node package materialization resolved NodeConfig with stale or unexpected "
            "ontology targets: "
            f"expected={expected_ontology_package_names!r} actual={actual_ontology_package_names!r}"
        )
    expected_interface_names = tuple(sorted(spec.interface_names))
    actual_interface_names = tuple(
        sorted(target.interface_name for target in node_config.interface_targets)
    )
    if actual_interface_names != expected_interface_names:
        raise RuntimeError(
            "Node package materialization resolved NodeConfig with stale or unexpected "
            "interface targets: "
            f"expected={expected_interface_names!r} actual={actual_interface_names!r}"
        )


def _validate_node_package_materialization_result(
    *,
    node_package: NodePackage,
    node_config: NodeConfig,
    code_package: CodePackage,
    spec: NodePackageMaterializationSpec,
) -> None:
    expected_node_package_id = stable_node_package_id(name=spec.package_name)
    if node_package.id != expected_node_package_id:
        raise RuntimeError(
            "Node package materialization resolved NodePackage with unexpected id: "
            + f"expected={expected_node_package_id} actual={node_package.id}"
        )
    if (node_package.name or "").strip() != spec.package_name:
        raise RuntimeError(
            "Node package materialization resolved NodePackage with unexpected name: "
            + f"expected={spec.package_name!r} actual={node_package.name!r}"
        )
    if node_package.node_config_id != node_config.id:
        raise RuntimeError(
            "Node package materialization resolved NodePackage with unexpected node_config_id: "
            + f"expected={node_config.id} actual={node_package.node_config_id}"
        )
    if node_package.source_code_package_id != code_package.id:
        raise RuntimeError(
            "Node package materialization resolved NodePackage with unexpected source_code_package_id: "
            + f"expected={code_package.id} actual={node_package.source_code_package_id}"
        )
    if node_package.fqn_prefix != (
        (spec.manifest_spec.node.fqn_prefix or "").strip() or None
    ):
        raise RuntimeError(
            "Node package materialization resolved NodePackage with unexpected fqn_prefix: "
            + f"expected={spec.manifest_spec.node.fqn_prefix!r} actual={node_package.fqn_prefix!r}"
        )
    if node_package.version_number != spec.manifest_spec.node.version_number:
        raise RuntimeError(
            "Node package materialization resolved NodePackage with unexpected version_number: "
            + f"expected={spec.manifest_spec.node.version_number} actual={node_package.version_number}"
        )
    if node_package.title != _normalize_optional_text(spec.manifest_spec.node.title):
        raise RuntimeError(
            "Node package materialization resolved NodePackage with unexpected title: "
            + f"expected={spec.manifest_spec.node.title!r} actual={node_package.title!r}"
        )
    if node_package.description != _normalize_optional_text(
        spec.manifest_spec.node.description
    ):
        raise RuntimeError(
            "Node package materialization resolved NodePackage with unexpected description: "
            + f"expected={spec.manifest_spec.node.description!r} actual={node_package.description!r}"
        )
    if node_package.aware_node_version != spec.manifest_spec.aware_node:
        raise RuntimeError(
            "Node package materialization resolved NodePackage with unexpected aware_node_version: "
            + f"expected={spec.manifest_spec.aware_node} actual={node_package.aware_node_version}"
        )
    expected_manifest_relative_path = _relative_to(
        path=spec.node_toml_path,
        root=spec.workspace_root,
        label="aware.node.toml",
    )
    expected_package_root = _relative_to(
        path=spec.package_root,
        root=spec.workspace_root,
        label="package_root",
    )
    expected_sources_root = _relative_to(
        path=spec.sources_root,
        root=spec.workspace_root,
        label="sources_root",
    )
    if node_package.manifest_relative_path != expected_manifest_relative_path:
        raise RuntimeError(
            "Node package materialization resolved NodePackage with unexpected manifest_relative_path: "
            + f"expected={expected_manifest_relative_path!r} actual={node_package.manifest_relative_path!r}"
        )
    if node_package.package_root != expected_package_root:
        raise RuntimeError(
            "Node package materialization resolved NodePackage with unexpected package_root: "
            + f"expected={expected_package_root!r} actual={node_package.package_root!r}"
        )
    if node_package.sources_root != expected_sources_root:
        raise RuntimeError(
            "Node package materialization resolved NodePackage with unexpected sources_root: "
            + f"expected={expected_sources_root!r} actual={node_package.sources_root!r}"
        )
    if list(node_package.include_paths) != list(spec.manifest_spec.build.include_paths):
        raise RuntimeError(
            "Node package materialization resolved NodePackage with unexpected include_paths: "
            + f"expected={spec.manifest_spec.build.include_paths!r} actual={list(node_package.include_paths)!r}"
        )
    if list(node_package.exclude_paths) != list(spec.manifest_spec.build.exclude_paths):
        raise RuntimeError(
            "Node package materialization resolved NodePackage with unexpected exclude_paths: "
            + f"expected={spec.manifest_spec.build.exclude_paths!r} actual={list(node_package.exclude_paths)!r}"
        )
    if node_package.force_fresh_scan != spec.manifest_spec.build.force_fresh_scan:
        raise RuntimeError(
            "Node package materialization resolved NodePackage with unexpected force_fresh_scan: "
            + f"expected={spec.manifest_spec.build.force_fresh_scan} actual={node_package.force_fresh_scan}"
        )
    if node_package.compilation_mode != str(
        _enum_value(spec.manifest_spec.build.compilation_mode)
    ):
        raise RuntimeError(
            "Node package materialization resolved NodePackage with unexpected compilation_mode: "
            + f"expected={_enum_value(spec.manifest_spec.build.compilation_mode)!r} "
            + f"actual={node_package.compilation_mode!r}"
        )
    if list(node_package.dependencies) != list(
        _node_package_dependencies_payload(spec.manifest_spec)
    ):
        raise RuntimeError(
            "Node package materialization resolved NodePackage with unexpected dependencies: "
            + f"expected={list(_node_package_dependencies_payload(spec.manifest_spec))!r} "
            + f"actual={list(node_package.dependencies)!r}"
        )
    expected_includes = tuple(
        sorted(include.included_package_name for include in spec.included_node_packages)
    )
    actual_includes = tuple(
        sorted(
            include.included_package_name
            for include in node_package.included_node_packages
        )
    )
    if actual_includes != expected_includes:
        raise RuntimeError(
            "Node package materialization resolved NodePackage with unexpected included_node_packages: "
            + f"expected={expected_includes!r} actual={actual_includes!r}"
        )
    for include in node_package.included_node_packages:
        expected_include_id = stable_node_package_included_node_package_id(
            node_package_id=node_package.id,
            included_package_name=include.included_package_name,
        )
        if include.id != expected_include_id:
            raise RuntimeError(
                "Node package materialization resolved NodePackage include with unexpected id: "
                + f"expected={expected_include_id} actual={include.id}"
            )


def _node_config_environment_target_snapshots(
    *,
    spec: NodePackageMaterializationSpec,
) -> tuple[NodeConfigEnvironmentTargetSnapshot, ...]:
    return tuple(
        NodeConfigEnvironmentTargetSnapshot(
            environment_handle=target.environment_handle,
            profile_mounts=tuple(
                NodeConfigEnvironmentProfileMountSnapshot(
                    package_name=mount.package_name,
                    profile_key=mount.profile_key,
                    mount_key=mount.mount_key,
                    mode=mount.mode,
                    position=mount.position,
                )
                for mount in target.profile_mounts
            ),
        )
        for target in spec.environment_targets
    )


def _node_config_service_target_snapshots(
    *,
    spec: NodePackageMaterializationSpec,
) -> tuple[NodeConfigServiceTargetSnapshot, ...]:
    return tuple(
        NodeConfigServiceTargetSnapshot(
            service_name=target.service_name,
            code_packages=tuple(
                NodeConfigServiceCodePackageSnapshot(
                    slot_key=package.slot_key,
                    package_name=package.package_name,
                    language=package.language,
                )
                for package in target.code_packages
            ),
        )
        for target in spec.service_targets
    )


def _node_package_include_snapshots(
    *,
    spec: NodePackageMaterializationSpec,
) -> tuple[NodePackageIncludedNodePackageSnapshot, ...]:
    return tuple(
        NodePackageIncludedNodePackageSnapshot(
            included_package_name=included.included_package_name,
            include_key=included.include_key,
            description=None,
        )
        for included in spec.included_node_packages
    )


def _code_package_payload_files(
    *,
    spec: NodePackageMaterializationSpec,
) -> tuple[tuple[str, Path], ...]:
    manifest_relative_path = _relative_to(
        path=spec.node_toml_path,
        root=spec.package_root,
        label="aware.node.toml",
    )
    items: list[tuple[str, Path]] = [
        (manifest_relative_path, spec.node_toml_path.resolve())
    ]
    for source_file in spec.source_files:
        items.append((source_file, (spec.package_root / source_file).resolve()))

    deduped: dict[str, Path] = {}
    for relative_path, path in items:
        deduped.setdefault(relative_path, path)
    return tuple((relative_path, deduped[relative_path]) for relative_path in deduped)


def _assert_within(*, base: Path, candidate: Path, label: str) -> None:
    base_resolved = base.resolve()
    candidate_resolved = candidate.resolve()
    if (
        candidate_resolved == base_resolved
        or base_resolved in candidate_resolved.parents
    ):
        return
    raise RuntimeError(
        "Node package materialization path resolved outside package boundary: "
        + f"label={label} base={base_resolved} candidate={candidate_resolved}"
    )


def _is_excluded(*, rel_path: str, exclude_patterns: list[str]) -> bool:
    token = PurePosixPath(rel_path)
    for raw_pattern in exclude_patterns:
        pattern = (raw_pattern or "").strip()
        if pattern and token.match(pattern):
            return True
    return False


def _relative_to(*, path: Path, root: Path, label: str) -> str:
    resolved_path = path.resolve()
    resolved_root = root.resolve()
    try:
        relative = resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise RuntimeError(
            "Node package materialization path resolved outside workspace root: "
            + f"label={label} root={resolved_root} path={resolved_path}"
        ) from exc
    relative_text = relative.as_posix()
    return relative_text or "."


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _enum_value(value: object) -> object:
    enum_value = getattr(value, "value", None)
    return enum_value if enum_value is not None else value


def _node_package_dependencies_payload(spec: AwareNodeTomlSpec) -> JsonArray:
    return JsonArray(
        [
            {
                "package_name": dependency.package_name,
                "version_number": dependency.version_number,
                "kind": _enum_value(dependency.kind),
            }
            for dependency in spec.dependencies
        ]
    )


def _resolve_node_package_materialization_read_model(
    *,
    workspace_root: Path,
    repo_root: Path | None = None,
    semantic_ontology_package_catalog: Mapping[str, object] | None = None,
) -> _NodePackageMaterializationReadModel:
    resolved_workspace_root = workspace_root.expanduser().resolve()
    read_model_repo_root = (
        repo_root.expanduser().resolve()
        if repo_root is not None
        else resolved_workspace_root
    )
    if not (read_model_repo_root / "modules").is_dir():
        raise RuntimeError(
            "Node package materialization requires an explicit read-model "
            "repo_root with a modules directory when workspace_root is not a "
            "source workspace root."
        )
    return read_workspace_meta_runtime_read_model(
        repo_root=read_model_repo_root,
        aware_root=(
            resolved_workspace_root
            if semantic_ontology_package_catalog is not None
            else read_model_repo_root
        ),
        required_projection_names=("CodePackage", "NodeConfig", "NodePackage"),
        semantic_ontology_package_catalog=semantic_ontology_package_catalog,
        composite_name="Aware Node Package Materialization Context",
    )


def _snapshot_commit_index(index: MetaGraphRuntimeIndexSnapshot) -> Any:
    return index


def _uuid_from_raw(value: object) -> UUID:
    if isinstance(value, UUID):
        return value
    return UUID(str(value))


async def _hydrate_lane_root_from_head(
    *,
    index: MetaGraphRuntimeIndexSnapshot,
    branch_id: UUID,
    projection_hash: str,
    projection_name: str,
    root_id: UUID | None,
    root_type: type[_TRoot],
) -> _TRoot | None:
    if root_id is None:
        return None

    commit_store = FSCommitStore()
    snapshot_store = FSSnapshotStore()
    head = await commit_store.head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    if head is None or head.get("commit_id") is None:
        return None

    return await reify_meta_orm_root_from_oig_commit(
        index=index,
        branch_id=branch_id,
        projection_hash=projection_hash,
        projection_name=projection_name,
        commit_id=_uuid_from_raw(head["commit_id"]),
        root_id=root_id,
        root_type=root_type,
        commit_store=commit_store,
        snapshot_store=snapshot_store,
    )
