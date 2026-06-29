from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Meta Ontology Orm Models
from aware_meta_ontology_orm_models.class_.class_config_enums import (
    ClassIdentityMode,
    ClassValueMode,
)

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_code_ontology_orm_models.class_.code_section_class import CodeSectionClass
    from aware_meta_ontology_orm_models.class_.class_config_attribute_config import ClassConfigAttributeConfig
    from aware_meta_ontology_orm_models.class_.class_config_function_config import ClassConfigFunctionConfig
    from aware_meta_ontology_orm_models.class_.class_config_relationship import ClassConfigRelationship


class ClassConfig(ORMModel):
    # Relationships
    class_config_attribute_configs: list[ClassConfigAttributeConfig] = Field(default_factory=list)
    class_config_function_configs: list[ClassConfigFunctionConfig] = Field(default_factory=list)
    class_config_relationships: list[ClassConfigRelationship] = Field(default_factory=list)
    parent_class: ClassConfig | None = Field(default=None, exclude=True)
    code_section_class: CodeSectionClass | None = Field(default=None, exclude=True)

    # Attributes
    class_fqn: str
    description: str | None = Field(default=None)
    name: str
    is_base: bool = Field(default=True)
    is_edge: bool = Field(default=False)
    value_mode: ClassValueMode = Field(default=ClassValueMode.graph_ref)
    identity_mode: ClassIdentityMode = Field(default=ClassIdentityMode.contained)

    # Foreign Keys
    object_config_graph_node_id: UUID | None = Field(
        default=None, description="Foreign key for ObjectConfigGraphNode.class_config"
    )
    parent_class_id: UUID | None = Field(default=None, description="Foreign key for ClassConfig.parent_class")
    code_section_class_id: UUID | None = Field(
        default=None, description="Foreign key for ClassConfig.code_section_class"
    )
