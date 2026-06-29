from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class AwareSdkCompilationMode(str, Enum):
    raw_xor = "raw_xor"
    sdk_ontology = "sdk_ontology"


class AwareSdkDependencyKind(str, Enum):
    package = "package"
    api = "api"
    api_package = "api_package"
    sdk_package = "sdk_package"


@dataclass(frozen=True, slots=True)
class AwareSdkTomlPythonProductTargetSpec:
    package_dir: str | None = None
    root_dir: str | None = None


@dataclass(frozen=True, slots=True)
class AwareSdkTomlDartProductTargetSpec:
    package_dir: str | None = None
    root_dir: str | None = None


@dataclass(frozen=True, slots=True)
class AwareSdkTomlPythonTargetSpec:
    root_dir: str | None = None
    public_package: AwareSdkTomlPythonProductTargetSpec = field(default_factory=AwareSdkTomlPythonProductTargetSpec)


@dataclass(frozen=True, slots=True)
class AwareSdkTomlDartTargetSpec:
    root_dir: str | None = None
    public_package: AwareSdkTomlDartProductTargetSpec = field(default_factory=AwareSdkTomlDartProductTargetSpec)


@dataclass(frozen=True, slots=True)
class AwareSdkTomlTargetsSpec:
    python: AwareSdkTomlPythonTargetSpec | None = None
    dart: AwareSdkTomlDartTargetSpec | None = None


@dataclass(frozen=True, slots=True)
class AwareSdkTomlPackageSpec:
    package_name: str
    fqn_prefix: str
    version_number: int = 1
    title: str | None = None
    description: str | None = None


@dataclass(frozen=True, slots=True)
class AwareSdkTomlBuildSpec:
    sources_dir: str = "sdks"
    include_paths: list[str] = field(default_factory=lambda: ["**/*.aware"])
    exclude_paths: list[str] = field(default_factory=list)
    force_fresh_scan: bool = True
    compilation_mode: AwareSdkCompilationMode = AwareSdkCompilationMode.raw_xor


@dataclass(frozen=True, slots=True)
class AwareSdkTomlDependencySpec:
    package_name: str
    version_number: int | None = None
    kind: AwareSdkDependencyKind = AwareSdkDependencyKind.package
    expected_hash_sha256: str | None = None
    object_instance_graph_commit_id: str | None = None


@dataclass(frozen=True, slots=True)
class AwareSdkTomlObjectConfigGraphPackageSpec:
    manifest: str
    role: str = "local_state"
    description: str | None = None
    expected_hash_sha256: str | None = None
    object_instance_graph_commit_id: str | None = None


@dataclass(frozen=True, slots=True)
class AwareSdkTomlSpec:
    aware_sdk: int
    sdk: AwareSdkTomlPackageSpec
    build: AwareSdkTomlBuildSpec
    dependencies: list[AwareSdkTomlDependencySpec]
    object_config_graph_packages: list[AwareSdkTomlObjectConfigGraphPackageSpec] = field(default_factory=list)
    targets: AwareSdkTomlTargetsSpec = field(default_factory=AwareSdkTomlTargetsSpec)


__all__ = [
    "AwareSdkCompilationMode",
    "AwareSdkDependencyKind",
    "AwareSdkTomlBuildSpec",
    "AwareSdkTomlDartProductTargetSpec",
    "AwareSdkTomlDartTargetSpec",
    "AwareSdkTomlDependencySpec",
    "AwareSdkTomlObjectConfigGraphPackageSpec",
    "AwareSdkTomlPackageSpec",
    "AwareSdkTomlPythonProductTargetSpec",
    "AwareSdkTomlPythonTargetSpec",
    "AwareSdkTomlSpec",
    "AwareSdkTomlTargetsSpec",
]
