from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Code Ontology Dto
from aware_code_ontology_dto.primitive.code_primitive_enums import CodePrimitiveBaseType

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_code_ontology_dto.primitive.code_primitive_type_element_type import CodePrimitiveTypeElementType
    from aware_code_ontology_dto.primitive.code_primitive_type_union_type import CodePrimitiveTypeUnionType


class CodePrimitiveType(BaseModel):
    """
    Primitive type representation.
    Rich representation of primitive types supporting nested structures.
    This class can represent complex nested types like:
    - Lists of dictionaries
    - Dictionaries with specific key/value types
    - Union types
    - And more
    """

    # Relationships
    item_type: CodePrimitiveType | None = Field(default=None)
    key_type: CodePrimitiveType | None = Field(default=None)
    value_type: CodePrimitiveType | None = Field(default=None)

    # Attributes
    signature: str
    base_type: CodePrimitiveBaseType
    constraints: JsonObject | None = Field(default=None)
