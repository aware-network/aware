from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Protocol
from uuid import UUID

from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.fs_snapshot_store import FSSnapshotStore
from aware_meta.runtime.graph_context import MetaGraphRuntimeIndexSnapshot
from aware_meta.runtime.oig_hydration import reify_meta_orm_root_from_oig_commit
from aware_meta.runtime.read_model_provider import (
    read_workspace_meta_runtime_read_model,
)
from aware_node_ontology.node.node_config import NodeConfig
from aware_node_ontology.node.node_package import NodePackage
from aware_node_ontology.stable_ids import stable_node_package_id

_REVISION_FILESYSTEM_MANIFEST_RELATIVE_PATH = Path(
    ".aware/workspace/revision-filesystem.manifest.json"
)


class NodeRuntimePackageRefReadModel(Protocol):
    @property
    def index(self) -> MetaGraphRuntimeIndexSnapshot: ...

    def projection_hash_for_name(self, projection_name: str) -> str: ...


@dataclass(frozen=True, slots=True)
class _StaticNodeRuntimePackageRefReadModel:
    index: MetaGraphRuntimeIndexSnapshot
    projection_hash_by_name: Mapping[str, str]

    def projection_hash_for_name(self, projection_name: str) -> str:
        target = projection_name.strip()
        if not target:
            raise ValueError("Projection name is required.")
        projection_hash = self.projection_hash_by_name.get(target)
        if projection_hash is None:
            raise ValueError(
                f"Projection {projection_name!r} was not found in Node package "
                "ref read model."
            )
        return projection_hash


@dataclass(frozen=True, slots=True)
class NodeRuntimePackageRef:
    """Runtime ref for a Workspace-selected NodePackage semantic package."""

    family_key: str
    package_kind: str
    package_name: str
    manifest_path: str | Path | None = None
    workspace_package_id: str | None = None
    semantic_package_id: str | None = None
    semantic_object_instance_graph_commit_id: str | None = None
    semantic_head_commit_id: str | None = None
    semantic_branch_id: str | None = None
    semantic_projection_hash: str | None = None
    semantic_root_kind: str | None = None
    semantic_root_id: str | None = None
    semantic_root_object_instance_graph_commit_id: str | None = None
    source_code_package_id: str | None = None

    @property
    def has_semantic_identity(self) -> bool:
        return bool(_clean(self.semantic_package_id) or _clean(self.semantic_root_id))


@dataclass(frozen=True, slots=True)
class NodeRuntimePackageDependency:
    package_name: str
    kind: str
    version_number: int | None = None

    def to_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "package_name": self.package_name,
            "kind": self.kind,
        }
        if self.version_number is not None:
            payload["version_number"] = self.version_number
        return payload


@dataclass(frozen=True, slots=True)
class NodeRuntimeIncludedNodePackage:
    included_package_name: str
    include_key: str
    included_node_package_id: UUID

    def to_payload(self) -> dict[str, object]:
        return {
            "included_package_name": self.included_package_name,
            "include_key": self.include_key,
            "included_node_package_id": str(self.included_node_package_id),
        }


@dataclass(frozen=True, slots=True)
class NodeRuntimeEnvironmentProfileMount:
    profile_key: str
    package_name: str
    mount_key: str
    mode: str
    position: int | None

    def to_payload(self) -> dict[str, object]:
        return {
            "profile_key": self.profile_key,
            "package_name": self.package_name,
            "mount_key": self.mount_key,
            "mode": self.mode,
            "position": self.position,
        }


@dataclass(frozen=True, slots=True)
class NodeRuntimeEnvironmentTarget:
    environment_handle: str
    profile_mounts: tuple[NodeRuntimeEnvironmentProfileMount, ...]

    def to_payload(self) -> dict[str, object]:
        return {
            "environment_handle": self.environment_handle,
            "profile_mounts": [mount.to_payload() for mount in self.profile_mounts],
        }


def _environment_profile_mounts_from_target(
    target: object,
) -> tuple[NodeRuntimeEnvironmentProfileMount, ...]:
    result: list[NodeRuntimeEnvironmentProfileMount] = []
    for mount in tuple(getattr(target, "profile_mounts", ()) or ()):
        profile_key = str(getattr(mount, "profile_key", "") or "").strip()
        package_name = str(getattr(mount, "package_name", "") or "").strip()
        mount_key = str(getattr(mount, "mount_key", "") or "").strip()
        if not profile_key or not package_name or not mount_key:
            raise RuntimeError(
                "NodeConfigEnvironmentTarget profile mount requires "
                "profile_key/package_name/mount_key: "
                f"environment_handle={getattr(target, 'environment_handle', None)!r}"
            )
        mode = str(getattr(mount, "mode", "") or "").strip() or "mounted"
        result.append(
            NodeRuntimeEnvironmentProfileMount(
                profile_key=profile_key,
                package_name=package_name,
                mount_key=mount_key,
                mode=mode,
                position=getattr(mount, "position", None),
            )
        )
    return tuple(
        sorted(
            result,
            key=lambda item: (
                item.position is None,
                item.position or 0,
                item.mount_key,
            ),
        )
    )


@dataclass(frozen=True, slots=True)
class NodeRuntimeServiceTarget:
    service_name: str

    def to_payload(self) -> dict[str, object]:
        return {"service_name": self.service_name}


@dataclass(frozen=True, slots=True)
class NodeRuntimeInterfaceTarget:
    interface_name: str

    def to_payload(self) -> dict[str, object]:
        return {"interface_name": self.interface_name}


@dataclass(frozen=True, slots=True)
class ResolvedNodeRuntimePackageRef:
    """Resolved NodePackage coordinates plus hosted target intent."""

    package_ref: NodeRuntimePackageRef
    materialized_workspace_root: Path
    manifest_path: Path
    manifest_relative_path: str
    package_name: str
    node_config_name: str
    node_package_id: UUID
    node_config_id: UUID
    source_code_package_id: UUID | None
    dependencies: tuple[NodeRuntimePackageDependency, ...]
    included_node_packages: tuple[NodeRuntimeIncludedNodePackage, ...]
    environment_targets: tuple[NodeRuntimeEnvironmentTarget, ...]
    service_targets: tuple[NodeRuntimeServiceTarget, ...]
    interface_targets: tuple[NodeRuntimeInterfaceTarget, ...]
    effective_environment_targets: tuple[NodeRuntimeEnvironmentTarget, ...]
    effective_service_targets: tuple[NodeRuntimeServiceTarget, ...]
    effective_interface_targets: tuple[NodeRuntimeInterfaceTarget, ...]
    semantic_branch_id: str
    semantic_package_id: str
    semantic_object_instance_graph_commit_id: str | None = None
    semantic_head_commit_id: str | None = None
    semantic_root_kind: str | None = None
    semantic_root_id: str | None = None
    semantic_root_object_instance_graph_commit_id: str | None = None
    workspace_package_id: str | None = None

    @property
    def service_names(self) -> tuple[str, ...]:
        return tuple(target.service_name for target in self.service_targets)

    @property
    def effective_service_names(self) -> tuple[str, ...]:
        return tuple(target.service_name for target in self.effective_service_targets)


async def resolve_committed_node_runtime_package_ref(
    *,
    package_ref: NodeRuntimePackageRef,
    materialized_workspace_root: str | Path,
    read_model: NodeRuntimePackageRefReadModel | None = None,
    index: MetaGraphRuntimeIndexSnapshot | None = None,
    repo_root: str | Path | None = None,
    aware_root: str | Path | None = None,
) -> ResolvedNodeRuntimePackageRef:
    """Resolve a committed NodePackage ref without rebuilding source."""

    _validate_node_ref(package_ref)
    root = Path(materialized_workspace_root).expanduser().resolve()
    _validate_revision_filesystem_root(root)
    package_commit_ref_label = "semantic_object_instance_graph_commit_id"
    package_commit_ref_value = _clean(
        package_ref.semantic_object_instance_graph_commit_id
    )
    if package_commit_ref_value is None:
        package_commit_ref_label = "semantic_head_commit_id"
        package_commit_ref_value = _clean(package_ref.semantic_head_commit_id)
    package_commit_ref_id = _required_uuid(
        package_commit_ref_value,
        label=package_commit_ref_label,
    )
    branch_id = _optional_uuid(package_ref.semantic_branch_id)
    if (
        branch_id is None
        and _clean(package_ref.semantic_object_instance_graph_commit_id) is None
    ):
        raise RuntimeError(
            "Branchless Node runtime package refs require "
            "semantic_object_instance_graph_commit_id; legacy "
            "semantic_head_commit_id refs must also provide semantic_branch_id."
        )
    resolved_read_model = _resolve_node_package_ref_read_model(
        read_model=read_model,
        index=index,
        materialized_workspace_root=root,
        repo_root=repo_root,
        aware_root=aware_root,
    )
    runtime_index = resolved_read_model.index
    node_package_projection_hash = _required_node_package_projection_hash(
        read_model=resolved_read_model,
        package_ref=package_ref,
    )
    store = FSCommitStore(root_dir=root)
    snapshots = FSSnapshotStore(root_dir=root)
    if branch_id is None:
        package_commit_refs = (
            await store.domain_commit_refs_for_object_instance_graph_commit_id(
                projection_hash=node_package_projection_hash,
                object_instance_graph_commit_id=package_commit_ref_id,
            )
        )
        if not package_commit_refs:
            raise RuntimeError(
                "Node runtime package ref semantic_object_instance_graph_commit_id "
                "did not resolve to any indexed NodePackage branch: "
                f"semantic_object_instance_graph_commit_id={package_commit_ref_id} "
                f"projection_hash={node_package_projection_hash}"
            )
        if len(package_commit_refs) != 1:
            raise RuntimeError(
                "Node runtime package ref semantic_object_instance_graph_commit_id "
                "resolved to multiple NodePackage branches: "
                f"semantic_object_instance_graph_commit_id={package_commit_ref_id} "
                f"projection_hash={node_package_projection_hash} "
                f"branches={[str(ref.branch_id) for ref in package_commit_refs]!r}"
            )
        package_commit_ref = package_commit_refs[0]
        branch_id = package_commit_ref.branch_id
        package_domain_commit_id = package_commit_ref.domain_commit_id
    else:
        package_domain_commit_id = (
            await store.domain_commit_id_for_object_instance_graph_commit_id(
                branch_id=branch_id,
                projection_hash=node_package_projection_hash,
                object_instance_graph_commit_id=package_commit_ref_id,
            )
        )
        if package_domain_commit_id is None:
            legacy_domain_commit = await store.get_commit(
                branch_id=branch_id,
                projection_hash=node_package_projection_hash,
                commit_id=package_commit_ref_id,
            )
            if legacy_domain_commit is None:
                raise RuntimeError(
                    f"Node runtime package ref {package_commit_ref_label} is neither "
                    "an indexed ObjectInstanceGraphCommit id nor a domain commit id: "
                    f"{package_commit_ref_label}={package_commit_ref_id} "
                    f"branch_id={branch_id} "
                    f"projection_hash={node_package_projection_hash}"
                )
            package_domain_commit_id = package_commit_ref_id

    node_package_id = _optional_uuid(
        package_ref.semantic_package_id
    ) or stable_node_package_id(name=package_ref.package_name)
    node_package = await reify_meta_orm_root_from_oig_commit(
        index=runtime_index,
        branch_id=branch_id,
        projection_hash=node_package_projection_hash,
        projection_name="NodePackage",
        commit_id=package_domain_commit_id,
        root_id=node_package_id,
        root_type=NodePackage,
        commit_store=store,
        snapshot_store=snapshots,
    )
    if node_package is None:
        raise RuntimeError(
            "Node runtime package ref could not hydrate NodePackage from semantic "
            f"commit: package_name={package_ref.package_name!r} "
            f"semantic_package_id={node_package_id}"
        )
    node_config = node_package.node_config
    if node_config is None:
        node_config = await _hydrate_node_config_for_package_ref(
            read_model=resolved_read_model,
            package_ref=package_ref,
            branch_id=branch_id,
            node_package=node_package,
            commit_store=store,
            snapshot_store=snapshots,
        )
    if node_config is None:
        raise RuntimeError(
            "Node runtime package ref hydrated NodePackage without portal-backed "
            f"NodeConfig: package_name={package_ref.package_name!r} "
            f"node_config_id={node_package.node_config_id}"
        )
    _validate_node_package_ref_pair(
        package_ref=package_ref,
        node_package=node_package,
    )
    _validate_node_config_ref_pair(
        package_ref=package_ref,
        node_package=node_package,
        node_config=node_config,
    )
    manifest_path = _resolve_manifest_path_from_node_package(
        node_package=node_package,
        package_ref=package_ref,
        materialized_workspace_root=root,
    )
    return ResolvedNodeRuntimePackageRef(
        package_ref=package_ref,
        materialized_workspace_root=root,
        manifest_path=manifest_path,
        manifest_relative_path=_relative_to_root(
            path=manifest_path,
            root=root,
            label="manifest_path",
        ),
        package_name=node_package.name,
        node_config_name=node_config.name,
        node_package_id=node_package.id,
        node_config_id=node_config.id,
        source_code_package_id=node_package.source_code_package_id,
        dependencies=_dependencies_from_package_payload(node_package.dependencies),
        included_node_packages=_included_node_packages_from_package(node_package),
        environment_targets=_environment_targets_from_config(node_config),
        service_targets=_service_targets_from_config(node_config),
        interface_targets=_interface_targets_from_config(node_config),
        effective_environment_targets=_environment_targets_from_config(node_config),
        effective_service_targets=_service_targets_from_config(node_config),
        effective_interface_targets=_interface_targets_from_config(node_config),
        semantic_branch_id=str(branch_id),
        semantic_package_id=str(node_package.id),
        semantic_object_instance_graph_commit_id=_clean(
            package_ref.semantic_object_instance_graph_commit_id
        ),
        semantic_head_commit_id=_clean(package_ref.semantic_head_commit_id),
        semantic_root_kind=_clean(package_ref.semantic_root_kind),
        semantic_root_id=_clean(package_ref.semantic_root_id),
        semantic_root_object_instance_graph_commit_id=_clean(
            package_ref.semantic_root_object_instance_graph_commit_id
        ),
        workspace_package_id=_clean(package_ref.workspace_package_id),
    )


async def resolve_committed_node_runtime_package_refs(
    *,
    package_refs: Sequence[NodeRuntimePackageRef],
    materialized_workspace_root: str | Path,
    read_model: NodeRuntimePackageRefReadModel | None = None,
    index: MetaGraphRuntimeIndexSnapshot | None = None,
    repo_root: str | Path | None = None,
    aware_root: str | Path | None = None,
) -> tuple[ResolvedNodeRuntimePackageRef, ...]:
    resolved_root = Path(materialized_workspace_root).expanduser().resolve()
    resolved_read_model = _resolve_node_package_ref_read_model(
        read_model=read_model,
        index=index,
        materialized_workspace_root=resolved_root,
        repo_root=repo_root,
        aware_root=aware_root,
    )
    resolved = tuple(
        [
            await resolve_committed_node_runtime_package_ref(
                read_model=resolved_read_model,
                package_ref=package_ref,
                materialized_workspace_root=resolved_root,
            )
            for package_ref in package_refs
        ]
    )
    _reject_duplicate_resolved_refs(resolved)
    return _attach_effective_target_closure(resolved)


def _validate_node_ref(package_ref: NodeRuntimePackageRef) -> None:
    if _clean(package_ref.family_key) not in {"node", "aware_node"}:
        raise RuntimeError(
            "Node runtime package ref requires family_key='node' or "
            f"'aware_node': {package_ref.family_key!r}"
        )
    if _clean(package_ref.package_kind) not in {"node", "node_package"}:
        raise RuntimeError(
            "Node runtime package ref requires package_kind='node' or "
            f"'node_package': {package_ref.package_kind!r}"
        )
    if not _clean(package_ref.package_name):
        raise RuntimeError("Node runtime package ref requires a package_name.")
    semantic_root_kind = _clean(package_ref.semantic_root_kind)
    if semantic_root_kind is not None and semantic_root_kind not in {
        "node_config",
        "node_package",
    }:
        raise RuntimeError(
            "Node runtime package ref semantic_root_kind must be "
            "'node_config' or 'node_package' when provided: "
            f"{semantic_root_kind!r}"
        )


def _validate_revision_filesystem_root(root: Path) -> None:
    if not root.is_dir():
        raise FileNotFoundError(
            "Node runtime package ref requires an existing materialized "
            f"workspace root: {root}"
        )
    manifest_path = (root / _REVISION_FILESYSTEM_MANIFEST_RELATIVE_PATH).resolve()
    if not manifest_path.is_file():
        raise FileNotFoundError(
            "Node runtime package ref requires a WorkspaceRevision filesystem "
            f"manifest at {manifest_path}"
        )


def _required_node_package_projection_hash(
    *,
    read_model: NodeRuntimePackageRefReadModel,
    package_ref: NodeRuntimePackageRef,
) -> str:
    explicit_hash = _clean(package_ref.semantic_projection_hash)
    if explicit_hash is not None:
        return explicit_hash
    return read_model.projection_hash_for_name("NodePackage")


def _resolve_manifest_path_from_node_package(
    *,
    node_package: NodePackage,
    package_ref: NodeRuntimePackageRef,
    materialized_workspace_root: Path,
) -> Path:
    """Resolve the declared package manifest path for provenance.

    The committed NodePackage/NodeConfig graph is the runtime truth for deployment.
    A WorkspaceRevision filesystem root may intentionally materialize package source
    and semantic artifacts without carrying every semantic TOML manifest. Keep the
    declared manifest path target-local for receipts, but do not require the file to
    exist before runtime inputs can be derived from committed package truth.
    """

    raw_manifest_path = _clean(node_package.manifest_relative_path)
    if raw_manifest_path is None:
        raw_manifest_path = (
            str(package_ref.manifest_path)
            if package_ref.manifest_path is not None
            else None
        )
    if raw_manifest_path is None or not raw_manifest_path.strip():
        raise RuntimeError(
            "Committed NodePackage runtime ref requires "
            "NodePackage.manifest_relative_path or package_ref.manifest_path."
        )
    manifest_path = Path(raw_manifest_path).expanduser()
    if not manifest_path.is_absolute():
        manifest_path = materialized_workspace_root / manifest_path
    resolved_manifest_path = manifest_path.resolve()
    _relative_to_root(
        path=resolved_manifest_path,
        root=materialized_workspace_root,
        label="manifest_path",
    )
    return resolved_manifest_path


async def _hydrate_node_config_for_package_ref(
    *,
    read_model: NodeRuntimePackageRefReadModel,
    package_ref: NodeRuntimePackageRef,
    branch_id: UUID,
    node_package: NodePackage,
    commit_store: FSCommitStore,
    snapshot_store: FSSnapshotStore,
) -> NodeConfig | None:
    node_config_id = node_package.node_config_id
    runtime_index = read_model.index
    node_config_projection_hash = read_model.projection_hash_for_name("NodeConfig")

    semantic_root_kind = _clean(package_ref.semantic_root_kind)
    semantic_root_id = _optional_uuid(package_ref.semantic_root_id)
    if semantic_root_id is not None and semantic_root_kind == "node_config":
        if semantic_root_id != node_config_id:
            raise RuntimeError(
                "Node runtime package ref semantic_root_id does not match "
                "NodePackage.node_config_id: "
                f"ref={semantic_root_id} node_config_id={node_config_id}"
            )

    node_config_commit_id: UUID | None = None
    semantic_root_commit_id = _optional_uuid(
        _clean(package_ref.semantic_root_object_instance_graph_commit_id)
    )
    if semantic_root_kind == "node_config" and semantic_root_commit_id is not None:
        node_config_commit_id = (
            await commit_store.domain_commit_id_for_object_instance_graph_commit_id(
                branch_id=branch_id,
                projection_hash=node_config_projection_hash,
                object_instance_graph_commit_id=semantic_root_commit_id,
            )
        )
        if node_config_commit_id is None:
            legacy_domain_commit = await commit_store.get_commit(
                branch_id=branch_id,
                projection_hash=node_config_projection_hash,
                commit_id=semantic_root_commit_id,
            )
            if legacy_domain_commit is None:
                raise RuntimeError(
                    "Node runtime package ref semantic_root_object_instance_graph_commit_id "
                    "is neither an indexed ObjectInstanceGraphCommit id nor a domain "
                    "commit id: "
                    f"semantic_root_object_instance_graph_commit_id={semantic_root_commit_id} "
                    f"branch_id={branch_id} "
                    f"projection_hash={node_config_projection_hash}"
                )
            node_config_commit_id = semantic_root_commit_id

    if node_config_commit_id is None:
        head = await commit_store.head(
            branch_id=branch_id,
            projection_hash=node_config_projection_hash,
        )
        if head is None or head.get("commit_id") is None:
            return None
        node_config_commit_id = _required_uuid(
            str(head["commit_id"]),
            label="node_config head commit_id",
        )

    return await reify_meta_orm_root_from_oig_commit(
        index=runtime_index,
        branch_id=branch_id,
        projection_hash=node_config_projection_hash,
        projection_name="NodeConfig",
        commit_id=node_config_commit_id,
        root_id=node_config_id,
        root_type=NodeConfig,
        commit_store=commit_store,
        snapshot_store=snapshot_store,
    )


def _validate_node_package_ref_pair(
    *,
    package_ref: NodeRuntimePackageRef,
    node_package: NodePackage,
) -> None:
    if node_package.name != package_ref.package_name:
        raise RuntimeError(
            "Node runtime package ref package_name does not match NodePackage: "
            f"ref={package_ref.package_name!r} node_package={node_package.name!r}"
        )
    semantic_package_id = _optional_uuid(package_ref.semantic_package_id)
    if semantic_package_id is not None and semantic_package_id != node_package.id:
        raise RuntimeError(
            "Node runtime package ref semantic_package_id does not match "
            f"NodePackage: ref={semantic_package_id} node_package={node_package.id}"
        )


def _validate_node_config_ref_pair(
    *,
    package_ref: NodeRuntimePackageRef,
    node_package: NodePackage,
    node_config: NodeConfig,
) -> None:
    if node_config.id != node_package.node_config_id:
        raise RuntimeError(
            "NodePackage points at a different NodeConfig than the hydrated root: "
            f"package={node_package.node_config_id} node_config={node_config.id}"
        )
    semantic_root_id = _optional_uuid(package_ref.semantic_root_id)
    if semantic_root_id is None:
        return
    semantic_root_kind = _clean(package_ref.semantic_root_kind)
    expected_root_id = (
        node_config.id if semantic_root_kind == "node_config" else node_package.id
    )
    if semantic_root_id != expected_root_id:
        raise RuntimeError(
            "Node runtime package ref semantic_root_id does not match "
            f"{semantic_root_kind or 'node_package'} root: "
            f"ref={semantic_root_id} expected={expected_root_id}"
        )


def _dependencies_from_package_payload(
    payload: object,
) -> tuple[NodeRuntimePackageDependency, ...]:
    if payload is None:
        return ()
    if not isinstance(payload, Sequence) or isinstance(payload, (str, bytes)):
        raise RuntimeError("NodePackage.dependencies must be a JSON array.")
    dependencies: list[NodeRuntimePackageDependency] = []
    for item in payload:
        if not isinstance(item, Mapping):
            raise RuntimeError("NodePackage.dependencies entries must be objects.")
        dependencies.append(
            NodeRuntimePackageDependency(
                package_name=_required_text(
                    item.get("package_name"),
                    label="dependencies[].package_name",
                ),
                kind=_required_text(item.get("kind"), label="dependencies[].kind"),
                version_number=_optional_int(
                    item.get("version_number"),
                    label="dependencies[].version_number",
                ),
            )
        )
    return tuple(dependencies)


def _included_node_packages_from_package(
    node_package: NodePackage,
) -> tuple[NodeRuntimeIncludedNodePackage, ...]:
    return tuple(
        sorted(
            (
                NodeRuntimeIncludedNodePackage(
                    included_package_name=_required_text(
                        include.included_package_name,
                        label="included_node_packages[].included_package_name",
                    ),
                    include_key=_required_text(
                        include.include_key or include.included_package_name,
                        label="included_node_packages[].include_key",
                    ),
                    included_node_package_id=include.included_node_package_id,
                )
                for include in node_package.included_node_packages
            ),
            key=lambda item: (item.included_package_name, item.include_key),
        )
    )


def _attach_effective_target_closure(
    resolved: tuple[ResolvedNodeRuntimePackageRef, ...],
) -> tuple[ResolvedNodeRuntimePackageRef, ...]:
    by_name = {item.package_name: item for item in resolved}
    return tuple(
        _with_effective_targets(item=item, by_name=by_name) for item in resolved
    )


def _with_effective_targets(
    *,
    item: ResolvedNodeRuntimePackageRef,
    by_name: Mapping[str, ResolvedNodeRuntimePackageRef],
) -> ResolvedNodeRuntimePackageRef:
    closure = _resolved_node_package_closure(item=item, by_name=by_name)
    return replace(
        item,
        effective_environment_targets=_environment_targets_from_resolved_refs(closure),
        effective_service_targets=_service_targets_from_resolved_refs(closure),
        effective_interface_targets=_interface_targets_from_resolved_refs(closure),
    )


def _resolved_node_package_closure(
    *,
    item: ResolvedNodeRuntimePackageRef,
    by_name: Mapping[str, ResolvedNodeRuntimePackageRef],
) -> tuple[ResolvedNodeRuntimePackageRef, ...]:
    ordered: list[ResolvedNodeRuntimePackageRef] = []
    visiting: set[str] = set()
    visited: set[str] = set()

    def _visit(current: ResolvedNodeRuntimePackageRef) -> None:
        if current.package_name in visited:
            return
        if current.package_name in visiting:
            raise RuntimeError(
                "NodePackage include cycle detected while resolving effective composition: "
                f"package_name={current.package_name!r}"
            )
        visiting.add(current.package_name)
        ordered.append(current)
        for include in current.included_node_packages:
            included = by_name.get(include.included_package_name)
            if included is None:
                raise RuntimeError(
                    "NodePackage include target is not present in the committed package ref set: "
                    f"package_name={current.package_name!r} "
                    f"included_package_name={include.included_package_name!r}"
                )
            _visit(included)
        visiting.remove(current.package_name)
        visited.add(current.package_name)

    _visit(item)
    return tuple(ordered)


def _environment_targets_from_config(
    node_config: NodeConfig,
) -> tuple[NodeRuntimeEnvironmentTarget, ...]:
    return tuple(
        sorted(
            (
                NodeRuntimeEnvironmentTarget(
                    environment_handle=target.environment_handle,
                    profile_mounts=_environment_profile_mounts_from_target(target),
                )
                for target in node_config.environment_targets
            ),
            key=lambda target: (target.environment_handle,),
        )
    )


def _environment_targets_from_configs(
    node_configs: Sequence[NodeConfig],
) -> tuple[NodeRuntimeEnvironmentTarget, ...]:
    targets: dict[str, NodeRuntimeEnvironmentTarget] = {}
    for node_config in node_configs:
        for target in _environment_targets_from_config(node_config):
            targets[target.environment_handle] = target
    return tuple(
        sorted(
            targets.values(),
            key=lambda target: (target.environment_handle,),
        )
    )


def _environment_targets_from_resolved_refs(
    resolved: Sequence[ResolvedNodeRuntimePackageRef],
) -> tuple[NodeRuntimeEnvironmentTarget, ...]:
    targets: dict[str, NodeRuntimeEnvironmentTarget] = {}
    for item in resolved:
        for target in item.environment_targets:
            targets[target.environment_handle] = target
    return tuple(
        sorted(
            targets.values(),
            key=lambda target: (target.environment_handle,),
        )
    )


def _service_targets_from_config(
    node_config: NodeConfig,
) -> tuple[NodeRuntimeServiceTarget, ...]:
    return tuple(
        sorted(
            (
                NodeRuntimeServiceTarget(service_name=target.service_name)
                for target in node_config.service_targets
            ),
            key=lambda target: target.service_name,
        )
    )


def _service_targets_from_configs(
    node_configs: Sequence[NodeConfig],
) -> tuple[NodeRuntimeServiceTarget, ...]:
    targets: dict[str, NodeRuntimeServiceTarget] = {}
    for node_config in node_configs:
        for target in _service_targets_from_config(node_config):
            targets[target.service_name] = target
    return tuple(sorted(targets.values(), key=lambda target: target.service_name))


def _service_targets_from_resolved_refs(
    resolved: Sequence[ResolvedNodeRuntimePackageRef],
) -> tuple[NodeRuntimeServiceTarget, ...]:
    targets: dict[str, NodeRuntimeServiceTarget] = {}
    for item in resolved:
        for target in item.service_targets:
            targets[target.service_name] = target
    return tuple(sorted(targets.values(), key=lambda target: target.service_name))


def _interface_targets_from_config(
    node_config: NodeConfig,
) -> tuple[NodeRuntimeInterfaceTarget, ...]:
    return tuple(
        sorted(
            (
                NodeRuntimeInterfaceTarget(interface_name=target.interface_name)
                for target in node_config.interface_targets
            ),
            key=lambda target: target.interface_name,
        )
    )


def _interface_targets_from_configs(
    node_configs: Sequence[NodeConfig],
) -> tuple[NodeRuntimeInterfaceTarget, ...]:
    targets: dict[str, NodeRuntimeInterfaceTarget] = {}
    for node_config in node_configs:
        for target in _interface_targets_from_config(node_config):
            targets[target.interface_name] = target
    return tuple(sorted(targets.values(), key=lambda target: target.interface_name))


def _interface_targets_from_resolved_refs(
    resolved: Sequence[ResolvedNodeRuntimePackageRef],
) -> tuple[NodeRuntimeInterfaceTarget, ...]:
    targets: dict[str, NodeRuntimeInterfaceTarget] = {}
    for item in resolved:
        for target in item.interface_targets:
            targets[target.interface_name] = target
    return tuple(sorted(targets.values(), key=lambda target: target.interface_name))


def _reject_duplicate_resolved_refs(
    refs: tuple[ResolvedNodeRuntimePackageRef, ...],
) -> None:
    seen: dict[str, ResolvedNodeRuntimePackageRef] = {}
    for ref in refs:
        key = _resolved_ref_key(ref)
        existing = seen.get(key)
        if existing is not None and existing.manifest_path != ref.manifest_path:
            raise RuntimeError(
                "Conflicting node runtime package refs resolve to the same "
                f"semantic package identity: {key!r}"
            )
        seen[key] = ref


def _resolved_ref_key(ref: ResolvedNodeRuntimePackageRef) -> str:
    if ref.semantic_package_id:
        return f"semantic_package_id:{ref.semantic_package_id}"
    if ref.semantic_root_id is not None:
        return f"semantic_root_id:{ref.semantic_root_id}"
    return f"manifest_path:{ref.manifest_path.as_posix()}"


def _resolve_node_package_ref_read_model(
    *,
    read_model: NodeRuntimePackageRefReadModel | None,
    index: MetaGraphRuntimeIndexSnapshot | None,
    materialized_workspace_root: Path,
    repo_root: str | Path | None,
    aware_root: str | Path | None,
) -> NodeRuntimePackageRefReadModel:
    if read_model is not None and index is not None:
        raise RuntimeError(
            "Node runtime package ref resolution accepts either read_model or "
            "index, not both."
        )
    if read_model is not None:
        return read_model
    if index is not None:
        return _StaticNodeRuntimePackageRefReadModel(
            index=index,
            projection_hash_by_name=_projection_hash_by_name_from_index(index),
        )
    resolved_repo_root = _resolve_meta_read_model_repo_root(
        materialized_workspace_root=materialized_workspace_root,
        repo_root=repo_root,
    )
    return read_workspace_meta_runtime_read_model(
        repo_root=resolved_repo_root,
        aware_root=(
            Path(aware_root).expanduser().resolve()
            if aware_root is not None
            else resolved_repo_root
        ),
        required_projection_names=("NodePackage", "NodeConfig"),
        composite_name="Aware Node Package Ref Resolution Read Model",
    )


def _projection_hash_by_name_from_index(
    index: MetaGraphRuntimeIndexSnapshot,
) -> Mapping[str, str]:
    values: dict[str, str] = {}
    for projection_hash, opg in index.opg_by_hash.items():
        name = str(getattr(opg, "name", "") or "").strip()
        if name and projection_hash:
            values.setdefault(name, projection_hash)
    for opg in tuple(getattr(index.ocg, "object_projection_graphs", ()) or ()):
        name = str(getattr(opg, "name", "") or "").strip()
        projection_hash = str(getattr(opg, "projection_hash", "") or "").strip()
        if name and projection_hash:
            values.setdefault(name, projection_hash)
    return values


def _resolve_meta_read_model_repo_root(
    *,
    materialized_workspace_root: Path,
    repo_root: str | Path | None,
) -> Path:
    if repo_root is not None:
        resolved_repo_root = Path(repo_root).expanduser().resolve()
        if (resolved_repo_root / "modules").is_dir():
            return resolved_repo_root
        raise RuntimeError(
            "Node runtime package ref resolution requires repo_root to contain "
            f"a modules directory: {resolved_repo_root}"
        )
    if (materialized_workspace_root / "modules").is_dir():
        return materialized_workspace_root
    raise RuntimeError(
        "Node runtime package ref resolution requires an explicit read-model "
        "repo_root with a modules directory when materialized_workspace_root "
        "is not a source workspace root."
    )


def _relative_to_root(*, path: Path, root: Path, label: str) -> str:
    resolved_path = path.expanduser().resolve()
    resolved_root = root.expanduser().resolve()
    try:
        relative = resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise RuntimeError(
            "Node runtime package ref path resolved outside materialized "
            f"workspace root: label={label} root={resolved_root} path={resolved_path}"
        ) from exc
    return relative.as_posix() or "."


def _required_uuid(value: str | None, *, label: str) -> UUID:
    parsed = _optional_uuid(value)
    if parsed is None:
        raise RuntimeError(f"Node runtime package ref requires {label}.")
    return parsed


def _optional_uuid(value: str | UUID | None) -> UUID | None:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    stripped = value.strip()
    if not stripped:
        return None
    return UUID(stripped)


def _required_text(value: object, *, label: str) -> str:
    text = str(value).strip() if value is not None else ""
    if not text:
        raise RuntimeError(f"Node runtime package ref requires {label}.")
    return text


def _optional_int(value: object, *, label: str) -> int | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        raise RuntimeError(f"Node runtime package ref expected integer for {label}.")
    if isinstance(value, int):
        return value
    try:
        return int(str(value).strip())
    except (TypeError, ValueError) as exc:
        raise RuntimeError(
            f"Node runtime package ref expected integer for {label}."
        ) from exc


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


__all__ = [
    "NodeRuntimeEnvironmentTarget",
    "NodeRuntimeInterfaceTarget",
    "NodeRuntimePackageDependency",
    "NodeRuntimePackageRef",
    "NodeRuntimePackageRefReadModel",
    "NodeRuntimeServiceTarget",
    "ResolvedNodeRuntimePackageRef",
    "resolve_committed_node_runtime_package_ref",
    "resolve_committed_node_runtime_package_refs",
]
