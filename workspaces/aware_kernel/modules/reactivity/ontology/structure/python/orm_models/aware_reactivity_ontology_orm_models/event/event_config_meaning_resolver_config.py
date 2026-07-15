from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_reactivity_ontology_orm_models.action.action_config import ActionConfig


class EventConfigMeaningResolverConfig(ORMModel):
    # Relationships
    action_config: ActionConfig | None = Field(default=None, exclude=True)

    # Attributes
    resolver_key: str = Field(default="default")
    priority: int = Field(default=0)
    is_enabled: bool = Field(default=True)

    # Foreign Keys
    event_config_id: UUID = Field(description="Foreign key for EventConfig.event_config_meaning_resolver_configs")
    action_config_id: UUID = Field(description="Foreign key for EventConfigMeaningResolverConfig.action_config")
