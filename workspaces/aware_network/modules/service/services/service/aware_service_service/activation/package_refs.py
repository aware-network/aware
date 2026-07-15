from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import replace
from pathlib import Path
from typing import Any

from aware_service_runtime.package_ref_resolution import (
    ResolvedServiceRuntimePackageRef,
    ServiceRuntimePackageRef,
    resolve_committed_service_runtime_package_refs,
    resolve_service_runtime_package_refs,
    resolve_service_runtime_package_refs_from_manifest_paths,
)

from aware_service_service.config import (
    ServiceHostAppConfig,
    ServiceHostImplementationPackageRef,
)

CommittedServiceRuntimePackageRefResolver = Callable[
    ...,
    Awaitable[tuple[ResolvedServiceRuntimePackageRef, ...]],
]


def resolve_implementation_package_refs(
    *,
    config: ServiceHostAppConfig,
) -> tuple[ResolvedServiceRuntimePackageRef, ...]:
    package_refs = tuple(
        service_runtime_package_ref_from_config_ref(package_ref)
        for package_ref in config.implementation_packages.package_refs
    )
    if not package_refs:
        return ()
    committed_refs = tuple(
        package_ref
        for package_ref in package_refs
        if has_committed_package_ref_coordinates(package_ref)
    )
    if committed_refs:
        if len(committed_refs) != len(package_refs):
            raise RuntimeError(
                "ServiceHostApp implementation package refs cannot mix committed "
                "semantic coordinates and TOML-only refs in one activation."
            )
        if config.implementation_packages.toml_paths:
            raise RuntimeError(
                "ServiceHostApp committed implementation package refs cannot be "
                "combined with implementation TOML paths."
            )
        return ()
    artifact_root = config.artifact.root
    if artifact_root is not None:
        resolved = resolve_service_runtime_package_refs_from_manifest_paths(
            package_refs=package_refs_with_artifact_root_manifest_paths(
                package_refs=package_refs,
                artifact_root=artifact_root,
            ),
        )
        validate_package_ref_toml_paths(
            toml_paths=config.implementation_packages.toml_paths,
            resolved_package_refs=resolved,
        )
        return resolved
    materialized_root = config.artifact_root
    if materialized_root is None:
        resolved = resolve_service_runtime_package_refs_from_manifest_paths(
            package_refs=package_refs,
        )
        validate_package_ref_toml_paths(
            toml_paths=config.implementation_packages.toml_paths,
            resolved_package_refs=resolved,
        )
        return resolved
    resolved = resolve_service_runtime_package_refs(
        package_refs=package_refs,
        materialized_workspace_root=materialized_root,
    )
    validate_package_ref_toml_paths(
        toml_paths=config.implementation_packages.toml_paths,
        resolved_package_refs=resolved,
    )
    return resolved


def package_refs_with_artifact_root_manifest_paths(
    *,
    package_refs: tuple[ServiceRuntimePackageRef, ...],
    artifact_root: Path,
) -> tuple[ServiceRuntimePackageRef, ...]:
    resolved_root = artifact_root.expanduser().resolve()
    normalized_refs: list[ServiceRuntimePackageRef] = []
    for package_ref in package_refs:
        manifest_path = package_ref.manifest_path
        if manifest_path is None:
            normalized_refs.append(package_ref)
            continue
        path = Path(manifest_path).expanduser()
        if not path.is_absolute():
            path = resolved_root / path
        normalized_refs.append(replace(package_ref, manifest_path=path.resolve()))
    return tuple(normalized_refs)


def implementation_package_toml_paths(
    *,
    config: ServiceHostAppConfig,
    resolved_package_refs: tuple[ResolvedServiceRuntimePackageRef, ...],
) -> tuple[Path, ...]:
    if resolved_package_refs:
        return tuple(
            ref.manifest_path
            for ref in resolved_package_refs
            if ref.manifest_path is not None
        )
    return tuple(
        path.expanduser().resolve()
        for path in config.implementation_packages.toml_paths
    )


def has_committed_package_ref_coordinates(
    package_ref: Any,
) -> bool:
    has_oig_commit = bool(
        package_ref.semantic_object_instance_graph_commit_id
        and str(package_ref.semantic_object_instance_graph_commit_id).strip()
    )
    has_branch = bool(
        package_ref.semantic_branch_id and str(package_ref.semantic_branch_id).strip()
    )
    has_legacy_head = bool(
        package_ref.semantic_head_commit_id
        and str(package_ref.semantic_head_commit_id).strip()
    )
    return has_oig_commit or (has_branch and has_legacy_head)


def requires_remote_environment_sdk(config: ServiceHostAppConfig) -> bool:
    if config.artifact_root is None:
        return False
    package_refs = tuple(
        service_runtime_package_ref_from_config_ref(package_ref)
        for package_ref in config.implementation_packages.package_refs
    )
    return any(has_committed_package_ref_coordinates(ref) for ref in package_refs)


async def resolve_committed_implementation_package_refs(
    *,
    config: ServiceHostAppConfig,
    index: Any,
    committed_ref_resolver: CommittedServiceRuntimePackageRefResolver = (
        resolve_committed_service_runtime_package_refs
    ),
) -> tuple[ResolvedServiceRuntimePackageRef, ...] | None:
    package_refs = tuple(
        service_runtime_package_ref_from_config_ref(package_ref)
        for package_ref in config.implementation_packages.package_refs
    )
    if not package_refs:
        return None
    committed_refs = tuple(
        package_ref
        for package_ref in package_refs
        if has_committed_package_ref_coordinates(package_ref)
    )
    if not committed_refs:
        return None
    if len(committed_refs) != len(package_refs):
        raise RuntimeError(
            "ServiceHostApp implementation package refs cannot mix committed "
            "semantic coordinates and TOML-only refs in one activation."
        )
    materialized_root = config.artifact_root
    if materialized_root is None:
        raise RuntimeError(
            "ServiceHostApp requires artifact.root "
            "when committed implementation package_refs are configured."
        )
    resolved = await committed_ref_resolver(
        index=index,
        package_refs=package_refs,
        materialized_workspace_root=materialized_root,
        dependency_workspace_roots=(
            (config.kernel_repo_root,) if config.kernel_repo_root is not None else ()
        ),
    )
    validate_package_ref_toml_paths(
        toml_paths=config.implementation_packages.toml_paths,
        resolved_package_refs=resolved,
    )
    return resolved


def service_runtime_package_ref_from_config_ref(
    package_ref: ServiceHostImplementationPackageRef,
) -> ServiceRuntimePackageRef:
    return ServiceRuntimePackageRef(
        family_key=package_ref.family_key,
        package_kind=package_ref.package_kind,
        package_name=package_ref.package_name,
        manifest_path=package_ref.manifest_path,
        workspace_package_id=package_ref.workspace_package_id,
        semantic_package_id=package_ref.semantic_package_id,
        semantic_object_instance_graph_commit_id=(
            package_ref.semantic_object_instance_graph_commit_id
        ),
        semantic_head_commit_id=package_ref.semantic_head_commit_id,
        semantic_branch_id=package_ref.semantic_branch_id,
        semantic_root_kind=package_ref.semantic_root_kind,
        semantic_root_id=package_ref.semantic_root_id,
        semantic_root_object_instance_graph_commit_id=(
            package_ref.semantic_root_object_instance_graph_commit_id
        ),
        source_code_package_id=package_ref.source_code_package_id,
    )


def validate_package_ref_toml_paths(
    *,
    toml_paths: tuple[Path, ...],
    resolved_package_refs: tuple[ResolvedServiceRuntimePackageRef, ...],
) -> None:
    if not toml_paths:
        return
    configured_paths = tuple(path.expanduser().resolve() for path in toml_paths)
    resolved_paths = tuple(
        ref.manifest_path
        for ref in resolved_package_refs
        if ref.manifest_path is not None
    )
    if len(resolved_paths) != len(resolved_package_refs):
        raise RuntimeError(
            "ServiceHostApp committed implementation package refs cannot be "
            "validated through implementation TOML paths."
        )
    if frozenset(configured_paths) != frozenset(resolved_paths):
        raise RuntimeError(
            "ServiceHostApp implementation package_refs do not match configured "
            "implementation TOML paths: "
            f"package_ref_paths={[path.as_posix() for path in resolved_paths]!r} "
            f"toml_paths={[path.as_posix() for path in configured_paths]!r}"
        )


def committed_package_source_path(
    *,
    package_ref: ResolvedServiceRuntimePackageRef,
) -> Path | None:
    if package_ref.manifest_path is not None:
        return package_ref.manifest_path.expanduser().resolve()
    raw_manifest_relative_path = str(package_ref.manifest_relative_path or "").strip()
    if not raw_manifest_relative_path:
        return None
    path = (
        package_ref.materialized_workspace_root
        / Path(raw_manifest_relative_path).expanduser()
    ).resolve()
    try:
        path.relative_to(package_ref.materialized_workspace_root.resolve())
    except ValueError as exc:
        raise RuntimeError(
            "Committed Service package manifest escapes the revision root: "
            f"manifest_relative_path={raw_manifest_relative_path!r}"
        ) from exc
    return path


__all__ = [
    "CommittedServiceRuntimePackageRefResolver",
    "committed_package_source_path",
    "has_committed_package_ref_coordinates",
    "implementation_package_toml_paths",
    "package_refs_with_artifact_root_manifest_paths",
    "requires_remote_environment_sdk",
    "resolve_committed_implementation_package_refs",
    "resolve_implementation_package_refs",
    "service_runtime_package_ref_from_config_ref",
    "validate_package_ref_toml_paths",
]
