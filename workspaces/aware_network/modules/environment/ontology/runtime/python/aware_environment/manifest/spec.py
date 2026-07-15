from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class AwareEnvironmentProfileTomlPackageSpec:
    package_name: str
    profile_key: str
    environment_handle: str
    version_number: int = 1
    title: str | None = None
    description: str | None = None


@dataclass(frozen=True, slots=True)
class AwareEnvironmentProfileTomlBuildSpec:
    sources_dir: str = "profiles"
    include_paths: list[str] = field(default_factory=lambda: ["**/*.aware"])
    exclude_paths: list[str] = field(default_factory=list)
    force_fresh_scan: bool = True


@dataclass(frozen=True, slots=True)
class AwareEnvironmentProfileTomlDependencySpec:
    package_name: str
    version_number: int | None = None
    expected_hash_sha256: str | None = None


@dataclass(frozen=True, slots=True)
class AwareEnvironmentProfileTomlSpec:
    aware_environment_profile: int
    environment_profile: AwareEnvironmentProfileTomlPackageSpec
    build: AwareEnvironmentProfileTomlBuildSpec
    dependencies: list[AwareEnvironmentProfileTomlDependencySpec] = field(
        default_factory=list
    )


__all__ = [
    "AwareEnvironmentProfileTomlBuildSpec",
    "AwareEnvironmentProfileTomlDependencySpec",
    "AwareEnvironmentProfileTomlPackageSpec",
    "AwareEnvironmentProfileTomlSpec",
]
