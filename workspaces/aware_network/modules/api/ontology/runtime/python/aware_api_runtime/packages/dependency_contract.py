from __future__ import annotations

from collections.abc import Iterable

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.materialization.package_dependencies import (
    MaterializationPackageDependencyKind,
    MaterializationPackageDependencySpec,
    MaterializationResolvedPackageDependencies,
    resolve_materialization_package_dependencies,
)
from aware_meta.materialization.dart_package_dependencies import (
    dart_generated_package_dependency_specs,
    dart_path_dependency_specs,
)


_PYDANTIC_STABLE_LATEST_REQUIREMENT = ">=2.13.4,<3.0.0"


def api_public_package_python_dependency_specs(
    *,
    dependency_import_roots: Iterable[str] = (),
) -> tuple[MaterializationPackageDependencySpec, ...]:
    return (
        *_python_workspace_dependency_specs(
            dependency_import_roots,
            source="api_public_package.dependency_import_roots",
        ),
        _python_workspace_dependency("aware-api-client", source="api_public_package"),
        _python_workspace_dependency("aware-types", source="api_public_package"),
        _python_workspace_dependency("aware-utils", source="api_public_package"),
        _python_pydantic_dependency(source="api_public_package"),
    )


def api_public_package_dart_dependency_specs(
    *,
    path_dependencies: Iterable[tuple[str, str]] = (),
) -> tuple[MaterializationPackageDependencySpec, ...]:
    return (
        *dart_generated_package_dependency_specs(source="api_public_package.dart"),
        *dart_path_dependency_specs(
            path_dependencies,
            source="api_public_package.dart.path_dependencies",
        ),
    )


def api_service_protocol_python_dependency_specs(
    *,
    dependency_roots: Iterable[str] = (),
) -> tuple[MaterializationPackageDependencySpec, ...]:
    return (
        *_python_workspace_dependency_specs(
            dependency_roots,
            source="api_service_protocol.dependency_roots",
        ),
        _python_workspace_dependency("aware-utils", source="api_service_protocol"),
        _python_pydantic_dependency(source="api_service_protocol"),
    )


def api_dto_package_python_dependency_specs(
    *,
    dependency_distribution_names: Iterable[str] = (),
) -> tuple[MaterializationPackageDependencySpec, ...]:
    return (
        *_python_workspace_dependency_specs(
            dependency_distribution_names,
            source="api_dto.dependency_distribution_names",
        ),
        _python_workspace_dependency("aware-types", source="api_dto"),
        _python_workspace_dependency("aware-utils", source="api_dto"),
        _python_pydantic_dependency(source="api_dto"),
    )


def resolve_api_public_package_python_dependencies(
    *,
    dependency_import_roots: Iterable[str] = (),
) -> list[str]:
    return list(
        resolve_materialization_package_dependencies(
            api_public_package_python_dependency_specs(
                dependency_import_roots=dependency_import_roots,
            ),
            target_language=CodeLanguage.python,
        ).dependencies
    )


def resolve_api_public_package_dart_dependencies(
    *,
    path_dependencies: Iterable[tuple[str, str]] = (),
) -> MaterializationResolvedPackageDependencies:
    return resolve_materialization_package_dependencies(
        api_public_package_dart_dependency_specs(
            path_dependencies=path_dependencies,
        ),
        target_language=CodeLanguage.dart,
    )


def resolve_api_service_protocol_python_dependencies(
    *,
    dependency_roots: Iterable[str] = (),
) -> list[str]:
    return list(
        resolve_materialization_package_dependencies(
            api_service_protocol_python_dependency_specs(
                dependency_roots=dependency_roots,
            ),
            target_language=CodeLanguage.python,
        ).dependencies
    )


def resolve_api_dto_package_python_dependencies(
    *,
    dependency_distribution_names: Iterable[str] = (),
) -> list[str]:
    return list(
        resolve_materialization_package_dependencies(
            api_dto_package_python_dependency_specs(
                dependency_distribution_names=dependency_distribution_names,
            ),
            target_language=CodeLanguage.python,
        ).dependencies
    )


def _python_workspace_dependency_specs(
    names: Iterable[str],
    *,
    source: str,
) -> tuple[MaterializationPackageDependencySpec, ...]:
    return tuple(
        _python_workspace_dependency(name, source=source)
        for name in names
        if str(name or "").strip()
    )


def _python_workspace_dependency(
    name: str,
    *,
    source: str,
) -> MaterializationPackageDependencySpec:
    return MaterializationPackageDependencySpec(
        name=name.strip(),
        language=CodeLanguage.python,
        dependency_kind=MaterializationPackageDependencyKind.workspace_code_package,
        source=source,
    )


def _python_pydantic_dependency(
    *,
    source: str,
) -> MaterializationPackageDependencySpec:
    return MaterializationPackageDependencySpec(
        name="pydantic",
        language=CodeLanguage.python,
        requirement=_PYDANTIC_STABLE_LATEST_REQUIREMENT,
        dependency_kind=MaterializationPackageDependencyKind.external,
        source=source,
    )


__all__ = [
    "api_dto_package_python_dependency_specs",
    "api_public_package_dart_dependency_specs",
    "api_public_package_python_dependency_specs",
    "api_service_protocol_python_dependency_specs",
    "resolve_api_dto_package_python_dependencies",
    "resolve_api_public_package_dart_dependencies",
    "resolve_api_public_package_python_dependencies",
    "resolve_api_service_protocol_python_dependencies",
]
