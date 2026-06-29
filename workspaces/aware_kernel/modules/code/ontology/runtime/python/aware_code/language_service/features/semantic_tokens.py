from __future__ import annotations

from abc import ABC

from typing_extensions import override

from aware_code.language_service.capability_scope import (
    CapabilityExecutionPlan,
    CapabilityProviderExecutionContext,
    WorkspaceCapabilityConfiguration,
)
from aware_code.language_service.document import DocumentContext
from aware_code.language_service.features.base import ServiceMixinBase
from aware_code.language_service.features.semantic_tokens_capabilities import (
    TOKEN_MODIFIERS as _TOKEN_MODIFIERS,
    TOKEN_TYPES as _TOKEN_TYPES,
    ensure_builtin_semantic_tokens_capability_providers_registered,
    execute_semantic_tokens_capabilities,
    get_available_semantic_tokens_capability_provider_keys,
    get_registered_semantic_tokens_capability_descriptors,
)

from aware_workspace.compiler.workspace import WorkspaceSnapshot

TOKEN_TYPES = _TOKEN_TYPES
TOKEN_MODIFIERS = _TOKEN_MODIFIERS


class SemanticTokensMixin(ServiceMixinBase, ABC):
    _snapshot: WorkspaceSnapshot | None
    _workspace_capability_configuration: WorkspaceCapabilityConfiguration

    @override
    def _ensure_snapshot_for_uri(self, *, uri: str) -> None:
        raise NotImplementedError

    @override
    def _rebuild_full(self, *, focus_uri: str | None = None, reason: str = "change") -> None:
        raise NotImplementedError

    @override
    def _document_context(self, *, uri: str, document_text: str) -> DocumentContext:
        raise NotImplementedError

    def semantic_tokens_full(self, *, uri: str, document_text: str) -> dict[str, list[int]]:
        """Return LSP SemanticTokens for the full document (v0)."""
        if self._is_aware_config_uri(uri):
            return {"data": []}

        self._ensure_snapshot_for_uri(uri=uri)
        if self._snapshot is None:
            return {"data": []}

        code = self._snapshot.codes_by_uri.get(uri)
        if code is None:
            return {"data": []}

        execution_plan = self.semantic_tokens_capability_plan(uri=uri)
        provider_execution = CapabilityProviderExecutionContext(
            capability="semantic_tokens",
            uri=uri,
            workspace_root=self._workspace.workspace_root,
            document_path=self._workspace.uri_to_path(uri).resolve(),
            plan=execution_plan,
        )
        document_context = self._document_context(uri=uri, document_text=document_text)
        scope = self._snapshot.fqn_resolver.scope_for_code_id(code.id)
        data = execute_semantic_tokens_capabilities(
            code=code,
            provider_execution=provider_execution,
            scope=scope,
            mapper=document_context.mapper,
            document_bytes=document_context.document_bytes,
            workspace_language=self._workspace.language,
            execution_scope=execution_plan.effective_scope,
            provider_keys=tuple(
                provider.provider_key
                for provider in execution_plan.providers
                if provider.active
            ),
            overlay_descriptors=execution_plan.workspace_binding_provider_descriptors,
            overlay_providers=self._language_service_binding_overlay_providers(
                capability="semantic_tokens",
                uri=uri,
                provider_keys=(
                    provider.provider_key
                    for provider in execution_plan.providers
                    if provider.active
                ),
            ),
        )
        return {"data": data}

    def _effective_semantic_tokens_execution_scope(self, *, uri: str):
        return self.semantic_tokens_capability_plan(uri=uri).effective_scope

    def semantic_tokens_capability_plan(self, *, uri: str) -> CapabilityExecutionPlan:
        return self._capability_execution_plan_for_uri(
            capability="semantic_tokens",
            uri=uri,
            configured_selection=self._workspace_capability_configuration.semantic_tokens,
            ensure_providers_registered=ensure_builtin_semantic_tokens_capability_providers_registered,
            get_registered_descriptors=get_registered_semantic_tokens_capability_descriptors,
            get_available_provider_keys=get_available_semantic_tokens_capability_provider_keys,
        )
