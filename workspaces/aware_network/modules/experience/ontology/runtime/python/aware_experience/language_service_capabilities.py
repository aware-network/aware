from __future__ import annotations

from aware_language_service.core.features.diagnostics_capabilities.contracts import (
    AwareDiagnostic,
)
from aware_language_service.core.features.diagnostics_capabilities.environment import (
    collect_environment_diagnostics,
)
from aware_language_service.core.features.diagnostics_capabilities.executor import (
    DiagnosticsCapabilityContext,
)
from aware_language_service.core.features.diagnostics_capabilities.experience import (
    collect_experience_diagnostics,
)
from aware_language_service.core.features.diagnostics_capabilities.program import (
    collect_program_diagnostics,
)
from aware_language_service.core.features.diagnostics_capabilities.role_actor import (
    collect_role_actor_diagnostics,
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
from aware_experience.semantic_analysis import analyze_experience_semantic_capability


def _experience_projection_provider(context: DiagnosticsCapabilityContext) -> list[AwareDiagnostic]:
    collect_experience_diagnostics(
        projection_root=context.projection_root,
        document_bytes=context.document_bytes,
        lookup=context.projection_lookup,
        add=context.add,
        suggest=context.suggest,
        uri=context.uri,
        uri_to_path=context.uri_to_path,
        enabled_groups=frozenset({"projection"}),
    )
    return []


def _experience_graph_provider(context: DiagnosticsCapabilityContext) -> list[AwareDiagnostic]:
    collect_experience_diagnostics(
        projection_root=context.projection_root,
        document_bytes=context.document_bytes,
        lookup=context.projection_lookup,
        add=context.add,
        suggest=context.suggest,
        uri=context.uri,
        uri_to_path=context.uri_to_path,
        enabled_groups=frozenset({"graph"}),
    )
    return []


def _experience_role_provider(context: DiagnosticsCapabilityContext) -> list[AwareDiagnostic]:
    collect_role_actor_diagnostics(
        projection_root=context.projection_root,
        document_bytes=context.document_bytes,
        scope=context.scope,
        class_candidates=context.class_candidates,
        add=context.add,
        suggest=context.suggest,
        enabled_groups=frozenset({"role"}),
    )
    return []


def _experience_actor_provider(context: DiagnosticsCapabilityContext) -> list[AwareDiagnostic]:
    collect_role_actor_diagnostics(
        projection_root=context.projection_root,
        document_bytes=context.document_bytes,
        scope=context.scope,
        class_candidates=context.class_candidates,
        add=context.add,
        suggest=context.suggest,
        enabled_groups=frozenset({"actor"}),
    )
    return []


def _environment_provider(context: DiagnosticsCapabilityContext) -> list[AwareDiagnostic]:
    collect_environment_diagnostics(
        projection_root=context.projection_root,
        document_bytes=context.document_bytes,
        add=context.add,
        suggest=context.suggest,
    )
    return []


def _program_provider(context: DiagnosticsCapabilityContext) -> list[AwareDiagnostic]:
    try:
        return collect_program_diagnostics(
            snapshot=context.snapshot,
            uri_to_path=context.uri_to_path,
            common_primitive_tokens=context.common_primitive_tokens,
            uri=context.uri,
            document_bytes=context.document_bytes,
            mapper=context.mapper,
        )
    except Exception:
        return []


def _experience_semantic_analysis_provider(
    request: SemanticAnalysisCapabilityRequest,
) -> SemanticAnalysisCapabilityResult:
    return analyze_experience_semantic_capability(request)


def _semantic_tokens_provider(
    collector: SemanticTokenCollector,
    *,
    owner_group: str,
) -> None:
    collect_aware_contextual_tokens_for_owner_groups(
        collector=collector,
        enabled_owner_groups=frozenset({owner_group}),
    )


def _experience_projection_tokens_provider(collector: SemanticTokenCollector) -> None:
    _semantic_tokens_provider(collector, owner_group="experience_projection")


def _experience_graph_tokens_provider(collector: SemanticTokenCollector) -> None:
    _semantic_tokens_provider(collector, owner_group="experience_graph")


def _experience_program_tokens_provider(collector: SemanticTokenCollector) -> None:
    _semantic_tokens_provider(collector, owner_group="experience_program")


def _experience_environment_tokens_provider(collector: SemanticTokenCollector) -> None:
    _semantic_tokens_provider(collector, owner_group="experience_environment")


def _experience_role_tokens_provider(collector: SemanticTokenCollector) -> None:
    _semantic_tokens_provider(collector, owner_group="experience_role")


def _experience_actor_tokens_provider(collector: SemanticTokenCollector) -> None:
    _semantic_tokens_provider(collector, owner_group="experience_actor")


def _experience_action_tokens_provider(collector: SemanticTokenCollector) -> None:
    _semantic_tokens_provider(collector, owner_group="experience_action")


def _experience_event_tokens_provider(collector: SemanticTokenCollector) -> None:
    _semantic_tokens_provider(collector, owner_group="experience_event")
