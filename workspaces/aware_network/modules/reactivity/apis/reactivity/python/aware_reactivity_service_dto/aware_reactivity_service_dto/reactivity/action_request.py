from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)


class ReactivityActionExecutionRequest(BaseModel):
    """
    Canonical DTOs for Reactivity-owned action execution dispatch.
    Reactivity owns the semantic action request/result lifecycle. Caller
    attribution lives above this rail in request context or provenance receipts.
    """

    # Attributes
    action_execution_id: UUID | None = Field(default=None)
    event_id: UUID
    event_type: str
    source: str
    branch_id: UUID
    projection_hash: str
    commit_id: UUID
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


class ReactivityActionExecutionResult(BaseModel):
    # Attributes
    action_execution_id: UUID | None = Field(default=None)
    event_id: UUID
    handled: bool = Field(default=True)
    info: str | None = Field(default=None)
    execution_request_id: UUID | None = Field(default=None)
