from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TypeVar
from uuid import NAMESPACE_URL, UUID, uuid5

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
from aware_network_ontology.network.network_node_config import NetworkNodeConfig
from aware_network_ontology.network.network_node_package import NetworkNodePackage
from aware_network_ontology.stable_ids import (
    stable_network_node_config_id,
    stable_network_node_package_id,
)
from aware_orm.models.base_model import BaseORMModel
from aware_orm.session.change_collector import ORMChangeSet

_TModel = TypeVar("_TModel", bound=BaseORMModel)


@dataclass(frozen=True, slots=True)
class NetworkNodeConfigSnapshotCommitResult:
    network_node_config: NetworkNodeConfig
    commit_id: UUID
    head_commit_id: UUID
    object_instance_graph_commit_id: UUID
    object_count: int
    change_count: int


@dataclass(frozen=True, slots=True)
class NetworkNodePackageSnapshotCommitResult:
    network_node_package: NetworkNodePackage
    commit_id: UUID
    head_commit_id: UUID
    object_instance_graph_commit_id: UUID
    object_count: int
    change_count: int


_NETWORK_NODE_CONFIG_SNAPSHOT_COMMIT_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware://network/node-config/manifest-snapshot-commit/v1",
)
_NETWORK_NODE_PACKAGE_SNAPSHOT_COMMIT_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware://network/node-package/manifest-snapshot-commit/v1",
)


async def commit_network_node_config_manifest_snapshot(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    branch_id: UUID,
    projection_hash: str,
    name: str,
    description: str | None,
) -> NetworkNodeConfigSnapshotCommitResult:
    network_node_config, objects_by_id = _build_network_node_config_snapshot_objects(
        name=name,
        description=description,
    )
    commit = await _commit_snapshot(
        index=index,
        actor_id=actor_id,
        branch_id=branch_id,
        projection_hash=projection_hash,
        root_object_id=network_node_config.id,
        root_object=network_node_config,
        objects_by_id=objects_by_id,
        operation_label="NetworkNodeConfig.materialize_manifest_snapshot",
        commit_id_namespace=_NETWORK_NODE_CONFIG_SNAPSHOT_COMMIT_NAMESPACE,
    )
    return NetworkNodeConfigSnapshotCommitResult(
        network_node_config=network_node_config,
        commit_id=commit.commit_id,
        head_commit_id=commit.head_commit_id,
        object_instance_graph_commit_id=commit.object_instance_graph_commit_id,
        object_count=commit.object_count,
        change_count=commit.change_count,
    )


async def commit_network_node_package_manifest_snapshot(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    branch_id: UUID,
    projection_hash: str,
    name: str,
    network_node_config_id: UUID,
    source_code_package_id: UUID | None,
) -> NetworkNodePackageSnapshotCommitResult:
    network_node_package, objects_by_id = _build_network_node_package_snapshot_objects(
        name=name,
        network_node_config_id=network_node_config_id,
        source_code_package_id=source_code_package_id,
    )
    commit = await _commit_snapshot(
        index=index,
        actor_id=actor_id,
        branch_id=branch_id,
        projection_hash=projection_hash,
        root_object_id=network_node_package.id,
        root_object=network_node_package,
        objects_by_id=objects_by_id,
        operation_label="NetworkNodePackage.materialize_manifest_snapshot",
        commit_id_namespace=_NETWORK_NODE_PACKAGE_SNAPSHOT_COMMIT_NAMESPACE,
    )
    return NetworkNodePackageSnapshotCommitResult(
        network_node_package=network_node_package,
        commit_id=commit.commit_id,
        head_commit_id=commit.head_commit_id,
        object_instance_graph_commit_id=commit.object_instance_graph_commit_id,
        object_count=commit.object_count,
        change_count=commit.change_count,
    )


def _build_network_node_config_snapshot_objects(
    *,
    name: str,
    description: str | None,
) -> tuple[NetworkNodeConfig, dict[UUID, BaseORMModel]]:
    objects_by_id: dict[UUID, BaseORMModel] = {}
    normalized_name = (name or "").strip()
    if not normalized_name:
        raise RuntimeError("NetworkNodeConfig snapshot requires non-empty name")
    network_node_config = _remember(
        objects_by_id,
        NetworkNodeConfig(
            id=stable_network_node_config_id(name=normalized_name),
            name=normalized_name,
            description=_normalize_optional_text(description),
        ),
    )
    return network_node_config, objects_by_id


def _build_network_node_package_snapshot_objects(
    *,
    name: str,
    network_node_config_id: UUID,
    source_code_package_id: UUID | None,
) -> tuple[NetworkNodePackage, dict[UUID, BaseORMModel]]:
    objects_by_id: dict[UUID, BaseORMModel] = {}
    normalized_name = (name or "").strip()
    if not normalized_name:
        raise RuntimeError("NetworkNodePackage snapshot requires non-empty name")
    network_node_package = _remember(
        objects_by_id,
        NetworkNodePackage(
            id=stable_network_node_package_id(name=normalized_name),
            name=normalized_name,
            network_node_config_id=network_node_config_id,
            source_code_package_id=source_code_package_id,
        ),
    )
    return network_node_package, objects_by_id


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
            "Network snapshot commit missing projection hash: " f"{projection_hash}"
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
            "Network snapshot commit missing ObjectProjectionGraphIdentity: "
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
                "Network snapshot commit produced no OIG changes and no existing "
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
            "Network snapshot commit did not append a lane commit: "
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
        raise RuntimeError(f"Network snapshot duplicate object id: {obj_id}")
    objects_by_id[obj_id] = obj
    return obj


__all__ = [
    "NetworkNodeConfigSnapshotCommitResult",
    "NetworkNodePackageSnapshotCommitResult",
    "commit_network_node_config_manifest_snapshot",
    "commit_network_node_package_manifest_snapshot",
]
