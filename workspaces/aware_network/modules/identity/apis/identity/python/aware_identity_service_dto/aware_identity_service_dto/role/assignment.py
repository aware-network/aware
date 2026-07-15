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


class RoleAssignmentRequest(BaseModel):
    """
    Canonical DTOs for identity-owned actor-role assignment.
    Ownership:
    - Identity API: shared assignment contract over `Role + ActorRole` truth.
    - Product services: translate domain-specific assignment intent into this contract.
    Non-goals:
    - workflow-local owner/session fields
    - object-local assignment semantics
    - runtime execution logic
    """

    # Attributes
    actor_id: UUID
    role_config_id: UUID | None = Field(default=None)
    role_config_name: str | None = Field(default=None)
    class_instance_identity_id: UUID
    object_instance_graph_branch_key: str = Field(default="all")
    object_instance_graph_branch_id: UUID | None = Field(default=None)
    request_id: UUID | None = Field(default=None)
    reason: str | None = Field(default=None)
    source_service: str | None = Field(default=None)
    grant_authority_kind: str | None = Field(default=None)
    grant_authority_id: UUID | None = Field(default=None)
    grant_context_kind: str | None = Field(default=None)
    grant_context_id: UUID | None = Field(default=None)
    grant_context_ref: str | None = Field(default=None)
    grant_evidence: JsonObject = Field(default_factory=JsonObject)


class RoleAssignmentBinding(BaseModel):
    # Attributes
    actor_id: UUID
    role_config_id: UUID
    role_id: UUID
    actor_role_id: UUID
    role_class_instance_id: UUID
    class_instance_identity_id: UUID
    role_config_class_config_id: UUID
    object_instance_graph_identity_id: UUID
    object_instance_graph_branch_key: str = Field(default="all")
    object_instance_graph_branch_id: UUID | None = Field(default=None)
    grant_authority_kind: str | None = Field(default=None)
    grant_authority_id: UUID | None = Field(default=None)
    grant_context_kind: str | None = Field(default=None)
    grant_context_id: UUID | None = Field(default=None)
    grant_context_ref: str | None = Field(default=None)
    grant_evidence: JsonObject = Field(default_factory=JsonObject)


class RoleAssignmentReceipt(BaseModel):
    # Attributes
    request_id: UUID | None = Field(default=None)
    binding: RoleAssignmentBinding
    role_created: bool = Field(default=False)
    actor_role_created: bool = Field(default=False)
    role_class_instance_created: bool = Field(default=False)
    grant_authority_kind: str | None = Field(default=None)
    grant_authority_id: UUID | None = Field(default=None)
    grant_context_kind: str | None = Field(default=None)
    grant_context_id: UUID | None = Field(default=None)
    grant_context_ref: str | None = Field(default=None)
    grant_evidence: JsonObject = Field(default_factory=JsonObject)
    info: str | None = Field(default=None)


class RoleAssignmentResolveRequest(BaseModel):
    # Attributes
    actor_id: UUID | None = Field(default=None)
    role_config_id: UUID | None = Field(default=None)
    role_config_name: str | None = Field(default=None)
    class_instance_identity_id: UUID
    object_instance_graph_branch_key: str = Field(default="all")
    object_instance_graph_branch_id: UUID | None = Field(default=None)
    request_id: UUID | None = Field(default=None)


class RoleAssignmentResolveResult(BaseModel):
    # Attributes
    request_id: UUID | None = Field(default=None)
    bindings: list[RoleAssignmentBinding] = Field(default_factory=list)
    info: str | None = Field(default=None)


class RoleUnassignmentRequest(BaseModel):
    # Attributes
    actor_id: UUID
    role_config_id: UUID | None = Field(default=None)
    role_config_name: str | None = Field(default=None)
    class_instance_identity_id: UUID
    object_instance_graph_branch_key: str = Field(default="all")
    object_instance_graph_branch_id: UUID | None = Field(default=None)
    request_id: UUID | None = Field(default=None)
    reason: str | None = Field(default=None)
    source_service: str | None = Field(default=None)


class RoleUnassignmentReceipt(BaseModel):
    # Attributes
    request_id: UUID | None = Field(default=None)
    binding: RoleAssignmentBinding
    actor_role_removed: bool = Field(default=False)
    role_class_instance_removed: bool = Field(default=False)
    role_removed: bool = Field(default=False)
    info: str | None = Field(default=None)
