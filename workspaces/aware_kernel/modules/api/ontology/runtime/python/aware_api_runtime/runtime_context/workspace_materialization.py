from __future__ import annotations

from aware_code.semantic_materialization import (
    SEMANTIC_MATERIALIZATION_TARGET_MANIFEST_PATHS_CONTEXT_KEY,
    SemanticPackageMaterializationRuntimeContextRequest,
)
from aware_meta.runtime.graph_context import (
    MetaWorkspaceMaterializationRuntimeContext,
    build_meta_workspace_materialization_runtime_context,
)


def build_api_workspace_materialization_runtime_context(
    request: SemanticPackageMaterializationRuntimeContextRequest,
) -> MetaWorkspaceMaterializationRuntimeContext | None:
    """Build API's Workspace materialization runtime context through Meta."""

    return build_meta_workspace_materialization_runtime_context(
        _meta_runtime_context_request_for_api(request=request),
    )


def _meta_runtime_context_request_for_api(
    *,
    request: SemanticPackageMaterializationRuntimeContextRequest,
) -> SemanticPackageMaterializationRuntimeContextRequest:
    if not _is_api_dto_materialization_request(request=request):
        return request
    context = dict(request.context)
    context.pop(SEMANTIC_MATERIALIZATION_TARGET_MANIFEST_PATHS_CONTEXT_KEY, None)
    return SemanticPackageMaterializationRuntimeContextRequest(
        provider_key=request.provider_key,
        semantic_owner=request.semantic_owner,
        workspace_root=request.workspace_root,
        repo_root=request.repo_root,
        actor_id=request.actor_id,
        manifest_path=None,
        context=context,
        provider_payload=dict(request.provider_payload),
    )


def _is_api_dto_materialization_request(
    *,
    request: SemanticPackageMaterializationRuntimeContextRequest,
) -> bool:
    return (
        _context_text(request=request, key="workspace_manifest_kind") == "api_dto"
        or _context_text(request=request, key="semantic_package_kind")
        == "api_dto_package"
    )


def _context_text(
    *,
    request: SemanticPackageMaterializationRuntimeContextRequest,
    key: str,
) -> str:
    value = request.context.get(key)
    return str(value or "").strip()


__all__ = ["build_api_workspace_materialization_runtime_context"]
