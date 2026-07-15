from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class AwareRenderComponentTomlPackageSpec:
    package_name: str
    fqn_prefix: str
    version_number: int = 1
    title: str | None = None
    description: str | None = None


@dataclass(frozen=True, slots=True)
class AwareRenderComponentTomlBuildSpec:
    sources_dir: str = "."
    include_paths: list[str] = field(default_factory=lambda: ["**/*.aware"])
    exclude_paths: list[str] = field(default_factory=list)
    force_fresh_scan: bool = True


@dataclass(frozen=True, slots=True)
class AwareRenderComponentTomlPythonTextualSpec:
    module: str
    symbol: str


@dataclass(frozen=True, slots=True)
class AwareRenderComponentTomlPythonSpec:
    package_path: str
    import_root: str
    textual: AwareRenderComponentTomlPythonTextualSpec | None = None


@dataclass(frozen=True, slots=True)
class AwareRenderComponentTomlDartFlutterSpec:
    library: str
    symbol: str


@dataclass(frozen=True, slots=True)
class AwareRenderComponentTomlDartSpec:
    package_path: str
    package_name: str
    flutter: AwareRenderComponentTomlDartFlutterSpec | None = None


@dataclass(frozen=True, slots=True)
class AwareRenderComponentTomlSpec:
    aware_render_component: int
    render_component: AwareRenderComponentTomlPackageSpec
    build: AwareRenderComponentTomlBuildSpec
    python: AwareRenderComponentTomlPythonSpec | None = None
    dart: AwareRenderComponentTomlDartSpec | None = None


__all__ = [
    "AwareRenderComponentTomlBuildSpec",
    "AwareRenderComponentTomlDartFlutterSpec",
    "AwareRenderComponentTomlDartSpec",
    "AwareRenderComponentTomlPackageSpec",
    "AwareRenderComponentTomlPythonSpec",
    "AwareRenderComponentTomlPythonTextualSpec",
    "AwareRenderComponentTomlSpec",
]
