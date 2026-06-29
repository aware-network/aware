from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Reactivity Ontology Orm Models
from aware_reactivity_ontology_orm_models.action.action_enums import ActionStatus

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_reactivity_ontology_orm_models.action.action_config import ActionConfig


class Action(ORMModel):
    # Relationships
    config: ActionConfig | None = Field(default=None, exclude=True)

    # Attributes
    execution_context: JsonObject = Field(default_factory=JsonObject)
    result_info: str | None = Field(default=None)
    status: ActionStatus = Field(default=ActionStatus.requested)

    # Foreign Keys
    event_id: UUID = Field(description="Foreign key for Event.actions")
    config_id: UUID = Field(description="Foreign key for Action.config")
