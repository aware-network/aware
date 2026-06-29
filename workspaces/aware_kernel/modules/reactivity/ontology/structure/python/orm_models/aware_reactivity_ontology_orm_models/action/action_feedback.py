from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Reactivity Ontology Orm Models
from aware_reactivity_ontology_orm_models.action.action_enums import (
    ActionFeedbackStage,
    ActionFeedbackStatus,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.class_.inline_value_instance import InlineValueInstance


class ActionFeedback(ORMModel):
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

    # Foreign Keys
    action_execution_id: UUID = Field(description="Foreign key for ActionExecution.action_feedback")
    payload_model_id: UUID | None = Field(default=None, description="Foreign key for ActionFeedback.payload_model")
