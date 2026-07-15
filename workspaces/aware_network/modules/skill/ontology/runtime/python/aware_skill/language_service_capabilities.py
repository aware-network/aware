from __future__ import annotations

from aware_code.semantic_capability import (
    SemanticAnalysisCapabilityRequest,
    SemanticAnalysisCapabilityResult,
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
from aware_skill.semantic_analysis import analyze_skill_semantic_capability


def _skill_config_diagnostics_provider(
    context: DiagnosticsCapabilityContext,
) -> list[AwareDiagnostic]:
    del context
    return []


def _skill_api_diagnostics_provider(
    context: DiagnosticsCapabilityContext,
) -> list[AwareDiagnostic]:
    del context
    return []


def _skill_endpoint_diagnostics_provider(
    context: DiagnosticsCapabilityContext,
) -> list[AwareDiagnostic]:
    del context
    return []


def _skill_step_diagnostics_provider(
    context: DiagnosticsCapabilityContext,
) -> list[AwareDiagnostic]:
    del context
    return []


def _skill_semantic_analysis_provider(
    request: SemanticAnalysisCapabilityRequest,
) -> SemanticAnalysisCapabilityResult:
    return analyze_skill_semantic_capability(request)


def _semantic_tokens_provider(
    collector: SemanticTokenCollector,
    *,
    owner_group: str,
) -> None:
    collect_aware_contextual_tokens_for_owner_groups(
        collector=collector,
        enabled_owner_groups=frozenset({owner_group}),
    )


def _skill_config_tokens_provider(collector: SemanticTokenCollector) -> None:
    _semantic_tokens_provider(collector, owner_group="skill_config")


def _skill_api_tokens_provider(collector: SemanticTokenCollector) -> None:
    _semantic_tokens_provider(collector, owner_group="skill_api")


def _skill_endpoint_tokens_provider(collector: SemanticTokenCollector) -> None:
    _semantic_tokens_provider(collector, owner_group="skill_endpoint")


def _skill_step_tokens_provider(collector: SemanticTokenCollector) -> None:
    _semantic_tokens_provider(collector, owner_group="skill_step")
