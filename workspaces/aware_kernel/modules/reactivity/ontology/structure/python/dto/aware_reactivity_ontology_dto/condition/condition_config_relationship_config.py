from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Reactivity Ontology Dto
from aware_reactivity_ontology_dto.condition.condition_enums import RelationshipEvalMode

if TYPE_CHECKING:
    from aware_meta_ontology_dto.class_.class_config_relationship import ClassConfigRelationship
    from aware_reactivity_ontology_dto.condition.condition_config import ConditionConfig


class ConditionConfigRelationshipConfig(BaseModel):
    # Relationships
    nested_condition_config: ConditionConfig | None = Field(default=None)
    class_config_relationship: ClassConfigRelationship | None = Field(default=None)

    # Attributes
    count_threshold: int | None = Field(default=None)
    eval_mode: RelationshipEvalMode = Field(default=RelationshipEvalMode.exists)
