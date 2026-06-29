from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ActorSubscriptionBridgeConfig(BaseModel):
    id: UUID
    actor_id: UUID
    event_config_condition_config_scope_id: UUID
    event_config_condition_config_id: UUID
    object_instance_graph_identity_id: UUID
    object_instance_graph_branch_id: UUID | None = Field(default=None)
    name: str
    action_type: str | None = Field(default=None)
    event_config_action_config_ids: list[UUID] = Field(default_factory=list)
    addressing_policy: str = Field(default="any")
    is_enabled: bool = Field(default=True)
    status: str = Field(default="active")
    priority: int = Field(default=0)
    filter_config: Any | None = Field(default=None)


__all__ = [
    "ActorSubscriptionBridgeConfig",
]
