from __future__ import annotations

from pathlib import Path

from aware_code.package.schemas import CodePackageInfo
from aware_code.semantic_scope import (
    SemanticScopeProvider,
    SemanticScopeRegistry,
    SemanticScopeResolution,
)
from aware_meta.semantic_contract import META_SEMANTIC_PROJECTION_MUTATION_SCOPES
from aware_meta.semantic_projection_mutation_scope import (
    code_package_matches_meta_projection_mutation_scope,
    meta_semantic_projection_mutation_scope_resolution,
)


class _MetaSemanticProjectionMutationScopeProvider(SemanticScopeProvider):
    @property
    def provider_key(self) -> str:
        return "aware_meta"

    @property
    def scope_keys(self) -> tuple[str, ...]:
        return tuple(
            descriptor.scope_key
            for descriptor in META_SEMANTIC_PROJECTION_MUTATION_SCOPES
        )

    def resolve(
        self,
        code_package: CodePackageInfo,
        *,
        workspace_root: Path,
    ) -> tuple[SemanticScopeResolution, ...]:
        if not code_package_matches_meta_projection_mutation_scope(code_package):
            return ()
        return tuple(
            meta_semantic_projection_mutation_scope_resolution(
                descriptor=descriptor,
                code_package=code_package,
                provider_key=self.provider_key,
                workspace_root=workspace_root,
            )
            for descriptor in META_SEMANTIC_PROJECTION_MUTATION_SCOPES
        )


_PROVIDER = _MetaSemanticProjectionMutationScopeProvider()


def register_semantic_scope_providers() -> None:
    SemanticScopeRegistry.register(_PROVIDER)


__all__ = [
    "register_semantic_scope_providers",
]
