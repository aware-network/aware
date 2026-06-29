from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Reactivity Ontology Orm Models
from aware_reactivity_ontology_orm_models.condition.condition_enums import RelationshipEvalMode

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.class_.class_config_relationship import ClassConfigRelationship
    from aware_reactivity_ontology_orm_models.condition.condition_config import ConditionConfig


class ConditionConfigRelationshipConfig(ORMModel):
    # Relationships
    nested_condition_config: ConditionConfig | None = Field(default=None, exclude=True)
    class_config_relationship: ClassConfigRelationship | None = Field(default=None, exclude=True)

    # Attributes
    count_threshold: int | None = Field(default=None)
    eval_mode: RelationshipEvalMode = Field(default=RelationshipEvalMode.exists)

    # Foreign Keys
    condition_config_attribute_config_id: UUID | None = Field(
        default=None, description="Foreign key for ConditionConfigAttributeConfig.condition_config_relationship_config"
    )
    nested_condition_config_id: UUID | None = Field(
        default=None, description="Foreign key for ConditionConfigRelationshipConfig.nested_condition_config"
    )
    class_config_relationship_id: UUID = Field(
        description="Foreign key for ConditionConfigRelationshipConfig.class_config_relationship"
    )
