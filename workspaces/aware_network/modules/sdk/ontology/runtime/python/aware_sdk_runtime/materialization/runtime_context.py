from __future__ import annotations

from aware_code.semantic_materialization import (
    SemanticPackageMaterializationRuntimeContextRequest,
)
from aware_meta.runtime.factory import (
    build_meta_graph_runtime_for_aware_package_manifests,
)
from aware_meta.runtime.graph_context import (
    MetaWorkspaceMaterializationRuntimeContext,
    resolve_workspace_required_projection_package_manifest_paths,
)


def build_sdk_workspace_materialization_runtime_context(
    request: SemanticPackageMaterializationRuntimeContextRequest,
) -> MetaWorkspaceMaterializationRuntimeContext | None:
    """Build SDK's Workspace materialization context without parsing SDK TOML as OCG."""

    manifest_paths = resolve_workspace_required_projection_package_manifest_paths(
        request
    )
    if not manifest_paths:
        return None

    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=manifest_paths,
        workspace_root=request.workspace_root,
        composite_name="Aware SDK Workspace Materialization Context",
    )
    meta_context = runtime.context
    if meta_context is None:
        raise RuntimeError("SDK Meta graph runtime did not expose its graph context.")
    return MetaWorkspaceMaterializationRuntimeContext(
        meta_context=meta_context,
        runtime=runtime,
        actor_id=request.actor_id,
    )

__all__ = ["build_sdk_workspace_materialization_runtime_context"]
