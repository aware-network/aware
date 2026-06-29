"""Compatibility facade for Code-owned module scaffold helpers."""

from aware_code.module_manifest.scaffold import (
    ModulePackageRegistration,
    ModuleScaffoldResult,
    ModuleScaffoldSpec,
    build_module_package_registrations,
    build_module_scaffold_files,
    build_module_scaffold_spec,
    scaffold_module,
)

__all__ = [
    "ModulePackageRegistration",
    "ModuleScaffoldResult",
    "ModuleScaffoldSpec",
    "build_module_package_registrations",
    "build_module_scaffold_files",
    "build_module_scaffold_spec",
    "scaffold_module",
]
