from __future__ import annotations

from aware_code.semantic_materialization import (
    SemanticPackageMaterializationRuntimeContextRequest,
)
from aware_meta.runtime.graph_context import (
    MetaWorkspaceMaterializationRuntimeContext,
    build_meta_workspace_materialization_runtime_context,
)

MaterializationRuntimeContext = MetaWorkspaceMaterializationRuntimeContext


def ensure_materialization_runtime_context(
    *,
    request: SemanticPackageMaterializationRuntimeContextRequest,
) -> MetaWorkspaceMaterializationRuntimeContext | None:
    """Build the Meta-owned workspace materialization context from semantic input."""

    return build_meta_workspace_materialization_runtime_context(request)


__all__ = [
    "MaterializationRuntimeContext",
    "MetaWorkspaceMaterializationRuntimeContext",
    "build_meta_workspace_materialization_runtime_context",
    "ensure_materialization_runtime_context",
]
