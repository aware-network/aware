"""Compatibility facade for Code-owned `aware.module.toml` rails."""

from aware_code.module_manifest import (
    AwareModulePackageSpec,
    AwareModulePluginSpec,
    AwareModuleRuntimeSpec,
    AwareModuleServiceSpec,
    AwareModuleSpec,
    AwareModuleTomlError,
    ModuleOntologyPaths,
    ModuleScaffoldResult,
    ModuleScaffoldSpec,
    build_module_scaffold_files,
    build_module_scaffold_spec,
    load_aware_module_spec,
    resolve_module_ontology_paths,
    scaffold_module,
)

__all__ = [
    "AwareModulePackageSpec",
    "AwareModulePluginSpec",
    "AwareModuleRuntimeSpec",
    "AwareModuleServiceSpec",
    "AwareModuleSpec",
    "AwareModuleTomlError",
    "ModuleOntologyPaths",
    "ModuleScaffoldResult",
    "ModuleScaffoldSpec",
    "build_module_scaffold_files",
    "build_module_scaffold_spec",
    "load_aware_module_spec",
    "resolve_module_ontology_paths",
    "scaffold_module",
]
