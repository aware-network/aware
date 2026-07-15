from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TypeVar
from uuid import NAMESPACE_URL, UUID, uuid5

from aware_code.types import JsonArray, JsonObject
from aware_interface_ontology.interface.app_config import AppConfig
from aware_interface_ontology.interface.app_config_screen_config import (
    AppConfigScreenConfig,
)
from aware_interface_ontology.interface.app_package import AppPackage
from aware_interface_ontology.interface.app_package_experience_package import (
    AppPackageExperiencePackage,
)
from aware_interface_ontology.interface.app_package_interface_package import (
    AppPackageInterfacePackage,
)
from aware_interface_ontology.interface.interface_config import InterfaceConfig
from aware_interface_ontology.interface.interface_config_pane_config import (
    InterfaceConfigPaneConfig,
)
from aware_interface_ontology.interface.interface_config_pane_config_section_config import (
    InterfaceConfigPaneConfigSectionConfig,
)
from aware_interface_ontology.interface.interface_config_window_config import (
    InterfaceConfigWindowConfig,
)
from aware_interface_ontology.interface.interface_package import InterfacePackage
from aware_interface_ontology.interface.interface_package_experience_package import (
    InterfacePackageExperiencePackage,
)
from aware_interface_ontology.interface.pane_config import PaneConfig
from aware_interface_ontology.interface.window_config import WindowConfig
from aware_interface_ontology.interface.window_config_layout_config import (
    WindowConfigLayoutConfig,
)
from aware_interface_ontology.stable_ids import (
    stable_app_config_id,
    stable_app_config_screen_config_id,
    stable_app_package_experience_package_id,
    stable_app_package_id,
    stable_app_package_interface_package_id,
    stable_interface_config_pane_config_id,
    stable_interface_package_experience_package_id,
    stable_interface_package_id,
)
from aware_interface_ontology.render.pane_render_spec import PaneRenderSpec
from aware_interface_service_dto.comms.models.interface_config_bundle import (
    InterfaceConfigBundle,
)
from aware_meta.graph.instance.builder import build_rooted_object_instance_graph_base
from aware_meta.graph.instance.commit.builder import (
    build_object_instance_graph_commit_from_changes,
)
from aware_meta.graph.instance.commit.committer import FSLaneCommitter
from aware_meta.graph.instance.commit.contract import CommitActionDescriptor
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.fs_snapshot_store import FSSnapshotStore
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
from aware_meta.graph.instance.diff_orm import (
    build_object_instance_graph_changes_from_orm_change_set,
)
from aware_meta.graph.instance.root import resolve_root_source_object_id
from aware_meta_ontology.stable_ids import (
    stable_object_instance_graph_commit_id,
    stable_object_instance_graph_id,
    stable_object_instance_graph_identity_id,
)
from aware_meta.runtime.author import resolve_meta_author_id
from aware_meta.runtime.graph_identity import resolve_meta_graph_ocgi_opgi
from aware_meta.runtime.handler_executor import MetaGraphRuntimeIndex
from aware_meta.runtime.oig_post import materialize_meta_oig_post
from aware_meta.runtime.value_resolvers import default_meta_enum_option_resolver
from aware_orm.models.base_model import BaseORMModel
from aware_orm.session.change_collector import ORMChangeSet

_TModel = TypeVar("_TModel", bound=BaseORMModel)


@dataclass(frozen=True, slots=True)
class InterfaceConfigSnapshotCommitResult:
    interface_config: InterfaceConfig
    window_configs: tuple[WindowConfig, ...]
    pane_configs: tuple[PaneConfig, ...]
    interface_config_window_configs: tuple[InterfaceConfigWindowConfig, ...]
    window_config_layout_configs: tuple[WindowConfigLayoutConfig, ...]
    interface_config_pane_configs: tuple[InterfaceConfigPaneConfig, ...]
    projection_experience_view_bindings: tuple[PaneConfig, ...]
    section_mounts: tuple[InterfaceConfigPaneConfigSectionConfig, ...]
    commit_id: UUID
    head_commit_id: UUID
    object_instance_graph_commit_id: UUID
    object_count: int
    change_count: int


@dataclass(frozen=True, slots=True)
class InterfacePackageExperiencePackageSnapshotRef:
    experience_package_id: UUID
    description: str | None = None


@dataclass(frozen=True, slots=True)
class InterfacePackageManifestSnapshotCommitResult:
    interface_package: InterfacePackage
    experience_packages: tuple[InterfacePackageExperiencePackage, ...]
    commit_id: UUID
    head_commit_id: UUID
    object_instance_graph_commit_id: UUID
    object_count: int
    change_count: int


@dataclass(frozen=True, slots=True)
class PaneRenderSpecSnapshotCommitResult:
    pane_render_spec: PaneRenderSpec
    commit_id: UUID
    head_commit_id: UUID
    object_instance_graph_commit_id: UUID
    object_count: int
    change_count: int


@dataclass(frozen=True, slots=True)
class AppConfigScreenSnapshotRef:
    screen_key: str
    projection_experience_id: UUID
    projection_experience_layout_graph_binding_id: UUID


@dataclass(frozen=True, slots=True)
class AppConfigSnapshotCommitResult:
    app_config: AppConfig
    screen_configs: tuple[AppConfigScreenConfig, ...]
    commit_id: UUID
    head_commit_id: UUID
    object_instance_graph_commit_id: UUID
    object_count: int
    change_count: int


@dataclass(frozen=True, slots=True)
class AppPackageExperiencePackageSnapshotRef:
    experience_package_id: UUID
    experience_package_object_instance_graph_commit_id: UUID
    role: str = "experience"
    description: str | None = None


@dataclass(frozen=True, slots=True)
class AppPackageInterfacePackageSnapshotRef:
    interface_package_id: UUID
    interface_package_object_instance_graph_commit_id: UUID | None = None
    role: str = "interface"
    description: str | None = None


@dataclass(frozen=True, slots=True)
class AppPackageManifestSnapshotCommitResult:
    app_package: AppPackage
    experience_packages: tuple[AppPackageExperiencePackage, ...]
    interface_packages: tuple[AppPackageInterfacePackage, ...]
    commit_id: UUID
    head_commit_id: UUID
    object_instance_graph_commit_id: UUID
    object_count: int
    change_count: int


@dataclass(frozen=True, slots=True)
class _SnapshotCommit:
    commit_id: UUID
    head_commit_id: UUID
    object_instance_graph_commit_id: UUID
    object_count: int
    change_count: int


@dataclass(frozen=True, slots=True)
class _SchemaReplacementHead:
    commit_id: UUID
    graph_hash_post: str


@dataclass(frozen=True, slots=True)
class _InterfaceConfigSnapshotObjects:
    interface_config: InterfaceConfig
    window_configs: tuple[WindowConfig, ...]
    pane_configs: tuple[PaneConfig, ...]
    interface_config_window_configs: tuple[InterfaceConfigWindowConfig, ...]
    window_config_layout_configs: tuple[WindowConfigLayoutConfig, ...]
    interface_config_pane_configs: tuple[InterfaceConfigPaneConfig, ...]
    projection_experience_view_bindings: tuple[PaneConfig, ...]
    section_mounts: tuple[InterfaceConfigPaneConfigSectionConfig, ...]
    window_objects_by_id: Mapping[UUID, BaseORMModel]
    pane_objects_by_id: Mapping[UUID, BaseORMModel]
    interface_config_objects_by_id: Mapping[UUID, BaseORMModel]


_INTERFACE_CONFIG_SNAPSHOT_COMMIT_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware://interface/config/snapshot-commit/v1",
)
_WINDOW_CONFIG_SNAPSHOT_COMMIT_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware://interface/window-config/snapshot-commit/v1",
)
_PANE_CONFIG_SNAPSHOT_COMMIT_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware://interface/pane-config/snapshot-commit/v1",
)
_INTERFACE_PACKAGE_MANIFEST_SNAPSHOT_COMMIT_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware://interface/package/manifest-snapshot-commit/v1",
)
_PANE_RENDER_SPEC_SNAPSHOT_COMMIT_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware://interface/pane-render-spec/snapshot-commit/v1",
)
_APP_CONFIG_SNAPSHOT_COMMIT_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware://interface/app-config/snapshot-commit/v1",
)
_APP_PACKAGE_MANIFEST_SNAPSHOT_COMMIT_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware://interface/app-package/manifest-snapshot-commit/v1",
)


async def commit_app_config_snapshot(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    branch_id: UUID,
    projection_hash: str,
    name: str,
    title: str | None,
    description: str | None,
    screen_refs: Sequence[AppConfigScreenSnapshotRef],
) -> AppConfigSnapshotCommitResult:
    app_config, objects_by_id, screen_configs = _build_app_config_snapshot_objects(
        name=name,
        title=title,
        description=description,
        screen_refs=screen_refs,
    )
    snapshot_commit = await _commit_snapshot(
        index=index,
        actor_id=actor_id,
        branch_id=branch_id,
        projection_hash=projection_hash,
        root_object_id=app_config.id,
        root_object=app_config,
        objects_by_id=objects_by_id,
        operation_label="AppConfig.materialize_snapshot",
        commit_id_namespace=_APP_CONFIG_SNAPSHOT_COMMIT_NAMESPACE,
    )
    return AppConfigSnapshotCommitResult(
        app_config=app_config,
        screen_configs=screen_configs,
        commit_id=snapshot_commit.commit_id,
        head_commit_id=snapshot_commit.head_commit_id,
        object_instance_graph_commit_id=(snapshot_commit.object_instance_graph_commit_id),
        object_count=snapshot_commit.object_count,
        change_count=snapshot_commit.change_count,
    )


async def commit_app_package_manifest_snapshot(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    branch_id: UUID,
    projection_hash: str,
    name: str,
    app_config_id: UUID,
    app_config_object_instance_graph_commit_id: UUID,
    source_code_package_id: UUID | None,
    version_number: int,
    title: str | None,
    description: str | None,
    aware_app_version: int,
    manifest_relative_path: str | None,
    package_root: str,
    dependencies: JsonArray,
    dart: JsonObject,
    metadata_json: JsonObject,
    experience_package_refs: Sequence[AppPackageExperiencePackageSnapshotRef],
    interface_package_refs: Sequence[AppPackageInterfacePackageSnapshotRef],
) -> AppPackageManifestSnapshotCommitResult:
    (
        app_package,
        objects_by_id,
        experience_packages,
        interface_packages,
    ) = _build_app_package_manifest_snapshot_objects(
        name=name,
        app_config_id=app_config_id,
        app_config_object_instance_graph_commit_id=(app_config_object_instance_graph_commit_id),
        source_code_package_id=source_code_package_id,
        version_number=version_number,
        title=title,
        description=description,
        aware_app_version=aware_app_version,
        manifest_relative_path=manifest_relative_path,
        package_root=package_root,
        dependencies=dependencies,
        dart=dart,
        metadata_json=metadata_json,
        experience_package_refs=experience_package_refs,
        interface_package_refs=interface_package_refs,
    )
    snapshot_commit = await _commit_snapshot(
        index=index,
        actor_id=actor_id,
        branch_id=branch_id,
        projection_hash=projection_hash,
        root_object_id=app_package.id,
        root_object=app_package,
        objects_by_id=objects_by_id,
        operation_label="AppPackage.materialize_manifest_snapshot",
        commit_id_namespace=_APP_PACKAGE_MANIFEST_SNAPSHOT_COMMIT_NAMESPACE,
    )
    return AppPackageManifestSnapshotCommitResult(
        app_package=app_package,
        experience_packages=experience_packages,
        interface_packages=interface_packages,
        commit_id=snapshot_commit.commit_id,
        head_commit_id=snapshot_commit.head_commit_id,
        object_instance_graph_commit_id=(snapshot_commit.object_instance_graph_commit_id),
        object_count=snapshot_commit.object_count,
        change_count=snapshot_commit.change_count,
    )


async def commit_interface_config_snapshot(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    branch_id: UUID,
    interface_config_projection_hash: str,
    window_config_projection_hash: str,
    pane_config_projection_hash: str,
    bundle: InterfaceConfigBundle,
) -> InterfaceConfigSnapshotCommitResult:
    snapshot = _build_interface_config_snapshot_objects(bundle=bundle)

    if snapshot.window_configs:
        await _commit_snapshot(
            index=index,
            actor_id=actor_id,
            branch_id=branch_id,
            projection_hash=window_config_projection_hash,
            root_object_id=snapshot.window_configs[0].id,
            root_object=snapshot.window_configs[0],
            objects_by_id=snapshot.window_objects_by_id,
            operation_label="WindowConfig.materialize_snapshot",
            commit_id_namespace=_WINDOW_CONFIG_SNAPSHOT_COMMIT_NAMESPACE,
        )
    if snapshot.pane_configs:
        await _commit_snapshot(
            index=index,
            actor_id=actor_id,
            branch_id=branch_id,
            projection_hash=pane_config_projection_hash,
            root_object_id=snapshot.pane_configs[0].id,
            root_object=snapshot.pane_configs[0],
            objects_by_id=snapshot.pane_objects_by_id,
            operation_label="PaneConfig.materialize_snapshot",
            commit_id_namespace=_PANE_CONFIG_SNAPSHOT_COMMIT_NAMESPACE,
        )

    interface_config_commit = await _commit_snapshot(
        index=index,
        actor_id=actor_id,
        branch_id=branch_id,
        projection_hash=interface_config_projection_hash,
        root_object_id=snapshot.interface_config.id,
        root_object=snapshot.interface_config,
        objects_by_id=snapshot.interface_config_objects_by_id,
        operation_label="InterfaceConfig.materialize_snapshot",
        commit_id_namespace=_INTERFACE_CONFIG_SNAPSHOT_COMMIT_NAMESPACE,
    )
    return InterfaceConfigSnapshotCommitResult(
        interface_config=snapshot.interface_config,
        window_configs=snapshot.window_configs,
        pane_configs=snapshot.pane_configs,
        interface_config_window_configs=snapshot.interface_config_window_configs,
        window_config_layout_configs=snapshot.window_config_layout_configs,
        interface_config_pane_configs=snapshot.interface_config_pane_configs,
        projection_experience_view_bindings=(snapshot.projection_experience_view_bindings),
        section_mounts=snapshot.section_mounts,
        commit_id=interface_config_commit.commit_id,
        head_commit_id=interface_config_commit.head_commit_id,
        object_instance_graph_commit_id=(interface_config_commit.object_instance_graph_commit_id),
        object_count=interface_config_commit.object_count,
        change_count=interface_config_commit.change_count,
    )


async def commit_interface_package_manifest_snapshot(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    branch_id: UUID,
    projection_hash: str,
    package_name: str,
    interface_config_id: UUID,
    interface_config_object_instance_graph_commit_id: UUID | None,
    source_code_package_id: UUID | None,
    fqn_prefix: str | None,
    version_number: int,
    title: str | None,
    description: str | None,
    aware_interface_version: int,
    manifest_relative_path: str | None,
    package_root: str,
    sources_root: str,
    config_bundle_path: str | None,
    include_paths: JsonArray,
    exclude_paths: JsonArray,
    force_fresh_scan: bool,
    compilation_mode: str,
    dependencies: JsonArray,
    dart: JsonObject,
    experience_package_refs: Sequence[InterfacePackageExperiencePackageSnapshotRef] = (),
) -> InterfacePackageManifestSnapshotCommitResult:
    interface_package, objects_by_id, experience_edges = _build_interface_package_manifest_snapshot_objects(
        package_name=package_name,
        interface_config_id=interface_config_id,
        interface_config_object_instance_graph_commit_id=(interface_config_object_instance_graph_commit_id),
        source_code_package_id=source_code_package_id,
        fqn_prefix=fqn_prefix,
        version_number=version_number,
        title=title,
        description=description,
        aware_interface_version=aware_interface_version,
        manifest_relative_path=manifest_relative_path,
        package_root=package_root,
        sources_root=sources_root,
        config_bundle_path=config_bundle_path,
        include_paths=include_paths,
        exclude_paths=exclude_paths,
        force_fresh_scan=force_fresh_scan,
        compilation_mode=compilation_mode,
        dependencies=dependencies,
        dart=dart,
        experience_package_refs=experience_package_refs,
    )
    snapshot_commit = await _commit_snapshot(
        index=index,
        actor_id=actor_id,
        branch_id=branch_id,
        projection_hash=projection_hash,
        root_object_id=interface_package.id,
        root_object=interface_package,
        objects_by_id=objects_by_id,
        operation_label="InterfacePackage.materialize_manifest_snapshot",
        commit_id_namespace=_INTERFACE_PACKAGE_MANIFEST_SNAPSHOT_COMMIT_NAMESPACE,
    )
    return InterfacePackageManifestSnapshotCommitResult(
        interface_package=interface_package,
        experience_packages=experience_edges,
        commit_id=snapshot_commit.commit_id,
        head_commit_id=snapshot_commit.head_commit_id,
        object_instance_graph_commit_id=snapshot_commit.object_instance_graph_commit_id,
        object_count=snapshot_commit.object_count,
        change_count=snapshot_commit.change_count,
    )


async def commit_pane_render_spec_snapshot(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    branch_id: UUID,
    projection_hash: str,
    pane_render_spec: PaneRenderSpec,
    objects_by_id: Mapping[UUID, BaseORMModel],
) -> PaneRenderSpecSnapshotCommitResult:
    snapshot_commit = await _commit_snapshot(
        index=index,
        actor_id=actor_id,
        branch_id=branch_id,
        projection_hash=projection_hash,
        root_object_id=pane_render_spec.id,
        root_object=pane_render_spec,
        objects_by_id=objects_by_id,
        operation_label="PaneRenderSpec.materialize_snapshot",
        commit_id_namespace=_PANE_RENDER_SPEC_SNAPSHOT_COMMIT_NAMESPACE,
    )
    return PaneRenderSpecSnapshotCommitResult(
        pane_render_spec=pane_render_spec,
        commit_id=snapshot_commit.commit_id,
        head_commit_id=snapshot_commit.head_commit_id,
        object_instance_graph_commit_id=snapshot_commit.object_instance_graph_commit_id,
        object_count=snapshot_commit.object_count,
        change_count=snapshot_commit.change_count,
    )


def _build_app_config_snapshot_objects(
    *,
    name: str,
    title: str | None,
    description: str | None,
    screen_refs: Sequence[AppConfigScreenSnapshotRef],
) -> tuple[
    AppConfig,
    dict[UUID, BaseORMModel],
    tuple[AppConfigScreenConfig, ...],
]:
    objects_by_id: dict[UUID, BaseORMModel] = {}
    normalized_name = (name or "").strip()
    if not normalized_name:
        raise RuntimeError("AppConfig snapshot requires non-empty name")
    app_config = _remember(
        objects_by_id,
        AppConfig(
            id=stable_app_config_id(name=normalized_name),
            screen_configs=[],
            name=normalized_name,
            title=_text_or_none(title),
            description=_text_or_none(description),
        ),
    )
    screen_configs: list[AppConfigScreenConfig] = []
    seen_screen_keys: set[str] = set()
    for screen_ref in sorted(
        screen_refs,
        key=lambda item: item.screen_key.strip().casefold(),
    ):
        screen_key = (screen_ref.screen_key or "").strip()
        normalized_screen_key = screen_key.casefold()
        if not screen_key:
            raise RuntimeError("AppConfig screen snapshot requires screen_key")
        if normalized_screen_key in seen_screen_keys:
            raise RuntimeError("AppConfig screen snapshot contains duplicate screen_key: " f"{screen_key!r}")
        seen_screen_keys.add(normalized_screen_key)
        screen_config = _remember(
            objects_by_id,
            AppConfigScreenConfig(
                id=stable_app_config_screen_config_id(
                    app_config_id=app_config.id,
                    projection_experience_id=(screen_ref.projection_experience_id),
                    projection_experience_layout_graph_binding_id=(
                        screen_ref.projection_experience_layout_graph_binding_id
                    ),
                    screen_key=screen_key,
                ),
                app_config_id=app_config.id,
                projection_experience_id=screen_ref.projection_experience_id,
                projection_experience_layout_graph_binding_id=(
                    screen_ref.projection_experience_layout_graph_binding_id
                ),
                screen_key=screen_key,
            ),
        )
        app_config.screen_configs.append(screen_config)
        screen_configs.append(screen_config)
    if not screen_configs:
        raise RuntimeError("AppConfig snapshot requires at least one screen")
    return app_config, objects_by_id, tuple(screen_configs)


def _build_app_package_manifest_snapshot_objects(
    *,
    name: str,
    app_config_id: UUID,
    app_config_object_instance_graph_commit_id: UUID,
    source_code_package_id: UUID | None,
    version_number: int,
    title: str | None,
    description: str | None,
    aware_app_version: int,
    manifest_relative_path: str | None,
    package_root: str,
    dependencies: JsonArray,
    dart: JsonObject,
    metadata_json: JsonObject,
    experience_package_refs: Sequence[AppPackageExperiencePackageSnapshotRef],
    interface_package_refs: Sequence[AppPackageInterfacePackageSnapshotRef],
) -> tuple[
    AppPackage,
    dict[UUID, BaseORMModel],
    tuple[AppPackageExperiencePackage, ...],
    tuple[AppPackageInterfacePackage, ...],
]:
    objects_by_id: dict[UUID, BaseORMModel] = {}
    normalized_name = (name or "").strip()
    if not normalized_name:
        raise RuntimeError("AppPackage snapshot requires non-empty name")
    app_package = _remember(
        objects_by_id,
        AppPackage(
            id=stable_app_package_id(name=normalized_name),
            source_code_package_id=source_code_package_id,
            app_config_id=app_config_id,
            app_config_object_instance_graph_commit_id=(app_config_object_instance_graph_commit_id),
            experience_packages=[],
            interface_packages=[],
            aware_app_version=aware_app_version,
            dart=JsonObject(dart or {}),
            dependencies=JsonArray(dependencies or []),
            description=_text_or_none(description),
            manifest_relative_path=_text_or_none(manifest_relative_path),
            metadata_json=JsonObject(metadata_json or {}),
            name=normalized_name,
            package_root=(package_root or "").strip() or ".",
            title=_text_or_none(title),
            version_number=version_number,
        ),
    )
    experience_packages: list[AppPackageExperiencePackage] = []
    for package_ref in sorted(
        experience_package_refs,
        key=lambda item: str(item.experience_package_id),
    ):
        edge = _remember(
            objects_by_id,
            AppPackageExperiencePackage(
                id=stable_app_package_experience_package_id(
                    app_package_id=app_package.id,
                    experience_package_id=package_ref.experience_package_id,
                ),
                app_package_id=app_package.id,
                experience_package_id=package_ref.experience_package_id,
                experience_package_object_instance_graph_commit_id=(
                    package_ref.experience_package_object_instance_graph_commit_id
                ),
                role=(package_ref.role or "").strip() or "experience",
                description=_text_or_none(package_ref.description),
            ),
        )
        app_package.experience_packages.append(edge)
        experience_packages.append(edge)
    interface_packages: list[AppPackageInterfacePackage] = []
    for package_ref in sorted(
        interface_package_refs,
        key=lambda item: str(item.interface_package_id),
    ):
        edge = _remember(
            objects_by_id,
            AppPackageInterfacePackage(
                id=stable_app_package_interface_package_id(
                    app_package_id=app_package.id,
                    interface_package_id=package_ref.interface_package_id,
                ),
                app_package_id=app_package.id,
                interface_package_id=package_ref.interface_package_id,
                interface_package_object_instance_graph_commit_id=(
                    package_ref.interface_package_object_instance_graph_commit_id
                ),
                role=(package_ref.role or "").strip() or "interface",
                description=_text_or_none(package_ref.description),
            ),
        )
        app_package.interface_packages.append(edge)
        interface_packages.append(edge)
    return (
        app_package,
        objects_by_id,
        tuple(experience_packages),
        tuple(interface_packages),
    )


def _build_interface_config_snapshot_objects(
    *,
    bundle: InterfaceConfigBundle,
) -> _InterfaceConfigSnapshotObjects:
    objects_by_id: dict[UUID, BaseORMModel] = {}
    interface_config_window_configs: list[InterfaceConfigWindowConfig] = []
    window_config_layout_configs: list[WindowConfigLayoutConfig] = []
    interface_config_pane_configs: list[InterfaceConfigPaneConfig] = []
    projection_bindings: list[PaneConfig] = []
    section_mounts: list[InterfaceConfigPaneConfigSectionConfig] = []
    window_objects_by_id: dict[UUID, BaseORMModel] = {}
    pane_objects_by_id: dict[UUID, BaseORMModel] = {}

    interface_config = _remember(
        objects_by_id,
        InterfaceConfig(
            id=bundle.interface_config_id,
            interfaces=[],
            interface_config_window_configs=[],
            interface_config_pane_configs=[],
            name=(bundle.name or "").strip(),
            description=_text_or_none(bundle.description),
        ),
    )

    window_configs: list[WindowConfig] = []
    for window_bundle in bundle.window_configs:
        window_config = _remember(
            window_objects_by_id,
            WindowConfig(
                id=window_bundle.window_config_id,
                layout_configs=[],
                key=(window_bundle.key or "").strip(),
                description=_text_or_none(window_bundle.description),
            ),
        )
        window_configs.append(window_config)
        for layout_bundle in window_bundle.layout_configs:
            layout_edge = _remember(
                window_objects_by_id,
                WindowConfigLayoutConfig(
                    id=layout_bundle.window_config_layout_config_id,
                    window_config_id=window_config.id,
                    layout_config_id=layout_bundle.layout_config_id,
                    description=None,
                    is_default=layout_bundle.is_default,
                ),
            )
            window_config.layout_configs.append(layout_edge)
            window_config_layout_configs.append(layout_edge)

        config_window_edge = _remember(
            objects_by_id,
            InterfaceConfigWindowConfig(
                id=window_bundle.interface_config_window_config_id,
                interface_config_id=interface_config.id,
                window_config_id=window_config.id,
            ),
        )
        interface_config.interface_config_window_configs.append(config_window_edge)
        interface_config_window_configs.append(config_window_edge)

    pane_configs: list[PaneConfig] = []
    for pane_bundle in bundle.pane_configs:
        if len(pane_bundle.projection_experience_views) != 1:
            raise ValueError(
                "Interface PaneConfig snapshot commit requires exactly one "
                "ProjectionExperienceView per pane; "
                f"pane={pane_bundle.name!r} got {len(pane_bundle.projection_experience_views)}"
            )
        view_bundle = pane_bundle.projection_experience_views[0]
        pane_config = _remember(
            pane_objects_by_id,
            PaneConfig(
                id=pane_bundle.pane_config_id,
                projection_experience_view_id=view_bundle.projection_experience_view_id,
                name=(pane_bundle.name or "").strip(),
                pane_kind=(pane_bundle.pane_kind or "").strip(),
                view_ref=_text_or_none(view_bundle.view_ref),
                description=_text_or_none(pane_bundle.description),
            ),
        )
        pane_configs.append(pane_config)
        projection_bindings.append(pane_config)

        config_pane_edge = _remember(
            objects_by_id,
            InterfaceConfigPaneConfig(
                id=stable_interface_config_pane_config_id(
                    interface_config_id=interface_config.id,
                    pane_config_id=pane_config.id,
                ),
                interface_config_id=interface_config.id,
                pane_config_id=pane_config.id,
                section_mounts=[],
                narrative_key=_text_or_none(pane_bundle.narrative_key),
            ),
        )
        interface_config.interface_config_pane_configs.append(config_pane_edge)
        interface_config_pane_configs.append(config_pane_edge)
        for view_bundle in pane_bundle.projection_experience_views:
            if view_bundle.binding_id != pane_config.id:
                raise RuntimeError(
                    "Interface snapshot pane-view binding must match PaneConfig identity: "
                    f"binding_id={view_bundle.binding_id}"
                )
            for mount_bundle in view_bundle.section_mounts:
                mount_edge = _remember(
                    objects_by_id,
                    InterfaceConfigPaneConfigSectionConfig(
                        id=mount_bundle.mount_id,
                        interface_config_pane_config_id=config_pane_edge.id,
                        pane_config_id=pane_config.id,
                        layout_config_section_config_id=(mount_bundle.layout_config_section_config_id),
                    ),
                )
                config_pane_edge.section_mounts.append(mount_edge)
                section_mounts.append(mount_edge)

    return _InterfaceConfigSnapshotObjects(
        interface_config=interface_config,
        window_configs=tuple(window_configs),
        pane_configs=tuple(pane_configs),
        interface_config_window_configs=tuple(interface_config_window_configs),
        window_config_layout_configs=tuple(window_config_layout_configs),
        interface_config_pane_configs=tuple(interface_config_pane_configs),
        projection_experience_view_bindings=tuple(projection_bindings),
        section_mounts=tuple(section_mounts),
        window_objects_by_id=window_objects_by_id,
        pane_objects_by_id=pane_objects_by_id,
        interface_config_objects_by_id=objects_by_id,
    )


def _build_interface_package_manifest_snapshot_objects(
    *,
    package_name: str,
    interface_config_id: UUID,
    interface_config_object_instance_graph_commit_id: UUID | None,
    source_code_package_id: UUID | None,
    fqn_prefix: str | None,
    version_number: int,
    title: str | None,
    description: str | None,
    aware_interface_version: int,
    manifest_relative_path: str | None,
    package_root: str,
    sources_root: str,
    config_bundle_path: str | None,
    include_paths: JsonArray,
    exclude_paths: JsonArray,
    force_fresh_scan: bool,
    compilation_mode: str,
    dependencies: JsonArray,
    dart: JsonObject,
    experience_package_refs: Sequence[InterfacePackageExperiencePackageSnapshotRef],
) -> tuple[
    InterfacePackage,
    dict[UUID, BaseORMModel],
    tuple[InterfacePackageExperiencePackage, ...],
]:
    objects_by_id: dict[UUID, BaseORMModel] = {}
    normalized_name = (package_name or "").strip()
    if not normalized_name:
        raise RuntimeError("InterfacePackage snapshot requires non-empty package_name")
    interface_package = _remember(
        objects_by_id,
        InterfacePackage(
            id=bundle_interface_package_id(normalized_name),
            name=normalized_name,
            experience_packages=[],
            pane_packages=[],
            render_component_packages=[],
            interface_config_id=interface_config_id,
            interface_config_object_instance_graph_commit_id=(interface_config_object_instance_graph_commit_id),
            source_code_package_id=source_code_package_id,
            fqn_prefix=_text_or_none(fqn_prefix),
            version_number=version_number,
            title=_text_or_none(title),
            description=_text_or_none(description),
            aware_interface_version=aware_interface_version,
            manifest_relative_path=_text_or_none(manifest_relative_path),
            package_root=(package_root or "").strip() or ".",
            sources_root=(sources_root or "").strip() or ".",
            config_bundle_path=_text_or_none(config_bundle_path),
            include_paths=JsonArray(include_paths or []),
            exclude_paths=JsonArray(exclude_paths or []),
            force_fresh_scan=force_fresh_scan,
            compilation_mode=(compilation_mode or "").strip() or "raw_xor",
            dependencies=JsonArray(dependencies or []),
            dart=JsonObject(dart or {}),
        ),
    )
    experience_edges: list[InterfacePackageExperiencePackage] = []
    for experience_ref in sorted(
        experience_package_refs,
        key=lambda item: str(item.experience_package_id),
    ):
        edge = _remember(
            objects_by_id,
            InterfacePackageExperiencePackage(
                id=stable_interface_package_experience_package_id(
                    interface_package_id=interface_package.id,
                    experience_package_id=experience_ref.experience_package_id,
                ),
                interface_package_id=interface_package.id,
                experience_package_id=experience_ref.experience_package_id,
                description=_text_or_none(experience_ref.description),
            ),
        )
        interface_package.experience_packages.append(edge)
        experience_edges.append(edge)
    return interface_package, objects_by_id, tuple(experience_edges)


def bundle_interface_package_id(package_name: str) -> UUID:
    return stable_interface_package_id(name=package_name)


async def _commit_snapshot(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    branch_id: UUID,
    projection_hash: str,
    root_object_id: UUID,
    root_object: BaseORMModel,
    objects_by_id: Mapping[UUID, BaseORMModel],
    operation_label: str,
    commit_id_namespace: UUID,
) -> _SnapshotCommit:
    opg = index.opg_by_hash.get(projection_hash)
    if opg is None:
        raise RuntimeError("Interface snapshot commit missing projection hash: " f"{projection_hash}")
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
            "Interface snapshot commit missing ObjectProjectionGraphIdentity: " f"projection_hash={projection_hash}"
        )
    oigi_id = stable_object_instance_graph_identity_id(
        object_projection_graph_identity_id=opgi.id,
        object_instance_graph_id=domain_oig_id,
    )
    schema_replacement_head: _SchemaReplacementHead | None = None
    try:
        before_oig = await _load_before_oig(
            index=index,
            branch_id=branch_id,
            projection_hash=projection_hash,
            domain_oig_id=domain_oig_id,
            root_object_id=root_object_id,
        )
    except Exception as exc:
        schema_replacement_head = await _schema_replacement_head_for_error(
            branch_id=branch_id,
            projection_hash=projection_hash,
            exc=exc,
        )
        if schema_replacement_head is None:
            raise
        before_oig = build_rooted_object_instance_graph_base(
            key=str(branch_id),
            name=f"OIG_{branch_id.hex[:8]}",
            description="ROOTED_BASE",
            object_config_graph=index.ocg,
            object_projection_graph=opg,
            root_source_object_id=root_object_id,
            oig_id=domain_oig_id,
        )
    lane_root_object_id = resolve_root_source_object_id(before_oig)
    object_ids = frozenset(objects_by_id)
    change_set = ORMChangeSet(
        collected_at=datetime.now(UTC),
        created_ids=object_ids,
        touched_ids=object_ids,
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
        head = await FSCommitStore().head(
            branch_id=branch_id,
            projection_hash=projection_hash,
        )
        raw_head_commit_id = None if head is None else head.get("commit_id")
        if raw_head_commit_id is None:
            raise RuntimeError(
                "Interface snapshot commit produced no OIG changes and no "
                f"existing lane head: operation_label={operation_label!r}"
            )
        head_commit_id = raw_head_commit_id if isinstance(raw_head_commit_id, UUID) else UUID(str(raw_head_commit_id))
        return _SnapshotCommit(
            commit_id=head_commit_id,
            head_commit_id=head_commit_id,
            object_instance_graph_commit_id=stable_object_instance_graph_commit_id(
                object_instance_graph_identity_id=oigi_id,
                commit_id=head_commit_id,
            ),
            object_count=len(objects_by_id),
            change_count=0,
        )
    after_oig = materialize_meta_oig_post(
        before_oig=before_oig,
        changes=changes,
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )
    if schema_replacement_head is not None:
        return await _commit_schema_replacement_snapshot(
            branch_id=branch_id,
            projection_hash=projection_hash,
            object_projection_graph_identity_id=opgi.id,
            object_instance_graph_identity_id=oigi_id,
            object_instance_graph_id=domain_oig_id,
            before_oig=before_oig,
            after_oig=after_oig,
            changes=changes,
            graph_hash_pre=schema_replacement_head.graph_hash_post,
            parent_commit_id=schema_replacement_head.commit_id,
            author_id=resolve_meta_author_id(actor_id),
            root_object=root_object,
            lane_root_object_id=lane_root_object_id,
            operation_label=operation_label,
            commit_id_namespace=commit_id_namespace,
            object_count=len(objects_by_id),
        )
    commit_id = _snapshot_commit_id(
        namespace=commit_id_namespace,
        branch_id=branch_id,
        projection_hash=projection_hash,
        root_object_id=root_object_id,
        graph_hash_post=after_oig.hash,
    )
    commit = await FSLaneCommitter().commit(
        branch_id=branch_id,
        projection_hash=projection_hash,
        object_instance_graph_identity_id=oigi_id,
        object_instance_graph_id=domain_oig_id,
        before_oig=before_oig,
        root_object_id=lane_root_object_id,
        changes=changes,
        graph_hash_pre=before_oig.hash,
        graph_hash_post=after_oig.hash,
        author_id=resolve_meta_author_id(actor_id),
        commit_id=commit_id,
        commit_action=CommitActionDescriptor(
            operation_label=operation_label,
            call_target="generated_materialization",
            object_id=root_object.id,
        ),
    )
    if commit is None or commit.commit is None:
        raise RuntimeError(
            "Interface snapshot commit did not append a lane commit: "
            f"operation_label={operation_label!r} root_object_id={root_object_id}"
        )
    return _SnapshotCommit(
        commit_id=commit.commit.id,
        head_commit_id=commit.commit.id,
        object_instance_graph_commit_id=stable_object_instance_graph_commit_id(
            object_instance_graph_identity_id=commit.object_instance_graph_identity_id,
            commit_id=commit.commit.id,
        ),
        object_count=len(objects_by_id),
        change_count=len(changes),
    )


async def _commit_schema_replacement_snapshot(
    *,
    branch_id: UUID,
    projection_hash: str,
    object_projection_graph_identity_id: UUID,
    object_instance_graph_identity_id: UUID,
    object_instance_graph_id: UUID,
    before_oig,
    after_oig,
    changes,
    graph_hash_pre: str,
    parent_commit_id: UUID,
    author_id: UUID,
    root_object: BaseORMModel,
    lane_root_object_id: UUID,
    operation_label: str,
    commit_id_namespace: UUID,
    object_count: int,
) -> _SnapshotCommit:
    commit_id = _schema_replacement_snapshot_commit_id(
        namespace=commit_id_namespace,
        branch_id=branch_id,
        projection_hash=projection_hash,
        root_object_id=root_object.id,
        parent_commit_id=parent_commit_id,
        graph_hash_post=after_oig.hash,
    )
    commit = build_object_instance_graph_commit_from_changes(
        before_oig=before_oig,
        changes=changes,
        branch_id=branch_id,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        object_instance_graph_id=object_instance_graph_id,
        projection_hash=projection_hash,
        graph_hash_pre=graph_hash_pre,
        graph_hash_post=after_oig.hash,
        author_id=author_id,
        parent_commit_id=parent_commit_id,
        commit_id=commit_id,
    )
    snapshot_store = FSSnapshotStore()
    await snapshot_store.put(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit.commit.id,
        oig=after_oig,
        indexes=OIGMaterializer().indexes_from_graph(after_oig),
    )
    await FSCommitStore().append(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit=commit,
        root_object_id=lane_root_object_id,
        commit_action=CommitActionDescriptor(
            operation_label=f"{operation_label}.schema_replacement",
            call_target="generated_materialization",
            object_id=root_object.id,
        ),
        object_projection_graph_identity_id=object_projection_graph_identity_id,
    )
    return _SnapshotCommit(
        commit_id=commit.commit.id,
        head_commit_id=commit.commit.id,
        object_instance_graph_commit_id=stable_object_instance_graph_commit_id(
            object_instance_graph_identity_id=commit.object_instance_graph_identity_id,
            commit_id=commit.commit.id,
        ),
        object_count=object_count,
        change_count=len(changes),
    )


async def _schema_replacement_head_for_error(
    *,
    branch_id: UUID,
    projection_hash: str,
    exc: Exception,
) -> _SchemaReplacementHead | None:
    if not _is_missing_attribute_config_replay_error(exc):
        return None
    head = await FSCommitStore().head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    if head is None:
        return None
    raw_commit_id = head.get("commit_id")
    graph_hash_post = str(head.get("graph_hash_post") or "")
    if raw_commit_id is None or not graph_hash_post:
        return None
    commit_id = raw_commit_id if isinstance(raw_commit_id, UUID) else UUID(str(raw_commit_id))
    return _SchemaReplacementHead(
        commit_id=commit_id,
        graph_hash_post=graph_hash_post,
    )


async def _load_before_oig(
    *,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    projection_hash: str,
    domain_oig_id: UUID,
    root_object_id: UUID,
):
    opg = index.opg_by_hash[projection_hash]
    head = await FSCommitStore().head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    if head is not None and head.get("commit_id") is not None:
        oig, _ = await OIGMaterializer().get(
            branch_id=branch_id,
            ocg=index.ocg,
            opg=opg,
            commit_id=None,
            attribute_configs_by_id=index.attribute_configs_by_id,
            class_configs_by_id=index.class_configs_by_id,
        )
        return oig
    return build_rooted_object_instance_graph_base(
        key=str(branch_id),
        name=f"OIG_{branch_id.hex[:8]}",
        description="ROOTED_BASE",
        object_config_graph=index.ocg,
        object_projection_graph=opg,
        root_source_object_id=root_object_id,
        oig_id=domain_oig_id,
    )


def _snapshot_commit_id(
    *,
    namespace: UUID,
    branch_id: UUID,
    projection_hash: str,
    root_object_id: UUID,
    graph_hash_post: str,
) -> UUID:
    return uuid5(
        namespace,
        f"{branch_id}:{projection_hash}:{root_object_id}:{graph_hash_post}",
    )


def _schema_replacement_snapshot_commit_id(
    *,
    namespace: UUID,
    branch_id: UUID,
    projection_hash: str,
    root_object_id: UUID,
    parent_commit_id: UUID,
    graph_hash_post: str,
) -> UUID:
    return uuid5(
        namespace,
        "schema-replacement:"
        f"{branch_id}:{projection_hash}:{root_object_id}:"
        f"{parent_commit_id}:{graph_hash_post}",
    )


def _is_missing_attribute_config_replay_error(exc: Exception) -> bool:
    message = str(exc)
    return (
        "Missing AttributeConfig for attribute_config_id=" in message
        and "class_instance_id=" in message
        and "class_config_id=" in message
        and "attribute_id=" in message
    )


def _text_or_none(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _remember(
    objects_by_id: dict[UUID, BaseORMModel],
    obj: _TModel,
) -> _TModel:
    obj_id = obj.id
    if obj_id in objects_by_id and objects_by_id[obj_id] is not obj:
        raise RuntimeError("Interface snapshot duplicate object id: " f"object_id={obj_id} class={type(obj).__name__}")
    objects_by_id[obj_id] = obj
    return obj


__all__ = [
    "AppConfigScreenSnapshotRef",
    "AppConfigSnapshotCommitResult",
    "AppPackageExperiencePackageSnapshotRef",
    "AppPackageInterfacePackageSnapshotRef",
    "AppPackageManifestSnapshotCommitResult",
    "InterfaceConfigSnapshotCommitResult",
    "InterfacePackageExperiencePackageSnapshotRef",
    "InterfacePackageManifestSnapshotCommitResult",
    "PaneRenderSpecSnapshotCommitResult",
    "commit_app_config_snapshot",
    "commit_app_package_manifest_snapshot",
    "commit_interface_config_snapshot",
    "commit_interface_package_manifest_snapshot",
    "commit_pane_render_spec_snapshot",
]
