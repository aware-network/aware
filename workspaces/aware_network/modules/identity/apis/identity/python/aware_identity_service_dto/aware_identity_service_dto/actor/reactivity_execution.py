from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)


class ActorReactivityActionExecutionRequest(BaseModel):
    """
    Canonical DTOs for actor-scoped reactivity action dispatch.
    Ownership:
    - Identity API: actor/subscription execution context.
    - Reactivity API: semantic bridge events and condition-action bindings.
    - Agent runtime (or any actor runtime): implementation of action execution.
    """

    # Attributes
    action_execution_id: UUID | None = Field(default=None)
    event_id: UUID
    event_type: str
    source: str
    environment_id: UUID
    branch_id: UUID
    projection_hash: str
    commit_id: UUID
    actor_id: UUID | None = Field(default=None)
    target_actor_id: UUID | None = Field(default=None)
    actor_subscription_id: UUID | None = Field(default=None)
    event_config_condition_config_id: UUID | None = Field(default=None)
    action_binding_id: UUID | None = Field(default=None)
    action_config_id: UUID | None = Field(default=None)
    action_type: str | None = Field(default=None)
    root_object_id: UUID | None = Field(default=None)
    object_instance_graph_id: UUID | None = Field(default=None)
    focus_scope_id: UUID | None = Field(default=None)
    focus_id: UUID | None = Field(default=None)
    view_id: UUID | None = Field(default=None)
    interface_id: UUID | None = Field(default=None)
    window_id: UUID | None = Field(default=None)
    window_layout_id: UUID | None = Field(default=None)
    window_section_id: UUID | None = Field(default=None)
    visible_window_section_ids: list[UUID] = Field(default_factory=list)
    graph_hash_post: str | None = Field(default=None)


class ActorReactivityActionExecutionResult(BaseModel):
    # Attributes
    action_execution_id: UUID | None = Field(default=None)
    event_id: UUID
    handled: bool = Field(default=True)
    info: str | None = Field(default=None)
    actor_identity_id: UUID | None = Field(default=None)
    actor_process_thread_id: UUID | None = Field(default=None)
    execution_request_id: UUID | None = Field(default=None)
