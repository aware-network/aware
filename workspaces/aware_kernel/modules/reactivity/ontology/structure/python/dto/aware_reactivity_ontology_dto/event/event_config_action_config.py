from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_reactivity_ontology_dto.action.action_config import ActionConfig


class EventConfigActionConfig(BaseModel):
    # Relationships
    action_config: ActionConfig | None = Field(default=None)

    # Attributes
    continue_on_fail: bool = Field(default=True)
    execution_order: int = Field(default=0)
    is_enabled: bool = Field(default=True)
    is_required: bool = Field(default=False)
    priority: int = Field(default=0)
