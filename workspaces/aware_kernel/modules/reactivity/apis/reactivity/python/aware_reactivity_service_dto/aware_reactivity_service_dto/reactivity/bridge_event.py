from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)


class ActorReactivityBridgeEvent(BaseModel):
    """
    Canonical DTO for reactivity bridge semantic events.
    Ownership:
    - Reactivity API owns semantic bridge events.
    - Caller attribution lives above the rail in caller-plane receipts/context.
    """

    # Attributes
    event_id: UUID
    event_type: str
    source: str
    created_at_unix_ms: int
    branch_id: UUID
    projection_hash: str
    commit_id: UUID
    event_config_condition_config_id: UUID | None = Field(default=None)
    root_object_id: UUID | None = Field(default=None)
    object_instance_graph_id: UUID | None = Field(default=None)
    graph_hash_post: str | None = Field(default=None)
