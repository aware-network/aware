from __future__ import annotations

from aware_language_service.core.features.diagnostics_capabilities.api import (
    collect_api_diagnostics,
)
from aware_language_service.core.features.diagnostics_capabilities.contracts import (
    AwareDiagnostic,
)
from aware_language_service.core.features.diagnostics_capabilities.executor import (
    DiagnosticsCapabilityContext,
)
from aware_language_service.core.features.semantic_tokens_capabilities.aware_context import (
    collect_aware_contextual_tokens_for_owner_groups,
)
from aware_language_service.core.features.semantic_tokens_capabilities.collector import (
    SemanticTokenCollector,
)
from aware_code.semantic_capability import (
    SemanticAnalysisCapabilityRequest,
    SemanticAnalysisCapabilityResult,
)

from aware_api_runtime.source.semantic_analysis import analyze_api_semantic_capability


def _api_root_diagnostics_provider(
    context: DiagnosticsCapabilityContext,
) -> list[AwareDiagnostic]:
    collect_api_diagnostics(
        projection_root=context.projection_root,
        document_bytes=context.document_bytes,
        snapshot=context.snapshot,
        lookup=context.projection_lookup,
        add=context.add,
        suggest=context.suggest,
        enabled_groups=frozenset({"api"}),
    )
    return []


def _api_projection_diagnostics_provider(
    context: DiagnosticsCapabilityContext,
) -> list[AwareDiagnostic]:
    collect_api_diagnostics(
        projection_root=context.projection_root,
        document_bytes=context.document_bytes,
        snapshot=context.snapshot,
        lookup=context.projection_lookup,
        add=context.add,
        suggest=context.suggest,
        enabled_groups=frozenset({"projection"}),
    )
    return []


def _api_semantic_analysis_provider(
    request: SemanticAnalysisCapabilityRequest,
) -> SemanticAnalysisCapabilityResult:
    return analyze_api_semantic_capability(request)


def _semantic_tokens_provider(
    collector: SemanticTokenCollector,
    *,
    owner_group: str,
) -> None:
    collect_aware_contextual_tokens_for_owner_groups(
        collector=collector,
        enabled_owner_groups=frozenset({owner_group}),
    )


def _api_tokens_provider(collector: SemanticTokenCollector) -> None:
    _semantic_tokens_provider(collector, owner_group="api_api")


def _api_capability_tokens_provider(collector: SemanticTokenCollector) -> None:
    _semantic_tokens_provider(collector, owner_group="api_capability")


def _api_graph_tokens_provider(collector: SemanticTokenCollector) -> None:
    _semantic_tokens_provider(collector, owner_group="api_graph")


def _api_projection_tokens_provider(collector: SemanticTokenCollector) -> None:
    _semantic_tokens_provider(collector, owner_group="api_projection")
