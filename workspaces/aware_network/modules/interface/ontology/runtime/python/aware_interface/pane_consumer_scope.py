from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from aware_experience.compiler.workspace import ExperienceWorkspace
from aware_experience.projection.compiler import load_projection_experience_ownership_from_sources
from aware_interface.compiler import load_interface_ownership_from_sources
from aware_experience.manifest import load_aware_experience_toml_spec
from aware_interface.manifest import (
    AwareInterfaceDependencyKind,
    load_aware_interface_toml_spec,
    load_aware_pane_toml_spec,
)


@dataclass(frozen=True, slots=True)
class InterfaceExperienceTruth:
    observables: dict[str, frozenset[str]]


@dataclass(frozen=True, slots=True)
class PaneConsumerScope:
    interface_name: str
    interface_package_name: str
    manifest_path: Path
    declared_experience_package_names: tuple[str, ...]
    experience_catalog: dict[str, InterfaceExperienceTruth]


@dataclass(frozen=True, slots=True)
class InterfaceDependencyScope:
    interface_package_name: str
    manifest_path: Path
    declared_experience_package_names: tuple[str, ...]
    experience_catalog: dict[str, InterfaceExperienceTruth]


@dataclass(frozen=True, slots=True)
class WorkspacePaneCatalogEntry:
    view_refs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class WorkspacePaneCatalogResolution:
    pane_catalog: dict[str, WorkspacePaneCatalogEntry]
    declared_workspace: bool


@dataclass(frozen=True, slots=True)
class WorkspaceManifestPathsResolution:
    manifest_paths: tuple[Path, ...]
    declared_workspace: bool


def _ancestor_roots(*, start: Path) -> tuple[Path, ...]:
    cursor = start.resolve()
    if cursor.is_file():
        cursor = cursor.parent
    return tuple([cursor, *cursor.parents])


def resolve_workspace_manifest_paths(
    *,
    start: Path,
    directory_name: str,
    filename: str,
) -> WorkspaceManifestPathsResolution:
    for root in _ancestor_roots(start=start):
        search_root = (root / directory_name).resolve()
        if not search_root.is_dir():
            continue
        matches = tuple(
            sorted(
                path.resolve()
                for path in search_root.glob(f"*/{filename}")
                if path.is_file()
            )
        )
        if matches:
            return WorkspaceManifestPathsResolution(
                manifest_paths=matches,
                declared_workspace=False,
            )
    return WorkspaceManifestPathsResolution(
        manifest_paths=(),
        declared_workspace=False,
    )


def _find_workspace_manifest_paths(
    *,
    start: Path,
    directory_name: str,
    filename: str,
) -> tuple[Path, ...]:
    resolution = resolve_workspace_manifest_paths(
        start=start,
        directory_name=directory_name,
        filename=filename,
    )
    return resolution.manifest_paths


def _is_excluded(*, rel_path: str, exclude_patterns: list[str]) -> bool:
    token = PurePosixPath(rel_path)
    for raw_pattern in exclude_patterns:
        pattern = (raw_pattern or "").strip()
        if pattern and token.match(pattern):
            return True
    return False


def _collect_package_source_files(
    *,
    package_root: Path,
    sources_dir: str,
    include_paths: list[str],
    exclude_paths: list[str],
) -> tuple[Path, ...]:
    sources_root = (package_root / sources_dir).resolve()
    if not sources_root.exists() or not sources_root.is_dir():
        return ()

    files_by_rel: dict[str, Path] = {}
    for include in include_paths:
        pattern = (include or "").strip()
        if not pattern:
            continue
        for candidate in sources_root.glob(pattern):
            if not candidate.is_file():
                continue
            resolved = candidate.resolve()
            try:
                rel_from_sources = resolved.relative_to(sources_root).as_posix()
                rel_from_package = resolved.relative_to(package_root).as_posix()
            except ValueError:
                continue
            if _is_excluded(rel_path=rel_from_sources, exclude_patterns=exclude_paths):
                continue
            files_by_rel[rel_from_package] = Path(rel_from_package)
    return tuple(files_by_rel[key] for key in sorted(files_by_rel))


def _find_experience_manifest_by_package_name(*, start: Path, package_name: str) -> Path | None:
    package_key = package_name.casefold()
    for manifest_path in _find_workspace_manifest_paths(
        start=start,
        directory_name="experiences",
        filename="aware.experience.toml",
    ):
        try:
            spec = load_aware_experience_toml_spec(toml_path=manifest_path)
        except Exception:
            continue
        if (spec.experience.package_name or "").strip().casefold() == package_key:
            return manifest_path
    return None


def _load_experience_catalog_from_manifest(
    *,
    manifest_path: Path,
) -> dict[str, InterfaceExperienceTruth]:
    try:
        snapshot = ExperienceWorkspace.from_toml(
            toml_path=manifest_path,
            repo_root=manifest_path.parent,
        ).build_snapshot()
        ownership = load_projection_experience_ownership_from_sources(
            package_root=snapshot.package_root,
            source_files=snapshot.source_files,
        )
    except Exception:
        return {}

    return {
        experience.name.casefold(): InterfaceExperienceTruth(
            observables={
                observable.key.casefold(): frozenset(view.key.casefold() for view in observable.views)
                for observable in experience.observables
            }
        )
        for experience in ownership
    }


def _merge_experience_catalogs(
    *,
    catalogs: tuple[dict[str, InterfaceExperienceTruth], ...],
) -> dict[str, InterfaceExperienceTruth]:
    merged: dict[str, dict[str, set[str]]] = {}
    for catalog in catalogs:
        for experience_key, truth in catalog.items():
            observable_catalog = merged.setdefault(experience_key, {})
            for observable_key, view_keys in truth.observables.items():
                observable_catalog.setdefault(observable_key, set()).update(view_keys)
    return {
        experience_key: InterfaceExperienceTruth(
            observables={
                observable_key: frozenset(sorted(view_keys))
                for observable_key, view_keys in observable_catalog.items()
            }
        )
        for experience_key, observable_catalog in merged.items()
    }


def _load_interface_experience_catalog(*, manifest_path: Path) -> dict[str, InterfaceExperienceTruth]:
    spec = load_aware_interface_toml_spec(toml_path=manifest_path)
    package_root = manifest_path.parent.resolve()
    dependency_manifests = tuple(
        manifest_candidate
        for dependency in spec.dependencies
        if dependency.kind == AwareInterfaceDependencyKind.experience_package
        for manifest_candidate in (
            _find_experience_manifest_by_package_name(
                start=package_root,
                package_name=dependency.package_name.strip(),
            ),
        )
        if manifest_candidate is not None
    )
    if not dependency_manifests:
        return {}
    return _merge_experience_catalogs(
        catalogs=tuple(
            _load_experience_catalog_from_manifest(manifest_path=dependency_manifest)
            for dependency_manifest in dependency_manifests
        )
    )


def _load_interface_source_files(*, manifest_path: Path) -> tuple[Path, ...]:
    spec = load_aware_interface_toml_spec(toml_path=manifest_path)
    package_root = manifest_path.parent.resolve()
    return _collect_package_source_files(
        package_root=package_root,
        sources_dir=spec.build.sources_dir,
        include_paths=spec.build.include_paths,
        exclude_paths=spec.build.exclude_paths,
    )


def _declared_dependency_package_names(
    *,
    spec,
    kind: AwareInterfaceDependencyKind,
) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                dependency.package_name.strip()
                for dependency in spec.dependencies
                if dependency.kind == kind and dependency.package_name.strip()
            },
            key=str.casefold,
        )
    )


def load_interface_dependency_scope(*, manifest_path: Path) -> InterfaceDependencyScope:
    spec = load_aware_interface_toml_spec(toml_path=manifest_path)
    package_root = manifest_path.parent.resolve()
    return InterfaceDependencyScope(
        interface_package_name=(spec.interface.package_name or "").strip() or package_root.name,
        manifest_path=manifest_path.resolve(),
        declared_experience_package_names=_declared_dependency_package_names(
            spec=spec,
            kind=AwareInterfaceDependencyKind.experience_package,
        ),
        experience_catalog=_load_interface_experience_catalog(manifest_path=manifest_path),
    )


def load_workspace_pane_catalog(*, start: Path) -> WorkspacePaneCatalogResolution:
    manifest_resolution = resolve_workspace_manifest_paths(
        start=start,
        directory_name="panes",
        filename="aware.pane.toml",
    )
    pane_catalog: dict[str, WorkspacePaneCatalogEntry] = {}
    for manifest_path in manifest_resolution.manifest_paths:
        try:
            spec = load_aware_pane_toml_spec(toml_path=manifest_path)
        except Exception:
            continue
        package_root = manifest_path.parent.resolve()
        source_files = _collect_package_source_files(
            package_root=package_root,
            sources_dir=spec.build.sources_dir,
            include_paths=spec.build.include_paths,
            exclude_paths=spec.build.exclude_paths,
        )
        if not source_files:
            continue
        try:
            ownership = load_interface_ownership_from_sources(
                package_root=package_root,
                source_files=source_files,
            )
        except Exception:
            continue
        for pane in ownership.pane_ownership:
            pane_catalog[pane.name.casefold()] = WorkspacePaneCatalogEntry(
                view_refs=tuple(sorted(view.ref for view in pane.views)),
            )
    return WorkspacePaneCatalogResolution(
        pane_catalog=pane_catalog,
        declared_workspace=manifest_resolution.declared_workspace,
    )


def load_workspace_pane_consumer_scopes(*, start: Path) -> dict[str, tuple[PaneConsumerScope, ...]]:
    manifests = _find_workspace_manifest_paths(
        start=start,
        directory_name="interfaces",
        filename="aware.interface.toml",
    )
    scopes_by_pane: dict[str, list[PaneConsumerScope]] = {}
    for manifest_path in manifests:
        try:
            package_root = manifest_path.parent.resolve()
            source_files = _load_interface_source_files(manifest_path=manifest_path)
            if not source_files:
                continue
            ownership = load_interface_ownership_from_sources(
                package_root=package_root,
                source_files=source_files,
            )
            dependency_scope = load_interface_dependency_scope(manifest_path=manifest_path)
        except Exception:
            continue

        for interface in ownership.interface_ownership:
            scope = PaneConsumerScope(
                interface_name=interface.name,
                interface_package_name=dependency_scope.interface_package_name,
                manifest_path=dependency_scope.manifest_path,
                declared_experience_package_names=dependency_scope.declared_experience_package_names,
                experience_catalog=dependency_scope.experience_catalog,
            )
            for pane in interface.panes:
                scopes_by_pane.setdefault(pane.pane_name.casefold(), []).append(scope)

    return {
        pane_name: tuple(
            sorted(
                scopes,
                key=lambda item: (
                    item.interface_package_name.casefold(),
                    item.interface_name.casefold(),
                    item.manifest_path.as_posix(),
                ),
            )
        )
        for pane_name, scopes in scopes_by_pane.items()
    }


__all__ = [
    "InterfaceDependencyScope",
    "InterfaceExperienceTruth",
    "PaneConsumerScope",
    "WorkspacePaneCatalogEntry",
    "WorkspacePaneCatalogResolution",
    "WorkspaceManifestPathsResolution",
    "load_interface_dependency_scope",
    "load_workspace_pane_catalog",
    "resolve_workspace_manifest_paths",
    "load_workspace_pane_consumer_scopes",
]
