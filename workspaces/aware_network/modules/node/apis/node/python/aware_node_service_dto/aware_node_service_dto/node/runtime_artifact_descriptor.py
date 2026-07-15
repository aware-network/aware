from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)


class BundlePublicStructureContractVectorEntry(BaseModel):
    """
    Node-owned environment runtime artifact descriptor/trust contract.
    This is the public descriptor envelope emitted by Node HTTP artifact routes
    and consumed by Interface/session bootstrap. It is not Structure composition
    truth and must not be owned by Structure API.
    """

    # Attributes
    package_name: str
    package_kind: str
    contract_hash: str
    compatibility_class: str


class BundleModuleEvolutionRecord(BaseModel):
    # Attributes
    schema_version: int | None = Field(default=None)
    source_stage: str | None = Field(default=None)
    package_name: str
    package_kind: str
    package_version_number: int | None = Field(default=None)
    dependency_package_names: list[str] = Field(default_factory=list)
    ontology_anchor_package_name: str | None = Field(default=None)
    ontology_anchor_contract_hash: str | None = Field(default=None)
    ontology_anchor_commit_id: str | None = Field(default=None)
    runtime_revision: int | None = Field(default=None)
    representation_revision: int | None = Field(default=None)
    public_structure_contract_vector: list[BundlePublicStructureContractVectorEntry] = Field(default_factory=list)


class BundleReleaseIdentity(BaseModel):
    # Attributes
    schema_version: int
    environment_config_id: UUID
    module_evolution_record_vector: list[BundleModuleEvolutionRecord] = Field(default_factory=list)


class BundleModuleServiceProviderVectorEntry(BaseModel):
    # Attributes
    module_id: str
    provider_modules: list[str] = Field(default_factory=list)


class BundleCompatibilityPayload(BaseModel):
    # Attributes
    schema_version: int
    environment_id: UUID
    environment_config_id: UUID
    status: str
    ocg_hash: str | None = Field(default=None)
    opg_hashes: list[str] = Field(default_factory=list)
    bundle_head_id: str
    bundle_manifest_sha256: str
    bundle_manifest_size_bytes: int
    release_identity: BundleReleaseIdentity | None = Field(default=None)
    environment_service_provider_modules: list[str] = Field(default_factory=list)
    environment_module_service_provider_vector: list[BundleModuleServiceProviderVectorEntry] = Field(
        default_factory=list
    )


class BundleCompatibilitySignature(BaseModel):
    # Attributes
    schema_version: str
    algorithm: str
    signer_id: str | None = Field(default=None)
    key_id: str | None = Field(default=None)
    public_key: str | None = Field(default=None)
    payload_sha256: str
    signature: str


class EnvironmentBundleDescriptor(BaseModel):
    # Attributes
    environment_id: UUID
    environment_config_id: UUID
    environment_config_title: str | None = Field(default=None)
    environment_title: str | None = Field(default=None)
    status: str
    error: str | None = Field(default=None)
    ocg_hash: str | None = Field(default=None)
    opg_hashes: list[str] = Field(default_factory=list)
    bundle_manifest_http_path: str
    bundle_artifact_http_path_prefix: str
    bundle_head_id: str
    bundle_manifest_sha256: str
    bundle_manifest_size_bytes: int
    release_identity: BundleReleaseIdentity | None = Field(default=None)
    environment_service_provider_modules: list[str] = Field(default_factory=list)
    environment_module_service_provider_vector: list[BundleModuleServiceProviderVectorEntry] = Field(
        default_factory=list
    )
    compatibility_payload: BundleCompatibilityPayload
    compatibility_signature: BundleCompatibilitySignature


class EnvironmentBundleHints(BaseModel):
    # Attributes
    bundle_manifest_http_path: str | None = Field(default=None)
    bundle_artifact_http_path_prefix: str | None = Field(default=None)
    bundle_descriptor_http_path: str | None = Field(default=None)
    bundle_head_id: str | None = Field(default=None)
    bundle_release_identity: BundleReleaseIdentity | None = Field(default=None)
