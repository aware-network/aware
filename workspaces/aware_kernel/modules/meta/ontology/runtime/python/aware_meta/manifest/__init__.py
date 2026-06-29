"""Meta-owned manifest facade."""

from aware_meta.manifest.loader import (
    AwareTomlError,
    load_aware_toml_spec,
    load_aware_toml_spec_from_text,
)
from aware_meta.manifest.spec import (
    AwarePackageKind,
    AwareTomlBuildSpec,
    AwareTomlDependencySpec,
    AwareTomlLanguageMaterializationSpec,
    AwareTomlNamespaceMappingSpec,
    AwareTomlNamespaceSpec,
    AwareTomlPackageSpec,
    AwareTomlSpec,
)


__all__ = [
    "AwarePackageKind",
    "AwareTomlBuildSpec",
    "AwareTomlDependencySpec",
    "AwareTomlError",
    "AwareTomlLanguageMaterializationSpec",
    "AwareTomlNamespaceMappingSpec",
    "AwareTomlNamespaceSpec",
    "AwareTomlPackageSpec",
    "AwareTomlSpec",
    "load_aware_toml_spec",
    "load_aware_toml_spec_from_text",
]
