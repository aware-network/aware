from __future__ import annotations

from aware_code.semantic_capability import (
    SemanticAnalysisCapabilityRequest,
    SemanticAnalysisCapabilityResult,
)
from aware_node.semantic_analysis import analyze_node_semantic_capability


def _node_semantic_analysis_provider(
    request: SemanticAnalysisCapabilityRequest,
) -> SemanticAnalysisCapabilityResult:
    return analyze_node_semantic_capability(request)


__all__ = ["_node_semantic_analysis_provider"]
