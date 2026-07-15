from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TypeVar
from uuid import UUID

from aware_interface_ontology.interface.interface_config import InterfaceConfig
from aware_interface_ontology.interface.interface_package import InterfacePackage
from aware_interface_ontology.stable_ids import stable_interface_package_id
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.fs_snapshot_store import FSSnapshotStore
from aware_meta.runtime import (
    MetaGraphRuntimeIndexSnapshot,
    find_meta_graph_projection_hash_by_name,
    reify_meta_orm_root_from_oig_commit,
)
from aware_orm.models.orm_model import ORMModel

_REVISION_FILESYSTEM_MANIFEST_RELATIVE_PATH = Path(
    ".aware/workspace/revision-filesystem.manifest.json"
)
_TRoot = TypeVar("_TRoot", bound=ORMModel)


@dataclass(frozen=True, slots=True)
class InterfaceRuntimePackageRef:
    """Runtime ref for a Workspace-selected InterfacePackage semantic package."""

    family_key: str
    package_kind: str
    package_name: str
    manifest_path: str | Path | None = None
    workspace_package_id: str | None = None
    semantic_package_id: str | None = None
    semantic_head_commit_id: str | None = None
    semantic_branch_id: str | None = None
    semantic_root_kind: str | None = None
    semantic_root_id: str | None = None
    semantic_root_object_instance_graph_commit_id: str | None = None
    source_code_package_id: str | None = None

    @property
    def has_semantic_identity(self) -> bool:
        return bool(_clean(self.semantic_package_id) or _clean(self.semantic_root_id))


@dataclass(frozen=True, slots=True)
class ResolvedInterfaceRuntimePackageRef:
    """Resolved InterfacePackage coordinates from committed WorkspaceRevision truth."""

    package_ref: InterfaceRuntimePackageRef
    materialized_workspace_root: Path
    manifest_path: Path
    manifest_relative_path: str
    package_name: str
    fqn_prefix: str | None
    config_bundle_path: str | None
    interface_package_id: UUID
    interface_config_id: UUID
    interface_config_object_instance_graph_commit_id: UUID
    interface_package: InterfacePackage
    interface_config: InterfaceConfig
    workspace_package_id: str | None = None
    semantic_package_id: str | None = None
    semantic_head_commit_id: str | None = None
    semantic_branch_id: str | None = None
    semantic_root_kind: str | None = None
    semantic_root_id: str | None = None
    semantic_root_object_instance_graph_commit_id: str | None = None
    source_code_package_id: str | None = None


async def resolve_committed_interface_runtime_package_ref(
    *,
    index: MetaGraphRuntimeIndexSnapshot,
    package_ref: InterfaceRuntimePackageRef,
    materialized_workspace_root: str | Path,
) -> ResolvedInterfaceRuntimePackageRef:
    """Resolve a committed InterfacePackage ref without reopening TOML as truth."""

    _validate_interface_ref(package_ref)
    root = Path(materialized_workspace_root).expanduser().resolve()
    _validate_revision_filesystem_root(root)
    branch_id = _required_uuid(
        package_ref.semantic_branch_id,
        label="semantic_branch_id",
    )
    head_commit_id = _required_uuid(
        package_ref.semantic_head_commit_id,
        label="semantic_head_commit_id",
    )
    interface_package_projection_hash = find_meta_graph_projection_hash_by_name(
        index=index,
        projection_name="InterfacePackage",
    )
    store = FSCommitStore()
    package_domain_commit_id = (
        await store.domain_commit_id_for_object_instance_graph_commit_id(
            branch_id=branch_id,
            projection_hash=interface_package_projection_hash,
            object_instance_graph_commit_id=head_commit_id,
        )
    )
    if package_domain_commit_id is None:
        legacy_domain_commit = await store.get_commit(
            branch_id=branch_id,
            projection_hash=interface_package_projection_hash,
            commit_id=head_commit_id,
        )
        if legacy_domain_commit is None:
            raise RuntimeError(
                "Interface runtime package ref semantic_head_commit_id is neither "
                "an indexed ObjectInstanceGraphCommit id nor a domain commit id: "
                f"semantic_head_commit_id={head_commit_id} branch_id={branch_id} "
                f"projection_hash={interface_package_projection_hash}"
            )
        package_domain_commit_id = head_commit_id

    interface_package_id = _optional_uuid(
        package_ref.semantic_package_id
    ) or stable_interface_package_id(name=package_ref.package_name)
    interface_package = await _hydrate_root_from_commit(
        index=index,
        branch_id=branch_id,
        projection_hash=interface_package_projection_hash,
        commit_id=package_domain_commit_id,
        root_id=interface_package_id,
        root_type=InterfacePackage,
        hydrate_portal_targets=True,
    )
    if interface_package is None:
        raise RuntimeError(
            "Interface runtime package ref could not hydrate InterfacePackage "
            "from semantic commit: "
            f"package_name={package_ref.package_name!r} "
            f"semantic_package_id={interface_package_id}"
        )

    _validate_interface_package_ref_pair(
        package_ref=package_ref,
        interface_package=interface_package,
    )
    interface_config_domain_commit_id = _interface_config_domain_commit_id_from_package(
        interface_package
    )
    if interface_config_domain_commit_id is None:
        raise RuntimeError(
            "Interface runtime package ref resolved InterfacePackage without a "
            "hydrated interface_config_object_instance_graph_commit.commit_id: "
            f"interface_package={interface_package.id}"
        )
    interface_config_projection_hash = find_meta_graph_projection_hash_by_name(
        index=index,
        projection_name="InterfaceConfig",
    )
    interface_config = await _hydrate_root_from_commit(
        index=index,
        branch_id=branch_id,
        projection_hash=interface_config_projection_hash,
        commit_id=interface_config_domain_commit_id,
        root_id=interface_package.interface_config_id,
        root_type=InterfaceConfig,
        hydrate_portal_targets=True,
    )
    if interface_config is None:
        raise RuntimeError(
            "Interface runtime package ref could not hydrate pinned "
            f"InterfaceConfig root: interface_config_id={interface_package.interface_config_id} "
            f"commit_id={interface_config_domain_commit_id}"
        )
    _validate_interface_config_ref_pair(
        package_ref=package_ref,
        interface_package=interface_package,
        interface_config=interface_config,
    )

    manifest_path = _resolve_manifest_path_from_interface_package(
        interface_package=interface_package,
        package_ref=package_ref,
        materialized_workspace_root=root,
    )
    root_commit_id = interface_package.interface_config_object_instance_graph_commit_id
    if root_commit_id is None:
        raise RuntimeError(
            "Committed InterfacePackage runtime ref requires "
            "interface_config_object_instance_graph_commit_id."
        )
    return ResolvedInterfaceRuntimePackageRef(
        package_ref=package_ref,
        materialized_workspace_root=root,
        manifest_path=manifest_path,
        manifest_relative_path=_relative_to_root(
            path=manifest_path,
            root=root,
            label="manifest_path",
        ),
        package_name=interface_package.name,
        fqn_prefix=interface_package.fqn_prefix,
        config_bundle_path=interface_package.config_bundle_path,
        interface_package_id=interface_package.id,
        interface_config_id=interface_config.id,
        interface_config_object_instance_graph_commit_id=root_commit_id,
        interface_package=interface_package,
        interface_config=interface_config,
        workspace_package_id=_clean(package_ref.workspace_package_id),
        semantic_package_id=str(interface_package.id),
        semantic_head_commit_id=_clean(package_ref.semantic_head_commit_id),
        semantic_branch_id=_clean(package_ref.semantic_branch_id),
        semantic_root_kind=_clean(package_ref.semantic_root_kind),
        semantic_root_id=_clean(package_ref.semantic_root_id),
        semantic_root_object_instance_graph_commit_id=str(root_commit_id),
        source_code_package_id=(
            str(interface_package.source_code_package_id)
            if interface_package.source_code_package_id is not None
            else _clean(package_ref.source_code_package_id)
        ),
    )


async def resolve_committed_interface_runtime_package_refs(
    *,
    index: MetaGraphRuntimeIndexSnapshot,
    package_refs: Sequence[InterfaceRuntimePackageRef],
    materialized_workspace_root: str | Path,
) -> tuple[ResolvedInterfaceRuntimePackageRef, ...]:
    resolved = tuple(
        [
            await resolve_committed_interface_runtime_package_ref(
                index=index,
                package_ref=package_ref,
                materialized_workspace_root=materialized_workspace_root,
            )
            for package_ref in package_refs
        ]
    )
    _reject_duplicate_resolved_refs(resolved)
    return resolved


def _validate_interface_ref(package_ref: InterfaceRuntimePackageRef) -> None:
    if _clean(package_ref.family_key) != "interface":
        raise RuntimeError(
            "Interface runtime package ref requires family_key='interface': "
            f"{package_ref.family_key!r}"
        )
    if _clean(package_ref.package_kind) != "interface":
        raise RuntimeError(
            "Interface runtime package ref requires package_kind='interface': "
            f"{package_ref.package_kind!r}"
        )
    if not _clean(package_ref.package_name):
        raise RuntimeError("Interface runtime package ref requires a package_name.")
    semantic_root_kind = _clean(package_ref.semantic_root_kind)
    if semantic_root_kind is not None and semantic_root_kind not in {
        "interface_config",
        "interface_package",
    }:
        raise RuntimeError(
            "Interface runtime package ref semantic_root_kind must be "
            "'interface_config' or 'interface_package' when provided: "
            f"{semantic_root_kind!r}"
        )


def _validate_revision_filesystem_root(root: Path) -> None:
    if not root.is_dir():
        raise FileNotFoundError(
            "Interface runtime package ref requires an existing materialized "
            f"workspace root: {root}"
        )
    manifest_path = (root / _REVISION_FILESYSTEM_MANIFEST_RELATIVE_PATH).resolve()
    if not manifest_path.is_file():
        raise FileNotFoundError(
            "Interface runtime package ref requires a WorkspaceRevision "
            f"filesystem manifest at {manifest_path}"
        )


def _resolve_manifest_path_from_interface_package(
    *,
    interface_package: InterfacePackage,
    package_ref: InterfaceRuntimePackageRef,
    materialized_workspace_root: Path,
) -> Path:
    raw_manifest_path = _clean(interface_package.manifest_relative_path)
    if raw_manifest_path is None:
        raw_manifest_path = (
            str(package_ref.manifest_path)
            if package_ref.manifest_path is not None
            else None
        )
    if raw_manifest_path is None or not raw_manifest_path.strip():
        raise RuntimeError(
            "Committed InterfacePackage runtime ref requires "
            "InterfacePackage.manifest_relative_path or package_ref.manifest_path."
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
    if not resolved_manifest_path.is_file():
        raise FileNotFoundError(
            "Committed InterfacePackage manifest path does not exist inside "
            f"the materialized workspace root: {resolved_manifest_path}"
        )
    return resolved_manifest_path


def _reject_duplicate_resolved_refs(
    refs: tuple[ResolvedInterfaceRuntimePackageRef, ...],
) -> None:
    seen: dict[str, ResolvedInterfaceRuntimePackageRef] = {}
    for ref in refs:
        key = _resolved_ref_key(ref)
        existing = seen.get(key)
        if existing is not None and existing.manifest_path != ref.manifest_path:
            raise RuntimeError(
                "Conflicting interface runtime package refs resolve to the same "
                f"semantic package identity: {key!r}"
            )
        seen[key] = ref


def _resolved_ref_key(ref: ResolvedInterfaceRuntimePackageRef) -> str:
    if ref.semantic_package_id is not None:
        return f"semantic_package_id:{ref.semantic_package_id}"
    if ref.semantic_root_id is not None:
        return f"semantic_root_id:{ref.semantic_root_id}"
    return f"manifest_path:{ref.manifest_path.as_posix()}"


def _validate_interface_package_ref_pair(
    *,
    package_ref: InterfaceRuntimePackageRef,
    interface_package: InterfacePackage,
) -> None:
    if interface_package.name != package_ref.package_name:
        raise RuntimeError(
            "Interface runtime package ref package_name does not match "
            f"InterfacePackage: ref={package_ref.package_name!r} "
            f"interface_package={interface_package.name!r}"
        )
    semantic_package_id = _optional_uuid(package_ref.semantic_package_id)
    if semantic_package_id is not None and semantic_package_id != interface_package.id:
        raise RuntimeError(
            "Interface runtime package ref semantic_package_id does not match "
            f"InterfacePackage: ref={semantic_package_id} "
            f"interface_package={interface_package.id}"
        )
    pinned_commit_id = _optional_uuid(
        package_ref.semantic_root_object_instance_graph_commit_id
    )
    if (
        pinned_commit_id is not None
        and pinned_commit_id
        != interface_package.interface_config_object_instance_graph_commit_id
    ):
        raise RuntimeError(
            "Interface runtime package ref semantic_root_object_instance_graph_commit_id "
            "does not match InterfacePackage pin: "
            f"ref={pinned_commit_id} "
            f"interface_package={interface_package.interface_config_object_instance_graph_commit_id}"
        )


def _validate_interface_config_ref_pair(
    *,
    package_ref: InterfaceRuntimePackageRef,
    interface_package: InterfacePackage,
    interface_config: InterfaceConfig,
) -> None:
    if interface_config.id != interface_package.interface_config_id:
        raise RuntimeError(
            "InterfacePackage points at a different InterfaceConfig than the "
            f"hydrated interface root: package={interface_package.interface_config_id} "
            f"interface_config={interface_config.id}"
        )
    semantic_root_kind = _clean(package_ref.semantic_root_kind)
    semantic_root_id = _optional_uuid(package_ref.semantic_root_id)
    if semantic_root_id is None:
        return
    expected_root_id = (
        interface_config.id
        if semantic_root_kind == "interface_config"
        else interface_package.id
    )
    if semantic_root_id != expected_root_id:
        raise RuntimeError(
            "Interface runtime package ref semantic_root_id does not match "
            f"{semantic_root_kind or 'interface_package'} root: "
            f"ref={semantic_root_id} expected={expected_root_id}"
        )


def _interface_config_domain_commit_id_from_package(
    interface_package: InterfacePackage,
) -> UUID | None:
    interface_config_commit = (
        interface_package.interface_config_object_instance_graph_commit
    )
    if interface_config_commit is None:
        return None
    return interface_config_commit.commit_id


async def _hydrate_root_from_commit(
    *,
    index: MetaGraphRuntimeIndexSnapshot,
    branch_id: UUID,
    projection_hash: str,
    commit_id: UUID,
    root_id: UUID,
    root_type: type[_TRoot],
    hydrate_portal_targets: bool,
) -> _TRoot | None:
    del hydrate_portal_targets
    return await reify_meta_orm_root_from_oig_commit(
        index=index,
        branch_id=branch_id,
        projection_hash=projection_hash,
        projection_name=getattr(root_type, "__name__", ""),
        commit_id=commit_id,
        root_id=root_id,
        root_type=root_type,
        commit_store=FSCommitStore(),
        snapshot_store=FSSnapshotStore(),
    )


def _relative_to_root(*, path: Path, root: Path, label: str) -> str:
    resolved_path = path.expanduser().resolve()
    resolved_root = root.expanduser().resolve()
    try:
        relative = resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise RuntimeError(
            "Interface runtime package ref path resolved outside materialized "
            f"workspace root: label={label} root={resolved_root} path={resolved_path}"
        ) from exc
    return relative.as_posix() or "."


def _required_uuid(value: str | None, *, label: str) -> UUID:
    parsed = _optional_uuid(value)
    if parsed is None:
        raise RuntimeError(f"Interface runtime package ref requires {label}.")
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


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


__all__ = [
    "InterfaceRuntimePackageRef",
    "ResolvedInterfaceRuntimePackageRef",
    "resolve_committed_interface_runtime_package_ref",
    "resolve_committed_interface_runtime_package_refs",
]
