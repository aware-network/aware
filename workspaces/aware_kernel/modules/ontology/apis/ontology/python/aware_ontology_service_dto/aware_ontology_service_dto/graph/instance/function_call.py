from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Ontology Service Dto
from aware_ontology_service_dto.graph.instance.function_call_target import OntologyGraphFunctionCallTarget

# Types
from aware_types import (
    JsonArray,
    JsonObject,
    JsonValue,
)

if TYPE_CHECKING:
    from aware_ontology_service_dto.graph.instance.commit_event import OntologyCommitEventEnvelope
    from aware_ontology_service_dto.graph.instance.commit_event import OntologyRequiredReactionReceipt


class OntologyGraphInvokeFunctionRequest(BaseModel):
    """
    Ontology GraphOS function-call DTOs.
    These payloads are the public graph operation contract for services and
    environments. Ontology service may delegate to Meta internally, but this
    boundary is Ontology-owned.
    """

    # Attributes
    actor_id: UUID | None = Field(default=None)
    domain_branch_id: UUID | None = Field(default=None)
    domain_projection_hash: str | None = Field(default=None)
    call_target: OntologyGraphFunctionCallTarget = Field(default=OntologyGraphFunctionCallTarget.instance)
    target_object_id: UUID | None = Field(default=None)
    object_projection_graph_id: UUID | None = Field(default=None)
    function_id: UUID
    args: JsonArray = Field(default_factory=JsonArray)
    kwargs: JsonObject = Field(default_factory=JsonObject)
    expected_graph_hash_pre: str | None = Field(default=None)
    expected_head_commit_id: UUID | None = Field(default=None)
    commit: bool = Field(default=True)
    publish: bool = Field(default=False)


class OntologyGraphInvokeFunctionResponse(BaseModel):
    # Attributes
    status: str
    actor_id: UUID | None = Field(default=None)
    domain_branch_id: UUID | None = Field(default=None)
    domain_projection_hash: str | None = Field(default=None)
    payload: JsonValue | None = Field(default=None)
    error: str | None = Field(default=None)
    logs: list[str] = Field(default_factory=list)
    execution_time_ms: int | None = Field(default=None)
    root_object_id: UUID | None = Field(default=None)
    graph_hash_pre: str | None = Field(default=None)
    graph_hash_post: str | None = Field(default=None)
    changes: JsonArray = Field(default_factory=JsonArray)
    domain_commit_id: UUID | None = Field(default=None)
    object_instance_graph_commit_id: UUID | None = Field(default=None)
    function_call_id: UUID | None = Field(default=None)
    function_call_response_id: UUID | None = Field(default=None)
    required_reactions: list[OntologyRequiredReactionReceipt] = Field(default_factory=list)
    commit_event: OntologyCommitEventEnvelope | None = Field(default=None)


class OntologyGraphGetLaneHeadRequest(BaseModel):
    # Attributes
    actor_id: UUID | None = Field(default=None)
    domain_branch_id: UUID
    domain_projection_hash: str


class OntologyGraphGetLaneHeadResponse(BaseModel):
    # Attributes
    status: str
    actor_id: UUID | None = Field(default=None)
    domain_branch_id: UUID
    domain_projection_hash: str
    error: str | None = Field(default=None)
    domain_commit_id: UUID | None = Field(default=None)
    graph_hash_post: str | None = Field(default=None)
    object_instance_graph_id: UUID | None = Field(default=None)
    root_object_id: UUID | None = Field(default=None)
    head_version: int | None = Field(default=None)


class OntologyGraphGetObjectInstanceGraphCommitRequest(BaseModel):
    # Attributes
    actor_id: UUID | None = Field(default=None)
    domain_branch_id: UUID
    domain_projection_hash: str
    domain_commit_id: UUID


class OntologyGraphGetObjectInstanceGraphCommitResponse(BaseModel):
    # Attributes
    status: str
    actor_id: UUID | None = Field(default=None)
    domain_branch_id: UUID | None = Field(default=None)
    domain_projection_hash: str | None = Field(default=None)
    domain_commit_id: UUID | None = Field(default=None)
    object_instance_graph_commit_id: UUID | None = Field(default=None)
    object_instance_graph_id: UUID | None = Field(default=None)
    object_instance_graph_identity_id: UUID | None = Field(default=None)
    root_object_id: UUID | None = Field(default=None)
    graph_hash_pre: str | None = Field(default=None)
    graph_hash_post: str | None = Field(default=None)
    source_language: str | None = Field(default=None)
    commit_author_id: UUID | None = Field(default=None)
    commit_created_at_unix_ms: int | None = Field(default=None)
    commit: JsonObject | None = Field(default=None)
    error: str | None = Field(default=None)


class OntologyGraphResolveProjectionRequest(BaseModel):
    # Attributes
    actor_id: UUID | None = Field(default=None)
    projection_name: str | None = Field(default=None)
    projection_hash: str | None = Field(default=None)
    object_projection_graph_id: UUID | None = Field(default=None)
    include_available: bool = Field(default=False)


class OntologyGraphResolveProjectionResponse(BaseModel):
    # Attributes
    status: str
    actor_id: UUID | None = Field(default=None)
    projection_name: str | None = Field(default=None)
    projection_hash: str | None = Field(default=None)
    object_projection_graph_id: UUID | None = Field(default=None)
    object_projection_graph_identity_id: UUID | None = Field(default=None)
    object_config_graph_id: UUID | None = Field(default=None)
    object_config_graph_identity_id: UUID | None = Field(default=None)
    language: str | None = Field(default=None)
    supports_virtual_build: bool | None = Field(default=None)
    matched_projection_hashes: list[str] = Field(default_factory=list)
    available_projection_names: list[str] = Field(default_factory=list)
    error: str | None = Field(default=None)
