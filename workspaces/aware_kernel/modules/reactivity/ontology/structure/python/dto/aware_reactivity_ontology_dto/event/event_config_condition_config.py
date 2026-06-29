from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_reactivity_ontology_dto.condition.condition_config import ConditionConfig
    from aware_reactivity_ontology_dto.event.event_config_condition_config_scope import EventConfigConditionConfigScope


class EventConfigConditionConfig(BaseModel):
    # Relationships
    condition_config: ConditionConfig | None = Field(default=None)
    event_config_condition_config_scopes: list[EventConfigConditionConfigScope] = Field(default_factory=list)

    # Attributes
    cache_result: bool = Field(default=False)
    cache_ttl_seconds: int | None = Field(default=None)
    continue_on_fail: bool = Field(default=True)
    execution_order: int = Field(default=0)
    is_enabled: bool = Field(default=True)
    is_required: bool = Field(default=False)
    priority: int = Field(default=0)
    stop_on_match: bool = Field(default=False)
