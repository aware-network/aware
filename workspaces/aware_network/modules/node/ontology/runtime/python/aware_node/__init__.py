"""Runtime package for the Node module."""

from importlib import import_module
from typing import Any

_LAZY_EXPORTS = {
    "NodeCompilePlan": ".compile",
    "NodeCompilePlanArtifact": ".compile",
    "NodeCompileResult": ".compile",
    "build_node_compile_plan": ".compile",
    "compile_node_workspace": ".compile",
    "emit_node_compile_plan_artifact": ".compile",
    "resolve_node_runtime_package_dir": ".compile",
    "NodeEnvironmentProfileMountOwnership": ".compiler",
    "NodeEnvironmentTargetOwnership": ".compiler",
    "NodeInterfaceTargetOwnership": ".compiler",
    "NodeOwnership": ".compiler",
    "NodeServiceTargetOwnership": ".compiler",
    "load_node_ownership_from_sources": ".compiler",
    "NodeRuntimeEnvironmentTarget": ".package_ref_resolution",
    "NodeRuntimeInterfaceTarget": ".package_ref_resolution",
    "NodeRuntimePackageDependency": ".package_ref_resolution",
    "NodeRuntimePackageRef": ".package_ref_resolution",
    "NodeRuntimeServiceTarget": ".package_ref_resolution",
    "ResolvedNodeRuntimePackageRef": ".package_ref_resolution",
    "resolve_committed_node_runtime_package_ref": ".package_ref_resolution",
    "resolve_committed_node_runtime_package_refs": ".package_ref_resolution",
    "NodeWorkspace": ".workspace",
    "NodeWorkspaceSnapshot": ".workspace",
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
