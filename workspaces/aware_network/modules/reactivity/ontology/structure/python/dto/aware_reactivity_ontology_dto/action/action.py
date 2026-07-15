from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Reactivity Ontology Dto
from aware_reactivity_ontology_dto.action.action_enums import ActionStatus

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_reactivity_ontology_dto.action.action_config import ActionConfig


class Action(BaseModel):
    # Relationships
    config: ActionConfig | None = Field(default=None)

    # Attributes
    execution_context: JsonObject = Field(default_factory=JsonObject)
    result_info: str | None = Field(default=None)
    status: ActionStatus = Field(default=ActionStatus.requested)
