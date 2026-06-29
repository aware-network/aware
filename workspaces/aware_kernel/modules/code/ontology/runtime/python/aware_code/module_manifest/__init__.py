"""Code-owned module contract rails for `aware.module.toml`."""

from aware_code.module_manifest.loader import (
    AwareModuleTomlError,
    load_aware_module_spec,
)
from aware_code.module_manifest.paths import (
    ModuleOntologyPaths,
    resolve_module_ontology_paths,
)
from aware_code.module_manifest.scaffold import (
    ModuleScaffoldResult,
    ModuleScaffoldSpec,
    build_module_scaffold_files,
    build_module_scaffold_spec,
    scaffold_module,
)
from aware_code.module_manifest.spec import (
    AwareModulePackageSpec,
    AwareModulePluginSpec,
    AwareModuleRuntimeSpec,
    AwareModuleServiceSpec,
    AwareModuleSpec,
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
