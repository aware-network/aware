"""Module discovery and compile-preflight stages."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import cast
import tomllib

from aware_workspace_operator.models import (
    DiscoveredPackage,
    DuplicatePackage,
    MissingDependency,
    ModuleBootstrapResult,
    WorkspaceBootstrapOptions,
    WorkspacePreflightState,
)


_PACKAGE_MANIFEST_FILENAMES = frozenset(
    {
        "aware.toml",
        "aware.api.toml",
        "aware.attention.toml",
        "aware.experience.toml",
        "aware.interface.toml",
        "aware.node.toml",
        "aware.ontology.toml",
        "aware.pane.toml",
        "aware.sdk.toml",
        "aware.service.toml",
    }
)
_PACKAGE_TABLE_NAMES = (
    "package",
    "ontology",
    "api",
    "service",
    "sdk",
    "experience",
    "attention",
    "interface",
    "pane",
    "node",
)
_SKIP_DISCOVERY_PARTS = frozenset(
    {
        ".aware",
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".tmp",
        ".venv",
        "__pycache__",
        "_aware",
        "docs",
        "node_modules",
        "tests",
        "venv",
    }
)
_SKIP_DISCOVERY_ROOTS = frozenset(
    {
        "build",
        "dist",
        "targets",
    }
)


@dataclass(frozen=True)
class _PackageManifestSummary:
    package_name: str
    dependency_package_names: tuple[str, ...]


def run_preflight_stage(
    *,
    request: WorkspaceBootstrapOptions,
    repo_root: Path,
) -> WorkspacePreflightState:
    """Discover modules, validate dependency closure, and compile preflight workflows."""

    if request.bootstrap_mode == "remote-managed":
        return _run_remote_managed_preflight(request=request, repo_root=repo_root)
    if request.bootstrap_mode != "full-local":
        raise ValueError(f"Unsupported bootstrap mode: {request.bootstrap_mode!r}")

    try:
        from aware_code.module_manifest.loader import load_aware_module_spec
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "Workspace bootstrap requires the monorepo uv workspace "
            "(aware-grammar + aware-meta) to be importable. "
            f"Error: {exc}"
        ) from exc

    selected_module_ids = resolve_module_ids(
        repo_root=repo_root,
        requested_modules=request.requested_module_ids,
    )

    package_path_by_name: dict[str, Path] = {}
    duplicate_packages: dict[str, list[Path]] = {}
    for aware_toml_path in _discover_package_manifests(repo_root):
        try:
            package_summary = _load_package_manifest_summary(aware_toml_path)
        except Exception:
            continue
        if package_summary is None:
            continue
        package_name = package_summary.package_name
        if not package_name:
            continue
        existing = package_path_by_name.get(package_name)
        if existing is None:
            package_path_by_name[package_name] = aware_toml_path
            continue
        duplicate_packages.setdefault(package_name, []).append(aware_toml_path)

    results: list[ModuleBootstrapResult] = []
    all_missing: list[MissingDependency] = []
    has_errors = False

    for module_id in selected_module_ids:
        module_root = (repo_root / "modules" / module_id).resolve()
        module_toml = (module_root / "aware.module.toml").resolve()
        module_errors: list[str] = []
        missing: list[MissingDependency] = []
        package_names: list[str] = []

        if not module_toml.exists():
            module_errors.append(f"aware.module.toml not found: {module_toml}")
            has_errors = True
            results.append(
                ModuleBootstrapResult(
                    module_id=module_id,
                    package_names=[],
                    missing_dependencies=[],
                    errors=module_errors,
                )
            )
            continue

        try:
            module_spec = load_aware_module_spec(toml_path=module_toml)
        except Exception as exc:
            module_errors.append(f"Failed to load {module_toml}: {exc}")
            has_errors = True
            results.append(
                ModuleBootstrapResult(
                    module_id=module_id,
                    package_names=[],
                    missing_dependencies=[],
                    errors=module_errors,
                )
            )
            continue

        workflow_paths = _discover_module_workflow_paths(
            module_root=module_root,
            structure_root=module_spec.structure_root,
        )
        if not workflow_paths:
            module_errors.append(
                "aware.workflows.toml not found under module: " f"{module_root}",
            )
            has_errors = True

        for package_spec in module_spec.packages:
            aware_toml_path = (module_root / package_spec.manifest).resolve()
            if not aware_toml_path.exists():
                module_errors.append(f"Package manifest not found: {aware_toml_path}")
                has_errors = True
                continue

            try:
                package_summary = _load_package_manifest_summary(aware_toml_path)
            except Exception as exc:
                module_errors.append(
                    f"Failed to load package manifest {aware_toml_path}: {exc}",
                )
                has_errors = True
                continue
            if package_summary is None:
                continue

            package_name = package_summary.package_name
            package_names.append(package_name)
            for dep_name in package_summary.dependency_package_names:
                dep_path = package_path_by_name.get(dep_name)
                if dep_path is not None:
                    continue
                missing_dep = MissingDependency(
                    module_id=module_id,
                    package_name=package_name,
                    dependency_package_name=dep_name,
                    dependency_aware_toml_path=aware_toml_path.as_posix(),
                )
                missing.append(missing_dep)
                all_missing.append(missing_dep)

        for workflow_path in workflow_paths:
            try:
                _validate_workflow_manifest(workflow_path)
            except Exception as exc:
                module_errors.append(
                    f"Compile preflight failed for {workflow_path}: {exc}"
                )
                has_errors = True

        results.append(
            ModuleBootstrapResult(
                module_id=module_id,
                package_names=sorted(set(package_names)),
                missing_dependencies=missing,
                errors=module_errors,
            )
        )

    discovered_packages = [
        DiscoveredPackage(package_name=name, aware_toml_path=path.as_posix())
        for name, path in sorted(package_path_by_name.items())
    ]
    duplicates_payload = [
        DuplicatePackage(
            package_name=name,
            kept_aware_toml_path=package_path_by_name[name].as_posix(),
            ignored_aware_toml_paths=[p.as_posix() for p in sorted(paths)],
        )
        for name, paths in sorted(duplicate_packages.items())
        if name in package_path_by_name
    ]

    return WorkspacePreflightState(
        module_ids=list(selected_module_ids),
        modules=results,
        missing_dependencies=all_missing,
        discovered_packages=discovered_packages,
        duplicate_packages=duplicates_payload,
        has_errors=has_errors,
    )


def _run_remote_managed_preflight(
    *,
    request: WorkspaceBootstrapOptions,
    repo_root: Path,
) -> WorkspacePreflightState:
    selected_module_ids = resolve_module_ids(
        repo_root=repo_root,
        requested_modules=request.requested_module_ids,
    )
    results: list[ModuleBootstrapResult] = []
    has_errors = False

    for module_id in selected_module_ids:
        module_root = (repo_root / "modules" / module_id).resolve()
        module_toml = (module_root / "aware.module.toml").resolve()
        module_errors: list[str] = []
        if not module_toml.exists():
            module_errors.append(f"aware.module.toml not found: {module_toml}")
            has_errors = True

        results.append(
            ModuleBootstrapResult(
                module_id=module_id,
                package_names=[],
                missing_dependencies=[],
                errors=module_errors,
            )
        )

    return WorkspacePreflightState(
        module_ids=list(selected_module_ids),
        modules=results,
        missing_dependencies=[],
        discovered_packages=[],
        duplicate_packages=[],
        has_errors=has_errors,
    )


def resolve_module_ids(
    *, repo_root: Path, requested_modules: tuple[str, ...]
) -> tuple[str, ...]:
    """Resolve explicit module ids or discover modules under canonical roots."""

    requested = tuple(
        sorted({str(item).strip() for item in requested_modules if str(item).strip()})
    )
    if requested:
        return requested

    modules_root = (repo_root / "modules").resolve()
    if not modules_root.exists() or not modules_root.is_dir():
        return ()

    module_ids: list[str] = []
    for module_toml in sorted(modules_root.glob("*/aware.module.toml")):
        module_ids.append(module_toml.parent.name)
    return tuple(module_ids)


def _discover_package_manifests(repo_root: Path) -> tuple[Path, ...]:
    manifests: list[Path] = []
    for path in sorted(repo_root.rglob("aware*.toml")):
        if path.name not in _PACKAGE_MANIFEST_FILENAMES:
            continue
        if _is_discovery_skipped(path=path, repo_root=repo_root):
            continue
        manifests.append(path.resolve())
    return tuple(manifests)


def _discover_module_workflow_paths(
    *,
    module_root: Path,
    structure_root: str,
) -> tuple[Path, ...]:
    primary = (module_root / structure_root / "aware.workflows.toml").resolve()
    paths: list[Path] = []
    if primary.exists():
        paths.append(primary)

    for candidate in sorted(module_root.rglob("aware.workflows.toml")):
        resolved = candidate.resolve()
        if resolved == primary:
            continue
        if _is_discovery_skipped(path=resolved, repo_root=module_root):
            continue
        paths.append(resolved)

    return tuple(dict.fromkeys(paths))


def _is_discovery_skipped(*, path: Path, repo_root: Path) -> bool:
    try:
        relpath = path.resolve().relative_to(repo_root.resolve())
    except ValueError:
        return True
    parts = relpath.parts
    if set(parts) & _SKIP_DISCOVERY_PARTS:
        return True
    rel = relpath.as_posix()
    return any(
        rel == root or rel.startswith(f"{root}/") for root in _SKIP_DISCOVERY_ROOTS
    )


def _load_package_manifest_summary(path: Path) -> _PackageManifestSummary | None:
    if path.name not in _PACKAGE_MANIFEST_FILENAMES:
        return None

    raw_obj = tomllib.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw_obj, dict):
        raise ValueError(f"Expected TOML root object at {path}")
    raw = cast(dict[str, object], raw_obj)

    package_name = _extract_package_name(raw)
    if package_name is None:
        return None

    dependency_package_names: list[str] = []
    deps = raw.get("dependencies", [])
    if deps is None:
        deps = []
    if not isinstance(deps, list):
        raise ValueError(f"Expected [[dependencies]] array in {path}")
    for index, dep in enumerate(deps):
        if not isinstance(dep, dict):
            raise ValueError(
                f"Expected dependency table at dependencies[{index}] in {path}"
            )
        dep_name = str(dep.get("package_name") or "").strip()
        if dep_name:
            dependency_package_names.append(dep_name)

    return _PackageManifestSummary(
        package_name=package_name,
        dependency_package_names=tuple(dependency_package_names),
    )


def _extract_package_name(raw: dict[str, object]) -> str | None:
    for table_name in _PACKAGE_TABLE_NAMES:
        table = raw.get(table_name)
        if not isinstance(table, dict):
            continue
        package_name = str(table.get("package_name") or "").strip()
        if package_name:
            return package_name
    return None


def _validate_workflow_manifest(path: Path) -> None:
    raw_obj = tomllib.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw_obj, dict):
        raise ValueError(f"Expected TOML root object at {path}")
    raw = cast(dict[str, object], raw_obj)
    aware_version = raw.get("aware")
    if aware_version != 1:
        raise ValueError(f"Unsupported aware.workflows.toml version {aware_version!r}")
    workflow = raw.get("workflow")
    if not isinstance(workflow, dict):
        raise ValueError("aware.workflows.toml must declare [workflow]")
    mode = str(workflow.get("mode") or "").strip()
    if mode not in {"build"}:
        raise ValueError("[workflow].mode must be 'build'")
    module_toml_path = str(workflow.get("module_toml_path") or "").strip()
    if not module_toml_path:
        raise ValueError("[workflow].module_toml_path is required")


__all__ = ["resolve_module_ids", "run_preflight_stage"]
