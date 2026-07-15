from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import JsonObject


class OntologyRuntimeArtifactRef(BaseModel):
    """
    Ontology runtime artifact-set DTOs.
    This is the ontology-owned descriptor for artifacts produced by ontology
    materialization and later carried by WorkspaceRevision or Hub. Resolving an
    artifact set is provenance-only; it does not activate or upgrade a running
    service runtime.
    """

    # Attributes
    artifact_family: str
    artifact_key: str
    artifact_role: str = Field(default="runtime")
    output_key: str | None = Field(default=None)
    output_kind: str | None = Field(default=None)
    required_for: list[str] = Field(default_factory=list)
    status: str = Field(default="available")
    producer_provider_key: str | None = Field(default=None)
    producer_key: str | None = Field(default=None)
    producer_kind: str | None = Field(default=None)
    package_name: str | None = Field(default=None)
    fqn_prefix: str | None = Field(default=None)
    digest: str | None = Field(default=None)
    digest_algorithm: str = Field(default="sha256")
    uri: str | None = Field(default=None)
    workspace_relative_path: str | None = Field(default=None)
    manifest_path: str | None = Field(default=None)
    media_type: str | None = Field(default=None)
    size_bytes: int | None = Field(default=None)
    runtime_contract_version: str | None = Field(default=None)
    provider_payload: JsonObject = Field(default_factory=JsonObject)
    receipt: JsonObject = Field(default_factory=JsonObject)
    error: str | None = Field(default=None)


class OntologyMaterializedSemanticRootRef(BaseModel):
    # Attributes
    semantic_root_kind: str
    semantic_projection_name: str
    semantic_projection_hash: str | None = Field(default=None)
    semantic_package_id: UUID | None = Field(default=None)
    semantic_root_id: UUID | None = Field(default=None)
    semantic_head_commit_id: UUID | None = Field(default=None)
    semantic_object_instance_graph_commit_id: UUID | None = Field(default=None)
    semantic_root_object_instance_graph_commit_id: UUID | None = Field(default=None)


class OntologyRuntimeArtifactSetProvenance(BaseModel):
    # Attributes
    source_kind: str = Field(default="ontology_materialization")
    workspace_revision_id: str | None = Field(default=None)
    workspace_revision_commit_id: str | None = Field(default=None)
    workspace_deployment_revision_id: str | None = Field(default=None)
    workspace_deployment_channel: str | None = Field(default=None)
    workspace_deployment_artifact_key: str | None = Field(default=None)
    hub_artifact_revision_id: str | None = Field(default=None)
    materialization_ref: str | None = Field(default=None)
    materialization_index: int | None = Field(default=None)
    ontology_config_id: UUID | None = Field(default=None)
    ontology_config_commit_id: UUID | None = Field(default=None)
    ontology_config_head_commit_id: UUID | None = Field(default=None)
    ontology_config_object_instance_graph_commit_id: UUID | None = Field(default=None)
    ontology_package_id: UUID | None = Field(default=None)
    ontology_package_commit_id: UUID | None = Field(default=None)
    ontology_package_head_commit_id: UUID | None = Field(default=None)
    ontology_package_object_instance_graph_commit_id: UUID | None = Field(default=None)
    object_config_graph_id: UUID | None = Field(default=None)
    object_config_graph_commit_id: UUID | None = Field(default=None)
    object_config_graph_package_id: UUID | None = Field(default=None)
    source_code_package_id: UUID | None = Field(default=None)
    source_code_package_commit_id: UUID | None = Field(default=None)
    source_manifest_path: str | None = Field(default=None)
    ontology_manifest_path: str | None = Field(default=None)
    producer_receipt: JsonObject = Field(default_factory=JsonObject)


class OntologyRuntimeProjectionDescriptor(BaseModel):
    # Attributes
    projection_name: str
    projection_hash: str | None = Field(default=None)
    object_projection_graph_id: UUID | None = Field(default=None)
    constructor_function_id: UUID | None = Field(default=None)
    object_config_graph_id: UUID | None = Field(default=None)
    opg_hashes: list[str] = Field(default_factory=list)
    required_for: list[str] = Field(default_factory=list)
    metadata: JsonObject = Field(default_factory=JsonObject)


class OntologyRuntimeArtifactSet(BaseModel):
    # Attributes
    schema_version: int = Field(default=1)
    artifact_set_id: str
    package_name: str
    fqn_prefix: str
    runtime_contract_version: str = Field(default="aware.ontology.runtime_artifact_set.v1")
    lifecycle_state: str = Field(default="produced")
    activation_allowed: bool = Field(default=False)
    activation_policy: str = Field(default="workspace_revision_or_service_lifecycle_required")
    artifacts: list[OntologyRuntimeArtifactRef] = Field(default_factory=list)
    required_artifact_roles: list[str] = Field(default_factory=list)
    runtime_projection_descriptors: list[OntologyRuntimeProjectionDescriptor] = Field(default_factory=list)
    materialized_semantic_roots: list[OntologyMaterializedSemanticRootRef] = Field(default_factory=list)
    provenance: OntologyRuntimeArtifactSetProvenance
    metadata: JsonObject = Field(default_factory=JsonObject)


class OntologyRuntimeArtifactSetResolveRequest(BaseModel):
    # Attributes
    actor_id: UUID | None = Field(default=None)
    package_name: str | None = Field(default=None)
    fqn_prefix: str | None = Field(default=None)
    artifact_set_id: str | None = Field(default=None)
    workspace_revision_id: str | None = Field(default=None)
    materialization_ref: str | None = Field(default=None)
    include_artifacts: bool = Field(default=True)
    source_payload: JsonObject | None = Field(default=None)


class OntologyRuntimeArtifactSetResolveResponse(BaseModel):
    # Attributes
    status: str
    error: str | None = Field(default=None)
    actor_id: UUID | None = Field(default=None)
    package_name: str | None = Field(default=None)
    fqn_prefix: str | None = Field(default=None)
    artifact_set: OntologyRuntimeArtifactSet | None = Field(default=None)
    evidence: JsonObject = Field(default_factory=JsonObject)
