from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
import json
from pathlib import Path
from time import perf_counter
from typing import Protocol, TypeVar, cast
from uuid import UUID

from aware_code.package.snapshot_commit import commit_code_package_text_snapshot
from aware_code.types import JsonArray, JsonObject
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.package.code_package import CodePackage

from aware_code.stable_ids import (
    code_package_source_config_key,
    stable_code_package_config_id,
    stable_code_package_id,
)
from aware_experience_ontology.stable_ids import stable_experience_package_id
from aware_interface.compile import compile_interface_workspace
from aware_interface.builder import ApiViewStateTruth
from aware_interface.workspace import InterfaceWorkspace, InterfaceWorkspaceSnapshot
from aware_interface_service_dto.comms.models.interface_config_bundle import (
    InterfaceConfigBundle,
)
from aware_interface_ontology.interface.interface_config import InterfaceConfig
from aware_interface_ontology.interface.interface_config_window_config import (
    InterfaceConfigWindowConfig,
)
from aware_interface_ontology.interface.interface_package import InterfacePackage
from aware_interface_ontology.interface.interface_package_experience_package import (
    InterfacePackageExperiencePackage,
)
from aware_interface_ontology.stable_ids import stable_interface_package_id
from aware_meta_ontology.stable_ids import stable_object_instance_graph_commit_id
from aware_interface.materialization.snapshot_commit import (
    InterfacePackageExperiencePackageSnapshotRef,
    commit_interface_package_manifest_snapshot,
)
from aware_interface.manifest import (
    AwareInterfaceCompilationMode,
    AwareInterfaceDependencyKind,
    AwareInterfaceTomlSpec,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.fs_snapshot_store import FSSnapshotStore
from aware_meta.runtime import (
    MetaGraphBoundRuntimeLane,
    MetaGraphRuntimeIndexSnapshot,
    find_meta_graph_projection_hash_by_name,
    reify_meta_orm_root_from_oig_commit,
)

from aware_interface.ontology.materialization import (
    PaneRenderSpecMaterializationResult,
    materialize_interface_config_bundle,
    materialize_pane_render_specs_from_materialization_artifact,
)

_TRoot = TypeVar("_TRoot", CodePackage, InterfacePackage)


class _RuntimeProtocol(Protocol):
    def bind(
        self,
        *,
        projection: str,
        branch_id: UUID,
        actor_id: UUID | None = None,
    ) -> MetaGraphBoundRuntimeLane: ...


@dataclass(frozen=True, slots=True)
class InterfacePackageMaterializationSpec:
    interface_toml_path: Path
    workspace_root: Path
    package_root: Path
    source_files: tuple[Path, ...]
    manifest_spec: AwareInterfaceTomlSpec
    config_bundle_path: Path
    config_bundle: InterfaceConfigBundle
    package_name: str
    package_fqn_prefix: str
    pane_render_spec_materialization_path: Path | None = None


@dataclass(frozen=True, slots=True)
class InterfacePackageMaterializationResult:
    interface_toml_path: Path
    workspace_root: Path
    manifest_spec: AwareInterfaceTomlSpec
    config_bundle_path: Path
    config_bundle: InterfaceConfigBundle
    interface_config: InterfaceConfig
    interface_config_window_configs: tuple[InterfaceConfigWindowConfig, ...]
    interface_package: InterfacePackage
    interface_package_experience_packages: tuple[InterfacePackageExperiencePackage, ...]
    pane_render_spec_materialization_result: PaneRenderSpecMaterializationResult | None
    source_code_package_id: UUID | None
    interface_config_commit_id: UUID | None
    interface_config_head_commit_id: UUID | None
    interface_config_object_instance_graph_commit_id: UUID | None
    package_commit_id: UUID | None
    package_head_commit_id: UUID | None
    package_object_instance_graph_commit_id: UUID | None
    source_object_instance_graph_commit_id: UUID | None
    source_projection_hash: str | None
    interface_config_projection_hash: str | None
    package_projection_hash: str | None
    phase_timings_s: Mapping[str, float]


def resolve_interface_package_materialization_spec(
    *,
    interface_toml_path: Path,
    workspace_root: Path,
    projection_identity_ocg: ObjectConfigGraph | None = None,
    projection_identity_ocgs: Iterable[ObjectConfigGraph] | None = None,
    state_model_catalog: Mapping[str, UUID] | None = None,
    state_attribute_catalog: Mapping[str, Mapping[str, UUID]] | None = None,
    api_view_catalog: Mapping[str, ApiViewStateTruth] | None = None,
) -> InterfacePackageMaterializationSpec:
    resolved_interface_toml_path = interface_toml_path.resolve()
    resolved_workspace_root = workspace_root.resolve()
    snapshot = InterfaceWorkspace.from_toml(
        toml_path=resolved_interface_toml_path,
        repo_root=resolved_workspace_root,
    ).build_snapshot()
    pane_render_spec_materialization_path: Path | None = None
    if _interface_ontology_bundle_requires_compile(snapshot=snapshot):
        compile_result = compile_interface_workspace(
            toml_path=resolved_interface_toml_path,
            repo_root=resolved_workspace_root,
            emit_config_bundle=True,
            projection_identity_ocg=projection_identity_ocg,
            projection_identity_ocgs=projection_identity_ocgs,
            state_model_catalog=state_model_catalog,
            state_attribute_catalog=state_attribute_catalog,
            api_view_catalog=api_view_catalog,
        )
        snapshot = compile_result.snapshot
        if compile_result.render_spec_materialization_artifact is not None:
            pane_render_spec_materialization_path = (
                compile_result.render_spec_materialization_artifact.path
            )
    if not snapshot.config_bundle_path.exists():
        raise FileNotFoundError(
            "Interface package materialization requires compiled config bundle at "
            + str(snapshot.config_bundle_path)
        )
    config_bundle = InterfaceConfigBundle.model_validate_json(
        snapshot.config_bundle_path.read_text(encoding="utf-8")
    )
    package_name = (snapshot.spec.interface.package_name or "").strip()
    if not package_name:
        raise RuntimeError(
            "Interface package materialization requires non-empty [interface].package_name in aware.interface.toml: "
            + str(resolved_interface_toml_path)
        )
    package_fqn_prefix = (snapshot.spec.interface.fqn_prefix or "").strip()
    if not package_fqn_prefix:
        raise RuntimeError(
            "Interface package materialization requires non-empty [interface].fqn_prefix in aware.interface.toml: "
            + str(resolved_interface_toml_path)
        )
    return InterfacePackageMaterializationSpec(
        interface_toml_path=resolved_interface_toml_path,
        workspace_root=resolved_workspace_root,
        package_root=snapshot.package_root,
        source_files=tuple(snapshot.source_files),
        manifest_spec=snapshot.spec,
        config_bundle_path=snapshot.config_bundle_path,
        config_bundle=config_bundle,
        package_name=package_name,
        package_fqn_prefix=package_fqn_prefix,
        pane_render_spec_materialization_path=pane_render_spec_materialization_path,
    )


def _interface_ontology_bundle_requires_compile(
    *,
    snapshot: InterfaceWorkspaceSnapshot,
) -> bool:
    if (
        snapshot.spec.build.compilation_mode
        != AwareInterfaceCompilationMode.interface_ontology
        or not snapshot.source_files
    ):
        return False
    if snapshot.spec.build.force_fresh_scan:
        return True
    bundle_path = snapshot.config_bundle_path
    if not bundle_path.is_file():
        return True
    bundle_mtime_ns = bundle_path.stat().st_mtime_ns
    for source_file in snapshot.source_files:
        source_path = (snapshot.package_root / source_file).resolve()
        if not source_path.is_file():
            return True
        if source_path.stat().st_mtime_ns > bundle_mtime_ns:
            return True
    return False


async def materialize_interface_package_from_manifest(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndexSnapshot,
    actor_id: UUID | None,
    branch_id: UUID,
    workspace_root: Path,
    interface_toml_path: Path,
    projection_identity_ocg: ObjectConfigGraph | None = None,
    projection_identity_ocgs: Iterable[ObjectConfigGraph] | None = None,
    state_model_catalog: Mapping[str, UUID] | None = None,
    state_attribute_catalog: Mapping[str, Mapping[str, UUID]] | None = None,
    api_view_catalog: Mapping[str, ApiViewStateTruth] | None = None,
    prefer_snapshot_materialization: bool = False,
    environment_id: UUID | None = None,
    process_id: UUID | None = None,
    thread_id: UUID | None = None,
) -> InterfacePackageMaterializationResult:
    spec = resolve_interface_package_materialization_spec(
        interface_toml_path=interface_toml_path,
        workspace_root=workspace_root,
        projection_identity_ocg=projection_identity_ocg,
        projection_identity_ocgs=projection_identity_ocgs,
        state_model_catalog=state_model_catalog,
        state_attribute_catalog=state_attribute_catalog,
        api_view_catalog=api_view_catalog,
    )
    source_code_package_config_id = stable_code_package_config_id(
        config_key=code_package_source_config_key(
            manifest_kind="aware_interface_toml",
            surface="representation",
        )
    )
    expected_source_code_package_id = stable_code_package_id(
        code_package_config_id=source_code_package_config_id,
        package_name=spec.package_name,
        language=CodeLanguage.aware.value,
    )
    expected_interface_package_id = stable_interface_package_id(name=spec.package_name)
    code_package_projection_hash = find_meta_graph_projection_hash_by_name(
        index=index,
        projection_name="CodePackage",
    )
    manifest_relative_path = _relative_to(
        path=spec.interface_toml_path,
        root=spec.workspace_root,
        label="aware.interface.toml",
    )
    package_root_relative = _relative_to(
        path=spec.interface_toml_path.parent,
        root=spec.workspace_root,
        label="package_root",
    )
    sources_root_relative = _relative_to(
        path=spec.interface_toml_path.parent / spec.manifest_spec.build.sources_dir,
        root=spec.workspace_root,
        label="sources_root",
    )
    config_bundle_relative_path = _relative_to(
        path=spec.config_bundle_path,
        root=spec.workspace_root,
        label="config_bundle_path",
    )
    if prefer_snapshot_materialization or not hasattr(runtime, "bind"):
        return await _materialize_interface_package_snapshot(
            runtime=runtime,
            index=index,
            actor_id=actor_id,
            environment_id=environment_id,
            process_id=process_id,
            thread_id=thread_id,
            branch_id=branch_id,
            spec=spec,
            code_package_projection_hash=code_package_projection_hash,
            manifest_relative_path=manifest_relative_path,
            package_root_relative=package_root_relative,
            sources_root_relative=sources_root_relative,
            config_bundle_relative_path=config_bundle_relative_path,
        )
    source_texts_by_relative_path: dict[str, str] = {}
    for source_file in spec.source_files:
        source_path = (spec.package_root / source_file).resolve()
        if source_path.is_file():
            source_texts_by_relative_path[source_file.as_posix()] = (
                source_path.read_text(encoding="utf-8")
            )
    source_snapshot = await commit_code_package_text_snapshot(
        index=cast(object, index),
        actor_id=actor_id,
        branch_id=branch_id,
        projection_hash=code_package_projection_hash,
        code_package_config_id=source_code_package_config_id,
        package_name=spec.package_name,
        language=CodeLanguage.aware,
        surface="representation",
        manifest_kind="aware_interface_toml",
        manifest_relative_path=manifest_relative_path,
        package_root=package_root_relative,
        sources_root=sources_root_relative,
        fqn_prefix=spec.package_fqn_prefix,
        source_texts_by_relative_path=source_texts_by_relative_path,
    )
    source_code_package = source_snapshot.code_package
    if source_code_package.id != expected_source_code_package_id:
        raise RuntimeError(
            "Interface source CodePackage id mismatch: "
            + f"expected={expected_source_code_package_id} actual={source_code_package.id}"
        )

    config_result = await materialize_interface_config_bundle(
        runtime=runtime,
        index=index,
        actor_id=actor_id,
        environment_id=environment_id,
        process_id=process_id,
        thread_id=thread_id,
        branch_id=branch_id,
        bundle=spec.config_bundle,
        prefer_snapshot_materialization=prefer_snapshot_materialization,
    )
    interface_config_projection_hash = find_meta_graph_projection_hash_by_name(
        index=index,
        projection_name="InterfaceConfig",
    )
    interface_config_domain_commit_id = (
        config_result.last_commit_id
        or await _lane_head_commit_id(
            branch_id=config_result.branch_id,
            projection_hash=interface_config_projection_hash,
        )
    )
    interface_config_object_instance_graph_commit_id = (
        await _object_instance_graph_commit_id_from_domain_commit(
            branch_id=config_result.branch_id,
            projection_hash=interface_config_projection_hash,
            domain_commit_id=interface_config_domain_commit_id,
        )
        if interface_config_domain_commit_id is not None
        else None
    )
    if interface_config_object_instance_graph_commit_id is None:
        raise RuntimeError(
            "Interface package materialization requires a committed InterfaceConfig "
            f"semantic root before building InterfacePackage: package_name={spec.package_name!r}"
        )
    pane_render_spec_materialization_result = (
        await _materialize_pane_render_specs_for_interface_package(
            runtime=runtime,
            index=index,
            actor_id=actor_id,
            environment_id=environment_id,
            process_id=process_id,
            thread_id=thread_id,
            spec=spec,
            prefer_snapshot_materialization=prefer_snapshot_materialization,
        )
    )

    interface_package_projection_hash = find_meta_graph_projection_hash_by_name(
        index=index,
        projection_name="InterfacePackage",
    )
    interface_package_lane = runtime.bind(
        branch_id=branch_id,
        projection=interface_package_projection_hash,
        actor_id=actor_id,
    )
    interface_package = await _hydrate_lane_root_from_head(
        index=index,
        branch_id=branch_id,
        projection_hash=interface_package_projection_hash,
        root_id=expected_interface_package_id,
        root_type=InterfacePackage,
    )
    interface_package_experience_packages: list[InterfacePackageExperiencePackage] = []
    interface_package_fqn_prefix = (
        spec.manifest_spec.interface.fqn_prefix or ""
    ).strip() or None
    interface_package_include_paths = JsonArray(spec.manifest_spec.build.include_paths)
    interface_package_exclude_paths = JsonArray(spec.manifest_spec.build.exclude_paths)
    interface_package_compilation_mode = str(
        _enum_value(spec.manifest_spec.build.compilation_mode)
    )
    interface_package_dependencies = _interface_package_dependencies_payload(
        spec.manifest_spec
    )
    interface_package_dart = _interface_package_dart_payload(spec.manifest_spec)
    with interface_package_lane.activate(commit=True, publish=False):
        if interface_package is None:
            interface_package = await InterfacePackage.build(
                name=spec.package_name,
                interface_config_id=config_result.interface_config.id,
                interface_config_object_instance_graph_commit_id=(
                    interface_config_object_instance_graph_commit_id
                ),
                source_code_package_id=source_code_package.id,
                fqn_prefix=interface_package_fqn_prefix,
                version_number=spec.manifest_spec.interface.version_number,
                title=spec.manifest_spec.interface.title,
                description=spec.manifest_spec.interface.description,
                aware_interface_version=spec.manifest_spec.aware_interface,
                manifest_relative_path=manifest_relative_path,
                package_root=package_root_relative,
                sources_root=sources_root_relative,
                config_bundle_path=config_bundle_relative_path,
                include_paths=interface_package_include_paths,
                exclude_paths=interface_package_exclude_paths,
                force_fresh_scan=spec.manifest_spec.build.force_fresh_scan,
                compilation_mode=interface_package_compilation_mode,
                dependencies=interface_package_dependencies,
                dart=interface_package_dart,
            )
        else:
            if (
                interface_package.interface_config_id
                != config_result.interface_config.id
            ):
                raise RuntimeError(
                    "Interface package materialization resolved committed InterfacePackage with "
                    + "unexpected interface_config_id: "
                    + f"package_name={spec.package_name!r} expected={config_result.interface_config.id} "
                    + f"actual={interface_package.interface_config_id}"
                )
            interface_package = await interface_package.sync_manifest_truth(
                interface_config_object_instance_graph_commit_id=(
                    interface_config_object_instance_graph_commit_id
                ),
                source_code_package_id=source_code_package.id,
                fqn_prefix=interface_package_fqn_prefix,
                version_number=spec.manifest_spec.interface.version_number,
                title=spec.manifest_spec.interface.title,
                description=spec.manifest_spec.interface.description,
                aware_interface_version=spec.manifest_spec.aware_interface,
                manifest_relative_path=manifest_relative_path,
                package_root=package_root_relative,
                sources_root=sources_root_relative,
                config_bundle_path=config_bundle_relative_path,
                include_paths=interface_package_include_paths,
                exclude_paths=interface_package_exclude_paths,
                force_fresh_scan=spec.manifest_spec.build.force_fresh_scan,
                compilation_mode=interface_package_compilation_mode,
                dependencies=interface_package_dependencies,
                dart=interface_package_dart,
            )
        for dependency in spec.manifest_spec.dependencies:
            if dependency.kind != AwareInterfaceDependencyKind.experience_package:
                continue
            interface_package_experience_packages.append(
                await interface_package.attach_experience_package(
                    experience_package_id=stable_experience_package_id(
                        name=dependency.package_name
                    ),
                )
            )
    _validate_interface_package_manifest_truth(
        interface_package=interface_package,
        spec=spec,
        source_code_package=source_code_package,
        interface_config=config_result.interface_config,
        interface_config_object_instance_graph_commit_id=(
            interface_config_object_instance_graph_commit_id
        ),
        manifest_relative_path=manifest_relative_path,
        package_root=package_root_relative,
        sources_root=sources_root_relative,
        config_bundle_path=config_bundle_relative_path,
    )
    interface_package_domain_commit_id = (
        interface_package_lane.last_commit_id
        or await _lane_head_commit_id(
            branch_id=branch_id,
            projection_hash=interface_package_projection_hash,
        )
    )
    interface_package_object_instance_graph_commit_id = (
        await _object_instance_graph_commit_id_from_domain_commit(
            branch_id=branch_id,
            projection_hash=interface_package_projection_hash,
            domain_commit_id=interface_package_domain_commit_id,
        )
        if interface_package_domain_commit_id is not None
        else None
    )

    return InterfacePackageMaterializationResult(
        interface_toml_path=spec.interface_toml_path,
        workspace_root=spec.workspace_root,
        manifest_spec=spec.manifest_spec,
        config_bundle_path=spec.config_bundle_path,
        config_bundle=spec.config_bundle,
        interface_config=config_result.interface_config,
        interface_config_window_configs=config_result.interface_config_window_configs,
        interface_package=interface_package,
        interface_package_experience_packages=tuple(
            interface_package_experience_packages
        ),
        pane_render_spec_materialization_result=(
            pane_render_spec_materialization_result
        ),
        source_code_package_id=source_code_package.id,
        interface_config_commit_id=interface_config_domain_commit_id,
        interface_config_head_commit_id=config_result.last_head_commit_id,
        interface_config_object_instance_graph_commit_id=(
            interface_config_object_instance_graph_commit_id
        ),
        package_commit_id=interface_package_domain_commit_id,
        package_head_commit_id=interface_package_domain_commit_id,
        package_object_instance_graph_commit_id=(
            interface_package_object_instance_graph_commit_id
        ),
        source_object_instance_graph_commit_id=(
            source_snapshot.object_instance_graph_commit_id
        ),
        source_projection_hash=code_package_projection_hash,
        interface_config_projection_hash=interface_config_projection_hash,
        package_projection_hash=interface_package_projection_hash,
        phase_timings_s={},
    )


async def _materialize_interface_package_snapshot(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndexSnapshot,
    actor_id: UUID | None,
    branch_id: UUID,
    spec: InterfacePackageMaterializationSpec,
    code_package_projection_hash: str,
    manifest_relative_path: str,
    package_root_relative: str,
    sources_root_relative: str,
    config_bundle_relative_path: str,
    environment_id: UUID | None = None,
    process_id: UUID | None = None,
    thread_id: UUID | None = None,
) -> InterfacePackageMaterializationResult:
    phase_timings_s: dict[str, float] = {}
    phase_started = perf_counter()
    source_texts_by_relative_path: dict[str, str] = {}
    for source_file in spec.source_files:
        source_path = (spec.package_root / source_file).resolve()
        if source_path.is_file():
            source_texts_by_relative_path[source_file.as_posix()] = (
                source_path.read_text(encoding="utf-8")
            )
    phase_timings_s["read_source_texts_s"] = perf_counter() - phase_started
    source_code_package_config_id = stable_code_package_config_id(
        config_key=code_package_source_config_key(
            manifest_kind="aware_interface_toml",
            surface="representation",
        )
    )
    phase_started = perf_counter()
    source_snapshot = await commit_code_package_text_snapshot(
        index=cast(object, index),
        actor_id=actor_id,
        branch_id=branch_id,
        projection_hash=code_package_projection_hash,
        code_package_config_id=source_code_package_config_id,
        package_name=spec.package_name,
        language=CodeLanguage.aware,
        surface="representation",
        manifest_kind="aware_interface_toml",
        manifest_relative_path=manifest_relative_path,
        package_root=package_root_relative,
        sources_root=sources_root_relative,
        fqn_prefix=spec.package_fqn_prefix,
        source_texts_by_relative_path=source_texts_by_relative_path,
    )
    phase_timings_s["commit_source_code_package_snapshot_s"] = (
        perf_counter() - phase_started
    )
    source_code_package = source_snapshot.code_package
    phase_started = perf_counter()
    config_result = await materialize_interface_config_bundle(
        runtime=object(),
        index=index,
        actor_id=actor_id,
        environment_id=environment_id,
        process_id=process_id,
        thread_id=thread_id,
        branch_id=branch_id,
        bundle=spec.config_bundle,
        prefer_snapshot_materialization=True,
    )
    phase_timings_s["commit_interface_config_snapshot_s"] = (
        perf_counter() - phase_started
    )
    interface_config_projection_hash = find_meta_graph_projection_hash_by_name(
        index=index,
        projection_name="InterfaceConfig",
    )
    interface_config_domain_commit_id = config_result.last_commit_id
    interface_config_object_instance_graph_commit_id = (
        config_result.object_instance_graph_commit_id
    )
    if interface_config_object_instance_graph_commit_id is None:
        raise RuntimeError(
            "Interface package snapshot materialization requires a committed "
            f"InterfaceConfig semantic root: package_name={spec.package_name!r}"
        )
    interface_package_projection_hash = find_meta_graph_projection_hash_by_name(
        index=index,
        projection_name="InterfacePackage",
    )
    interface_package_fqn_prefix = (
        spec.manifest_spec.interface.fqn_prefix or ""
    ).strip() or None
    interface_package_include_paths = JsonArray(spec.manifest_spec.build.include_paths)
    interface_package_exclude_paths = JsonArray(spec.manifest_spec.build.exclude_paths)
    interface_package_compilation_mode = str(
        _enum_value(spec.manifest_spec.build.compilation_mode)
    )
    interface_package_dependencies = _interface_package_dependencies_payload(
        spec.manifest_spec
    )
    interface_package_dart = _interface_package_dart_payload(spec.manifest_spec)
    phase_started = perf_counter()
    package_snapshot = await commit_interface_package_manifest_snapshot(
        index=cast(object, index),
        actor_id=actor_id,
        branch_id=branch_id,
        projection_hash=interface_package_projection_hash,
        package_name=spec.package_name,
        interface_config_id=config_result.interface_config.id,
        interface_config_object_instance_graph_commit_id=(
            interface_config_object_instance_graph_commit_id
        ),
        source_code_package_id=source_code_package.id,
        fqn_prefix=interface_package_fqn_prefix,
        version_number=spec.manifest_spec.interface.version_number,
        title=spec.manifest_spec.interface.title,
        description=spec.manifest_spec.interface.description,
        aware_interface_version=spec.manifest_spec.aware_interface,
        manifest_relative_path=manifest_relative_path,
        package_root=package_root_relative,
        sources_root=sources_root_relative,
        config_bundle_path=config_bundle_relative_path,
        include_paths=interface_package_include_paths,
        exclude_paths=interface_package_exclude_paths,
        force_fresh_scan=spec.manifest_spec.build.force_fresh_scan,
        compilation_mode=interface_package_compilation_mode,
        dependencies=interface_package_dependencies,
        dart=interface_package_dart,
        experience_package_refs=tuple(
            InterfacePackageExperiencePackageSnapshotRef(
                experience_package_id=stable_experience_package_id(
                    name=dependency.package_name,
                ),
            )
            for dependency in spec.manifest_spec.dependencies
            if dependency.kind == AwareInterfaceDependencyKind.experience_package
        ),
    )
    phase_timings_s["commit_interface_package_snapshot_s"] = (
        perf_counter() - phase_started
    )
    _validate_interface_package_manifest_truth(
        interface_package=package_snapshot.interface_package,
        spec=spec,
        source_code_package=source_code_package,
        interface_config=config_result.interface_config,
        interface_config_object_instance_graph_commit_id=(
            interface_config_object_instance_graph_commit_id
        ),
        manifest_relative_path=manifest_relative_path,
        package_root=package_root_relative,
        sources_root=sources_root_relative,
        config_bundle_path=config_bundle_relative_path,
    )
    if interface_config_domain_commit_id is None:
        interface_config_domain_commit_id = await _lane_head_commit_id(
            branch_id=branch_id,
            projection_hash=interface_config_projection_hash,
        )
    phase_started = perf_counter()
    pane_render_spec_materialization_result = (
        await _materialize_pane_render_specs_for_interface_package(
            runtime=runtime,
            index=index,
            actor_id=actor_id,
            environment_id=environment_id,
            process_id=process_id,
            thread_id=thread_id,
            spec=spec,
            prefer_snapshot_materialization=True,
        )
    )
    phase_timings_s["commit_pane_render_spec_snapshot_s"] = (
        perf_counter() - phase_started
    )
    return InterfacePackageMaterializationResult(
        interface_toml_path=spec.interface_toml_path,
        workspace_root=spec.workspace_root,
        manifest_spec=spec.manifest_spec,
        config_bundle_path=spec.config_bundle_path,
        config_bundle=spec.config_bundle,
        interface_config=config_result.interface_config,
        interface_config_window_configs=(config_result.interface_config_window_configs),
        interface_package=package_snapshot.interface_package,
        interface_package_experience_packages=package_snapshot.experience_packages,
        pane_render_spec_materialization_result=(
            pane_render_spec_materialization_result
        ),
        source_code_package_id=source_code_package.id,
        interface_config_commit_id=interface_config_domain_commit_id,
        interface_config_head_commit_id=config_result.last_head_commit_id,
        interface_config_object_instance_graph_commit_id=(
            interface_config_object_instance_graph_commit_id
        ),
        package_commit_id=package_snapshot.commit_id,
        package_head_commit_id=package_snapshot.head_commit_id,
        package_object_instance_graph_commit_id=(
            package_snapshot.object_instance_graph_commit_id
        ),
        source_object_instance_graph_commit_id=(
            source_snapshot.object_instance_graph_commit_id
        ),
        source_projection_hash=code_package_projection_hash,
        interface_config_projection_hash=interface_config_projection_hash,
        package_projection_hash=interface_package_projection_hash,
        phase_timings_s=phase_timings_s,
    )


async def _materialize_pane_render_specs_for_interface_package(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndexSnapshot,
    actor_id: UUID | None,
    spec: InterfacePackageMaterializationSpec,
    environment_id: UUID | None = None,
    process_id: UUID | None = None,
    thread_id: UUID | None = None,
    prefer_snapshot_materialization: bool = False,
) -> PaneRenderSpecMaterializationResult | None:
    materialization_path = spec.pane_render_spec_materialization_path
    if materialization_path is None or not materialization_path.is_file():
        return None
    if not _pane_render_spec_materialization_has_rows(materialization_path):
        return None
    return await materialize_pane_render_specs_from_materialization_artifact(
        runtime=runtime,
        index=index,
        actor_id=actor_id,
        environment_id=environment_id,
        process_id=process_id,
        thread_id=thread_id,
        materialization_path=materialization_path,
        prefer_snapshot_materialization=prefer_snapshot_materialization,
    )


def _pane_render_spec_materialization_has_rows(materialization_path: Path) -> bool:
    payload = json.loads(materialization_path.read_text(encoding="utf-8") or "{}")
    if not isinstance(payload, dict):
        return False
    rows = payload.get("render_specs")
    return isinstance(rows, list) and bool(rows)


def _relative_to(*, path: Path, root: Path, label: str) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise RuntimeError(
            f"Interface package materialization requires {label} under workspace root: "
            + f"path={path.resolve()} workspace_root={root.resolve()}"
        ) from exc


def _enum_value(value: object) -> object:
    enum_value = getattr(value, "value", None)
    return enum_value if enum_value is not None else value


def _interface_package_dependencies_payload(spec: AwareInterfaceTomlSpec) -> JsonArray:
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


def _interface_package_dart_payload(spec: AwareInterfaceTomlSpec) -> JsonObject:
    if spec.dart is None:
        return JsonObject()
    return JsonObject(
        {
            "package_path": spec.dart.package_path,
            "package_name": spec.dart.package_name,
        }
    )


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _validate_interface_package_manifest_truth(
    *,
    interface_package: InterfacePackage,
    spec: InterfacePackageMaterializationSpec,
    source_code_package: CodePackage,
    interface_config: InterfaceConfig,
    interface_config_object_instance_graph_commit_id: UUID,
    manifest_relative_path: str,
    package_root: str,
    sources_root: str,
    config_bundle_path: str,
) -> None:
    if interface_package.interface_config_id != interface_config.id:
        raise RuntimeError(
            "Interface package materialization resolved InterfacePackage with unexpected "
            + f"interface_config_id: expected={interface_config.id} actual={interface_package.interface_config_id}"
        )
    if interface_package.source_code_package_id != source_code_package.id:
        raise RuntimeError(
            "Interface package materialization resolved InterfacePackage with unexpected "
            + "source_code_package_id: "
            + f"expected={source_code_package.id} actual={interface_package.source_code_package_id}"
        )
    if (
        interface_package.interface_config_object_instance_graph_commit_id
        != interface_config_object_instance_graph_commit_id
    ):
        raise RuntimeError(
            "Interface package materialization resolved InterfacePackage with unexpected "
            + "interface_config_object_instance_graph_commit_id: "
            + f"expected={interface_config_object_instance_graph_commit_id} "
            + f"actual={interface_package.interface_config_object_instance_graph_commit_id}"
        )
    if interface_package.fqn_prefix != (
        (spec.manifest_spec.interface.fqn_prefix or "").strip() or None
    ):
        raise RuntimeError(
            "Interface package materialization resolved InterfacePackage with unexpected fqn_prefix: "
            + f"expected={spec.manifest_spec.interface.fqn_prefix!r} actual={interface_package.fqn_prefix!r}"
        )
    if interface_package.version_number != spec.manifest_spec.interface.version_number:
        raise RuntimeError(
            "Interface package materialization resolved InterfacePackage with unexpected version_number: "
            + f"expected={spec.manifest_spec.interface.version_number} actual={interface_package.version_number}"
        )
    if interface_package.title != _normalize_optional_text(
        spec.manifest_spec.interface.title
    ):
        raise RuntimeError(
            "Interface package materialization resolved InterfacePackage with unexpected title: "
            + f"expected={spec.manifest_spec.interface.title!r} actual={interface_package.title!r}"
        )
    if interface_package.description != _normalize_optional_text(
        spec.manifest_spec.interface.description
    ):
        raise RuntimeError(
            "Interface package materialization resolved InterfacePackage with unexpected description: "
            + f"expected={spec.manifest_spec.interface.description!r} actual={interface_package.description!r}"
        )
    if interface_package.aware_interface_version != spec.manifest_spec.aware_interface:
        raise RuntimeError(
            "Interface package materialization resolved InterfacePackage with unexpected aware_interface_version: "
            + f"expected={spec.manifest_spec.aware_interface} actual={interface_package.aware_interface_version}"
        )
    if interface_package.manifest_relative_path != manifest_relative_path:
        raise RuntimeError(
            "Interface package materialization resolved InterfacePackage with unexpected manifest_relative_path: "
            + f"expected={manifest_relative_path!r} actual={interface_package.manifest_relative_path!r}"
        )
    if interface_package.package_root != package_root:
        raise RuntimeError(
            "Interface package materialization resolved InterfacePackage with unexpected package_root: "
            + f"expected={package_root!r} actual={interface_package.package_root!r}"
        )
    if interface_package.sources_root != sources_root:
        raise RuntimeError(
            "Interface package materialization resolved InterfacePackage with unexpected sources_root: "
            + f"expected={sources_root!r} actual={interface_package.sources_root!r}"
        )
    if interface_package.config_bundle_path != config_bundle_path:
        raise RuntimeError(
            "Interface package materialization resolved InterfacePackage with unexpected config_bundle_path: "
            + f"expected={config_bundle_path!r} actual={interface_package.config_bundle_path!r}"
        )
    if list(interface_package.include_paths) != list(
        spec.manifest_spec.build.include_paths
    ):
        raise RuntimeError(
            "Interface package materialization resolved InterfacePackage with unexpected include_paths: "
            + f"expected={spec.manifest_spec.build.include_paths!r} actual={list(interface_package.include_paths)!r}"
        )
    if list(interface_package.exclude_paths) != list(
        spec.manifest_spec.build.exclude_paths
    ):
        raise RuntimeError(
            "Interface package materialization resolved InterfacePackage with unexpected exclude_paths: "
            + f"expected={spec.manifest_spec.build.exclude_paths!r} actual={list(interface_package.exclude_paths)!r}"
        )
    if interface_package.force_fresh_scan != spec.manifest_spec.build.force_fresh_scan:
        raise RuntimeError(
            "Interface package materialization resolved InterfacePackage with unexpected force_fresh_scan: "
            + f"expected={spec.manifest_spec.build.force_fresh_scan} actual={interface_package.force_fresh_scan}"
        )
    if interface_package.compilation_mode != str(
        _enum_value(spec.manifest_spec.build.compilation_mode)
    ):
        raise RuntimeError(
            "Interface package materialization resolved InterfacePackage with unexpected compilation_mode: "
            + f"expected={_enum_value(spec.manifest_spec.build.compilation_mode)!r} "
            + f"actual={interface_package.compilation_mode!r}"
        )
    if list(interface_package.dependencies) != list(
        _interface_package_dependencies_payload(spec.manifest_spec)
    ):
        raise RuntimeError(
            "Interface package materialization resolved InterfacePackage with unexpected dependencies: "
            + f"expected={list(_interface_package_dependencies_payload(spec.manifest_spec))!r} "
            + f"actual={list(interface_package.dependencies)!r}"
        )
    if dict(interface_package.dart) != dict(
        _interface_package_dart_payload(spec.manifest_spec)
    ):
        raise RuntimeError(
            "Interface package materialization resolved InterfacePackage with unexpected dart payload: "
            + f"expected={dict(_interface_package_dart_payload(spec.manifest_spec))!r} "
            + f"actual={dict(interface_package.dart)!r}"
        )


async def _hydrate_lane_root_from_head(
    *,
    index: MetaGraphRuntimeIndexSnapshot,
    branch_id: UUID,
    projection_hash: str,
    root_id: UUID,
    root_type: type[_TRoot],
) -> _TRoot | None:
    head = await FSCommitStore().head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    if head is None or head.get("commit_id") is None:
        return None

    return await reify_meta_orm_root_from_oig_commit(
        index=index,
        branch_id=branch_id,
        projection_hash=projection_hash,
        projection_name=getattr(root_type, "__name__", ""),
        commit_id=UUID(str(head["commit_id"])),
        root_id=root_id,
        root_type=root_type,
        commit_store=FSCommitStore(),
        snapshot_store=FSSnapshotStore(),
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
    if head is None or head.get("commit_id") is None:
        return None
    return UUID(str(head["commit_id"]))


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


__all__ = [
    "InterfacePackageMaterializationResult",
    "InterfacePackageMaterializationSpec",
    "materialize_interface_package_from_manifest",
    "resolve_interface_package_materialization_spec",
]
