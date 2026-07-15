from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import Enum

from aware_code_ontology.code.code_enums import CodeLanguage


class MaterializationPackageDependencyKind(str, Enum):
    """Where a generated package dependency is resolved from."""

    external = "external"
    workspace_code_package = "workspace_code_package"
    semantic_package = "semantic_package"


class MaterializationPackageDependencyScope(str, Enum):
    """Package-manager dependency surface for a materialized package."""

    runtime = "runtime"
    dev = "dev"
    optional = "optional"


@dataclass(frozen=True, slots=True)
class MaterializationPackageDependencySpec:
    """Upper package dependency declaration before language package rendering.

    This is intentionally above ObjectConfigGraphPackageSpec. Materialization
    code declares dependency intent here, then lowers it to the render carrier
    after resolving target language and scope.
    """

    name: str
    language: CodeLanguage | str | None = None
    requirement: str | None = None
    package_manager_name: str | None = None
    dependency_kind: MaterializationPackageDependencyKind | str = (
        MaterializationPackageDependencyKind.external
    )
    scope: MaterializationPackageDependencyScope | str = (
        MaterializationPackageDependencyScope.runtime
    )
    optional_group: str | None = None
    target: str | None = None
    source: str = "materialization"
    rendered_value: str | None = None

    def __post_init__(self) -> None:
        name = self.name.strip()
        rendered_value = (self.rendered_value or "").strip()
        if not name and not rendered_value:
            raise ValueError(
                "MaterializationPackageDependencySpec requires a name or rendered_value"
            )


@dataclass(frozen=True, slots=True)
class MaterializationResolvedPackageDependencies:
    """Dependencies lowered for ObjectConfigGraphPackageSpec."""

    dependencies: tuple[str, ...] = ()
    optional_dependencies: Mapping[str, tuple[str, ...]] = field(default_factory=dict)


def resolve_materialization_package_dependencies(
    dependencies: Iterable[MaterializationPackageDependencySpec],
    *,
    target_language: CodeLanguage | str | None = None,
    target: str | None = None,
) -> MaterializationResolvedPackageDependencies:
    """Lower declared dependency specs into package strategy dependency strings."""

    runtime_dependencies: list[str] = []
    optional_dependencies: dict[str, list[str]] = {}

    for dependency in dependencies:
        if not _matches_language(dependency, target_language=target_language):
            continue
        if not _matches_target(dependency, target=target):
            continue
        rendered = render_materialization_package_dependency(dependency)
        scope = _enum_value(dependency.scope)
        if scope == MaterializationPackageDependencyScope.runtime.value:
            _append_unique(runtime_dependencies, rendered)
            continue
        group = dependency.optional_group or (
            "dev" if scope == MaterializationPackageDependencyScope.dev.value else scope
        )
        group = str(group).strip() or "optional"
        group_dependencies = optional_dependencies.setdefault(group, [])
        _append_unique(group_dependencies, rendered)

    return MaterializationResolvedPackageDependencies(
        dependencies=tuple(runtime_dependencies),
        optional_dependencies={
            group: tuple(group_dependencies)
            for group, group_dependencies in optional_dependencies.items()
        },
    )


def render_materialization_package_dependency(
    dependency: MaterializationPackageDependencySpec,
) -> str:
    """Render one dependency for the target package manager."""

    rendered_value = (dependency.rendered_value or "").strip()
    if rendered_value:
        return rendered_value
    name = (dependency.package_manager_name or dependency.name).strip()
    if not name:
        raise ValueError("Package dependency name is required")
    requirement = (dependency.requirement or "").strip()
    if not requirement:
        return name
    language = _language_value(dependency.language)
    if language == CodeLanguage.dart.value:
        return f"{name}: {requirement}"
    return f"{name}{requirement}"


def _matches_language(
    dependency: MaterializationPackageDependencySpec,
    *,
    target_language: CodeLanguage | str | None,
) -> bool:
    if target_language is None or dependency.language is None:
        return True
    return _language_value(dependency.language) == _language_value(target_language)


def _matches_target(
    dependency: MaterializationPackageDependencySpec,
    *,
    target: str | None,
) -> bool:
    if target is None or dependency.target is None:
        return True
    return dependency.target == target


def _append_unique(values: list[str], value: str) -> None:
    if value not in values:
        values.append(value)


def _enum_value(value: object) -> str:
    return str(getattr(value, "value", value) or "").strip()


def _language_value(value: object) -> str:
    return _enum_value(value).replace("-", "_")


__all__ = [
    "MaterializationPackageDependencyKind",
    "MaterializationPackageDependencyScope",
    "MaterializationPackageDependencySpec",
    "MaterializationResolvedPackageDependencies",
    "render_materialization_package_dependency",
    "resolve_materialization_package_dependencies",
]
