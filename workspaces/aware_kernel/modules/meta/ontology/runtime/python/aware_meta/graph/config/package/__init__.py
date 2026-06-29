"""Package ontology builder utilities for aware.toml-backed package objects."""

from aware_meta.graph.config.package.builder import (
    AwareTomlBuildError,
    build_packages_from_specs,
)

__all__ = [
    "AwareTomlBuildError",
    "build_packages_from_specs",
]
