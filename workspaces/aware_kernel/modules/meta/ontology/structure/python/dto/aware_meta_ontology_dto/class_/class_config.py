from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Meta Ontology Dto
from aware_meta_ontology_dto.class_.class_config_enums import (
    ClassIdentityMode,
    ClassValueMode,
)

if TYPE_CHECKING:
    from aware_code_ontology_dto.class_.code_section_class import CodeSectionClass
    from aware_meta_ontology_dto.class_.class_config_attribute_config import ClassConfigAttributeConfig
    from aware_meta_ontology_dto.class_.class_config_function_config import ClassConfigFunctionConfig
    from aware_meta_ontology_dto.class_.class_config_relationship import ClassConfigRelationship


class ClassConfig(BaseModel):
    # Relationships
    class_config_attribute_configs: list[ClassConfigAttributeConfig] = Field(default_factory=list)
    class_config_function_configs: list[ClassConfigFunctionConfig] = Field(default_factory=list)
    class_config_relationships: list[ClassConfigRelationship] = Field(default_factory=list)
    parent_class: ClassConfig | None = Field(default=None)
    code_section_class: CodeSectionClass | None = Field(default=None)

    # Attributes
    class_fqn: str
    description: str | None = Field(default=None)
    name: str
    is_base: bool = Field(default=True)
    is_edge: bool = Field(default=False)
    value_mode: ClassValueMode = Field(default=ClassValueMode.graph_ref)
    identity_mode: ClassIdentityMode = Field(default=ClassIdentityMode.contained)
