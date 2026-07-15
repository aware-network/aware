from __future__ import annotations

from aware_code.language_service.features.diagnostics_capabilities.annotations import (
    collect_annotation_diagnostics,
)
from aware_code.language_service.features.diagnostics_capabilities.contracts import (
    AwareDiagnostic,
)
from aware_code.language_service.features.diagnostics_capabilities.defaults import (
    collect_default_value_diagnostics,
)
from aware_code.language_service.features.diagnostics_capabilities.executor import (
    DiagnosticsCapabilityContext,
)
from aware_code.language_service.features.diagnostics_capabilities.projection import (
    collect_projection_diagnostics,
)
from aware_code.language_service.features.diagnostics_capabilities.type_mirror import (
    collect_type_mirror_augment_diagnostics,
)
from aware_code.language_service.features.semantic_tokens_capabilities.annotations import (
    collect_annotation_path_tokens,
)
from aware_code.language_service.features.semantic_tokens_capabilities.aware_context import (
    collect_aware_contextual_tokens_for_owner_groups,
)
from aware_code.language_service.features.semantic_tokens_capabilities.collector import (
    SemanticTokenCollector,
)
from aware_code.semantic_capability import (
    SemanticAnalysisCapabilityRequest,
    SemanticAnalysisCapabilityResult,
)
from aware_meta.semantic_analysis import analyze_meta_ocg_semantic_capability


def _meta_object_config_graph_analysis_provider(
    request: SemanticAnalysisCapabilityRequest,
) -> SemanticAnalysisCapabilityResult:
    return analyze_meta_ocg_semantic_capability(request)


def _type_mirror_provider(context: DiagnosticsCapabilityContext) -> list[AwareDiagnostic]:
    return collect_type_mirror_augment_diagnostics(
        snapshot=context.snapshot,
        code=context.code,
        mapper=context.mapper,
        plugin=context.plugin,
        scope=context.scope,
        common_primitive_tokens=context.common_primitive_tokens,
        class_not_found_rx=context.class_not_found_rx,
        optional_list_rx=context.optional_list_rx,
    )


def _projection_provider(context: DiagnosticsCapabilityContext) -> list[AwareDiagnostic]:
    collect_projection_diagnostics(
        code=context.code,
        scope=context.scope,
        document_bytes=context.document_bytes,
        projection_root=context.projection_root,
        class_candidates=context.class_candidates,
        lookup=context.projection_lookup,
        add=context.add,
        suggest=context.suggest,
    )
    return []


def _defaults_provider(context: DiagnosticsCapabilityContext) -> list[AwareDiagnostic]:
    return collect_default_value_diagnostics(
        code=context.code,
        mapper=context.mapper,
        plugin=context.plugin,
    )


def _annotations_provider(context: DiagnosticsCapabilityContext) -> list[AwareDiagnostic]:
    collect_annotation_diagnostics(
        code=context.code,
        document_bytes=context.document_bytes,
        resolver=context.snapshot.fqn_resolver,
        scope=context.scope,
        class_candidates=context.class_candidates,
        enum_candidates=context.enum_candidates,
        add=context.add,
        suggest=context.suggest,
    )
    return []


def _meta_projection_tokens_provider(collector: SemanticTokenCollector) -> None:
    collect_aware_contextual_tokens_for_owner_groups(
        collector=collector,
        enabled_owner_groups=frozenset({"meta_projection"}),
    )


def _meta_identity_tokens_provider(collector: SemanticTokenCollector) -> None:
    collect_aware_contextual_tokens_for_owner_groups(
        collector=collector,
        enabled_owner_groups=frozenset({"meta_identity"}),
    )


def _annotation_path_tokens_provider(collector: SemanticTokenCollector) -> None:
    collect_annotation_path_tokens(collector=collector)
