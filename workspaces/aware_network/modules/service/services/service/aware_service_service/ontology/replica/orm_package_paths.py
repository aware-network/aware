from __future__ import annotations

from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
import sys
import tomllib
from typing import Protocol


class OntologyPackageRequirement(Protocol):
    package_name: str
    fqn_prefix: str
    role: str
    requirement_mode: str


@dataclass(frozen=True, slots=True)
class ResolvedOntologyOrmPackagePath:
    package_name: str
    fqn_prefix: str
    import_root: str
    path: Path
    manifest_path: Path


@dataclass(frozen=True, slots=True)
class _OntologyPackageManifest:
    package_name: str
    fqn_prefix: str
    dependencies: tuple[str, ...]
    manifest_path: Path
    orm_package_root: Path | None

    @property
    def import_root(self) -> str:
        return f"{self.fqn_prefix}_ontology_orm_models"


def resolve_required_ontology_orm_package_paths(
    *,
    repo_root: Path,
    ontology_packages: Iterable[OntologyPackageRequirement],
) -> tuple[ResolvedOntologyOrmPackagePath, ...]:
    requirements = tuple(ontology_packages)
    if not requirements:
        return ()

    resolved_repo_root = repo_root.expanduser().resolve()
    catalog = _discover_ontology_package_manifests(repo_root=resolved_repo_root)
    ordered: list[_OntologyPackageManifest] = []
    seen_packages: set[str] = set()

    def visit(
        *,
        package_name: str,
        expected_fqn_prefix: str | None,
        strict: bool,
    ) -> None:
        normalized_package_name = package_name.strip()
        if not normalized_package_name:
            return
        normalized_package_key = normalized_package_name.casefold()
        if normalized_package_key in seen_packages:
            return
        manifest_matches = catalog.get(normalized_package_key, ())
        if not manifest_matches:
            if strict:
                raise RuntimeError(
                    "ServiceHost could not resolve required ontology package "
                    f"manifest for {normalized_package_name!r} under "
                    f"{resolved_repo_root}."
                )
            return
        if len(manifest_matches) > 1:
            first, second = manifest_matches[:2]
            raise RuntimeError(
                "ServiceHost ontology replica ORM package catalog found duplicate "
                "ontology package authority under the selected artifact root: "
                f"package_name={normalized_package_name!r} "
                f"first={first.manifest_path} second={second.manifest_path}."
            )
        manifest = manifest_matches[0]
        normalized_expected_fqn = (expected_fqn_prefix or "").strip()
        if normalized_expected_fqn and normalized_expected_fqn != manifest.fqn_prefix:
            raise RuntimeError(
                "ServiceHost resolved ontology package manifest with a different "
                "fqn_prefix than the ServicePackage requirement: "
                f"package_name={normalized_package_name!r} "
                f"expected={normalized_expected_fqn!r} "
                f"actual={manifest.fqn_prefix!r} "
                f"manifest={manifest.manifest_path}."
            )
        seen_packages.add(normalized_package_key)
        ordered.append(manifest)
        for dependency_name in manifest.dependencies:
            visit(
                package_name=dependency_name,
                expected_fqn_prefix=None,
                strict=strict,
            )

    for requirement in requirements:
        visit(
            package_name=requirement.package_name,
            expected_fqn_prefix=requirement.fqn_prefix,
            strict=_is_required_ontology_package(requirement),
        )

    resolved_paths: list[ResolvedOntologyOrmPackagePath] = []
    seen_roots: set[Path] = set()
    for manifest in ordered:
        orm_package_root = manifest.orm_package_root
        if orm_package_root is None:
            raise RuntimeError(
                "ServiceHost resolved ontology package "
                f"{manifest.package_name!r}, but its generated ORM model package "
                f"{manifest.import_root!r} was not found under "
                f"{manifest.manifest_path.parent}."
            )
        resolved_root = orm_package_root.resolve()
        if resolved_root in seen_roots:
            continue
        seen_roots.add(resolved_root)
        resolved_paths.append(
            ResolvedOntologyOrmPackagePath(
                package_name=manifest.package_name,
                fqn_prefix=manifest.fqn_prefix,
                import_root=manifest.import_root,
                path=resolved_root,
                manifest_path=manifest.manifest_path,
            )
        )
    return tuple(resolved_paths)


@contextmanager
def expose_ontology_orm_package_paths(
    paths: Iterable[ResolvedOntologyOrmPackagePath | Path],
) -> Iterator[None]:
    roots = _dedupe_path_values(
        path.path if isinstance(path, ResolvedOntologyOrmPackagePath) else path
        for path in paths
    )
    inserted: list[str] = []
    try:
        for root in reversed(roots):
            location = root.as_posix()
            if location in sys.path:
                continue
            sys.path.insert(0, location)
            inserted.append(location)
        yield
    finally:
        for location in inserted:
            try:
                sys.path.remove(location)
            except ValueError:
                pass


@contextmanager
def expose_required_service_ontology_orm_package_paths(
    *,
    repo_root: Path,
    ontology_packages: Iterable[OntologyPackageRequirement],
) -> Iterator[tuple[ResolvedOntologyOrmPackagePath, ...]]:
    paths = resolve_required_ontology_orm_package_paths(
        repo_root=repo_root,
        ontology_packages=ontology_packages,
    )
    with expose_ontology_orm_package_paths(paths):
        yield paths


def _discover_ontology_package_manifests(
    *,
    repo_root: Path,
) -> dict[str, tuple[_OntologyPackageManifest, ...]]:
    manifests: dict[str, list[_OntologyPackageManifest]] = {}
    for manifest_path in _candidate_ontology_manifest_paths(repo_root=repo_root):
        manifest = _read_ontology_package_manifest(manifest_path=manifest_path)
        if manifest is None:
            continue
        package_key = manifest.package_name.casefold()
        manifests.setdefault(package_key, []).append(manifest)
    return {
        package_key: tuple(package_manifests)
        for package_key, package_manifests in manifests.items()
    }


def _candidate_ontology_manifest_paths(
    *,
    repo_root: Path,
) -> tuple[Path, ...]:
    paths: list[Path] = []
    seen: set[Path] = set()
    for search_root in _ontology_manifest_search_roots(repo_root=repo_root):
        patterns = _ontology_manifest_patterns_for_root(search_root=search_root)
        for pattern in patterns:
            for manifest_path in sorted(search_root.glob(pattern)):
                resolved = manifest_path.resolve()
                if resolved in seen:
                    continue
                seen.add(resolved)
                paths.append(resolved)
    return tuple(paths)


def _ontology_manifest_search_roots(*, repo_root: Path) -> tuple[Path, ...]:
    roots: list[Path] = []
    seen: set[Path] = set()

    def add(root: Path) -> None:
        resolved = root.expanduser().resolve()
        if resolved in seen:
            return
        seen.add(resolved)
        roots.append(resolved)

    add(repo_root)
    for dependency_root in _declared_workspace_dependency_roots(
        workspace_root=repo_root,
    ):
        add(dependency_root)
    return tuple(roots)


def _ontology_manifest_patterns_for_root(*, search_root: Path) -> tuple[str, ...]:
    patterns = [
        "workspaces/*/modules/*/structure/ontology/aware.toml",
        "workspaces/*/modules/*/ontology/structure/aware.toml",
    ]
    if _allow_direct_workspace_module_scan(workspace_root=search_root):
        patterns.extend(
            (
                "modules/*/structure/ontology/aware.toml",
                "modules/*/ontology/structure/aware.toml",
            )
        )
    return tuple(patterns)


def _allow_direct_workspace_module_scan(*, workspace_root: Path) -> bool:
    handle = _workspace_handle(workspace_root=workspace_root)
    if handle is None:
        return False
    if handle == "aware":
        return False
    return True


def _declared_workspace_dependency_roots(*, workspace_root: Path) -> tuple[Path, ...]:
    payload = _read_workspace_toml(workspace_root=workspace_root)
    workspace = payload.get("workspace") if isinstance(payload, dict) else None
    if not isinstance(workspace, dict):
        return ()
    dependencies = workspace.get("dependencies")
    if not isinstance(dependencies, list):
        return ()
    roots: list[Path] = []
    seen: set[Path] = set()
    for dependency in dependencies:
        if not isinstance(dependency, dict):
            continue
        if str(dependency.get("kind") or "").strip() != "workspace":
            continue
        source = str(dependency.get("source") or "").strip()
        prefix = "workspace://"
        if not source.startswith(prefix):
            continue
        handle = source.removeprefix(prefix).strip()
        if not handle:
            continue
        for candidate in _workspace_dependency_root_candidates(
            workspace_root=workspace_root,
            handle=handle,
        ):
            resolved = candidate.resolve()
            if resolved in seen:
                continue
            if not (resolved / "aware.workspace.toml").is_file():
                continue
            seen.add(resolved)
            roots.append(resolved)
            break
    return tuple(roots)


def _workspace_dependency_root_candidates(
    *,
    workspace_root: Path,
    handle: str,
) -> tuple[Path, ...]:
    return (
        workspace_root.parent / handle,
        workspace_root / "workspaces" / handle,
        workspace_root.parent / "workspaces" / handle,
        *(parent / "workspaces" / handle for parent in workspace_root.parents),
    )


def _workspace_handle(*, workspace_root: Path) -> str | None:
    payload = _read_workspace_toml(workspace_root=workspace_root)
    workspace = payload.get("workspace") if isinstance(payload, dict) else None
    if not isinstance(workspace, dict):
        return None
    handle = str(workspace.get("handle") or "").strip()
    return handle or None


def _read_workspace_toml(*, workspace_root: Path) -> dict[str, object]:
    workspace_toml = workspace_root / "aware.workspace.toml"
    try:
        payload = tomllib.loads(workspace_toml.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return {}
    return payload


def _read_ontology_package_manifest(
    *,
    manifest_path: Path,
) -> _OntologyPackageManifest | None:
    try:
        payload = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return None
    package = payload.get("package")
    if not isinstance(package, dict):
        return None
    if str(package.get("kind") or "").strip() != "ontology":
        return None
    package_name = str(package.get("package_name") or "").strip()
    fqn_prefix = str(package.get("fqn_prefix") or "").strip()
    if not package_name or not fqn_prefix:
        return None
    return _OntologyPackageManifest(
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        dependencies=_read_dependency_package_names(payload),
        manifest_path=manifest_path,
        orm_package_root=_resolve_orm_package_root(
            manifest_path=manifest_path,
            import_root=f"{fqn_prefix}_ontology_orm_models",
        ),
    )


def _read_dependency_package_names(payload: object) -> tuple[str, ...]:
    if not isinstance(payload, dict):
        return ()
    raw_dependencies = payload.get("dependencies")
    if not isinstance(raw_dependencies, list):
        return ()
    names: list[str] = []
    seen: set[str] = set()
    for dependency in raw_dependencies:
        if not isinstance(dependency, dict):
            continue
        package_name = str(dependency.get("package_name") or "").strip()
        if not package_name or package_name in seen:
            continue
        seen.add(package_name)
        names.append(package_name)
    return tuple(names)


def _resolve_orm_package_root(
    *,
    manifest_path: Path,
    import_root: str,
) -> Path | None:
    for candidate in _orm_package_root_candidates(manifest_path=manifest_path):
        if (candidate / import_root).is_dir():
            return candidate
    return None


def _orm_package_root_candidates(
    *,
    manifest_path: Path,
) -> tuple[Path, ...]:
    ontology_dir = manifest_path.parent
    return (
        ontology_dir.parent / "ontology_orm_models" / "python",
        ontology_dir / "python" / "orm_models",
    )


def _is_required_ontology_package(requirement: OntologyPackageRequirement) -> bool:
    return str(getattr(requirement, "requirement_mode", "required") or "").strip() in {
        "",
        "required",
    }


def _dedupe_path_values(paths: Iterable[Path]) -> tuple[Path, ...]:
    resolved_paths: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        resolved = path.expanduser().resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        resolved_paths.append(resolved)
    return tuple(resolved_paths)


__all__ = [
    "OntologyPackageRequirement",
    "ResolvedOntologyOrmPackagePath",
    "expose_ontology_orm_package_paths",
    "expose_required_service_ontology_orm_package_paths",
    "resolve_required_ontology_orm_package_paths",
]
