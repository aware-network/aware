from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Reactivity Service Dto
from aware_reactivity_service_dto.reactivity.action_feedback_enums import ActionIntentStatus

# Types
from aware_types import JsonValue


class ReactivityActionIntent(BaseModel):
    """
    Canonical DTOs for resolving actor-free action intents.
    Ownership:
    - Reactivity owns event-policy to action-intent resolution envelopes.
    - Caller provenance lives above this rail in subscription/program receipts.
    - Action services own fulfillment after an intent is emitted.
    """

    # Attributes
    action_intent_id: UUID
    intent_key: str = Field(
        description="Caller-derived opaque ActionIntent identity key.\nSubscription resolvers derive this from subscription provenance; the\nontology ActionIntent consumes it as actor-free idempotency input."
    )
    event_id: UUID
    event_type: str
    source: str
    branch_id: UUID
    projection_hash: str
    commit_id: UUID
    actor_id: UUID | None = Field(
        default=None,
        description="Deprecated subscription-provenance mirror.\nC0 keeps this optional compatibility field for the live subscription\nresolver. New consumers must use `intent_key` plus caller-plane\nprovenance receipts/context.",
    )
    target_actor_id: UUID | None = Field(
        default=None,
        description="Deprecated actor-routing mirror.\nDispatch-time registration, not the rail DTO, owns fulfillment routing.",
    )
    actor_subscription_id: UUID | None = Field(
        default=None,
        description="Deprecated subscription-provenance mirror.\nSubscription callers derive `intent_key`; subscription attribution\nbelongs to the bridge/policy plane.",
    )
    event_config_condition_config_scope_id: UUID
    event_config_condition_config_id: UUID | None = Field(default=None)
    event_config_action_config_id: UUID | None = Field(default=None)
    action_config_id: UUID | None = Field(default=None)
    action_type: str | None = Field(default=None)
    action_payload: JsonValue | None = Field(default=None)
    status: ActionIntentStatus = Field(default=ActionIntentStatus.requested)
    root_object_id: UUID | None = Field(default=None)
    object_instance_graph_id: UUID | None = Field(default=None)
    object_instance_graph_branch_id: UUID | None = Field(default=None)
    focus_scope_id: UUID | None = Field(default=None)
    focus_id: UUID | None = Field(default=None)
    view_id: UUID | None = Field(default=None)
    interface_id: UUID | None = Field(default=None)
    window_id: UUID | None = Field(default=None)
    window_layout_id: UUID | None = Field(default=None)
    window_section_id: UUID | None = Field(default=None)
    visible_window_section_ids: list[UUID] = Field(default_factory=list)
    graph_hash_post: str | None = Field(default=None)
    subscription_filter_config: JsonValue | None = Field(
        default=None,
        description="Deprecated subscription policy mirror.\nKept only for live resolver compatibility until the C2 mirror-removal\nwave.",
    )
    subscription_priority: int = Field(
        default=0,
        description="Deprecated subscription sorting mirror.\nKept only for live resolver compatibility until the C2 mirror-removal\nwave.",
    )


class ReactivityActionIntentResolveRequest(BaseModel):
    # Attributes
    request_id: UUID | None = Field(default=None)
    subscriber_id: str | None = Field(default=None)
    event_id: UUID
    event_type: str
    source: str
    created_at_unix_ms: int = Field(default=0)
    branch_id: UUID
    projection_hash: str
    commit_id: UUID
    actor_id: UUID | None = Field(
        default=None,
        description="Deprecated caller-context mirror.\nRequesting callers should use caller-plane context. The resolver keeps\nthis optional field only while subscription bridge consumers migrate.",
    )
    target_actor_id: UUID | None = Field(
        default=None,
        description="Deprecated caller-context mirror.\nFulfillment targeting is dispatch-time registration, not request DTO\nidentity.",
    )
    event_config_condition_config_scope_id: UUID | None = Field(default=None)
    event_config_condition_config_id: UUID | None = Field(default=None)
    root_object_id: UUID | None = Field(default=None)
    object_instance_graph_id: UUID | None = Field(default=None)
    object_instance_graph_branch_id: UUID | None = Field(default=None)
    focus_scope_id: UUID | None = Field(default=None)
    focus_id: UUID | None = Field(default=None)
    view_id: UUID | None = Field(default=None)
    interface_id: UUID | None = Field(default=None)
    window_id: UUID | None = Field(default=None)
    window_layout_id: UUID | None = Field(default=None)
    window_section_id: UUID | None = Field(default=None)
    visible_window_section_ids: list[UUID] = Field(default_factory=list)
    graph_hash_post: str | None = Field(default=None)
    action_type_filters: list[str] = Field(default_factory=list)
    event_config_action_config_id_filters: list[UUID] = Field(default_factory=list)
    include_disabled_subscriptions: bool = Field(default=False)
    include_inactive_subscriptions: bool = Field(default=False)


class ReactivityActionIntentResolveResponse(BaseModel):
    # Attributes
    request_id: UUID | None = Field(default=None)
    accepted: bool = Field(default=True)
    intents: list[ReactivityActionIntent] = Field(default_factory=list)
    info: str | None = Field(default=None)
    error: str | None = Field(default=None)
