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
    from aware_reactivity_service_dto.reactivity.bridge_event import ActorReactivityBridgeEvent


class ReactivityEventMeaningResolutionRequest(BaseModel):
    """
    Provider-neutral event-meaning contracts owned by Reactivity.
    Providers implement these DTOs at their API endpoints. Reactivity registers
    and selects the provider action but does not invoke it or persist meaning.
    """

    # Attributes
    event: ActorReactivityBridgeEvent


class ReactivityEventMeaningResolutionResult(BaseModel):
    # Attributes
    event_id: UUID
    event_type: str
    meaning_text: str
    provider_reference: str | None = Field(default=None)


class ReactivityEventMeaningResolutionResponse(BaseModel):
    # Attributes
    resolved_meaning: ReactivityEventMeaningResolutionResult


class ReactivityEventMeaningProviderIntent(BaseModel):
    # Attributes
    intent_id: UUID
    event: ActorReactivityBridgeEvent
    owner_ref: str
    policy_key: str
    resolver_key: str
    event_config_id: UUID
    event_config_meaning_resolver_config_id: UUID
    action_config_id: UUID
    api_capability_endpoint_id: UUID
    status: str = Field(default="requested")


class ReactivityEventMeaningProviderResolveRequest(BaseModel):
    # Attributes
    request_id: UUID | None = Field(default=None)
    event: ActorReactivityBridgeEvent
    event_config_id: UUID | None = Field(default=None)
    resolver_key: str | None = Field(default=None)


class ReactivityEventMeaningProviderResolveResponse(BaseModel):
    # Attributes
    request_id: UUID | None = Field(default=None)
    accepted: bool = Field(default=True)
    intent: ReactivityEventMeaningProviderIntent | None = Field(default=None)
    info: str | None = Field(default=None)
    error: str | None = Field(default=None)
