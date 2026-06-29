from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_reactivity_ontology_orm_models.condition.condition_config import ConditionConfig
    from aware_reactivity_ontology_orm_models.event.event_config_condition_config_scope import (
        EventConfigConditionConfigScope,
    )


class EventConfigConditionConfig(ORMModel):
    # Relationships
    condition_config: ConditionConfig | None = Field(default=None, exclude=True)
    event_config_condition_config_scopes: list[EventConfigConditionConfigScope] = Field(
        default_factory=list, exclude=True
    )

    # Attributes
    cache_result: bool = Field(default=False)
    cache_ttl_seconds: int | None = Field(default=None)
    continue_on_fail: bool = Field(default=True)
    execution_order: int = Field(default=0)
    is_enabled: bool = Field(default=True)
    is_required: bool = Field(default=False)
    priority: int = Field(default=0)
    stop_on_match: bool = Field(default=False)

    # Foreign Keys
    event_config_id: UUID = Field(description="Foreign key for EventConfig.event_config_condition_configs")
    condition_config_id: UUID = Field(description="Foreign key for EventConfigConditionConfig.condition_config")
