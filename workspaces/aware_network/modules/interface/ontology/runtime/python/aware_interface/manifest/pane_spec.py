from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class AwarePaneDependencyKind(str, Enum):
    experience_package = "experience_package"
    api_package = "api_package"


@dataclass(frozen=True, slots=True)
class AwarePaneTomlPackageSpec:
    package_name: str
    fqn_prefix: str
    pane_name: str
    version_number: int = 1
    title: str | None = None
    description: str | None = None


@dataclass(frozen=True, slots=True)
class AwarePaneTomlBuildSpec:
    sources_dir: str = "."
    include_paths: list[str] = field(default_factory=lambda: ["**/*.aware"])
    exclude_paths: list[str] = field(default_factory=list)
    force_fresh_scan: bool = True


@dataclass(frozen=True, slots=True)
class AwarePaneTomlPythonTextualSpec:
    module: str
    symbol: str


@dataclass(frozen=True, slots=True)
class AwarePaneTomlPythonSpec:
    package_path: str
    import_root: str
    textual: AwarePaneTomlPythonTextualSpec | None = None


@dataclass(frozen=True, slots=True)
class AwarePaneTomlDartFlutterSpec:
    library: str
    symbol: str


@dataclass(frozen=True, slots=True)
class AwarePaneTomlDartSpec:
    package_path: str
    package_name: str
    flutter: AwarePaneTomlDartFlutterSpec | None = None


@dataclass(frozen=True, slots=True)
class AwarePaneTomlDependencySpec:
    package_name: str
    version_number: int | None = None
    kind: AwarePaneDependencyKind = AwarePaneDependencyKind.experience_package
    description: str | None = None


@dataclass(frozen=True, slots=True)
class AwarePaneTomlSpec:
    aware_pane: int
    pane: AwarePaneTomlPackageSpec
    build: AwarePaneTomlBuildSpec
    dependencies: list[AwarePaneTomlDependencySpec] = field(default_factory=list)
    python: AwarePaneTomlPythonSpec | None = None
    dart: AwarePaneTomlDartSpec | None = None


__all__ = [
    "AwarePaneDependencyKind",
    "AwarePaneTomlBuildSpec",
    "AwarePaneTomlDependencySpec",
    "AwarePaneTomlDartFlutterSpec",
    "AwarePaneTomlDartSpec",
    "AwarePaneTomlPackageSpec",
    "AwarePaneTomlPythonSpec",
    "AwarePaneTomlPythonTextualSpec",
    "AwarePaneTomlSpec",
]
