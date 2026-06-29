"""Compatibility facade for Code-owned module path helpers."""

from aware_code.module_manifest.paths import (
    ModuleOntologyPaths,
    resolve_module_ontology_paths,
)

__all__ = [
    "ModuleOntologyPaths",
    "resolve_module_ontology_paths",
]
