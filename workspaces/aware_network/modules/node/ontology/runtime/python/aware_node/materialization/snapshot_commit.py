from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TypeVar
from uuid import NAMESPACE_URL, UUID, uuid5

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code.types import JsonArray
from aware_interface_ontology.stable_ids import stable_interface_config_id
from aware_meta.graph.instance.builder import build_rooted_object_instance_graph_base
from aware_meta.graph.instance.commit.committer import FSLaneCommitter
from aware_meta.graph.instance.commit.contract import CommitActionDescriptor
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
from aware_meta.graph.instance.diff_orm import (
    build_object_instance_graph_changes_from_orm_change_set,
)
from aware_meta.runtime.author import resolve_meta_author_id
from aware_meta.runtime.graph_identity import resolve_meta_graph_ocgi_opgi
from aware_meta.runtime.handler_executor.contracts import MetaGraphRuntimeIndex
from aware_meta.runtime.oig_post import materialize_meta_oig_post
from aware_meta.runtime.value_resolvers import default_meta_enum_option_resolver
from aware_meta_ontology.stable_ids import (
    stable_object_instance_graph_commit_id,
    stable_object_instance_graph_id,
    stable_object_instance_graph_identity_id,
)
from aware_node_ontology.node.node_config import NodeConfig
from aware_node_ontology.node.node_config_environment_profile_mount import (
    NodeConfigEnvironmentProfileMount,
)
from aware_node_ontology.node.node_config_environment_target import (
    NodeConfigEnvironmentTarget,
)
from aware_node_ontology.node.node_config_interface_target import (
    NodeConfigInterfaceTarget,
)
from aware_node_ontology.node.node_config_ontology_target import (
    NodeConfigOntologyTarget,
)
from aware_node_ontology.node.node_config_service_target import (
    NodeConfigServiceTarget,
)
from aware_node_ontology.node.node_config_service_code_package import (
    NodeConfigServiceCodePackage,
)
from aware_node_ontology.node.node_package import NodePackage
from aware_node_ontology.node.node_package_included_node_package import (
    NodePackageIncludedNodePackage,
)
from aware_node_ontology.stable_ids import (
    stable_node_config_environment_profile_mount_id,
    stable_node_config_environment_target_id,
    stable_node_config_id,
    stable_node_config_interface_target_id,
    stable_node_config_ontology_target_id,
    stable_node_config_service_code_package_id,
    stable_node_config_service_target_id,
    stable_node_package_id,
    stable_node_package_included_node_package_id,
)
from aware_environment_ontology.stable_ids import stable_environment_profile_package_id
from aware_orm.models.base_model import BaseORMModel
from aware_orm.session.change_collector import ORMChangeSet
from aware_service_ontology.stable_ids import stable_service_config_id
from aware_environment_ontology.stable_ids import stable_environment_config_id

from aware_node.ontology_package_identity import ontology_package_id_for_name

_TModel = TypeVar("_TModel", bound=BaseORMModel)


@dataclass(frozen=True, slots=True)
class NodeConfigEnvironmentProfileMountSnapshot:
    package_name: str
    profile_key: str
    mount_key: str
    mode: str = "mounted"
    position: int | None = None


@dataclass(frozen=True, slots=True)
class NodeConfigEnvironmentTargetSnapshot:
    environment_handle: str
    profile_mounts: tuple[NodeConfigEnvironmentProfileMountSnapshot, ...]


@dataclass(frozen=True, slots=True)
class NodeConfigServiceCodePackageSnapshot:
    slot_key: str
    package_name: str
    language: str = CodeLanguage.aware.value
    service_config_code_package_config_id: UUID | None = None
    code_package_id: UUID | None = None
    description: str | None = None


@dataclass(frozen=True, slots=True)
class NodeConfigServiceTargetSnapshot:
    service_name: str
    code_packages: tuple[NodeConfigServiceCodePackageSnapshot, ...] = ()


@dataclass(frozen=True, slots=True)
class NodePackageIncludedNodePackageSnapshot:
    included_package_name: str
    include_key: str | None = None
    description: str | None = None


@dataclass(frozen=True, slots=True)
class NodeConfigManifestSnapshotCommitResult:
    node_config: NodeConfig
    environment_targets: tuple[NodeConfigEnvironmentTarget, ...]
    ontology_targets: tuple[NodeConfigOntologyTarget, ...]
    service_targets: tuple[NodeConfigServiceTarget, ...]
    service_code_packages: tuple[NodeConfigServiceCodePackage, ...]
    interface_targets: tuple[NodeConfigInterfaceTarget, ...]
    commit_id: UUID
    head_commit_id: UUID
    object_instance_graph_commit_id: UUID
    object_count: int
    change_count: int


@dataclass(frozen=True, slots=True)
class NodePackageManifestSnapshotCommitResult:
    node_package: NodePackage
    included_node_packages: tuple[NodePackageIncludedNodePackage, ...]
    commit_id: UUID
    head_commit_id: UUID
    object_instance_graph_commit_id: UUID
    object_count: int
    change_count: int


_NODE_CONFIG_MANIFEST_SNAPSHOT_COMMIT_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware://node/config/manifest-snapshot-commit/v1",
)
_NODE_PACKAGE_MANIFEST_SNAPSHOT_COMMIT_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware://node/package/manifest-snapshot-commit/v1",
)


async def commit_node_config_manifest_snapshot(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    branch_id: UUID,
    projection_hash: str,
    name: str,
    description: str | None,
    environment_targets: Sequence[NodeConfigEnvironmentTargetSnapshot],
    ontology_package_names: Sequence[str],
    service_targets: Sequence[NodeConfigServiceTargetSnapshot],
    interface_names: Sequence[str],
) -> NodeConfigManifestSnapshotCommitResult:
    node_config, objects_by_id = _build_node_config_manifest_snapshot_objects(
        name=name,
        description=description,
        environment_targets=environment_targets,
        ontology_package_names=ontology_package_names,
        service_targets=service_targets,
        interface_names=interface_names,
    )
    commit = await _commit_snapshot(
        index=index,
        actor_id=actor_id,
        branch_id=branch_id,
        projection_hash=projection_hash,
        root_object_id=node_config.id,
        root_object=node_config,
        objects_by_id=objects_by_id,
        operation_label="NodeConfig.materialize_manifest_snapshot",
        commit_id_namespace=_NODE_CONFIG_MANIFEST_SNAPSHOT_COMMIT_NAMESPACE,
    )
    return NodeConfigManifestSnapshotCommitResult(
        node_config=node_config,
        environment_targets=tuple(node_config.environment_targets),
        ontology_targets=tuple(node_config.ontology_targets),
        service_targets=tuple(node_config.service_targets),
        service_code_packages=tuple(
            package
            for target in node_config.service_targets
            for package in target.code_packages
        ),
        interface_targets=tuple(node_config.interface_targets),
        commit_id=commit.commit_id,
        head_commit_id=commit.head_commit_id,
        object_instance_graph_commit_id=commit.object_instance_graph_commit_id,
        object_count=commit.object_count,
        change_count=commit.change_count,
    )


async def commit_node_package_manifest_snapshot(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    branch_id: UUID,
    projection_hash: str,
    name: str,
    node_config_id: UUID,
    source_code_package_id: UUID | None,
    fqn_prefix: str | None,
    version_number: int,
    title: str | None,
    description: str | None,
    aware_node_version: int,
    manifest_relative_path: str | None,
    package_root: str,
    sources_root: str,
    include_paths: JsonArray,
    exclude_paths: JsonArray,
    force_fresh_scan: bool,
    compilation_mode: str,
    dependencies: JsonArray,
    included_node_packages: Sequence[NodePackageIncludedNodePackageSnapshot],
) -> NodePackageManifestSnapshotCommitResult:
    node_package, objects_by_id = _build_node_package_manifest_snapshot_objects(
        name=name,
        node_config_id=node_config_id,
        source_code_package_id=source_code_package_id,
        fqn_prefix=fqn_prefix,
        version_number=version_number,
        title=title,
        description=description,
        aware_node_version=aware_node_version,
        manifest_relative_path=manifest_relative_path,
        package_root=package_root,
        sources_root=sources_root,
        include_paths=include_paths,
        exclude_paths=exclude_paths,
        force_fresh_scan=force_fresh_scan,
        compilation_mode=compilation_mode,
        dependencies=dependencies,
        included_node_packages=included_node_packages,
    )
    commit = await _commit_snapshot(
        index=index,
        actor_id=actor_id,
        branch_id=branch_id,
        projection_hash=projection_hash,
        root_object_id=node_package.id,
        root_object=node_package,
        objects_by_id=objects_by_id,
        operation_label="NodePackage.materialize_manifest_snapshot",
        commit_id_namespace=_NODE_PACKAGE_MANIFEST_SNAPSHOT_COMMIT_NAMESPACE,
    )
    return NodePackageManifestSnapshotCommitResult(
        node_package=node_package,
        included_node_packages=tuple(node_package.included_node_packages),
        commit_id=commit.commit_id,
        head_commit_id=commit.head_commit_id,
        object_instance_graph_commit_id=commit.object_instance_graph_commit_id,
        object_count=commit.object_count,
        change_count=commit.change_count,
    )


def _build_node_config_manifest_snapshot_objects(
    *,
    name: str,
    description: str | None,
    environment_targets: Sequence[NodeConfigEnvironmentTargetSnapshot],
    ontology_package_names: Sequence[str],
    service_targets: Sequence[NodeConfigServiceTargetSnapshot],
    interface_names: Sequence[str],
) -> tuple[NodeConfig, dict[UUID, BaseORMModel]]:
    objects_by_id: dict[UUID, BaseORMModel] = {}
    normalized_name = (name or "").strip()
    if not normalized_name:
        raise RuntimeError("NodeConfig snapshot requires non-empty name")
    node_config = _remember(
        objects_by_id,
        NodeConfig(
            id=stable_node_config_id(name=normalized_name),
            name=normalized_name,
            description=_normalize_optional_text(description),
        ),
    )
    for target_snapshot in environment_targets:
        target = _build_environment_target(
            objects_by_id=objects_by_id,
            node_config=node_config,
            target_snapshot=target_snapshot,
        )
        node_config.environment_targets.append(target)
    for package_name in sorted(
        {(name or "").strip() for name in ontology_package_names}
    ):
        if not package_name:
            continue
        ontology_target = _remember(
            objects_by_id,
            NodeConfigOntologyTarget(
                id=stable_node_config_ontology_target_id(
                    node_config_id=node_config.id,
                    package_name=package_name,
                ),
                node_config_id=node_config.id,
                package_name=package_name,
                ontology_package_id=ontology_package_id_for_name(package_name),
            ),
        )
        node_config.ontology_targets.append(ontology_target)
    service_snapshots_by_name = {
        (snapshot.service_name or "").strip(): snapshot for snapshot in service_targets
    }
    for service_name in sorted(service_snapshots_by_name):
        if not service_name:
            continue
        service_target = _remember(
            objects_by_id,
            NodeConfigServiceTarget(
                id=stable_node_config_service_target_id(
                    node_config_id=node_config.id,
                    service_name=service_name,
                ),
                node_config_id=node_config.id,
                service_name=service_name,
                service_config_id=stable_service_config_id(name=service_name),
            ),
        )
        for code_package_snapshot in service_snapshots_by_name[
            service_name
        ].code_packages:
            service_code_package = _build_service_code_package(
                objects_by_id=objects_by_id,
                service_target=service_target,
                code_package_snapshot=code_package_snapshot,
            )
            service_target.code_packages.append(service_code_package)
        node_config.service_targets.append(service_target)
    for interface_name in sorted({(name or "").strip() for name in interface_names}):
        if not interface_name:
            continue
        interface_target = _remember(
            objects_by_id,
            NodeConfigInterfaceTarget(
                id=stable_node_config_interface_target_id(
                    node_config_id=node_config.id,
                    interface_name=interface_name,
                ),
                node_config_id=node_config.id,
                interface_name=interface_name,
                interface_config_id=stable_interface_config_id(name=interface_name),
            ),
        )
        node_config.interface_targets.append(interface_target)
    return node_config, objects_by_id


def _build_service_code_package(
    *,
    objects_by_id: dict[UUID, BaseORMModel],
    service_target: NodeConfigServiceTarget,
    code_package_snapshot: NodeConfigServiceCodePackageSnapshot,
) -> NodeConfigServiceCodePackage:
    slot_key = (code_package_snapshot.slot_key or "").strip().casefold()
    package_name = (code_package_snapshot.package_name or "").strip()
    if not slot_key or not package_name:
        raise RuntimeError(
            "NodeConfig service code package requires non-empty slot_key and package_name: "
            f"service_name={service_target.service_name!r}"
        )
    language_value = (
        str(
            getattr(
                code_package_snapshot.language, "value", code_package_snapshot.language
            )
            or ""
        )
        .strip()
        .casefold()
        or CodeLanguage.aware.value
    )
    language = CodeLanguage(language_value)
    return _remember(
        objects_by_id,
        NodeConfigServiceCodePackage(
            id=stable_node_config_service_code_package_id(
                node_config_service_target_id=service_target.id,
                slot_key=slot_key,
                package_name=package_name,
                language=language.value,
            ),
            node_config_service_target_id=service_target.id,
            slot_key=slot_key,
            package_name=package_name,
            language=language,
            service_config_code_package_config_id=(
                code_package_snapshot.service_config_code_package_config_id
            ),
            code_package_id=code_package_snapshot.code_package_id,
            description=_normalize_optional_text(code_package_snapshot.description),
        ),
    )


def _build_environment_target(
    *,
    objects_by_id: dict[UUID, BaseORMModel],
    node_config: NodeConfig,
    target_snapshot: NodeConfigEnvironmentTargetSnapshot,
) -> NodeConfigEnvironmentTarget:
    environment_handle = (target_snapshot.environment_handle or "").strip()
    if not environment_handle:
        raise RuntimeError(
            f"NodeConfig snapshot contains empty environment target: {node_config.name}"
        )
    target = _remember(
        objects_by_id,
        NodeConfigEnvironmentTarget(
            id=stable_node_config_environment_target_id(
                node_config_id=node_config.id,
                environment_handle=environment_handle,
            ),
            node_config_id=node_config.id,
            environment_handle=environment_handle,
            environment_config_id=stable_environment_config_id(
                handle=environment_handle,
            ),
        ),
    )
    for mount_snapshot in target_snapshot.profile_mounts:
        mount = _build_environment_profile_mount(
            objects_by_id=objects_by_id,
            target=target,
            mount_snapshot=mount_snapshot,
        )
        target.profile_mounts.append(mount)
    return target


def _build_environment_profile_mount(
    *,
    objects_by_id: dict[UUID, BaseORMModel],
    target: NodeConfigEnvironmentTarget,
    mount_snapshot: NodeConfigEnvironmentProfileMountSnapshot,
) -> NodeConfigEnvironmentProfileMount:
    package_name = (mount_snapshot.package_name or "").strip()
    profile_key = (mount_snapshot.profile_key or "").strip()
    mount_key = (mount_snapshot.mount_key or "").strip()
    if not package_name or not profile_key or not mount_key:
        raise RuntimeError(
            "NodeConfig environment profile mount requires non-empty package_name, "
            f"profile_key, and mount_key: environment_handle={target.environment_handle!r}"
        )
    environment_profile_package_id = stable_environment_profile_package_id(
        name=package_name,
    )
    return _remember(
        objects_by_id,
        NodeConfigEnvironmentProfileMount(
            id=stable_node_config_environment_profile_mount_id(
                node_config_environment_target_id=target.id,
                mount_key=mount_key,
            ),
            node_config_environment_target_id=target.id,
            package_name=package_name,
            profile_key=profile_key,
            mount_key=mount_key,
            mode=(mount_snapshot.mode or "").strip() or "mounted",
            position=mount_snapshot.position,
            environment_profile_package_id=environment_profile_package_id,
        ),
    )


def _build_node_package_manifest_snapshot_objects(
    *,
    name: str,
    node_config_id: UUID,
    source_code_package_id: UUID | None,
    fqn_prefix: str | None,
    version_number: int,
    title: str | None,
    description: str | None,
    aware_node_version: int,
    manifest_relative_path: str | None,
    package_root: str,
    sources_root: str,
    include_paths: JsonArray,
    exclude_paths: JsonArray,
    force_fresh_scan: bool,
    compilation_mode: str,
    dependencies: JsonArray,
    included_node_packages: Sequence[NodePackageIncludedNodePackageSnapshot],
) -> tuple[NodePackage, dict[UUID, BaseORMModel]]:
    objects_by_id: dict[UUID, BaseORMModel] = {}
    normalized_name = (name or "").strip()
    if not normalized_name:
        raise RuntimeError("NodePackage snapshot requires non-empty name")
    node_package = _remember(
        objects_by_id,
        NodePackage(
            id=stable_node_package_id(name=normalized_name),
            name=normalized_name,
            node_config_id=node_config_id,
            source_code_package_id=source_code_package_id,
            fqn_prefix=(fqn_prefix or "").strip() or None,
            version_number=version_number,
            title=_normalize_optional_text(title),
            description=_normalize_optional_text(description),
            aware_node_version=aware_node_version,
            manifest_relative_path=(manifest_relative_path or "").strip() or None,
            package_root=(package_root or "").strip() or ".",
            sources_root=(sources_root or "").strip() or "nodes",
            include_paths=JsonArray(include_paths or []),
            exclude_paths=JsonArray(exclude_paths or []),
            force_fresh_scan=force_fresh_scan,
            compilation_mode=(compilation_mode or "").strip() or "raw_xor",
            dependencies=JsonArray(dependencies or []),
        ),
    )
    for included_snapshot in included_node_packages:
        included_package_name = (included_snapshot.included_package_name or "").strip()
        if not included_package_name:
            raise RuntimeError(
                f"NodePackage snapshot contains empty include: {normalized_name}"
            )
        included = _remember(
            objects_by_id,
            NodePackageIncludedNodePackage(
                id=stable_node_package_included_node_package_id(
                    node_package_id=node_package.id,
                    included_package_name=included_package_name,
                ),
                node_package_id=node_package.id,
                included_package_name=included_package_name,
                included_node_package_id=stable_node_package_id(
                    name=included_package_name,
                ),
                include_key=(included_snapshot.include_key or "").strip() or None,
                description=_normalize_optional_text(included_snapshot.description),
            ),
        )
        node_package.included_node_packages.append(included)
    return node_package, objects_by_id


@dataclass(frozen=True, slots=True)
class _SnapshotCommit:
    commit_id: UUID
    head_commit_id: UUID
    object_instance_graph_commit_id: UUID
    object_count: int
    change_count: int


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
        raise RuntimeError(
            "Node snapshot commit missing projection hash: " f"{projection_hash}"
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
            "Node snapshot commit missing ObjectProjectionGraphIdentity: "
            f"projection_hash={projection_hash}"
        )
    oigi_id = stable_object_instance_graph_identity_id(
        object_projection_graph_identity_id=opgi.id,
        object_instance_graph_id=domain_oig_id,
    )
    before_oig = await _load_before_oig(
        index=index,
        branch_id=branch_id,
        projection_hash=projection_hash,
        domain_oig_id=domain_oig_id,
        root_object_id=root_object_id,
    )
    object_ids = frozenset(objects_by_id)
    deleted_ids = _snapshot_deleted_source_ids(
        before_oig=before_oig,
        desired_object_ids=object_ids,
    )
    change_set = ORMChangeSet(
        collected_at=datetime.now(UTC),
        created_ids=object_ids,
        touched_ids=object_ids | deleted_ids,
        deleted_ids=deleted_ids,
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
        class_configs_by_id=dict(index.class_configs_by_id),
        relationships_by_id=dict(index.relationships_by_id),
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
                "Node snapshot commit produced no OIG changes and no existing "
                f"lane head: operation_label={operation_label!r}"
            )
        head_commit_id = (
            raw_head_commit_id
            if isinstance(raw_head_commit_id, UUID)
            else UUID(str(raw_head_commit_id))
        )
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
        root_object_id=root_object_id,
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
            "Node snapshot commit did not append a lane commit: "
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


def _snapshot_deleted_source_ids(
    *,
    before_oig: object,
    desired_object_ids: frozenset[UUID],
) -> frozenset[UUID]:
    stale_ids: set[UUID] = set()
    for class_instance in (
        getattr(before_oig, "root_class_instance", None),
        *tuple(getattr(before_oig, "class_instances", ()) or ()),
    ):
        if class_instance is None:
            continue
        source_object_id = getattr(class_instance, "source_object_id", None)
        if not isinstance(source_object_id, UUID):
            continue
        if source_object_id not in desired_object_ids:
            stale_ids.add(source_object_id)
    return frozenset(stale_ids)


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


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _remember(
    objects_by_id: dict[UUID, BaseORMModel],
    obj: _TModel,
) -> _TModel:
    obj_id = obj.id
    previous = objects_by_id.get(obj_id)
    if previous is not None and previous is not obj:
        raise RuntimeError(f"Node snapshot duplicate object id: {obj_id}")
    objects_by_id[obj_id] = obj
    return obj


__all__ = [
    "NodeConfigEnvironmentProfileMountSnapshot",
    "NodeConfigEnvironmentTargetSnapshot",
    "NodeConfigManifestSnapshotCommitResult",
    "NodeConfigServiceCodePackageSnapshot",
    "NodeConfigServiceTargetSnapshot",
    "NodePackageIncludedNodePackageSnapshot",
    "NodePackageManifestSnapshotCommitResult",
    "commit_node_config_manifest_snapshot",
    "commit_node_package_manifest_snapshot",
]
