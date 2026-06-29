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

from aware_api_runtime.workspace import APIWorkspace, APIWorkspaceSnapshot


API_SEMANTIC_SCOPE_KEY = "aware_api.semantic_scope"


@dataclass(frozen=True, slots=True)
class APISemanticScope:
    manifest_path: Path
    snapshot: APIWorkspaceSnapshot
    declared_dependency_package_names: tuple[str, ...]


def _workspace_relative_path_or_abs(*, path: Path, workspace_root: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(workspace_root.resolve()).as_posix()
    except Exception:
        return resolved.as_posix()


def _api_semantic_scope_payload(
    *,
    scope: APISemanticScope,
    workspace_root: Path,
) -> SemanticScopePayloadObject:
    payload: dict[str, SemanticScopePayloadValue] = {
        "apiPackageName": scope.snapshot.spec.api.package_name,
        "fqnPrefix": scope.snapshot.spec.api.fqn_prefix,
        "compilationMode": scope.snapshot.spec.build.compilation_mode.value,
        "packageRootRelativePath": _workspace_relative_path_or_abs(
            path=scope.snapshot.package_root,
            workspace_root=workspace_root,
        ),
        "manifestRelativePath": _workspace_relative_path_or_abs(
            path=scope.manifest_path,
            workspace_root=workspace_root,
        ),
        "sourcesDir": scope.snapshot.spec.build.sources_dir,
        "sourceFiles": [
            _workspace_relative_path_or_abs(
                path=(scope.snapshot.package_root / source_file).resolve(),
                workspace_root=workspace_root,
            )
            for source_file in scope.snapshot.source_files
        ],
        "declaredDependencyPackageNames": list(scope.declared_dependency_package_names),
    }
    return payload


def load_api_semantic_scope(
    *,
    manifest_path: Path,
    repo_root: Path | None = None,
) -> APISemanticScope:
    workspace = APIWorkspace.from_toml(toml_path=manifest_path, repo_root=repo_root)
    snapshot = workspace.build_snapshot()
    return APISemanticScope(
        manifest_path=manifest_path.resolve(),
        snapshot=snapshot,
        declared_dependency_package_names=tuple(
            sorted(
                dependency.package_name
                for dependency in snapshot.spec.dependencies
                if dependency.package_name
            )
        ),
    )


def _api_materialization_dependencies(
    *,
    scope: APISemanticScope,
    workspace_root: Path,
) -> tuple[SemanticScopeMaterializationDependency, ...]:
    source_ref = _workspace_relative_path_or_abs(
        path=scope.manifest_path,
        workspace_root=workspace_root,
    )
    return tuple(
        SemanticScopeMaterializationDependency(
            package_name=package_name,
            source_refs=(source_ref,),
            reason=(
                "API semantic materialization requires declared package "
                "dependencies before API package refs can resolve."
            ),
        )
        for package_name in scope.declared_dependency_package_names
    )


class _ApiSemanticScopeProvider(SemanticScopeProvider):
    @property
    def provider_key(self) -> str:
        return "aware_api"

    @property
    def scope_keys(self) -> tuple[str, ...]:
        return (API_SEMANTIC_SCOPE_KEY,)

    def resolve(
        self,
        code_package: CodePackageInfo,
        *,
        workspace_root: Path,
    ) -> tuple[SemanticScopeResolution, ...]:
        if code_package.metadata.get("manifest_kind") != "aware_api_toml":
            return ()

        manifest_path = (workspace_root / code_package.manifest_path).resolve()
        try:
            scope = load_api_semantic_scope(
                manifest_path=manifest_path,
                repo_root=workspace_root,
            )
        except Exception:
            return ()

        return (
            SemanticScopeResolution(
                scope_key=API_SEMANTIC_SCOPE_KEY,
                provider_key=self.provider_key,
                payload=_api_semantic_scope_payload(
                    scope=scope,
                    workspace_root=workspace_root,
                ),
                materialization_dependencies=_api_materialization_dependencies(
                    scope=scope,
                    workspace_root=workspace_root,
                ),
                runtime_value=scope,
            ),
        )


_PROVIDER = _ApiSemanticScopeProvider()


def register_semantic_scope_providers() -> None:
    SemanticScopeRegistry.register(_PROVIDER)


__all__ = [
    "APISemanticScope",
    "API_SEMANTIC_SCOPE_KEY",
    "load_api_semantic_scope",
    "register_semantic_scope_providers",
]
