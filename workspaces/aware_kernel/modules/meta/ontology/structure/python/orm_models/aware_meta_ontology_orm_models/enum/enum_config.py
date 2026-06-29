from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_code_ontology_orm_models.enum.code_section_enum import CodeSectionEnum
    from aware_meta_ontology_orm_models.enum.enum_option import EnumOption


class EnumConfig(ORMModel):
    # Relationships
    enum_options: list[EnumOption] = Field(default_factory=list)
    code_section_enum: CodeSectionEnum | None = Field(default=None, exclude=True)

    # Attributes
    enum_fqn: str
    name: str
    description: str | None = Field(default=None)

    # Foreign Keys
    object_config_graph_node_id: UUID | None = Field(
        default=None, description="Foreign key for ObjectConfigGraphNode.enum_config"
    )
    code_section_enum_id: UUID | None = Field(default=None, description="Foreign key for EnumConfig.code_section_enum")
