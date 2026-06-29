"""Ontology manifest spec models for `aware.ontology.toml`."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AwareOntologyDescriptorSpec:
    package_name: str
    fqn_prefix: str
    source_manifest: str
    version_number: int = 1
    title: str | None = None
    description: str | None = None
    package_root: str = "."
    sources_root: str = "structure/ontology/aware"
    stable_ids_ownership: str = "authored"
    stable_ids_parity_policy: str = "warn"
    stable_ids_resolution_policy: str = "class_strict"
    function_impl_ownership: str = "authored"
    function_impl_parity_policy: str = "off"


@dataclass(frozen=True, slots=True)
class AwareOntologyRuntimeSpec:
    manifest: str
    project_name: str
    import_root: str


@dataclass(frozen=True, slots=True)
class AwareOntologySemanticContractSpec:
    provider_key: str
    role: str
    module: str
    contract: str = "aware.semantic_provider"
    owns_manifest_kinds: tuple[str, ...] = ()
    capabilities: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class AwareOntologyLayoutSpec:
    profile: str
    source_dir: str
    generated_dir: str
    runtime_dir: str
    orm_models_dir: str
    output_dirs: dict[str, dict[str, str]]


@dataclass(frozen=True, slots=True)
class AwareOntologyDependencySpec:
    package_name: str
    version_number: int | None = None
    expected_hash_sha256: str | None = None


@dataclass(frozen=True, slots=True)
class AwareOntologyLanguageMaterializationTargetSpec:
    role: str
    language: str
    output_dir: str
    import_root: str
    package_name: str
    materialization_source: str
    code_package_surface: str = "structure"
    source_is_runtime: bool = False
    renderer_profile: str | None = None
    renderer_kind: str | None = None
    stable_ids_import_root: str | None = None


@dataclass(frozen=True, slots=True)
class AwareOntologyTomlSpec:
    aware_ontology: int
    ontology: AwareOntologyDescriptorSpec
    runtime: AwareOntologyRuntimeSpec | None = None
    semantic_contract: AwareOntologySemanticContractSpec | None = None
    layout: AwareOntologyLayoutSpec | None = None
    dependencies: tuple[AwareOntologyDependencySpec, ...] = ()
    language_materialization_targets: tuple[
        AwareOntologyLanguageMaterializationTargetSpec,
        ...,
    ] = ()


__all__ = [
    "AwareOntologyDependencySpec",
    "AwareOntologyDescriptorSpec",
    "AwareOntologyLanguageMaterializationTargetSpec",
    "AwareOntologyLayoutSpec",
    "AwareOntologyRuntimeSpec",
    "AwareOntologySemanticContractSpec",
    "AwareOntologyTomlSpec",
]
