from importlib import import_module
from typing import Any

_LAZY_EXPORTS = {
    "InterfaceActionPort": ".ports",
    "InterfaceActionReceipt": ".lifecycle",
    "InterfaceActionRequest": ".lifecycle",
    "InterfaceAttentionFocusTargetState": ".lifecycle",
    "InterfaceBackendState": ".lifecycle",
    "InterfaceCommitMaterializer": ".commit_materialization",
    "InterfaceExperiencePort": ".ports",
    "InterfaceGatePort": ".ports",
    "InterfaceGateState": ".lifecycle",
    "InterfaceGateStep": ".lifecycle",
    "InterfaceHostCapabilityAction": ".host_capabilities",
    "InterfaceHostCapabilityConsumer": ".host_capabilities",
    "InterfaceHostCapabilityOperation": ".host_capabilities",
    "InterfaceHostCapabilityScreen": ".host_capabilities",
    "InterfaceHostCapabilitySnapshot": ".host_capabilities",
    "InterfaceHostCapabilityTarget": ".host_capabilities",
    "InterfaceHostCapabilityTraceEntry": ".host_capabilities",
    "InterfaceHostRuntime": ".host_runtime",
    "InterfaceLaneStores": ".lane_stores",
    "InterfaceLaneSyncResult": ".lane_sync",
    "InterfaceLaneSyncService": ".lane_sync",
    "InterfaceLaneSyncSource": ".lane_sync",
    "InterfaceLocalDb": ".local_db",
    "InterfaceLocalDbConfig": ".local_db",
    "InterfaceMaterializationPostHashMismatchDetails": ".commit_materialization",
    "InterfaceMaterializationPostHashMismatchError": ".commit_materialization",
    "InterfaceMaterializedLane": ".commit_materialization",
    "InterfaceMaterializedPaneState": ".lifecycle",
    "InterfaceProjectionPlanBundle": ".projection_runtime",
    "InterfaceProjectionRuntime": ".projection_runtime",
    "InterfaceProjectionRuntimeResult": ".projection_runtime",
    "InterfaceRemoteLaneMaterialization": ".lane_sync",
    "InterfaceResolvedPaneDescriptor": ".lifecycle",
    "InterfaceResolvedSectionStateAddress": ".lifecycle",
    "InterfaceResolvedView": ".lifecycle",
    "InterfaceRuntimeCoordinator": ".lifecycle",
    "InterfaceRuntimeArtifactRef": ".runtime_artifact_refs",
    "InterfaceRuntimeFocusState": ".lifecycle",
    "InterfaceRuntimeFocusTarget": ".lifecycle",
    "InterfaceRuntimeLayoutState": ".lifecycle",
    "InterfaceRuntimePaneRenderSpecState": ".lifecycle",
    "InterfaceRuntimeSectionRepresentationState": ".lifecycle",
    "InterfaceRuntimeState": ".lifecycle",
    "InterfaceRuntimeWindowState": ".lifecycle",
    "InterfaceRuntimeWindowNavigationContextState": ".lifecycle",
    "InterfaceSessionPort": ".ports",
    "InterfaceNavigationContextLayoutPort": ".ports",
    "InterfaceNavigationContextLayoutTargetState": ".lifecycle",
    "InterfaceWindowLayoutSectionState": ".lifecycle",
    "InterfaceWindowLayoutState": ".lifecycle",
    "LocalCommitActionRecord": ".lane_stores",
    "LocalCommitRecord": ".lane_stores",
    "LocalLaneCommitRecord": ".lane_stores",
    "LocalLaneHeadRecord": ".lane_stores",
    "LocalProjectionCursorRecord": ".lane_stores",
    "LocalSnapshotRecord": ".lane_stores",
    "EnvironmentInterfaceGatePort": ".ports",
    "compose_interface_runtime_state": ".lifecycle",
    "describe_interface_backend_state": ".host_runtime",
    "load_workspace_interface_config_bundle": ".host_runtime",
    "runtime_artifact_refs_from_payload": ".runtime_artifact_refs",
    "resolve_bootstrap_window_layout_state": ".lifecycle",
    "resolve_bundle_backed_pane_descriptors": ".lifecycle",
}


def __getattr__(name: str) -> Any:
    module_name = _LAZY_EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module(module_name, __name__)
    value = getattr(module, name)
    globals()[name] = value
    return value


__all__ = sorted(_LAZY_EXPORTS)
