from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Meta Ontology Dto
from aware_meta_ontology_dto.class_.class_config_relationship_enums import ClassConfigRelationshipSideLoadingStrategy

if TYPE_CHECKING:
    from aware_meta_ontology_dto.class_.class_config import ClassConfig


class ClassConfigRelationshipAssociation(BaseModel):
    # Relationships
    class_config: ClassConfig | None = Field(default=None, description="Association target reference to ClassConfig")

    # Attributes
    forward_loading_strategy: ClassConfigRelationshipSideLoadingStrategy | None = Field(default=None)
    reverse_loading_strategy: ClassConfigRelationshipSideLoadingStrategy | None = Field(default=None)
