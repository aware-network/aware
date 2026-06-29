from __future__ import annotations

from aware_code.semantic_materialization import (
    SemanticPackageMaterializationRuntimeContextRequest,
)
from aware_meta.runtime.graph_context import (
    MetaWorkspaceMaterializationRuntimeContext,
    build_meta_workspace_materialization_runtime_context,
)


def build_code_workspace_materialization_runtime_context(
    request: SemanticPackageMaterializationRuntimeContextRequest,
) -> MetaWorkspaceMaterializationRuntimeContext | None:
    return build_meta_workspace_materialization_runtime_context(request)


__all__ = ["build_code_workspace_materialization_runtime_context"]
