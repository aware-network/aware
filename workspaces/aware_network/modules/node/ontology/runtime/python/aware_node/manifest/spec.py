from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class AwareNodeCompilationMode(str, Enum):
    raw_xor = "raw_xor"
    node_ontology = "node_ontology"


class AwareNodeDependencyKind(str, Enum):
    package = "package"
    environment_package = "environment_package"
    experience_package = "experience_package"
    ontology_package = "ontology_package"
    service_package = "service_package"
    interface_package = "interface_package"


@dataclass(frozen=True, slots=True)
class AwareNodeTomlPackageSpec:
    package_name: str
    fqn_prefix: str
    version_number: int = 1
    title: str | None = None
    description: str | None = None


@dataclass(frozen=True, slots=True)
class AwareNodeTomlBuildSpec:
    sources_dir: str = "nodes"
    include_paths: list[str] = field(default_factory=lambda: ["**/*.aware"])
    exclude_paths: list[str] = field(default_factory=list)
    force_fresh_scan: bool = True
    compilation_mode: AwareNodeCompilationMode = AwareNodeCompilationMode.raw_xor


@dataclass(frozen=True, slots=True)
class AwareNodeTomlDependencySpec:
    package_name: str
    version_number: int | None = None
    kind: AwareNodeDependencyKind = AwareNodeDependencyKind.package


@dataclass(frozen=True, slots=True)
class AwareNodeTomlSpec:
    aware_node: int
    node: AwareNodeTomlPackageSpec
    build: AwareNodeTomlBuildSpec
    dependencies: list[AwareNodeTomlDependencySpec]


__all__ = [
    "AwareNodeCompilationMode",
    "AwareNodeDependencyKind",
    "AwareNodeTomlBuildSpec",
    "AwareNodeTomlDependencySpec",
    "AwareNodeTomlPackageSpec",
    "AwareNodeTomlSpec",
]
