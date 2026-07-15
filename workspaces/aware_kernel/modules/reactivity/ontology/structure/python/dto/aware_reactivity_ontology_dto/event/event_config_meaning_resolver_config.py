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


class EventConfigMeaningResolverConfig(BaseModel):
    # Relationships
    action_config: ActionConfig | None = Field(default=None)

    # Attributes
    resolver_key: str = Field(default="default")
    priority: int = Field(default=0)
    is_enabled: bool = Field(default=True)
