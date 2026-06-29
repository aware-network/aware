from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Reactivity Ontology Dto
from aware_reactivity_ontology_dto.action.action_enums import (
    ActionFeedbackStage,
    ActionFeedbackStatus,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_meta_ontology_dto.class_.inline_value_instance import InlineValueInstance


class ActionFeedback(BaseModel):
    # Relationships
    payload_model: InlineValueInstance | None = Field(default=None)

    # Attributes
    created_at_unix_ms: int = Field(default=0)
    message: str | None = Field(default=None)
    payload: JsonObject = Field(
        default_factory=JsonObject,
        description="Deprecated compatibility payload mirror.\nCanonical typed feedback payload truth is `payload_model`, whose\nClassConfig is resolved from the bound endpoint stream event config.",
    )
    sequence: int
    stage: ActionFeedbackStage
    status: ActionFeedbackStatus
