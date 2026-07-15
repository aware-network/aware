from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit
    from aware_reactivity_ontology_orm_models.condition.condition_config import ConditionConfig


class Condition(ORMModel):
    # Relationships
    config: ConditionConfig | None = Field(default=None, exclude=True)
    trigger_object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None, exclude=True)

    # Attributes
    activation_id: UUID
    arguments: JsonObject = Field(default_factory=JsonObject)

    # Foreign Keys
    config_id: UUID = Field(description="Foreign key for Condition.config")
    trigger_object_instance_graph_commit_id: UUID = Field(
        description="Foreign key for Condition.trigger_object_instance_graph_commit"
    )
