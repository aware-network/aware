from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from aware_meta.materialization.deltas.code_dto import (
    CodeGeneratedMaterializationDeltaRequest,
    CodeGeneratedMaterializationDeltaResult,
)
from aware_meta.materialization.deltas.feature_contracts import (
    MetaProviderDeltaGeneratedMaterializationContext,
)
from aware_meta.materialization.deltas.typed_operation_contracts import (
    MetaProviderDeltaTypedOperation,
)


@dataclass(frozen=True, slots=True)
class MetaLanguageGeneratedMaterializationTargetHint:
    semantic_key: str | None = None
    owner_key: str | None = None
    target_key: str | None = None
    output_key: str | None = None
    relative_path: str | None = None
    artifact_family: str | None = None
    artifact_role: str | None = None


@dataclass(frozen=True, slots=True)
class MetaLanguageGeneratedMaterializationDeltaContext:
    package_name: str | None = None
    package_root: str | None = None
    sources_root: str | None = None
    target_language: str | None = None
    renderer_profile: str | None = None
    materialization_source: str | None = None
    product_intent: str | None = None
    artifact_family: str | None = None
    artifact_role: str | None = None
    target_hints: tuple[MetaLanguageGeneratedMaterializationTargetHint, ...] = field(
        default_factory=tuple
    )

    @classmethod
    def from_provider_context(
        cls,
        context: MetaProviderDeltaGeneratedMaterializationContext,
        *,
        renderer_profile: str | None = None,
        materialization_source: str | None = None,
        product_intent: str | None = None,
        artifact_family: str | None = None,
        artifact_role: str | None = None,
        target_hints: tuple[MetaLanguageGeneratedMaterializationTargetHint, ...] = (),
    ) -> "MetaLanguageGeneratedMaterializationDeltaContext":
        return cls(
            package_name=context.package_name,
            package_root=context.package_root,
            sources_root=context.sources_root,
            target_language=context.target_language,
            renderer_profile=renderer_profile,
            materialization_source=materialization_source,
            product_intent=product_intent,
            artifact_family=artifact_family,
            artifact_role=artifact_role,
            target_hints=target_hints,
        )

    def relative_path_for_owner(self, owner_key: str | None) -> str | None:
        if owner_key is None:
            return None
        for hint in self.target_hints:
            if hint.owner_key == owner_key and hint.relative_path:
                return hint.relative_path
        return None


@dataclass(frozen=True, slots=True)
class MetaLanguageGeneratedMaterializationDeltaRenderRequest:
    operation: MetaProviderDeltaTypedOperation
    context: MetaLanguageGeneratedMaterializationDeltaContext
    renderer_profile: str | None = None
    materialization_source: str | None = None
    capability_key: str | None = None


@dataclass(frozen=True, slots=True)
class MetaLanguageGeneratedMaterializationDeltaRenderResult:
    handled: bool
    reason: str
    delta_request: CodeGeneratedMaterializationDeltaRequest | None = None
    result: CodeGeneratedMaterializationDeltaResult | None = None

    @classmethod
    def unhandled(
        cls,
        *,
        reason: str,
    ) -> "MetaLanguageGeneratedMaterializationDeltaRenderResult":
        return cls(handled=False, reason=reason)

    @classmethod
    def from_evidence(
        cls,
        *,
        delta_request: CodeGeneratedMaterializationDeltaRequest,
        result: CodeGeneratedMaterializationDeltaResult,
        reason: str,
    ) -> "MetaLanguageGeneratedMaterializationDeltaRenderResult":
        return cls(
            handled=True,
            reason=reason,
            delta_request=delta_request,
            result=result,
        )


@runtime_checkable
class MetaLanguageGeneratedMaterializationDeltaRenderer(Protocol):
    renderer_key: str
    renderer_profile: str
    materialization_source: str

    def supports_generated_materialization_delta(
        self,
        request: MetaLanguageGeneratedMaterializationDeltaRenderRequest,
    ) -> bool:
        ...

    def render_generated_materialization_delta(
        self,
        request: MetaLanguageGeneratedMaterializationDeltaRenderRequest,
    ) -> MetaLanguageGeneratedMaterializationDeltaRenderResult:
        ...


__all__ = [
    "MetaLanguageGeneratedMaterializationDeltaContext",
    "MetaLanguageGeneratedMaterializationDeltaRenderer",
    "MetaLanguageGeneratedMaterializationDeltaRenderRequest",
    "MetaLanguageGeneratedMaterializationDeltaRenderResult",
    "MetaLanguageGeneratedMaterializationTargetHint",
]
