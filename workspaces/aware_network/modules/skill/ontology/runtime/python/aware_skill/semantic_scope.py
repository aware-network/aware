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
from aware_skill.manifest import AwareSkillDependencyKind
from aware_skill.workspace import SkillWorkspace, SkillWorkspaceSnapshot


SKILL_SEMANTIC_SCOPE_KEY = "aware_skill.semantic_scope"


@dataclass(frozen=True, slots=True)
class SkillSemanticScope:
    manifest_path: Path
    snapshot: SkillWorkspaceSnapshot
    declared_api_package_names: tuple[str, ...]


def _workspace_relative_path_or_abs(*, path: Path, workspace_root: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(workspace_root.resolve()).as_posix()
    except Exception:
        return resolved.as_posix()


def _skill_semantic_scope_payload(
    *,
    scope: SkillSemanticScope,
    workspace_root: Path,
) -> SemanticScopePayloadObject:
    payload: dict[str, SemanticScopePayloadValue] = {
        "skillPackageName": scope.snapshot.spec.skill.package_name,
        "fqnPrefix": scope.snapshot.spec.skill.fqn_prefix,
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
        "declaredApiPackageNames": list(scope.declared_api_package_names),
    }
    return payload


def load_skill_semantic_scope(
    *,
    manifest_path: Path,
    repo_root: Path | None = None,
) -> SkillSemanticScope:
    workspace = SkillWorkspace.from_toml(toml_path=manifest_path, repo_root=repo_root)
    snapshot = workspace.build_snapshot()
    return SkillSemanticScope(
        manifest_path=manifest_path.resolve(),
        snapshot=snapshot,
        declared_api_package_names=tuple(
            sorted(
                dependency.package_name
                for dependency in snapshot.spec.dependencies
                if dependency.package_name
                and dependency.kind
                in (AwareSkillDependencyKind.api, AwareSkillDependencyKind.api_package)
            )
        ),
    )


def _skill_materialization_dependencies(
    *,
    scope: SkillSemanticScope,
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
            dependency_kind="api_package",
            semantic_package_family="api",
            semantic_package_kind="api_package",
            semantic_package_name=package_name,
            source_refs=(source_ref,),
            reason=(
                "Skill semantic materialization requires declared API packages "
                "before SkillConfig endpoint refs can resolve."
            ),
        )
        for package_name in scope.declared_api_package_names
    )


class _SkillSemanticScopeProvider(SemanticScopeProvider):
    @property
    def provider_key(self) -> str:
        return "aware_skill"

    @property
    def scope_keys(self) -> tuple[str, ...]:
        return (SKILL_SEMANTIC_SCOPE_KEY,)

    def resolve(
        self,
        code_package: CodePackageInfo,
        *,
        workspace_root: Path,
    ) -> tuple[SemanticScopeResolution, ...]:
        if code_package.metadata.get("manifest_kind") != "aware_skill_toml":
            return ()

        manifest_path = (workspace_root / code_package.manifest_path).resolve()
        try:
            scope = load_skill_semantic_scope(
                manifest_path=manifest_path,
                repo_root=workspace_root,
            )
        except Exception:
            return ()

        return (
            SemanticScopeResolution(
                scope_key=SKILL_SEMANTIC_SCOPE_KEY,
                provider_key=self.provider_key,
                payload=_skill_semantic_scope_payload(
                    scope=scope,
                    workspace_root=workspace_root,
                ),
                materialization_dependencies=_skill_materialization_dependencies(
                    scope=scope,
                    workspace_root=workspace_root,
                ),
                runtime_value=scope,
            ),
        )


_PROVIDER = _SkillSemanticScopeProvider()


def register_semantic_scope_providers() -> None:
    SemanticScopeRegistry.register(_PROVIDER)


__all__ = [
    "SKILL_SEMANTIC_SCOPE_KEY",
    "SkillSemanticScope",
    "load_skill_semantic_scope",
    "register_semantic_scope_providers",
]
