from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class AwareInterfaceCompilationMode(str, Enum):
    raw_xor = "raw_xor"
    interface_ontology = "interface_ontology"


class AwareInterfaceDependencyKind(str, Enum):
    package = "package"
    attention_package = "attention_package"
    experience_package = "experience_package"
    pane_package = "pane_package"
    render_component_package = "render_component_package"


@dataclass(frozen=True, slots=True)
class AwareInterfaceTomlPackageSpec:
    package_name: str
    fqn_prefix: str
    version_number: int = 1
    title: str | None = None
    description: str | None = None


@dataclass(frozen=True, slots=True)
class AwareInterfaceTomlBuildSpec:
    config_bundle_path: str
    sources_dir: str = "."
    include_paths: list[str] = field(default_factory=lambda: ["**/*.aware"])
    exclude_paths: list[str] = field(default_factory=list)
    force_fresh_scan: bool = True
    compilation_mode: AwareInterfaceCompilationMode = AwareInterfaceCompilationMode.raw_xor


@dataclass(frozen=True, slots=True)
class AwareInterfaceTomlDartSpec:
    package_path: str
    package_name: str


@dataclass(frozen=True, slots=True)
class AwareInterfaceTomlDependencySpec:
    package_name: str
    version_number: int | None = None
    kind: AwareInterfaceDependencyKind = AwareInterfaceDependencyKind.package


@dataclass(frozen=True, slots=True)
class AwareInterfaceTomlSpec:
    aware_interface: int
    interface: AwareInterfaceTomlPackageSpec
    build: AwareInterfaceTomlBuildSpec
    dart: AwareInterfaceTomlDartSpec | None = None
    dependencies: list[AwareInterfaceTomlDependencySpec] = field(default_factory=list)


__all__ = [
    "AwareInterfaceCompilationMode",
    "AwareInterfaceTomlBuildSpec",
    "AwareInterfaceTomlDartSpec",
    "AwareInterfaceTomlDependencySpec",
    "AwareInterfaceDependencyKind",
    "AwareInterfaceTomlPackageSpec",
    "AwareInterfaceTomlSpec",
]
