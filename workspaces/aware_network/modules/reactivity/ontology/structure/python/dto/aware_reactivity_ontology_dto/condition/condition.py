from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_meta_ontology_dto.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit
    from aware_reactivity_ontology_dto.condition.condition_config import ConditionConfig


class Condition(BaseModel):
    # Relationships
    config: ConditionConfig | None = Field(default=None)
    trigger_object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None)

    # Attributes
    activation_id: UUID
    arguments: JsonObject = Field(default_factory=JsonObject)
