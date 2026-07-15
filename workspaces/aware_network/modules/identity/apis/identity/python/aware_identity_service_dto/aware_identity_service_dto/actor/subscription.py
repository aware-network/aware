from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import JsonValue


class ActorSubscriptionBridgeConfig(BaseModel):
    """
    Canonical DTO for actor subscription data exposed at Identity API boundary.
    This keeps subscription ownership in Identity API so downstream bridges
    (reactivity/agent) depend on a stable contract instead of local dataclasses.
    """

    # Attributes
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
    filter_config: JsonValue | None = Field(default=None)


class ActorSubscriptionEnsureRequest(BaseModel):
    # Attributes
    request_id: UUID | None = Field(default=None)
    actor_id: UUID
    event_config_condition_config_scope_id: UUID
    name: str
    description: str | None = Field(default=None)
    action_type: str | None = Field(default=None)
    event_config_action_config_ids: list[UUID] = Field(default_factory=list)
    addressing_policy: str = Field(default="any")
    is_enabled: bool = Field(default=True)
    status: str = Field(default="active")
    filter_mode: str = Field(default="all_instances")
    filter_config: JsonValue | None = Field(default=None)
    priority: int = Field(default=0)
    batch_mode: bool = Field(default=False)
    batch_window_ms: int = Field(default=1000)
    max_batch_size: int = Field(default=100)
    require_read_access: bool = Field(default=True)
    check_ownership: bool = Field(default=True)
    rate_limit_per_minute: int | None = Field(default=None)
    rate_limit_per_hour: int | None = Field(default=None)


class ActorSubscriptionEnsureReceipt(BaseModel):
    # Attributes
    request_id: UUID | None = Field(default=None)
    subscription: ActorSubscriptionBridgeConfig
    subscription_created: bool = Field(default=False)
    info: str | None = Field(default=None)


class ActorSubscriptionResolveRequest(BaseModel):
    # Attributes
    request_id: UUID | None = Field(default=None)
    actor_id: UUID | None = Field(default=None)
    event_config_condition_config_id: UUID | None = Field(default=None)
    object_instance_graph_identity_id: UUID | None = Field(default=None)
    object_instance_graph_branch_id: UUID | None = Field(default=None)
    include_inactive: bool = Field(default=False)
    include_disabled: bool = Field(default=False)


class ActorSubscriptionResolveResult(BaseModel):
    # Attributes
    request_id: UUID | None = Field(default=None)
    subscriptions: list[ActorSubscriptionBridgeConfig] = Field(default_factory=list)
    info: str | None = Field(default=None)
