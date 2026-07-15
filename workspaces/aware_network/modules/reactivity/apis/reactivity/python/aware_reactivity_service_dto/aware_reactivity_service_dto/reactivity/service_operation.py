from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_reactivity_service_dto.reactivity.action_execution import ActionExecution
    from aware_reactivity_service_dto.reactivity.action_feedback import ActionFeedback
    from aware_reactivity_service_dto.reactivity.action_intent import ReactivityActionIntent
    from aware_reactivity_service_dto.reactivity.action_terminal import ActionTerminal
    from aware_reactivity_service_dto.reactivity.bridge_event import ActorReactivityBridgeEvent


class ReactivityServiceStatusRequest(BaseModel):
    """
    Canonical Reactivity service API operation DTOs.
    These operations expose Reactivity-owned event/action streams. Upstream
    commit truth is consumed by the service through Environment SDK/API fanout,
    not through local graph store access.
    """

    # Attributes
    request_id: UUID | None = Field(default=None)
    subscriber_id: str | None = Field(default=None)


class ReactivityServiceStatusResponse(BaseModel):
    # Attributes
    request_id: UUID | None = Field(default=None)
    service_id: str = Field(default="reactivity")
    active: bool = Field(default=False)
    upstream_source: str = Field(default="environment_service_api_fanout")
    environment_fanout_attached: bool = Field(default=False)
    environment_fanout_running: bool = Field(default=False)
    identity_subscription_route_ready: bool = Field(default=False)
    blockers: list[str] = Field(default_factory=list)
    info: str | None = Field(default=None)
    error: str | None = Field(default=None)


class ReactivityEventSubscriptionRequest(BaseModel):
    # Attributes
    subscriber_id: str
    event_type_filters: list[str] = Field(default_factory=list)
    branch_filters: list[UUID] = Field(default_factory=list)
    projection_hash_filters: list[str] = Field(default_factory=list)
    object_instance_graph_filters: list[UUID] = Field(default_factory=list)
    include_replay: bool = Field(default=True)
    resume_after_event_id: UUID | None = Field(default=None)


class ReactivityEventSubscriptionResponse(BaseModel):
    # Attributes
    subscriber_id: str
    accepted: bool = Field(default=True)
    upstream_source: str = Field(default="meta_lane_fanout")
    resume_after_event_id: UUID | None = Field(default=None)
    info: str | None = Field(default=None)
    error: str | None = Field(default=None)


class ReactivitySemanticEventPublishRequest(BaseModel):
    """
    Publish one provider-neutral committed semantic event occurrence.
    Publication is observation ingress only. The event carries no action
    target or request payload; ActorSubscription resolution remains on the
    separate action-intent boundary.
    """

    # Attributes
    request_id: UUID | None = Field(default=None)
    publisher_id: str
    event: ActorReactivityBridgeEvent


class ReactivitySemanticEventPublishResponse(BaseModel):
    # Attributes
    request_id: UUID | None = Field(default=None)
    accepted: bool = Field(default=True)
    published: bool = Field(default=False)
    duplicate: bool = Field(default=False)
    event_id: UUID | None = Field(default=None)
    info: str | None = Field(default=None)
    error: str | None = Field(default=None)


class ReactivityActionLifecycleSubscriptionRequest(BaseModel):
    # Attributes
    subscriber_id: str
    event_id_filters: list[UUID] = Field(default_factory=list)
    action_intent_id_filters: list[UUID] = Field(default_factory=list)
    action_execution_id_filters: list[UUID] = Field(default_factory=list)
    action_type_filters: list[str] = Field(default_factory=list)
    branch_filters: list[UUID] = Field(default_factory=list)
    projection_hash_filters: list[str] = Field(default_factory=list)
    include_replay: bool = Field(default=True)
    resume_after_action_execution_id: UUID | None = Field(default=None)


class ReactivityActionLifecycleSubscriptionResponse(BaseModel):
    # Attributes
    subscriber_id: str
    accepted: bool = Field(default=True)
    upstream_source: str = Field(default="meta_lane_fanout")
    resume_after_action_execution_id: UUID | None = Field(default=None)
    info: str | None = Field(default=None)
    error: str | None = Field(default=None)


class ReactivityActionLifecyclePublishRequest(BaseModel):
    # Attributes
    request_id: UUID | None = Field(default=None)
    publisher_id: str
    intent: ReactivityActionIntent | None = Field(default=None)
    execution: ActionExecution | None = Field(default=None)
    feedback: ActionFeedback | None = Field(default=None)
    terminal: ActionTerminal | None = Field(default=None)


class ReactivityActionLifecyclePublishResponse(BaseModel):
    # Attributes
    request_id: UUID | None = Field(default=None)
    accepted: bool = Field(default=True)
    published_count: int = Field(default=0)
    action_intent_id: UUID | None = Field(default=None)
    action_execution_id: UUID | None = Field(default=None)
    action_feedback_id: UUID | None = Field(default=None)
    info: str | None = Field(default=None)
    error: str | None = Field(default=None)
