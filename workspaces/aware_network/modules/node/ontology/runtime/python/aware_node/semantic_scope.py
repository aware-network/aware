from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from aware_code.package.schemas import CodePackageInfo
from aware_code.semantic_scope import (
    SemanticScopeMaterializationDependency,
    SemanticScopeProvider,
    SemanticScopeRegistry,
    SemanticScopeResolution,
)
from aware_code.semantic_scope.schemas import (
    SemanticScopePayloadObject,
    SemanticScopePayloadValue,
)

from aware_node.manifest import (
    AwareNodeDependencyKind,
    AwareNodeTomlSpec,
    load_aware_node_toml_spec,
)


NODE_SEMANTIC_SCOPE_KEY = "aware_node.semantic_scope"


@dataclass(frozen=True, slots=True)
class NodeSemanticScope:
    manifest_path: Path
    spec: AwareNodeTomlSpec
    materialization_dependencies: tuple[
        SemanticScopeMaterializationDependency,
        ...,
    ]


def load_node_semantic_scope(
    *,
    manifest_path: Path,
    workspace_root: Path,
) -> NodeSemanticScope:
    spec = load_aware_node_toml_spec(toml_path=manifest_path)
    return NodeSemanticScope(
        manifest_path=manifest_path,
        spec=spec,
        materialization_dependencies=_node_materialization_dependencies(
            spec=spec,
            manifest_path=manifest_path,
            workspace_root=workspace_root,
        ),
    )


def _workspace_relative_path_or_abs(*, path: Path, workspace_root: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(workspace_root.resolve()).as_posix()
    except Exception:
        return resolved.as_posix()


def _node_semantic_scope_payload(
    *,
    scope: NodeSemanticScope,
    workspace_root: Path,
) -> SemanticScopePayloadObject:
    dependencies_by_kind = _node_dependency_package_names_by_kind(spec=scope.spec)
    payload: dict[str, SemanticScopePayloadValue] = {
        "nodePackageName": scope.spec.node.package_name,
        "nodeManifestRelativePath": _workspace_relative_path_or_abs(
            path=scope.manifest_path,
            workspace_root=workspace_root,
        ),
        "declaredDependencyPackageNames": [
            dependency.package_name for dependency in scope.spec.dependencies
        ],
        "declaredServicePackageNames": dependencies_by_kind.get(
            AwareNodeDependencyKind.service_package.value,
            [],
        ),
        "declaredInterfacePackageNames": dependencies_by_kind.get(
            AwareNodeDependencyKind.interface_package.value,
            [],
        ),
        "declaredExperiencePackageNames": dependencies_by_kind.get(
            AwareNodeDependencyKind.experience_package.value,
            [],
        ),
        "declaredOntologyPackageNames": dependencies_by_kind.get(
            AwareNodeDependencyKind.ontology_package.value,
            [],
        ),
        "declaredEnvironmentPackageNames": dependencies_by_kind.get(
            AwareNodeDependencyKind.environment_package.value,
            [],
        ),
        "declaredNodePackageNames": dependencies_by_kind.get(
            AwareNodeDependencyKind.package.value,
            [],
        ),
    }
    return payload


def _node_dependency_package_names_by_kind(
    *,
    spec: AwareNodeTomlSpec,
) -> dict[str, list[str]]:
    package_names_by_kind: dict[str, list[str]] = {}
    for dependency in spec.dependencies:
        package_name = dependency.package_name.strip()
        if not package_name:
            continue
        package_names_by_kind.setdefault(dependency.kind.value, []).append(package_name)
    return package_names_by_kind


def _node_materialization_dependencies(
    *,
    spec: AwareNodeTomlSpec,
    manifest_path: Path,
    workspace_root: Path,
) -> tuple[SemanticScopeMaterializationDependency, ...]:
    source_ref = _workspace_relative_path_or_abs(
        path=manifest_path,
        workspace_root=workspace_root,
    )
    dependencies: list[SemanticScopeMaterializationDependency] = []
    seen: set[tuple[str | None, str, str]] = set()
    for dependency in spec.dependencies:
        package_name = dependency.package_name.strip()
        if not package_name:
            continue
        shape = _node_dependency_shape(kind=dependency.kind)
        provider_key, semantic_owner, manifest_kind, family, semantic_kind = shape
        dependency_kind = semantic_kind or "semantic_package"
        dedupe_key = (provider_key, dependency_kind, package_name.casefold())
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        dependencies.append(
            SemanticScopeMaterializationDependency(
                package_name=package_name,
                provider_key=provider_key,
                semantic_owner=semantic_owner,
                manifest_kind=manifest_kind,
                dependency_kind=dependency_kind,
                semantic_package_family=family,
                semantic_package_kind=semantic_kind,
                semantic_package_name=package_name,
                source_refs=(source_ref,),
                reason=(
                    "NodePackage materialization requires declared target "
                    "semantic packages before NodeConfig can be consumed by "
                    "deploy/runtime aggregation."
                ),
                metadata={
                    "version_number": dependency.version_number,
                    "node_dependency_kind": dependency.kind.value,
                },
            )
        )
    return tuple(dependencies)


def _node_dependency_shape(
    *,
    kind: AwareNodeDependencyKind,
) -> tuple[str | None, str | None, str | None, str | None, str | None]:
    if kind is AwareNodeDependencyKind.environment_package:
        return (
            "aware_environment",
            "aware_environment.environment_config.provider",
            "aware_environment_toml",
            "environment",
            "environment_config_package",
        )
    if kind is AwareNodeDependencyKind.experience_package:
        return (
            "aware_experience",
            "aware_experience.provider",
            "aware_experience_toml",
            "experience",
            "experience_package",
        )
    if kind is AwareNodeDependencyKind.service_package:
        return (
            "aware_service",
            "aware_service.provider",
            "aware_service_toml",
            "service",
            "service_package",
        )
    if kind is AwareNodeDependencyKind.interface_package:
        return (
            "aware_interface",
            "aware_interface.provider",
            "aware_interface_toml",
            "interface",
            "interface_package",
        )
    if kind is AwareNodeDependencyKind.ontology_package:
        return (
            "aware_ontology",
            "aware_ontology.provider",
            "aware_ontology_toml",
            "ontology",
            "ontology_package",
        )
    return (None, None, None, None, None)


class _NodeSemanticScopeProvider(SemanticScopeProvider):
    @property
    def provider_key(self) -> str:
        return "aware_node"

    @property
    def scope_keys(self) -> tuple[str, ...]:
        return (NODE_SEMANTIC_SCOPE_KEY,)

    def resolve(
        self,
        code_package: CodePackageInfo,
        *,
        workspace_root: Path,
    ) -> tuple[SemanticScopeResolution, ...]:
        if code_package.metadata.get("manifest_kind") != "aware_node_toml":
            return ()

        manifest_path = (workspace_root / code_package.manifest_path).resolve()
        try:
            scope = load_node_semantic_scope(
                manifest_path=manifest_path,
                workspace_root=workspace_root,
            )
        except Exception:
            return ()

        return (
            SemanticScopeResolution(
                scope_key=NODE_SEMANTIC_SCOPE_KEY,
                provider_key=self.provider_key,
                payload=_node_semantic_scope_payload(
                    scope=scope,
                    workspace_root=workspace_root,
                ),
                materialization_dependencies=scope.materialization_dependencies,
                runtime_value=scope,
            ),
        )


_PROVIDER = _NodeSemanticScopeProvider()


def register_semantic_scope_providers() -> None:
    SemanticScopeRegistry.register(_PROVIDER)


__all__ = [
    "NODE_SEMANTIC_SCOPE_KEY",
    "NodeSemanticScope",
    "load_node_semantic_scope",
    "register_semantic_scope_providers",
]
