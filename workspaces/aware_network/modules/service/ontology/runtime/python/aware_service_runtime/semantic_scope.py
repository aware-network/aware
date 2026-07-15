from __future__ import annotations

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

from aware_service_runtime.compiler import load_service_ownership_from_sources
from aware_service_runtime.semantic_constants import SERVICE_SEMANTIC_SCOPE_KEY
from aware_service_runtime.dependency_scope import (
    ServiceDependencyScope,
    load_service_dependency_scope,
)
from aware_service_runtime.workspace import ServiceWorkspace


def _workspace_relative_path_or_abs(*, path: Path, workspace_root: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(workspace_root.resolve()).as_posix()
    except Exception:
        return resolved.as_posix()


def _service_dependency_scope_payload(
    *,
    scope: ServiceDependencyScope,
    workspace_root: Path,
) -> SemanticScopePayloadObject:
    payload: dict[str, SemanticScopePayloadValue] = {
        "servicePackageName": scope.service_package_name,
        "serviceManifestRelativePath": _workspace_relative_path_or_abs(
            path=scope.manifest_path,
            workspace_root=workspace_root,
        ),
        "declaredApiPackageNames": list(scope.declared_api_package_names),
        "resolvedApiPackageNames": list(scope.resolved_api_package_names),
        "resolvedApiNames": list(sorted(scope.api_catalog)),
        "apiCatalog": {
            api_name: {
                "endpointRefs": list(sorted(truth.endpoint_refs)),
            }
            for api_name, truth in sorted(scope.api_catalog.items())
        },
    }
    return payload


def _service_materialization_dependencies(
    *,
    scope: ServiceDependencyScope,
    workspace_root: Path,
) -> tuple[SemanticScopeMaterializationDependency, ...]:
    source_ref = _workspace_relative_path_or_abs(
        path=scope.manifest_path,
        workspace_root=workspace_root,
    )
    return tuple(
        SemanticScopeMaterializationDependency(
            package_name=package_name,
            provider_key="aware_api",
            semantic_owner="aware_api.provider",
            manifest_kind="aware_api_toml",
            dependency_kind="api_service_protocol",
            semantic_package_family="api",
            semantic_package_kind="api_package",
            semantic_package_name=package_name,
            source_refs=(source_ref,),
            reason=(
                "Service semantic materialization requires declared API service "
                "protocol packages before ServiceConfig refs can resolve."
            ),
        )
        for package_name in scope.declared_api_package_names
    )


def _service_experience_materialization_dependencies(
    *,
    manifest_path: Path,
    workspace_root: Path,
) -> tuple[SemanticScopeMaterializationDependency, ...]:
    try:
        snapshot = ServiceWorkspace.from_toml(
            toml_path=manifest_path,
            repo_root=workspace_root,
        ).build_snapshot()
        service_ownership = load_service_ownership_from_sources(
            package_root=snapshot.package_root,
            source_files=snapshot.source_files,
        )
    except Exception:
        return ()

    dependencies: list[SemanticScopeMaterializationDependency] = []
    seen_experience_refs: set[str] = set()
    for service in service_ownership:
        for experience in service.experiences:
            experience_ref = experience.experience_ref.strip()
            if not experience_ref:
                continue
            experience_key = experience_ref.casefold()
            if experience_key in seen_experience_refs:
                continue
            seen_experience_refs.add(experience_key)
            dependencies.append(
                SemanticScopeMaterializationDependency(
                    package_name=experience_ref,
                    provider_key="aware_experience",
                    semantic_owner="aware_experience.provider",
                    manifest_kind="aware_experience_toml",
                    dependency_kind="ProjectionExperience",
                    semantic_package_family="experience",
                    semantic_package_kind="experience_package",
                    semantic_package_name=experience_ref,
                    source_refs=(experience.source_path,),
                    reason=(
                        "Service semantic materialization requires the "
                        "ProjectionExperience semantic lane before ServiceConfig "
                        "can resolve experience refs."
                    ),
                    metadata={"experience_ref": experience_ref},
                )
            )
    return tuple(dependencies)


def _service_semantic_scope_materialization_dependencies(
    *,
    scope: ServiceDependencyScope,
    workspace_root: Path,
) -> tuple[SemanticScopeMaterializationDependency, ...]:
    return (
        *_service_materialization_dependencies(
            scope=scope,
            workspace_root=workspace_root,
        ),
        *_service_experience_materialization_dependencies(
            manifest_path=scope.manifest_path,
            workspace_root=workspace_root,
        ),
    )


class _ServiceSemanticScopeProvider(SemanticScopeProvider):
    @property
    def provider_key(self) -> str:
        return "aware_service"

    @property
    def scope_keys(self) -> tuple[str, ...]:
        return (SERVICE_SEMANTIC_SCOPE_KEY,)

    def resolve(
        self,
        code_package: CodePackageInfo,
        *,
        workspace_root: Path,
    ) -> tuple[SemanticScopeResolution, ...]:
        if code_package.metadata.get("manifest_kind") != "aware_service_toml":
            return ()

        manifest_path = (workspace_root / code_package.manifest_path).resolve()
        try:
            scope = load_service_dependency_scope(manifest_path=manifest_path)
        except Exception:
            return ()

        return (
            SemanticScopeResolution(
                scope_key=SERVICE_SEMANTIC_SCOPE_KEY,
                provider_key=self.provider_key,
                payload=_service_dependency_scope_payload(
                    scope=scope,
                    workspace_root=workspace_root,
                ),
                materialization_dependencies=(
                    _service_semantic_scope_materialization_dependencies(
                        scope=scope,
                        workspace_root=workspace_root,
                    )
                ),
                runtime_value=scope,
            ),
        )


_PROVIDER = _ServiceSemanticScopeProvider()


def register_semantic_scope_providers() -> None:
    SemanticScopeRegistry.register(_PROVIDER)


__all__ = [
    "SERVICE_SEMANTIC_SCOPE_KEY",
    "register_semantic_scope_providers",
]
