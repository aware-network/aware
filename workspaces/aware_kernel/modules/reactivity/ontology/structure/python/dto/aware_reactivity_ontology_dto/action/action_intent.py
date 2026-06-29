from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Reactivity Ontology Dto
from aware_reactivity_ontology_dto.action.action_enums import ActionIntentStatus

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_meta_ontology_dto.class_.inline_value_instance import InlineValueInstance
    from aware_reactivity_ontology_dto.action.action_config import ActionConfig
    from aware_reactivity_ontology_dto.action.action_execution import ActionExecution


class ActionIntent(BaseModel):
    # Relationships
    action_executions: list[ActionExecution] = Field(default_factory=list)
    config: ActionConfig | None = Field(default=None)
    payload_model: InlineValueInstance | None = Field(default=None)

    # Attributes
    action_payload: JsonObject = Field(
        default_factory=JsonObject,
        description="Deprecated compatibility payload mirror.\nCanonical typed payload truth is `payload_model`, whose ClassConfig is\nresolved by Experience policy from the bound endpoint request config.",
    )
    action_type: str | None = Field(default=None)
    actor_id: UUID | None = Field(
        default=None,
        description="Deprecated actor-provenance mirror.\nReactivity owns lifecycle only. Caller provenance is owned by the\nsubscription bridge or Experience program receipt rails.",
    )
    actor_subscription_id: UUID | None = Field(
        default=None,
        description="Deprecated subscription-provenance mirror.\nStable identity migrated to caller-supplied `intent_key`; subscription\ncallers derive that key in their bridge layer.",
    )
    intent_key: str = Field(
        description="Caller-supplied opaque idempotency key for this event/action intent.\nReactivity treats this as an uninterpreted primitive. Program,\nsubscription, and future caller rails own derivation/provenance."
    )
    priority: int = Field(default=0)
    status: ActionIntentStatus = Field(default=ActionIntentStatus.requested)
    subscription_filter_config: JsonObject = Field(
        default_factory=JsonObject,
        description="Deprecated subscription-provenance mirror.\nResolver-owned subscription policy context lives above Reactivity.",
    )
    target_actor_id: UUID | None = Field(
        default=None,
        description="Deprecated actor-provenance mirror.\nDispatch-time registration, not ActionIntent identity, decides\nfulfillment routing.",
    )
