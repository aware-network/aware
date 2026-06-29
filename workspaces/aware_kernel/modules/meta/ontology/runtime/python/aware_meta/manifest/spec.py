from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID


class AwarePackageKind(str, Enum):
    """Canonical package kind (SSOT: aware.toml)."""

    ontology = "ontology"
    api = "api"
    state = "state"


@dataclass(frozen=True, slots=True)
class AwareTomlPackageSpec:
    package_name: str
    fqn_prefix: str
    kind: AwarePackageKind
    # Canonical package version number (human-facing). Commit lineage can be resolved via lock/history later.
    version_number: int = 1
    title: str | None = None
    description: str | None = None
    # Package-level FunctionImpl execution authority.
    # - authored: generated/authored handlers remain execution authority.
    # - compiler: `.aware` FunctionImpl instruction bodies are execution authority.
    function_impl_ownership: str = "authored"
    # Package-level parity gate for FunctionImpl migration/proofs.
    function_impl_parity_policy: str = "off"


@dataclass(frozen=True, slots=True)
class AwareTomlNamespaceMappingSpec:
    path: str
    namespace: str


@dataclass(frozen=True, slots=True)
class AwareTomlNamespaceSpec:
    mappings: list[AwareTomlNamespaceMappingSpec] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class AwareTomlBuildSpec:
    environment_slug: str
    sources_dir: str = "aware"
    include_paths: list[str] = field(default_factory=lambda: ["**/*.aware"])
    exclude_paths: list[str] = field(default_factory=list)
    force_fresh_scan: bool = True
    namespace: AwareTomlNamespaceSpec = field(default_factory=AwareTomlNamespaceSpec)


@dataclass(frozen=True, slots=True)
class AwareTomlDependencySpec:
    package_name: str
    # Optional version pin (preferred over commit pins; lockfile may later make concrete).
    version_number: int | None = None
    # Transitional: optional commit pin (deprecated; retained for compatibility while OCGCommit is phased out).
    ocg_commit_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class AwareTomlLanguageMaterializationSpec:
    role: str
    language: str
    output_dir: str
    import_root: str
    package_name: str
    materialization_source: str = "ontology"
    renderer_kind: str | None = None
    renderer_profile: str | None = None
    stable_ids_import_root: str | None = None
    stable_ids_resolution_policy: str | None = None
    source_is_runtime: bool = False


@dataclass(frozen=True, slots=True)
class AwareTomlSpec:
    aware: int
    package: AwareTomlPackageSpec
    build: AwareTomlBuildSpec
    dependencies: list[AwareTomlDependencySpec]
    language_materializations: list[AwareTomlLanguageMaterializationSpec] = field(
        default_factory=list
    )


__all__ = [
    "AwareTomlSpec",
    "AwareTomlPackageSpec",
    "AwareTomlBuildSpec",
    "AwareTomlNamespaceMappingSpec",
    "AwareTomlNamespaceSpec",
    "AwareTomlDependencySpec",
    "AwareTomlLanguageMaterializationSpec",
    "AwarePackageKind",
]
