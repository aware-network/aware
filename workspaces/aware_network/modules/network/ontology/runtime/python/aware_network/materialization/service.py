from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Protocol, TypeVar
from uuid import UUID

from aware_code.package.snapshot_commit import commit_code_package_text_snapshot
from aware_code.stable_ids import (
    code_package_source_config_key,
    stable_code_package_config_id,
    stable_code_package_id,
)
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.package.code_package import CodePackage

from aware_node.manifest.loader import load_aware_node_toml_spec
from aware_node.manifest.spec import AwareNodeTomlSpec
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.fs_snapshot_store import FSSnapshotStore
from aware_meta.runtime.graph_context import MetaGraphRuntimeIndexSnapshot
from aware_meta.runtime.oig_hydration import reify_meta_orm_root_from_oig_commit
from aware_meta.runtime.read_model_provider import (
    read_workspace_meta_runtime_read_model,
)
from aware_network_ontology.network.network_node_config import NetworkNodeConfig
from aware_network_ontology.network.network_node_package import NetworkNodePackage
from aware_network_ontology.stable_ids import (
    stable_network_node_config_id,
    stable_network_node_package_id,
)
from aware_orm.models.orm_model import ORMModel

from .snapshot_commit import (
    commit_network_node_config_manifest_snapshot,
    commit_network_node_package_manifest_snapshot,
)

_TRoot = TypeVar("_TRoot", bound=ORMModel)


class _NetworkNodePackageMaterializationReadModel(Protocol):
    @property
    def index(self) -> MetaGraphRuntimeIndexSnapshot: ...

    def projection_hash_for_name(self, projection_name: str) -> str: ...


def _source_code_package_config_id() -> UUID:
    return stable_code_package_config_id(
        config_key=code_package_source_config_key(
            manifest_kind="aware_toml",
            surface="runtime",
        )
    )


@dataclass(frozen=True, slots=True)
class _NetworkNodeWorkspaceSnapshot:
    repo_root: Path
    package_root: Path
    spec_path: Path
    spec: AwareNodeTomlSpec
    sources_root: Path
    source_files: tuple[Path, ...]


@dataclass(frozen=True, slots=True)
class NetworkNodePackageMaterializationSpec:
    node_toml_path: Path
    workspace_root: Path
    package_root: Path
    sources_root: Path
    manifest_spec: AwareNodeTomlSpec
    package_name: str
    package_fqn_prefix: str
    config_name: str
    config_description: str | None
    source_files: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class NetworkNodePackageMaterializationResult:
    node_toml_path: Path
    workspace_root: Path
    manifest_spec: AwareNodeTomlSpec
    network_node_config: NetworkNodeConfig
    network_node_package: NetworkNodePackage
    source_files: tuple[str, ...]
    source_code_package_id: UUID | None
    network_node_config_commit_id: UUID | None
    network_node_config_head_commit_id: UUID | None
    package_commit_id: UUID | None
    package_head_commit_id: UUID | None


def resolve_network_node_package_materialization_spec(
    *,
    node_toml_path: Path,
    workspace_root: Path,
) -> NetworkNodePackageMaterializationSpec:
    snapshot = _build_network_node_workspace_snapshot(
        node_toml_path=node_toml_path,
        workspace_root=workspace_root,
    )
    package_name = (snapshot.spec.node.package_name or "").strip()
    if not package_name:
        raise RuntimeError(
            "Network node package materialization requires non-empty [node].package_name in aware.node.toml: "
            + str(snapshot.spec_path)
        )
    package_fqn_prefix = (snapshot.spec.node.fqn_prefix or "").strip()
    if not package_fqn_prefix:
        raise RuntimeError(
            "Network node package materialization requires non-empty [node].fqn_prefix in aware.node.toml: "
            + str(snapshot.spec_path)
        )
    return NetworkNodePackageMaterializationSpec(
        node_toml_path=snapshot.spec_path,
        workspace_root=snapshot.repo_root,
        package_root=snapshot.package_root,
        sources_root=snapshot.sources_root,
        manifest_spec=snapshot.spec,
        package_name=package_name,
        package_fqn_prefix=package_fqn_prefix,
        config_name=package_name,
        config_description=_normalize_optional_text(snapshot.spec.node.description),
        source_files=tuple(path.as_posix() for path in snapshot.source_files),
    )


async def materialize_network_node_package_from_manifest(
    *,
    runtime: object,
    index: object,
    actor_id: UUID | None,
    environment_id: UUID,
    process_id: UUID,
    thread_id: UUID,
    branch_id: UUID,
    workspace_root: Path,
    node_toml_path: Path,
    repo_root: Path | None = None,
    semantic_ontology_package_catalog: Mapping[str, object] | None = None,
) -> NetworkNodePackageMaterializationResult:
    spec = resolve_network_node_package_materialization_spec(
        node_toml_path=node_toml_path,
        workspace_root=workspace_root,
    )
    source_code_package_config_id = _source_code_package_config_id()
    expected_source_code_package_id = stable_code_package_id(
        code_package_config_id=source_code_package_config_id,
        package_name=spec.package_name,
        language=CodeLanguage.aware.value,
    )
    expected_network_node_config_id = stable_network_node_config_id(
        name=spec.config_name
    )
    expected_network_node_package_id = stable_network_node_package_id(
        name=spec.package_name
    )

    read_model = _resolve_network_node_package_materialization_read_model(
        workspace_root=workspace_root,
        repo_root=repo_root,
        semantic_ontology_package_catalog=semantic_ontology_package_catalog,
    )
    meta_index = read_model.index
    snapshot_index = _snapshot_commit_index(meta_index)

    code_package_projection_hash = read_model.projection_hash_for_name("CodePackage")
    network_node_config_projection_hash = read_model.projection_hash_for_name(
        "NetworkNodeConfig"
    )
    network_node_package_projection_hash = read_model.projection_hash_for_name(
        "NetworkNodePackage"
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

    _ = (runtime, index, environment_id, process_id, thread_id)

    source_texts_by_relative_path: dict[str, str] = {}
    for source_file in spec.source_files:
        source_path = (spec.package_root / source_file).resolve()
        source_texts_by_relative_path[source_file] = source_path.read_text(
            encoding="utf-8"
        )

    code_package_snapshot = await commit_code_package_text_snapshot(
        index=snapshot_index,
        actor_id=actor_id,
        branch_id=branch_id,
        projection_hash=code_package_projection_hash,
        code_package_config_id=source_code_package_config_id,
        package_name=spec.package_name,
        language=CodeLanguage.aware,
        surface="runtime",
        manifest_kind="aware_toml",
        manifest_relative_path=manifest_relative_path,
        package_root=package_root_relative,
        sources_root=sources_root_relative,
        fqn_prefix=spec.package_fqn_prefix,
        source_texts_by_relative_path=source_texts_by_relative_path,
    )
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
            "Network node package materialization could not hydrate canonical CodePackage after build: "
            + f"package_name={spec.package_name!r}"
        )
    if code_package.id != code_package_snapshot.code_package.id:
        raise RuntimeError(
            "Network node package materialization committed CodePackage with unexpected id: "
            f"expected={code_package_snapshot.code_package.id} actual={code_package.id}"
        )
    _validate_code_package_materialization_result(code_package=code_package, spec=spec)

    network_node_config_snapshot = await commit_network_node_config_manifest_snapshot(
        index=snapshot_index,
        actor_id=actor_id,
        branch_id=branch_id,
        projection_hash=network_node_config_projection_hash,
        name=spec.config_name,
        description=spec.config_description,
    )
    network_node_config = await _hydrate_lane_root_from_head(
        index=meta_index,
        branch_id=branch_id,
        projection_hash=network_node_config_projection_hash,
        projection_name="NetworkNodeConfig",
        root_id=expected_network_node_config_id,
        root_type=NetworkNodeConfig,
    )
    if network_node_config is None:
        raise RuntimeError(
            "Network node package materialization could not hydrate canonical NetworkNodeConfig after build: "
            + f"package_name={spec.package_name!r}"
        )
    _validate_network_node_config_materialization_result(
        network_node_config=network_node_config,
        spec=spec,
    )

    network_node_package_snapshot = await commit_network_node_package_manifest_snapshot(
        index=snapshot_index,
        actor_id=actor_id,
        branch_id=branch_id,
        projection_hash=network_node_package_projection_hash,
        name=spec.package_name,
        network_node_config_id=network_node_config.id,
        source_code_package_id=code_package.id,
    )
    network_node_package = await _hydrate_lane_root_from_head(
        index=meta_index,
        branch_id=branch_id,
        projection_hash=network_node_package_projection_hash,
        projection_name="NetworkNodePackage",
        root_id=expected_network_node_package_id,
        root_type=NetworkNodePackage,
    )
    if network_node_package is None:
        raise RuntimeError(
            "Network node package materialization could not hydrate canonical NetworkNodePackage after build: "
            + f"package_name={spec.package_name!r}"
        )
    _validate_network_node_package_materialization_result(
        network_node_package=network_node_package,
        network_node_config=network_node_config,
        code_package=code_package,
        spec=spec,
    )

    return NetworkNodePackageMaterializationResult(
        node_toml_path=spec.node_toml_path,
        workspace_root=spec.workspace_root,
        manifest_spec=spec.manifest_spec,
        network_node_config=network_node_config,
        network_node_package=network_node_package,
        source_files=spec.source_files,
        source_code_package_id=network_node_package.source_code_package_id,
        network_node_config_commit_id=network_node_config_snapshot.commit_id,
        network_node_config_head_commit_id=network_node_config_snapshot.head_commit_id,
        package_commit_id=network_node_package_snapshot.commit_id,
        package_head_commit_id=network_node_package_snapshot.head_commit_id,
    )


def _build_network_node_workspace_snapshot(
    *,
    node_toml_path: Path,
    workspace_root: Path,
) -> _NetworkNodeWorkspaceSnapshot:
    resolved_node_toml_path = node_toml_path.resolve()
    if not resolved_node_toml_path.exists():
        raise FileNotFoundError(f"aware.node.toml not found: {resolved_node_toml_path}")
    package_root = resolved_node_toml_path.parent.resolve()
    repo_root = workspace_root.resolve()
    spec = load_aware_node_toml_spec(toml_path=resolved_node_toml_path)
    sources_root = (package_root / spec.build.sources_dir).resolve()
    _assert_within(
        base=package_root, candidate=sources_root, label="[build].sources_dir"
    )
    if not sources_root.exists():
        raise FileNotFoundError(
            f"Network node sources_dir does not exist: {sources_root} (from {resolved_node_toml_path})"
        )
    if not sources_root.is_dir():
        raise NotADirectoryError(
            f"Network node sources_dir must be a directory: {sources_root}"
        )

    files_by_rel: dict[str, Path] = {}
    for include in spec.build.include_paths:
        pattern = (include or "").strip()
        if not pattern:
            continue
        for candidate in sources_root.glob(pattern):
            if not candidate.is_file():
                continue
            resolved = candidate.resolve()
            _assert_within(base=sources_root, candidate=resolved, label="include_paths")
            rel_from_sources = resolved.relative_to(sources_root).as_posix()
            if _is_excluded(
                rel_path=rel_from_sources, exclude_patterns=spec.build.exclude_paths
            ):
                continue
            rel_from_package = resolved.relative_to(package_root).as_posix()
            files_by_rel[rel_from_package] = Path(rel_from_package)

    ordered_source_files = tuple(files_by_rel[key] for key in sorted(files_by_rel))
    return _NetworkNodeWorkspaceSnapshot(
        repo_root=repo_root,
        package_root=package_root,
        spec_path=resolved_node_toml_path,
        spec=spec,
        sources_root=sources_root,
        source_files=ordered_source_files,
    )


def _validate_code_package_materialization_result(
    *,
    code_package: CodePackage,
    spec: NetworkNodePackageMaterializationSpec,
) -> None:
    expected_source_code_package_id = stable_code_package_id(
        code_package_config_id=_source_code_package_config_id(),
        package_name=spec.package_name,
        language=CodeLanguage.aware.value,
    )
    if code_package.id != expected_source_code_package_id:
        raise RuntimeError(
            "Network node package materialization resolved CodePackage with unexpected id: "
            + f"expected={expected_source_code_package_id} actual={code_package.id}"
        )
    if code_package.surface != "runtime":
        raise RuntimeError(
            "Network node package materialization resolved CodePackage with unexpected surface: "
            + f"expected={"runtime"} actual={code_package.surface}"
        )
    if (
        getattr(code_package, "code_package_config_id", None)
        != _source_code_package_config_id()
    ):
        raise RuntimeError(
            "Network node package materialization resolved CodePackage with unexpected CodePackageConfig: "
            + f"expected={_source_code_package_config_id()} "
            + f"actual={getattr(code_package, 'code_package_config_id', None)}"
        )


def _validate_network_node_config_materialization_result(
    *,
    network_node_config: NetworkNodeConfig,
    spec: NetworkNodePackageMaterializationSpec,
) -> None:
    expected_network_node_config_id = stable_network_node_config_id(
        name=spec.config_name
    )
    if network_node_config.id != expected_network_node_config_id:
        raise RuntimeError(
            "Network node package materialization resolved NetworkNodeConfig with unexpected id: "
            + f"expected={expected_network_node_config_id} actual={network_node_config.id}"
        )
    if (network_node_config.name or "").strip() != spec.config_name:
        raise RuntimeError(
            "Network node package materialization resolved NetworkNodeConfig with unexpected name: "
            + f"expected={spec.config_name!r} actual={network_node_config.name!r}"
        )
    if (
        _normalize_optional_text(network_node_config.description)
        != spec.config_description
    ):
        raise RuntimeError(
            "Network node package materialization resolved NetworkNodeConfig with unexpected description: "
            + f"expected={spec.config_description!r} actual={network_node_config.description!r}"
        )


def _validate_network_node_package_materialization_result(
    *,
    network_node_package: NetworkNodePackage,
    network_node_config: NetworkNodeConfig,
    code_package: CodePackage,
    spec: NetworkNodePackageMaterializationSpec,
) -> None:
    expected_network_node_package_id = stable_network_node_package_id(
        name=spec.package_name
    )
    if network_node_package.id != expected_network_node_package_id:
        raise RuntimeError(
            "Network node package materialization resolved NetworkNodePackage with unexpected id: "
            + f"expected={expected_network_node_package_id} actual={network_node_package.id}"
        )
    if (network_node_package.name or "").strip() != spec.package_name:
        raise RuntimeError(
            "Network node package materialization resolved NetworkNodePackage with unexpected name: "
            + f"expected={spec.package_name!r} actual={network_node_package.name!r}"
        )
    if network_node_package.network_node_config_id != network_node_config.id:
        raise RuntimeError(
            "Network node package materialization resolved NetworkNodePackage with unexpected "
            + "network_node_config_id: "
            + f"expected={network_node_config.id} actual={network_node_package.network_node_config_id}"
        )
    if network_node_package.source_code_package_id != code_package.id:
        raise RuntimeError(
            "Network node package materialization resolved NetworkNodePackage with unexpected "
            + "source_code_package_id: "
            + f"expected={code_package.id} actual={network_node_package.source_code_package_id}"
        )


def _assert_within(*, base: Path, candidate: Path, label: str) -> None:
    base_resolved = base.resolve()
    candidate_resolved = candidate.resolve()
    if (
        candidate_resolved == base_resolved
        or base_resolved in candidate_resolved.parents
    ):
        return
    raise RuntimeError(
        "Network node package materialization path resolved outside package boundary: "
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
            "Network node package materialization path resolved outside workspace root: "
            + f"label={label} root={resolved_root} path={resolved_path}"
        ) from exc
    relative_text = relative.as_posix()
    return relative_text or "."


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _resolve_network_node_package_materialization_read_model(
    *,
    workspace_root: Path,
    repo_root: Path | None = None,
    semantic_ontology_package_catalog: Mapping[str, object] | None = None,
) -> _NetworkNodePackageMaterializationReadModel:
    resolved_workspace_root = workspace_root.expanduser().resolve()
    read_model_repo_root = (
        repo_root.expanduser().resolve()
        if repo_root is not None
        else resolved_workspace_root
    )
    if not (read_model_repo_root / "modules").is_dir():
        raise RuntimeError(
            "Network node package materialization requires an explicit read-model "
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
        required_projection_names=(
            "CodePackage",
            "NetworkNodeConfig",
            "NetworkNodePackage",
        ),
        semantic_ontology_package_catalog=semantic_ontology_package_catalog,
        composite_name="Aware Network Node Package Materialization Context",
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


__all__ = [
    "NetworkNodePackageMaterializationResult",
    "NetworkNodePackageMaterializationSpec",
    "materialize_network_node_package_from_manifest",
    "resolve_network_node_package_materialization_spec",
]
