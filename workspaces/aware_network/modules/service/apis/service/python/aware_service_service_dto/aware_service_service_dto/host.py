from __future__ import annotations

# Standard
from enum import Enum
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import JsonObject


class ServiceHostContractCapabilityKey(Enum):
    """
    ServiceHost <-> ServiceProvider runtime contract DTOs.
    SSOT: `service-service-dto` generated from `apis/service/dto`.
    This file is intentionally separate from `comms/models/service.aware`.
    `comms` owns operation envelopes and transport control payloads; `host`
    owns the typed contract a ServiceHost uses to ask a hosted service provider
    what it requires to run under a Node-provided backend.
    """

    db_requirements = "db_requirements"
    projection_runtime_requirements = "projection_runtime_requirements"
    actor_context = "actor_context"
    service_contract = "service_contract"
    dependency_routes = "dependency_routes"
    runtime_session = "runtime_session"
    transport = "transport"


class ServiceHostDbRequirementKind(Enum):
    activation_projection = "activation_projection"
    ontology_authority = "ontology_authority"
    ontology_replica = "ontology_replica"
    local_state = "local_state"


class ServiceHostProjectionRuntimeRequirementKind(Enum):
    activation_projection = "activation_projection"
    experience_projection = "experience_projection"
    service_projection = "service_projection"


class ServiceHostContractStatus(Enum):
    succeeded = "succeeded"
    failed = "failed"
    pending = "pending"


class ServiceHostTargetContext(BaseModel):
    # Attributes
    service_package_name: str | None = Field(default=None)
    service_fqn_prefix: str | None = Field(default=None)
    service_toml_path: str | None = Field(default=None)
    service_import_root: str | None = Field(default=None)
    node_kind: str | None = Field(default=None)
    backend: str | None = Field(default=None)
    runtime_manifest_path: str | None = Field(default=None)
    artifact_root: str | None = Field(default=None)
    authority_root: str | None = Field(default=None)
    ontology_authority_source_kind: str | None = Field(default=None)
    ontology_authority_package_names: list[str] = Field(default_factory=list)
    implementation_toml_paths: list[str] = Field(default_factory=list)


class ServiceHostBackendContext(BaseModel):
    # Attributes
    backend_key: str = Field(default="default")
    persistence_backend: str | None = Field(default=None)
    adapter: str | None = Field(default=None)
    database_url_present: bool = Field(default=False)


class ServiceHostCapability(BaseModel):
    # Attributes
    capability_key: ServiceHostContractCapabilityKey
    required: bool = Field(default=True)
    status: str = Field(default="requested")
    description: str | None = Field(default=None)
    metadata: JsonObject = Field(default_factory=JsonObject)


class ServiceHostDbRequirement(BaseModel):
    # Attributes
    kind: ServiceHostDbRequirementKind
    provider_key: str | None = Field(default=None)
    package_name: str | None = Field(default=None)
    package_names: list[str] = Field(default_factory=list)
    role: str | None = Field(default=None)
    requirement_mode: str = Field(default="required")
    schema_scope: str | None = Field(default=None)
    manifest_paths: list[str] = Field(default_factory=list)
    sql_roots: list[str] = Field(default_factory=list)
    db_schema_hash: str | None = Field(default=None)
    authority: bool = Field(default=False)
    required: bool = Field(default=True)
    description: str | None = Field(default=None)
    metadata: JsonObject = Field(default_factory=JsonObject)


class ServiceHostDbRequirementPlan(BaseModel):
    # Attributes
    requirements: list[ServiceHostDbRequirement] = Field(default_factory=list)
    metadata: JsonObject = Field(default_factory=JsonObject)


class ServiceHostProjectionRuntimeRequirement(BaseModel):
    # Attributes
    kind: ServiceHostProjectionRuntimeRequirementKind
    provider_key: str | None = Field(default=None)
    package_name: str | None = Field(default=None)
    package_names: list[str] = Field(default_factory=list)
    projection_name: str | None = Field(default=None)
    projection_names: list[str] = Field(default_factory=list)
    role: str | None = Field(default=None)
    requirement_mode: str = Field(default="required")
    required: bool = Field(default=True)
    description: str | None = Field(default=None)
    metadata: JsonObject = Field(default_factory=JsonObject)


class ServiceHostProjectionRuntimeRequirementPlan(BaseModel):
    # Attributes
    requirements: list[ServiceHostProjectionRuntimeRequirement] = Field(default_factory=list)
    metadata: JsonObject = Field(default_factory=JsonObject)


class ServiceHostRuntimeRequirementReceipt(BaseModel):
    # Attributes
    capability_key: ServiceHostContractCapabilityKey
    status: ServiceHostContractStatus = Field(default=ServiceHostContractStatus.succeeded)
    requirement_kind: ServiceHostDbRequirementKind | None = Field(default=None)
    projection_requirement_kind: ServiceHostProjectionRuntimeRequirementKind | None = Field(default=None)
    requirement_count: int = Field(default=0)
    installed_count: int = Field(default=0)
    skipped_count: int = Field(default=0)
    error: str | None = Field(default=None)
    evidence: JsonObject = Field(default_factory=JsonObject)


class ServiceHostContractRequest(BaseModel):
    # Attributes
    request_id: UUID | None = Field(default=None)
    target: ServiceHostTargetContext
    backend: ServiceHostBackendContext
    capabilities: list[ServiceHostCapability] = Field(default_factory=list)


class ServiceHostContractResponse(BaseModel):
    # Attributes
    request_id: UUID | None = Field(default=None)
    status: ServiceHostContractStatus = Field(default=ServiceHostContractStatus.succeeded)
    error: str | None = Field(default=None)
    capabilities: list[ServiceHostCapability] = Field(default_factory=list)
    db_requirement_plan: ServiceHostDbRequirementPlan | None = Field(default=None)
    projection_runtime_requirement_plan: ServiceHostProjectionRuntimeRequirementPlan | None = Field(default=None)
    receipts: list[ServiceHostRuntimeRequirementReceipt] = Field(default_factory=list)
    metadata: JsonObject = Field(default_factory=JsonObject)
