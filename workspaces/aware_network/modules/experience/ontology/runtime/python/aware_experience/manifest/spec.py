from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class AwareExperienceDependencyKind(str, Enum):
    experience_package = "experience_package"
    attention_package = "attention_package"
    ontology_package = "ontology_package"


@dataclass(frozen=True, slots=True)
class AwareExperienceTomlPackageSpec:
    package_name: str
    fqn_prefix: str
    version_number: int = 1
    title: str | None = None
    description: str | None = None


@dataclass(frozen=True, slots=True)
class AwareExperienceTomlBuildSpec:
    environment_handle: str
    sources_dir: str = "experiences"
    include_paths: list[str] = field(default_factory=lambda: ["**/*.aware"])
    exclude_paths: list[str] = field(default_factory=list)
    force_fresh_scan: bool = True


@dataclass(frozen=True, slots=True)
class AwareExperienceTomlDependencySpec:
    package_name: str
    kind: AwareExperienceDependencyKind
    version_number: int | None = None


@dataclass(frozen=True, slots=True)
class AwareExperienceTomlLanguageTargetSpec:
    language: str
    root_dir: str
    package_dir: str


@dataclass(frozen=True, slots=True)
class AwareExperienceTomlSpec:
    aware_experience: int
    experience: AwareExperienceTomlPackageSpec
    build: AwareExperienceTomlBuildSpec
    dependencies: list[AwareExperienceTomlDependencySpec]
    targets: dict[str, AwareExperienceTomlLanguageTargetSpec] = field(
        default_factory=dict
    )


__all__ = [
    "AwareExperienceTomlSpec",
    "AwareExperienceTomlPackageSpec",
    "AwareExperienceTomlBuildSpec",
    "AwareExperienceDependencyKind",
    "AwareExperienceTomlDependencySpec",
    "AwareExperienceTomlLanguageTargetSpec",
]
