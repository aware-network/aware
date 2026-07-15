from __future__ import annotations

import os
from collections.abc import Iterable
from pathlib import Path

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.materialization.package_dependencies import (
    MaterializationPackageDependencyKind,
    MaterializationPackageDependencyScope,
    MaterializationPackageDependencySpec,
    MaterializationResolvedPackageDependencies,
    resolve_materialization_package_dependencies,
)


DART_AWARE_API_PACKAGE_NAME = "aware_api"
DART_AWARE_MODEL_HELPERS_PACKAGE_NAME = "aware_model_helpers"
_AWARE_REPO_ROOT_ENV = "AWARE_REPO_ROOT"

_DART_GENERATED_RUNTIME_DEPENDENCIES: tuple[tuple[str, str], ...] = (
    ("freezed_annotation", "^3.0.0"),
    ("json_annotation", "^4.9.0"),
    ("uuid", "^4.5.1"),
)
_DART_GENERATED_DEV_DEPENDENCIES: tuple[tuple[str, str], ...] = (
    ("build_runner", "^2.4.11"),
    ("freezed", "^3.0.0"),
    ("json_serializable", "^6.8.0"),
)
_DART_AWARE_MODEL_HELPERS_REL_PATHS: tuple[tuple[str, ...], ...] = (
    ("libs", "model_helpers", "dart", DART_AWARE_MODEL_HELPERS_PACKAGE_NAME),
    (
        "workspaces",
        "aware_kernel",
        "libs",
        "model_helpers",
        "dart",
        DART_AWARE_MODEL_HELPERS_PACKAGE_NAME,
    ),
)
_DART_AWARE_API_REL_PATHS: tuple[tuple[str, ...], ...] = (
    ("modules", "api", "libs", "api", "dart"),
    ("libs", "api", "dart"),
    ("workspaces", "aware_kernel", "modules", "api", "libs", "api", "dart"),
)


def dart_generated_runtime_dependency_specs(
    *,
    source: str = "dart.generated_package_defaults",
) -> tuple[MaterializationPackageDependencySpec, ...]:
    return tuple(
        MaterializationPackageDependencySpec(
            name=name,
            language=CodeLanguage.dart,
            requirement=requirement,
            dependency_kind=MaterializationPackageDependencyKind.external,
            scope=MaterializationPackageDependencyScope.runtime,
            source=source,
        )
        for name, requirement in _DART_GENERATED_RUNTIME_DEPENDENCIES
    )


def dart_generated_dev_dependency_specs(
    *,
    source: str = "dart.generated_package_defaults",
) -> tuple[MaterializationPackageDependencySpec, ...]:
    return tuple(
        MaterializationPackageDependencySpec(
            name=name,
            language=CodeLanguage.dart,
            requirement=requirement,
            dependency_kind=MaterializationPackageDependencyKind.external,
            scope=MaterializationPackageDependencyScope.dev,
            optional_group="dev",
            source=source,
        )
        for name, requirement in _DART_GENERATED_DEV_DEPENDENCIES
    )


def dart_generated_package_dependency_specs(
    *,
    source: str = "dart.generated_package_defaults",
) -> tuple[MaterializationPackageDependencySpec, ...]:
    return (
        *dart_generated_runtime_dependency_specs(source=source),
        *dart_generated_dev_dependency_specs(source=source),
    )


def resolve_dart_generated_package_dependencies(
    *,
    source: str = "dart.generated_package_defaults",
) -> MaterializationResolvedPackageDependencies:
    return resolve_materialization_package_dependencies(
        dart_generated_package_dependency_specs(source=source),
        target_language=CodeLanguage.dart,
    )


def resolve_dart_workspace_path_dependency_specs(
    *,
    package_root: Path,
    repo_root: Path | None = None,
    dependency_repo_roots: Iterable[Path] = (),
    include_aware_api: bool = True,
    source: str = "dart.workspace_path_dependencies",
) -> tuple[MaterializationPackageDependencySpec, ...]:
    package_root = Path(package_root).resolve()
    helpers_dir = _resolve_dart_workspace_dependency_dir(
        package_root=package_root,
        repo_root=repo_root,
        dependency_repo_roots=dependency_repo_roots,
        dependency_name=DART_AWARE_MODEL_HELPERS_PACKAGE_NAME,
        rel_paths=_DART_AWARE_MODEL_HELPERS_REL_PATHS,
    )
    dependencies: list[tuple[str, str]] = [
        (
            DART_AWARE_MODEL_HELPERS_PACKAGE_NAME,
            _package_relative_path(package_root=package_root, target=helpers_dir),
        )
    ]
    if include_aware_api:
        aware_api_dir = _resolve_dart_workspace_dependency_dir(
            package_root=package_root,
            repo_root=repo_root,
            dependency_repo_roots=dependency_repo_roots,
            dependency_name=DART_AWARE_API_PACKAGE_NAME,
            rel_paths=_DART_AWARE_API_REL_PATHS,
        )
        dependencies.append(
            (
                DART_AWARE_API_PACKAGE_NAME,
                _package_relative_path(package_root=package_root, target=aware_api_dir),
            )
        )
    return dart_path_dependency_specs(dependencies, source=source)


def resolve_dart_workspace_path_dependencies(
    *,
    package_root: Path,
    repo_root: Path | None = None,
    dependency_repo_roots: Iterable[Path] = (),
    include_aware_api: bool = True,
    source: str = "dart.workspace_path_dependencies",
) -> MaterializationResolvedPackageDependencies:
    return resolve_materialization_package_dependencies(
        resolve_dart_workspace_path_dependency_specs(
            package_root=package_root,
            repo_root=repo_root,
            dependency_repo_roots=dependency_repo_roots,
            include_aware_api=include_aware_api,
            source=source,
        ),
        target_language=CodeLanguage.dart,
    )


def infer_dart_workspace_repo_root(
    *,
    package_root: Path,
    repo_root: Path | None = None,
    dependency_repo_roots: Iterable[Path] = (),
) -> Path | None:
    for candidate in _dart_workspace_search_roots(
        package_root=Path(package_root),
        repo_root=repo_root,
        dependency_repo_roots=dependency_repo_roots,
    ):
        if (candidate / "aware.workspace.toml").is_file():
            return candidate
    for candidate in _dart_workspace_search_roots(
        package_root=Path(package_root),
        repo_root=repo_root,
        dependency_repo_roots=dependency_repo_roots,
    ):
        if (candidate / "aware.environment.toml").is_file():
            return candidate
    return None


def dart_path_dependency_spec(
    *,
    name: str,
    path: str,
    source: str,
) -> MaterializationPackageDependencySpec:
    return MaterializationPackageDependencySpec(
        name=name,
        language=CodeLanguage.dart,
        dependency_kind=MaterializationPackageDependencyKind.workspace_code_package,
        scope=MaterializationPackageDependencyScope.runtime,
        source=source,
        rendered_value=f"{name}:\n  path: {path}",
    )


def dart_path_dependency_specs(
    dependencies: Iterable[tuple[str, str]],
    *,
    source: str,
) -> tuple[MaterializationPackageDependencySpec, ...]:
    return tuple(
        dart_path_dependency_spec(name=name, path=path, source=source)
        for name, path in dependencies
        if name.strip() and path.strip()
    )


def _resolve_dart_workspace_dependency_dir(
    *,
    package_root: Path,
    repo_root: Path | None,
    dependency_repo_roots: Iterable[Path],
    dependency_name: str,
    rel_paths: tuple[tuple[str, ...], ...],
) -> Path:
    candidates: list[Path] = []
    for base in _dart_workspace_search_roots(
        package_root=package_root,
        repo_root=repo_root,
        dependency_repo_roots=dependency_repo_roots,
    ):
        for rel_path in rel_paths:
            candidate = (base.joinpath(*rel_path)).resolve()
            candidates.append(candidate)
            if candidate.exists():
                return candidate
    checked = ", ".join(path.as_posix() for path in dict.fromkeys(candidates))
    raise FileNotFoundError(
        f"Expected Dart workspace dependency {dependency_name}. Checked: {checked}"
    )


def _dart_workspace_search_roots(
    *,
    package_root: Path,
    repo_root: Path | None,
    dependency_repo_roots: Iterable[Path],
) -> tuple[Path, ...]:
    roots: list[Path] = []
    if repo_root is not None:
        roots.append(Path(repo_root).expanduser().resolve())
    raw_env_root = os.environ.get(_AWARE_REPO_ROOT_ENV)
    if raw_env_root:
        roots.append(Path(raw_env_root).expanduser().resolve())
    roots.extend(Path(root).expanduser().resolve() for root in dependency_repo_roots)
    package_root_resolved = Path(package_root).resolve()
    roots.extend((package_root_resolved, *package_root_resolved.parents))
    return tuple(dict.fromkeys(roots))


def _package_relative_path(*, package_root: Path, target: Path) -> str:
    return Path(
        os.path.relpath(target.resolve(), start=package_root.resolve())
    ).as_posix()


__all__ = [
    "DART_AWARE_API_PACKAGE_NAME",
    "DART_AWARE_MODEL_HELPERS_PACKAGE_NAME",
    "dart_generated_dev_dependency_specs",
    "dart_generated_package_dependency_specs",
    "dart_generated_runtime_dependency_specs",
    "dart_path_dependency_spec",
    "dart_path_dependency_specs",
    "infer_dart_workspace_repo_root",
    "resolve_dart_generated_package_dependencies",
    "resolve_dart_workspace_path_dependencies",
    "resolve_dart_workspace_path_dependency_specs",
]
