from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import os
from pathlib import Path
from typing import Any, Iterator, Mapping
from uuid import NAMESPACE_URL, UUID, uuid5

from aware_environment_sdk import EnvironmentGeneratedApiClient
from aware_experience.materialization import (
    ExperiencePackageInstallScope,
    materialize_experience_package_from_manifest,
)
from aware_experience.materialization.branches import (
    derive_experience_reference_branch_id,
)
from aware_experience.manifest.loader import load_aware_experience_toml_spec
from aware_experience.manifest.spec import AwareExperienceDependencyKind
from aware_experience.package_ref_resolution import (
    ExperienceRuntimePackageRef,
    resolve_committed_experience_runtime_package_refs,
)
from aware_environment.stable_ids import (
    stable_boot_process_id,
    stable_boot_thread_id,
)
from aware_service_service.config import (
    ServiceHostAppConfig,
    ServiceHostExperiencePackageRef,
)


@dataclass(frozen=True, slots=True)
class LocalExperienceReferenceMaterialization:
    experience_name: str
    experience_names: tuple[str, ...]
    package_name: str
    reference_branch_ids_by_name: Mapping[str, UUID]


@dataclass(frozen=True, slots=True)
class ExperienceReferenceBranchResolution:
    branch_ids_by_name: Mapping[str, UUID]
    commit_store_root: Path | None


async def resolve_experience_reference_branch_resolution(
    *,
    config: ServiceHostAppConfig,
    index: Any,
    runtime: Any | None = None,
    environment_id: UUID | None = None,
    actor_id: UUID | None = None,
    environment_api_client: EnvironmentGeneratedApiClient | None = None,
    local_workspace_root: Path | None = None,
) -> ExperienceReferenceBranchResolution:
    package_refs = config.experience_package_refs
    branch_ids_by_name: dict[str, UUID] = {}
    commit_store_root: Path | None = None
    committed_package_refs: list[ServiceHostExperiencePackageRef] = []
    local_package_ref_toml_paths: list[Path] = []
    for package_ref in package_refs:
        runtime_ref = experience_runtime_package_ref_from_config_ref(package_ref)
        if has_committed_experience_package_ref_coordinates(runtime_ref):
            committed_package_refs.append(package_ref)
            continue
        if package_ref.manifest_path is None:
            raise RuntimeError(
                "ServiceHostApp Experience package refs require either "
                "committed semantic coordinates or manifest_path."
            )
        local_package_ref_toml_paths.append(package_ref.manifest_path)
    if committed_package_refs:
        materialized_root = config.artifact_root
        if materialized_root is None:
            raise RuntimeError(
                "ServiceHostApp requires artifact.root "
                "when Experience package refs are configured."
            )
        commit_store_root = merge_experience_reference_commit_store_root(
            existing=commit_store_root,
            candidate=materialized_root,
            source="committed Experience package refs",
        )
        resolved_refs = await resolve_committed_experience_runtime_package_refs(
            index=index,
            package_refs=tuple(
                experience_runtime_package_ref_from_config_ref(package_ref)
                for package_ref in committed_package_refs
            ),
            materialized_workspace_root=materialized_root,
        )
        for resolved_ref in resolved_refs:
            branch_id = UUID(resolved_ref.semantic_branch_id)
            for name in (
                resolved_ref.experience_name,
                resolved_ref.package_name,
                resolved_ref.package_name.replace("-", "_"),
                *getattr(resolved_ref, "projection_experience_names", ()),
            ):
                record_experience_reference_branch_id(
                    branch_ids_by_name=branch_ids_by_name,
                    name=name,
                    branch_id=branch_id,
                )
    local_toml_paths = _dedupe_paths(
        (
            *config.reference_packages.experience_toml_paths,
            *local_package_ref_toml_paths,
        )
    )
    if local_toml_paths:
        if local_workspace_root is None:
            raise RuntimeError(
                "ServiceHostApp local Experience TOML refs require a local "
                "workspace root."
            )
        commit_store_root = merge_experience_reference_commit_store_root(
            existing=commit_store_root,
            candidate=local_workspace_root,
            source="local Experience TOML refs",
        )
        if runtime is None or environment_id is None:
            raise RuntimeError(
                "ServiceHostApp local Experience TOML refs require the hosted "
                "Meta activation runtime context."
            )
        process_id = stable_boot_process_id(environment_id=environment_id)
        thread_id = stable_boot_thread_id(environment_id=environment_id)
        local_toml_catalog = _local_experience_toml_catalog(local_toml_paths)
        for toml_path in local_toml_paths:
            resolved_toml_path = toml_path.expanduser().resolve()
            if not resolved_toml_path.is_file():
                raise RuntimeError(
                    "ServiceHostApp local Experience TOML was not found: "
                    f"{resolved_toml_path}"
                )
            base_branch_id = local_experience_package_base_branch_id(
                workspace_root=local_workspace_root,
                experience_toml_path=resolved_toml_path,
            )
            materialized = await materialize_local_experience_reference_lanes(
                runtime=runtime,
                index=index,
                actor_id=actor_id,
                environment_id=environment_id,
                process_id=process_id,
                thread_id=thread_id,
                branch_id=base_branch_id,
                workspace_root=local_workspace_root,
                experience_toml_path=resolved_toml_path,
                experience_toml_paths_by_package_name=local_toml_catalog,
                environment_api_client=environment_api_client,
            )
            for (
                name,
                reference_branch_id,
            ) in materialized.reference_branch_ids_by_name.items():
                record_experience_reference_branch_id(
                    branch_ids_by_name=branch_ids_by_name,
                    name=name,
                    branch_id=reference_branch_id,
                )
    return ExperienceReferenceBranchResolution(
        branch_ids_by_name=branch_ids_by_name,
        commit_store_root=commit_store_root,
    )


def experience_runtime_package_ref_from_config_ref(
    package_ref: ServiceHostExperiencePackageRef,
) -> ExperienceRuntimePackageRef:
    return ExperienceRuntimePackageRef(
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


def has_committed_experience_package_ref_coordinates(
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


def local_experience_package_base_branch_id(
    *,
    workspace_root: Path,
    experience_toml_path: Path,
) -> UUID:
    try:
        relative_path = (
            experience_toml_path.expanduser()
            .resolve()
            .relative_to(workspace_root.expanduser().resolve())
        )
    except ValueError:
        relative_path = experience_toml_path.expanduser().resolve()
    return uuid5(
        NAMESPACE_URL,
        "aware:service-host:local-experience-package:"
        f"{relative_path.as_posix().casefold()}",
    )


async def materialize_local_experience_reference_lanes(
    *,
    runtime: Any,
    index: Any,
    actor_id: UUID | None,
    environment_id: UUID,
    process_id: UUID,
    thread_id: UUID,
    branch_id: UUID,
    workspace_root: Path,
    experience_toml_path: Path,
    experience_toml_paths_by_package_name: Mapping[str, Path] | None = None,
    environment_api_client: EnvironmentGeneratedApiClient | None = None,
) -> LocalExperienceReferenceMaterialization:
    materialized_items: list[tuple[Any, UUID]] = []
    reference_branch_ids_by_name: dict[str, UUID] = {}
    seen_package_names: set[str] = set()

    def _record_reference_branch_ids_for_item(
        *, item: Any, item_branch_id: UUID
    ) -> None:
        for name in (item.experience_name, *item.experience_names):
            token = (name or "").strip()
            if not token:
                continue
            record_experience_reference_branch_id(
                branch_ids_by_name=reference_branch_ids_by_name,
                name=token,
                branch_id=derive_experience_reference_branch_id(
                    base_branch_id=item_branch_id,
                    experience_name=token,
                ),
            )
        for name in (
            item.experience_package.name,
            item.experience_package.name.replace("-", "_"),
        ):
            token = (name or "").strip()
            if not token:
                continue
            record_experience_reference_branch_id(
                branch_ids_by_name=reference_branch_ids_by_name,
                name=token,
                branch_id=derive_experience_reference_branch_id(
                    base_branch_id=item_branch_id,
                    experience_name=token,
                ),
            )

    async def _materialize_with_dependencies(
        toml_path: Path,
        *,
        package_branch_id: UUID,
        install_scope: ExperiencePackageInstallScope,
    ) -> Any:
        spec = load_aware_experience_toml_spec(toml_path=toml_path)
        package_name = spec.experience.package_name.strip()
        package_key = package_name.casefold()
        if package_key in seen_package_names:
            return None
        seen_package_names.add(package_key)
        for dependency in spec.dependencies:
            if dependency.kind is not AwareExperienceDependencyKind.experience_package:
                continue
            dependency_path = None
            if experience_toml_paths_by_package_name is not None:
                dependency_path = experience_toml_paths_by_package_name.get(
                    dependency.package_name.strip().casefold()
                )
            if dependency_path is None:
                dependency_path = resolve_local_experience_dependency_toml_path(
                    workspace_root=workspace_root,
                    source_experience_toml_path=toml_path,
                    package_name=dependency.package_name,
                )
            dependency_branch_id = local_experience_package_base_branch_id(
                workspace_root=workspace_root,
                experience_toml_path=dependency_path,
            )
            await _materialize_with_dependencies(
                dependency_path,
                package_branch_id=dependency_branch_id,
                install_scope=ExperiencePackageInstallScope.dependency_reference,
            )
        materialized = await materialize_experience_package_from_manifest(
            runtime=runtime,
            index=index,
            actor_id=actor_id,
            environment_id=environment_id,
            process_id=process_id,
            thread_id=thread_id,
            branch_id=package_branch_id,
            workspace_root=workspace_root,
            experience_toml_path=toml_path,
            allow_unresolved_projection_experiences=True,
            install_scope=install_scope,
            projection_reference_branch_ids_by_name=reference_branch_ids_by_name,
            environment_api_client=environment_api_client,
        )
        materialized_items.append((materialized, package_branch_id))
        _record_reference_branch_ids_for_item(
            item=materialized,
            item_branch_id=package_branch_id,
        )
        return materialized

    with _experience_materialization_runtime_persistence_context():
        materialized = await _materialize_with_dependencies(
            experience_toml_path,
            package_branch_id=branch_id,
            install_scope=ExperiencePackageInstallScope.activation,
        )
    if materialized is None:
        raise RuntimeError(
            "ServiceHostApp local Experience TOML materialization skipped primary "
            f"package unexpectedly: {experience_toml_path}"
        )
    experience_names: list[str] = []
    for item, _ in materialized_items:
        for name in (item.experience_name, *item.experience_names):
            token = (name or "").strip()
            if token and token not in experience_names:
                experience_names.append(token)
    return LocalExperienceReferenceMaterialization(
        experience_name=materialized.experience_name,
        experience_names=tuple(experience_names),
        package_name=materialized.experience_package.name,
        reference_branch_ids_by_name=reference_branch_ids_by_name,
    )


def _local_experience_toml_catalog(
    toml_paths: tuple[Path, ...],
) -> Mapping[str, Path]:
    catalog: dict[str, Path] = {}
    for toml_path in toml_paths:
        resolved_path = toml_path.expanduser().resolve()
        spec = load_aware_experience_toml_spec(toml_path=resolved_path)
        package_name = spec.experience.package_name.strip()
        package_key = package_name.casefold()
        existing = catalog.get(package_key)
        if existing is not None and existing != resolved_path:
            raise RuntimeError(
                "ServiceHostApp local Experience package catalog is ambiguous: "
                f"package_name={package_name!r} matches="
                f"{(existing.as_posix(), resolved_path.as_posix())}"
            )
        catalog[package_key] = resolved_path
    return catalog


def resolve_local_experience_dependency_toml_path(
    *,
    workspace_root: Path,
    source_experience_toml_path: Path,
    package_name: str,
) -> Path:
    package_key = (package_name or "").strip()
    if not package_key:
        raise RuntimeError("Experience dependency requires package_name.")
    sibling_path = (
        source_experience_toml_path.expanduser().resolve().parent.parent
        / package_key
        / "aware.experience.toml"
    )
    if sibling_path.is_file():
        return sibling_path.resolve()
    matches: list[Path] = []
    for toml_path in sorted(
        (workspace_root.expanduser().resolve() / "experiences").glob(
            "*/aware.experience.toml"
        )
    ):
        spec = load_aware_experience_toml_spec(toml_path=toml_path)
        if spec.experience.package_name.strip().casefold() == package_key.casefold():
            matches.append(toml_path.resolve())
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise RuntimeError(
            "ServiceHostApp local Experience dependency resolved ambiguously: "
            f"package_name={package_key!r} matches={tuple(path.as_posix() for path in matches)}"
        )
    raise RuntimeError(
        "ServiceHostApp local Experience dependency TOML was not found: "
        f"package_name={package_key!r} source={source_experience_toml_path}"
    )


def record_experience_reference_branch_id(
    *,
    branch_ids_by_name: dict[str, UUID],
    name: str | None,
    branch_id: UUID,
) -> None:
    token = str(name or "").strip()
    if not token:
        return
    existing = branch_ids_by_name.get(token.casefold())
    if existing is not None and existing != branch_id:
        raise RuntimeError(
            "ServiceHostApp resolved conflicting Experience package refs "
            f"for experience={token!r}."
        )
    branch_ids_by_name[token] = branch_id
    branch_ids_by_name[token.casefold()] = branch_id


def merge_experience_reference_commit_store_root(
    *,
    existing: Path | None,
    candidate: Path,
    source: str,
) -> Path:
    resolved_candidate = candidate.expanduser().resolve()
    if existing is None:
        return resolved_candidate
    resolved_existing = existing.expanduser().resolve()
    if resolved_existing == resolved_candidate:
        return resolved_existing
    raise RuntimeError(
        "ServiceHostApp Experience reference activation requires one committed "
        "lane store root, but resolved refs span multiple roots: "
        f"existing={resolved_existing} source={source} candidate={resolved_candidate}."
    )


def _dedupe_paths(paths: tuple[Path, ...]) -> tuple[Path, ...]:
    deduped: list[Path] = []
    for path in paths:
        resolved = path.expanduser().resolve()
        if resolved not in deduped:
            deduped.append(resolved)
    return tuple(deduped)


@contextmanager
def _experience_materialization_runtime_persistence_context() -> Iterator[None]:
    previous_backend = os.environ.get("AWARE_PERSISTENCE_BACKEND")
    os.environ["AWARE_PERSISTENCE_BACKEND"] = "fs"
    try:
        yield
    finally:
        if previous_backend is None:
            os.environ.pop("AWARE_PERSISTENCE_BACKEND", None)
        else:
            os.environ["AWARE_PERSISTENCE_BACKEND"] = previous_backend


__all__ = [
    "ExperienceReferenceBranchResolution",
    "LocalExperienceReferenceMaterialization",
    "derive_experience_reference_branch_id",
    "experience_runtime_package_ref_from_config_ref",
    "has_committed_experience_package_ref_coordinates",
    "local_experience_package_base_branch_id",
    "materialize_local_experience_reference_lanes",
    "merge_experience_reference_commit_store_root",
    "record_experience_reference_branch_id",
    "resolve_experience_reference_branch_resolution",
    "resolve_local_experience_dependency_toml_path",
]
