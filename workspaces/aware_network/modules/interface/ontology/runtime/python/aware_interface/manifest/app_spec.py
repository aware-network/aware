from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class AwareAppTomlPackageSpec:
    package_name: str
    app_name: str
    fqn_prefix: str
    kind: str = "app"
    version_number: int = 1
    title: str | None = None
    description: str | None = None


@dataclass(frozen=True, slots=True)
class AwareAppTomlDartSpec:
    package_path: str
    package_name: str
    entrypoint: str = "lib/main.dart"


@dataclass(frozen=True, slots=True)
class AwareAppTomlFactorySpec:
    package_name: str
    package_path: str | None = None


@dataclass(frozen=True, slots=True)
class AwareAppTomlBuildSpec:
    sources_dir: str = "."
    include_paths: tuple[str, ...] = ("*.aware",)
    exclude_paths: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class AwareAppTomlDependencySpec:
    package_name: str
    kind: str
    role: str


@dataclass(frozen=True, slots=True)
class AwareAppTomlControlSpec:
    requires_actor: bool = True
    default_screen: str = "control"
    admitted_screen: str | None = None


@dataclass(frozen=True, slots=True)
class AwareAppTomlLaunchSpec:
    seed_color_value: int = 0xFF2563EB
    generated_manifest_path: str = "lib/aware_app_launch_manifest.g.dart"


@dataclass(frozen=True, slots=True)
class AwareAppTomlPlatformSpec:
    target: str
    runner_path: str
    materializer: str = "flutter_create"
    binary_name: str | None = None
    application_id: str | None = None
    enabled: bool = True


@dataclass(frozen=True, slots=True)
class AwareAppTomlInterfaceSpec:
    package_name: str
    role: str
    runtime_import: str | None = None
    runtime_import_alias: str | None = None
    runtime_factory: str = "buildInterfacePackageRuntime"


@dataclass(frozen=True, slots=True)
class AwareAppTomlSpec:
    aware_app: int
    app: AwareAppTomlPackageSpec
    dart: AwareAppTomlDartSpec
    factory: AwareAppTomlFactorySpec
    build: AwareAppTomlBuildSpec = field(default_factory=AwareAppTomlBuildSpec)
    dependencies: list[AwareAppTomlDependencySpec] = field(default_factory=list)
    control: AwareAppTomlControlSpec = field(default_factory=AwareAppTomlControlSpec)
    launch: AwareAppTomlLaunchSpec = field(default_factory=AwareAppTomlLaunchSpec)
    platforms: list[AwareAppTomlPlatformSpec] = field(default_factory=list)
    interfaces: list[AwareAppTomlInterfaceSpec] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class AwareAppScreenSourceSpec:
    screen_key: str
    projection_experience: str
    projection_experience_layout: str
    source_path: str


@dataclass(frozen=True, slots=True)
class AwareAppSourceSpec:
    name: str
    title: str | None
    description: str | None
    screens: tuple[AwareAppScreenSourceSpec, ...]
    source_path: str


__all__ = [
    "AwareAppScreenSourceSpec",
    "AwareAppSourceSpec",
    "AwareAppTomlBuildSpec",
    "AwareAppTomlControlSpec",
    "AwareAppTomlDependencySpec",
    "AwareAppTomlDartSpec",
    "AwareAppTomlFactorySpec",
    "AwareAppTomlInterfaceSpec",
    "AwareAppTomlLaunchSpec",
    "AwareAppTomlPackageSpec",
    "AwareAppTomlPlatformSpec",
    "AwareAppTomlSpec",
]
