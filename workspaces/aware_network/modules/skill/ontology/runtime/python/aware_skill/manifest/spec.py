from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class AwareSkillCompilationMode(str, Enum):
    raw_xor = "raw_xor"
    skill_ontology = "skill_ontology"


class AwareSkillDependencyKind(str, Enum):
    package = "package"
    api = "api"
    api_package = "api_package"


@dataclass(frozen=True, slots=True)
class AwareSkillTomlPackageSpec:
    package_name: str
    fqn_prefix: str
    version_number: int = 1
    title: str | None = None
    description: str | None = None


@dataclass(frozen=True, slots=True)
class AwareSkillTomlBuildSpec:
    sources_dir: str = "skills"
    include_paths: list[str] = field(default_factory=lambda: ["**/*.aware"])
    exclude_paths: list[str] = field(default_factory=list)
    force_fresh_scan: bool = True
    compilation_mode: AwareSkillCompilationMode = AwareSkillCompilationMode.raw_xor


@dataclass(frozen=True, slots=True)
class AwareSkillTomlDependencySpec:
    package_name: str
    version_number: int | None = None
    kind: AwareSkillDependencyKind = AwareSkillDependencyKind.package
    expected_hash_sha256: str | None = None


@dataclass(frozen=True, slots=True)
class AwareSkillTomlSpec:
    aware_skill: int
    skill: AwareSkillTomlPackageSpec
    build: AwareSkillTomlBuildSpec
    dependencies: list[AwareSkillTomlDependencySpec]


__all__ = [
    "AwareSkillCompilationMode",
    "AwareSkillDependencyKind",
    "AwareSkillTomlBuildSpec",
    "AwareSkillTomlDependencySpec",
    "AwareSkillTomlPackageSpec",
    "AwareSkillTomlSpec",
]
