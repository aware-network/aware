from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class AwareApiCompilationMode(str, Enum):
    raw_xor = "raw_xor"
    api_ontology = "api_ontology"


class AwareApiSemanticPackageExportKind(str, Enum):
    api_dto = "api_dto"


@dataclass(frozen=True, slots=True)
class AwareApiTomlPythonProductTargetSpec:
    package_dir: str | None = None
    root_dir: str | None = None


@dataclass(frozen=True, slots=True)
class AwareApiTomlDartProductTargetSpec:
    package_dir: str | None = None
    root_dir: str | None = None


@dataclass(frozen=True, slots=True)
class AwareApiTomlPythonTargetSpec:
    root_dir: str | None = None
    public_package: AwareApiTomlPythonProductTargetSpec = field(default_factory=AwareApiTomlPythonProductTargetSpec)
    service_protocol: AwareApiTomlPythonProductTargetSpec = (
        field(default_factory=AwareApiTomlPythonProductTargetSpec)
    )


@dataclass(frozen=True, slots=True)
class AwareApiTomlDartTargetSpec:
    root_dir: str | None = None
    public_package: AwareApiTomlDartProductTargetSpec = field(default_factory=AwareApiTomlDartProductTargetSpec)


@dataclass(frozen=True, slots=True)
class AwareApiTomlTargetsSpec:
    python: AwareApiTomlPythonTargetSpec | None = None
    dart: AwareApiTomlDartTargetSpec | None = None


@dataclass(frozen=True, slots=True)
class AwareApiTomlPackageSpec:
    package_name: str
    fqn_prefix: str
    version_number: int = 1
    title: str | None = None
    description: str | None = None


@dataclass(frozen=True, slots=True)
class AwareApiTomlBuildSpec:
    sources_dir: str = "apis"
    include_paths: list[str] = field(default_factory=lambda: ["**/*.aware"])
    exclude_paths: list[str] = field(default_factory=list)
    force_fresh_scan: bool = True
    compilation_mode: AwareApiCompilationMode = AwareApiCompilationMode.raw_xor


@dataclass(frozen=True, slots=True)
class AwareApiTomlDependencySpec:
    package_name: str
    version_number: int | None = None


@dataclass(frozen=True, slots=True)
class AwareApiTomlSemanticPackageExportSpec:
    kind: AwareApiSemanticPackageExportKind
    package_name: str
    manifest_path: str
    code_package_surface: str
    workspace_materialization_primary: bool
    workspace_materialization_order: int
    workspace_materialization_branch: str
    workspace_materialization_commit: bool
    workspace_manifest_kind: str
    code_package_manifest_kind: str
    semantic_provider_key: str
    semantic_package_family: str
    semantic_package_kind: str
    semantic_package_name: str | None
    semantic_projection_name: str
    semantic_root_kind: str
    semantic_contract_role: str
    semantic_contract_name: str
    semantic_contract_provider_key: str
    semantic_contract_module: str


@dataclass(frozen=True, slots=True)
class AwareApiTomlSpec:
    aware_api: int
    api: AwareApiTomlPackageSpec
    build: AwareApiTomlBuildSpec
    dependencies: list[AwareApiTomlDependencySpec]
    targets: AwareApiTomlTargetsSpec = field(default_factory=AwareApiTomlTargetsSpec)
    semantic_package_exports: list[AwareApiTomlSemanticPackageExportSpec] = field(default_factory=list)


__all__ = [
    "AwareApiCompilationMode",
    "AwareApiSemanticPackageExportKind",
    "AwareApiTomlBuildSpec",
    "AwareApiTomlDartProductTargetSpec",
    "AwareApiTomlDartTargetSpec",
    "AwareApiTomlDependencySpec",
    "AwareApiTomlPackageSpec",
    "AwareApiTomlPythonProductTargetSpec",
    "AwareApiTomlPythonTargetSpec",
    "AwareApiTomlSemanticPackageExportSpec",
    "AwareApiTomlSpec",
    "AwareApiTomlTargetsSpec",
]
