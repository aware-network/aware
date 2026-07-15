from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology.attribute.attribute_config import AttributeConfig
    from aware_meta_ontology.attribute.attribute_config_overlay import AttributeConfigOverlay
    from aware_meta_ontology.class_.class_config import ClassConfig
    from aware_meta_ontology.class_.class_config_overlay import ClassConfigOverlay
    from aware_meta_ontology.enum.enum_config import EnumConfig
    from aware_meta_ontology.enum.enum_config_overlay import EnumConfigOverlay
    from aware_meta_ontology.enum.enum_option import EnumOption
    from aware_meta_ontology.enum.enum_option_overlay import EnumOptionOverlay
    from aware_meta_ontology.function.function_config import FunctionConfig
    from aware_meta_ontology.function.function_config_overlay import FunctionConfigOverlay


class ObjectConfigGraphOverlay(ORMModel):
    # Attributes
    language: CodeLanguage

    # Foreign Keys
    object_config_graph_id: UUID = Field(description="Foreign key for ObjectConfigGraph.object_config_graph_overlays")

    # Edges
    class_config_overlays: list[ClassConfigOverlay] = Field(
        default_factory=list, description="Edge association helper for classes"
    )
    function_config_overlays: list[FunctionConfigOverlay] = Field(
        default_factory=list, description="Edge association helper for functions"
    )
    attribute_config_overlays: list[AttributeConfigOverlay] = Field(
        default_factory=list, description="Edge association helper for attributes"
    )
    enum_config_overlays: list[EnumConfigOverlay] = Field(
        default_factory=list, description="Edge association helper for enums"
    )
    enum_option_overlays: list[EnumOptionOverlay] = Field(
        default_factory=list, description="Edge association helper for enum_options"
    )

    @property
    def classes(self) -> list[ClassConfig]:
        return [edge.class_config for edge in self.class_config_overlays if edge.class_config is not None]

    @property
    def functions(self) -> list[FunctionConfig]:
        return [edge.function_config for edge in self.function_config_overlays if edge.function_config is not None]

    @property
    def attributes(self) -> list[AttributeConfig]:
        return [edge.attribute_config for edge in self.attribute_config_overlays if edge.attribute_config is not None]

    @property
    def enums(self) -> list[EnumConfig]:
        return [edge.enum_config for edge in self.enum_config_overlays if edge.enum_config is not None]

    @property
    def enum_options(self) -> list[EnumOption]:
        return [edge.enum_option for edge in self.enum_option_overlays if edge.enum_option is not None]


FUNCTIONS = {
    "ObjectConfigGraphOverlay": {},
}

__all__ = [
    "ObjectConfigGraphOverlay",
    "FUNCTIONS",
]
