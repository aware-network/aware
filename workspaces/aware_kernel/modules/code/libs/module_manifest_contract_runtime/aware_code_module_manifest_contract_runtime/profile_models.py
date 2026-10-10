"""Immutable profile-manifest meaning; no source or execution authority."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CodeSemanticContractProfileProviderSpec:
    module_id: str
    provider_key: str
    required: bool = True
    status: str = "active"


@dataclass(frozen=True, slots=True)
class CodeSemanticContractProfileDescriptorSpec:
    key: str
    package_key: str
    runtime_import_mode: str = "dynamic_contract_module"
    runtime_import_required: bool = True
    status: str = "active"


@dataclass(frozen=True, slots=True)
class CodeSemanticContractProfileManifestSpec:
    aware_semantic_contract_profile: int
    profile: CodeSemanticContractProfileDescriptorSpec
    providers: tuple[CodeSemanticContractProfileProviderSpec, ...]
