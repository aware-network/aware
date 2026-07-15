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


class ActorRoleEntryV1(BaseModel):
    """
    API-owned view-state contracts for Identity actor surfaces.
    Public API view keys:
    - identity.actor_roles
    - identity.actor_commits
    - identity.actor_subscriptions
    """

    # Attributes
    role_assignment_id: UUID | None = Field(default=None)
    role_config_id: UUID | None = Field(default=None)
    role_config_name: str | None = Field(default=None)
    role_display_name: str | None = Field(default=None)
    scope: str | None = Field(default=None)
    status: str | None = Field(default=None)
    granted_at: str | None = Field(default=None)
    granted_by_actor_id: UUID | None = Field(default=None)
    granted_by_display_name: str | None = Field(default=None)
    metadata: JsonObject = Field(default_factory=JsonObject)


class ActorRolesViewStateV1(BaseModel):
    # Attributes
    status: str = Field(default="waiting")
    actor_id: UUID | None = Field(default=None)
    actor_display_name: str | None = Field(default=None)
    entries: list[ActorRoleEntryV1] = Field(default_factory=list)
    summary: str | None = Field(default=None)
    empty_message: str = Field(default="No roles assigned yet")
    error: str | None = Field(default=None)
    provenance: JsonObject = Field(default_factory=JsonObject)


class ActorCommitEntryV1(BaseModel):
    # Attributes
    actor_commit_id: UUID | None = Field(default=None)
    commit_id: UUID | None = Field(default=None)
    branch_id: UUID | None = Field(default=None)
    summary: str | None = Field(default=None)
    action_label: str | None = Field(default=None)
    target_kind: str | None = Field(default=None)
    target_label: str | None = Field(default=None)
    authored_at: str | None = Field(default=None)
    metadata: JsonObject = Field(default_factory=JsonObject)


class ActorCommitsViewStateV1(BaseModel):
    # Attributes
    status: str = Field(default="waiting")
    actor_id: UUID | None = Field(default=None)
    actor_display_name: str | None = Field(default=None)
    entries: list[ActorCommitEntryV1] = Field(default_factory=list)
    summary: str | None = Field(default=None)
    empty_message: str = Field(default="No commits authored yet")
    error: str | None = Field(default=None)
    provenance: JsonObject = Field(default_factory=JsonObject)


class ActorSubscriptionEntryV1(BaseModel):
    # Attributes
    actor_subscription_id: UUID | None = Field(default=None)
    event_kind: str | None = Field(default=None)
    event_label: str | None = Field(default=None)
    scope: str | None = Field(default=None)
    status: str | None = Field(default=None)
    activated_at: str | None = Field(default=None)
    last_triggered_at: str | None = Field(default=None)
    metadata: JsonObject = Field(default_factory=JsonObject)


class ActorSubscriptionsViewStateV1(BaseModel):
    # Attributes
    status: str = Field(default="waiting")
    actor_id: UUID | None = Field(default=None)
    actor_display_name: str | None = Field(default=None)
    entries: list[ActorSubscriptionEntryV1] = Field(default_factory=list)
    summary: str | None = Field(default=None)
    empty_message: str = Field(default="No subscriptions yet")
    error: str | None = Field(default=None)
    provenance: JsonObject = Field(default_factory=JsonObject)
