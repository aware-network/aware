from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Ontology Service Dto
from aware_ontology_service_dto.graph.instance.function_call_target import OntologyGraphFunctionCallTarget

# Types
from aware_types import JsonObject


class OntologyGraphCommitActionMetadata(BaseModel):
    """
    Ontology GraphOS commit receipt DTOs.
    Ontology service owns this public envelope. Meta commit events may back the
    implementation internally, but callers should not depend on Meta DTOs.
    """

    # Attributes
    call_target: OntologyGraphFunctionCallTarget | None = Field(default=None)
    function_id: UUID | None = Field(default=None)
    operation_label: str | None = Field(default=None)
    object_id: UUID | None = Field(default=None)
    source_class_instance_identity_id: UUID | None = Field(default=None)


class OntologyRequiredReactionReceipt(BaseModel):
    # Attributes
    reaction_key: str
    status: str
    commit_id: UUID | None = Field(default=None)
    object_instance_graph_commit_id: UUID | None = Field(default=None)
    object_instance_graph_identity_id: UUID | None = Field(default=None)
    graph_hash_post: str | None = Field(default=None)
    error: str | None = Field(default=None)
    metadata: JsonObject = Field(default_factory=JsonObject)


class OntologyCommitArtifactRef(BaseModel):
    # Attributes
    artifact_kind: str
    artifact_ref: str
    artifact_hash: str | None = Field(default=None)
    content_type: str | None = Field(default=None)
    metadata: JsonObject = Field(default_factory=JsonObject)


class OntologyCommitEventEnvelope(BaseModel):
    # Attributes
    event_id: UUID
    event_family: str = Field(default="ontology.oig_commit")
    schema_version: int = Field(default=1)
    emitted_at_unix_ms: int
    ontology_authority_id: str
    actor_id: UUID
    domain_branch_id: UUID
    domain_projection_hash: str
    domain_commit_id: UUID
    object_instance_graph_commit_id: UUID
    object_instance_graph_id: UUID
    object_instance_graph_identity_id: UUID
    object_instance_graph_branch_id: UUID
    graph_hash_pre: str | None = Field(default=None)
    graph_hash_post: str
    root_object_id: UUID | None = Field(default=None)
    head_version: int | None = Field(default=None)
    commit_action: OntologyGraphCommitActionMetadata | None = Field(default=None)
    required_reactions: list[OntologyRequiredReactionReceipt] = Field(default_factory=list)
    artifact_refs: list[OntologyCommitArtifactRef] = Field(default_factory=list)
    metadata: JsonObject = Field(default_factory=JsonObject)


class OntologyCommitSubscriptionRequest(BaseModel):
    # Attributes
    subscriber_id: str
    event_families: list[str] = Field(default_factory=list)
    branch_filters: list[UUID] = Field(default_factory=list)
    projection_hash_filters: list[str] = Field(default_factory=list)
    object_instance_graph_identity_filters: list[UUID] = Field(default_factory=list)
    package_filters: list[str] = Field(default_factory=list)
    include_artifact_refs: bool = Field(default=True)
    resume_after_event_id: UUID | None = Field(default=None)


class OntologyCommitSubscriptionResponse(BaseModel):
    # Attributes
    subscriber_id: str
    accepted: bool = Field(default=True)
    resume_after_event_id: UUID | None = Field(default=None)
    info: str | None = Field(default=None)
    error: str | None = Field(default=None)
