from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Code Ontology Dto
from aware_code_ontology_dto.code.code_enums import CodeLanguage

if TYPE_CHECKING:
    from aware_meta_ontology_dto.attribute.attribute_config import AttributeConfig
    from aware_meta_ontology_dto.attribute.attribute_config_overlay import AttributeConfigOverlay
    from aware_meta_ontology_dto.class_.class_config import ClassConfig
    from aware_meta_ontology_dto.class_.class_config_overlay import ClassConfigOverlay
    from aware_meta_ontology_dto.enum.enum_config import EnumConfig
    from aware_meta_ontology_dto.enum.enum_config_overlay import EnumConfigOverlay
    from aware_meta_ontology_dto.enum.enum_option import EnumOption
    from aware_meta_ontology_dto.enum.enum_option_overlay import EnumOptionOverlay
    from aware_meta_ontology_dto.function.function_config import FunctionConfig
    from aware_meta_ontology_dto.function.function_config_overlay import FunctionConfigOverlay


class ObjectConfigGraphOverlay(BaseModel):
    # Attributes
    language: CodeLanguage
