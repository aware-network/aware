from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING

_MODULE_EXPORTS: dict[str, tuple[str, ...]] = {
    ".package_ref_resolution": (
        "ResolvedSkillRuntimePackageRef",
        "SkillRuntimePackageRef",
        "resolve_committed_skill_runtime_package_ref",
        "resolve_committed_skill_runtime_package_refs",
    ),
}

_EXPORT_TO_MODULE: dict[str, str] = {
    export_name: module_name
    for module_name, export_names in _MODULE_EXPORTS.items()
    for export_name in export_names
}

__all__ = [
    "ResolvedSkillRuntimePackageRef",
    "SkillRuntimePackageRef",
    "resolve_committed_skill_runtime_package_ref",
    "resolve_committed_skill_runtime_package_refs",
]

if TYPE_CHECKING:
    from aware_skill.package_ref_resolution import (
        ResolvedSkillRuntimePackageRef,
        SkillRuntimePackageRef,
        resolve_committed_skill_runtime_package_ref,
        resolve_committed_skill_runtime_package_refs,
    )


def __getattr__(name: str) -> object:
    module_name = _EXPORT_TO_MODULE.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module = import_module(module_name, __name__)
    value = getattr(module, name)
    globals()[name] = value
    return value
