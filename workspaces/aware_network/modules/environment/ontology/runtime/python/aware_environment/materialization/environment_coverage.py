from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from aware_environment.manifest import load_aware_environment_spec
from aware_ontology.manifest.loader import load_aware_ontology_toml_spec


@dataclass(frozen=True, slots=True)
class EnvironmentEnvironmentSemanticPackageCoverage:
    """Environment-owned semantic package coverage declared by an environment."""

    workspace_manifest_kind: str
    coverage_owner: str
    environment_manifest_path: str
    manifest_path: str


@dataclass(frozen=True, slots=True)
class EnvironmentEnvironmentOntologyPackageClosure:
    """Ontology package selected by an EnvironmentConfig."""

    environment_manifest_path: str
    ontology_manifest_path: str
    ontology_package_name: str
    ontology_package_root: str
    source_manifest_path: str
    runtime_manifest_path: str | None = None
    runtime_project_name: str | None = None
    runtime_import_root: str | None = None


def environment_environment_semantic_package_coverage_for_manifest(
    *,
    workspace_root: Path,
    environment_toml_path: Path,
) -> tuple[EnvironmentEnvironmentSemanticPackageCoverage, ...]:
    """Return semantic package selectors covered by Environment environment materialization."""

    resolved_workspace_root = workspace_root.expanduser().resolve()
    resolved_environment_toml = environment_toml_path.expanduser().resolve()
    environment_manifest_path = _workspace_relative_path(
        workspace_root=resolved_workspace_root,
        path=resolved_environment_toml,
    )
    spec = load_aware_environment_spec(toml_path=resolved_environment_toml)
    coverage: list[EnvironmentEnvironmentSemanticPackageCoverage] = []
    for ontology_manifest_path in _environment_ontology_manifest_paths(
        workspace_root=resolved_workspace_root,
        ontology_manifest_paths=getattr(spec, "ontologies", ()),
    ):
        coverage.append(
            EnvironmentEnvironmentSemanticPackageCoverage(
                workspace_manifest_kind="ontology",
                coverage_owner="aware_environment.environment.ontology",
                environment_manifest_path=environment_manifest_path,
                manifest_path=ontology_manifest_path,
            )
        )
    return tuple(coverage)


def environment_environment_ontology_package_closure_for_manifest(
    *,
    workspace_root: Path,
    environment_toml_path: Path,
) -> tuple[EnvironmentEnvironmentOntologyPackageClosure, ...]:
    """Return ontology package closure selected by an EnvironmentConfig."""

    resolved_workspace_root = workspace_root.expanduser().resolve()
    closure: list[EnvironmentEnvironmentOntologyPackageClosure] = []
    for coverage in environment_environment_semantic_package_coverage_for_manifest(
        workspace_root=resolved_workspace_root,
        environment_toml_path=environment_toml_path,
    ):
        if coverage.workspace_manifest_kind != "ontology":
            continue
        ontology_manifest_path = (
            resolved_workspace_root / coverage.manifest_path
        ).resolve()
        spec = load_aware_ontology_toml_spec(toml_path=ontology_manifest_path)
        ontology_package_root = ontology_manifest_path.parent
        source_manifest_path = _safe_relative_path(
            base=ontology_package_root,
            relative=spec.ontology.source_manifest,
            label="source_manifest",
        )
        runtime_manifest_path: Path | None = None
        runtime_project_name: str | None = None
        runtime_import_root: str | None = None
        if spec.runtime is not None:
            runtime_manifest_path = _safe_relative_path(
                base=ontology_package_root,
                relative=spec.runtime.manifest,
                label="runtime.manifest",
            )
            runtime_project_name = _clean_optional_text(spec.runtime.project_name)
            runtime_import_root = _clean_optional_text(spec.runtime.import_root)
        closure.append(
            EnvironmentEnvironmentOntologyPackageClosure(
                environment_manifest_path=coverage.environment_manifest_path,
                ontology_manifest_path=_workspace_relative_path(
                    workspace_root=resolved_workspace_root,
                    path=ontology_manifest_path,
                ),
                ontology_package_name=spec.ontology.package_name,
                ontology_package_root=_workspace_relative_path(
                    workspace_root=resolved_workspace_root,
                    path=ontology_package_root,
                ),
                source_manifest_path=_workspace_relative_path(
                    workspace_root=resolved_workspace_root,
                    path=source_manifest_path,
                ),
                runtime_manifest_path=(
                    None
                    if runtime_manifest_path is None
                    else _workspace_relative_path(
                        workspace_root=resolved_workspace_root,
                        path=runtime_manifest_path,
                    )
                ),
                runtime_project_name=runtime_project_name,
                runtime_import_root=runtime_import_root,
            )
        )
    return tuple(closure)


def environment_environment_covers_semantic_package(
    coverage: EnvironmentEnvironmentSemanticPackageCoverage,
    *,
    workspace_manifest_kind: str,
    manifest_path: str,
    semantic_package_metadata: Mapping[str, object],
) -> bool:
    del semantic_package_metadata
    if coverage.workspace_manifest_kind != workspace_manifest_kind:
        return False
    return coverage.manifest_path == manifest_path


def _environment_ontology_manifest_paths(
    *,
    workspace_root: Path,
    ontology_manifest_paths: object,
) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            _workspace_relative_path(
                workspace_root=workspace_root,
                path=(
                    path.expanduser().resolve()
                    if path.is_absolute()
                    else (workspace_root / path).resolve()
                ),
            )
            for raw_path in _clean_text_tuple(ontology_manifest_paths)
            for path in (Path(raw_path),)
        )
    )


def _workspace_relative_path(*, workspace_root: Path, path: Path) -> str:
    try:
        return path.relative_to(workspace_root).as_posix()
    except ValueError:
        return path.as_posix()


def _safe_relative_path(*, base: Path, relative: str, label: str) -> Path:
    raw_path = Path(str(relative).strip())
    if raw_path.is_absolute() or _has_unsafe_part(raw_path):
        raise ValueError(f"Unsafe ontology {label} path: {relative!r}")
    return (base / raw_path).resolve()


def _has_unsafe_part(path: Path) -> bool:
    return any(part in {"", ".", ".."} for part in path.parts)


def _clean_optional_text(value: object) -> str | None:
    text = str(value if value is not None else "").strip()
    return text or None


def _clean_text_tuple(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value.strip(),) if value.strip() else ()
    if not isinstance(value, (list, tuple, set)):
        return ()
    items: list[str] = []
    for raw_item in cast(Iterable[object], value):
        item = str(raw_item if raw_item is not None else "").strip()
        if item:
            items.append(item)
    return tuple(dict.fromkeys(items))


__all__ = [
    "EnvironmentEnvironmentOntologyPackageClosure",
    "EnvironmentEnvironmentSemanticPackageCoverage",
    "environment_environment_covers_semantic_package",
    "environment_environment_ontology_package_closure_for_manifest",
    "environment_environment_semantic_package_coverage_for_manifest",
]
