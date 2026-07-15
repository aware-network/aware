from __future__ import annotations

from importlib import import_module
from typing import Any

__all__ = [
    "AppExperiencePackageReference",
    "AppPackageMaterializationResult",
    "AppScreenResolutionError",
    "AppScreenEntryResolutionError",
    "CommittedAppScreenEntryRequest",
    "CommittedAppScreenEntryResolution",
    "InterfacePackageMaterializationResult",
    "InterfacePackageMaterializationSpec",
    "materialize_app_package_snapshot",
    "materialize_interface_package_from_manifest",
    "resolve_committed_app_screen_entry",
    "resolve_interface_package_materialization_spec",
]


def __getattr__(name: str) -> Any:
    if name not in __all__:
        raise AttributeError(name)
    if name in {
        "AppScreenEntryResolutionError",
        "CommittedAppScreenEntryRequest",
        "CommittedAppScreenEntryResolution",
        "resolve_committed_app_screen_entry",
    }:
        module_name = "aware_interface.materialization.app_screen_entry"
    elif name in {
        "AppExperiencePackageReference",
        "AppPackageMaterializationResult",
        "AppScreenResolutionError",
        "materialize_app_package_snapshot",
    }:
        module_name = "aware_interface.materialization.app_package"
    else:
        module_name = "aware_interface.materialization.service"
    module = import_module(module_name)
    value = getattr(module, name)
    globals()[name] = value
    return value
