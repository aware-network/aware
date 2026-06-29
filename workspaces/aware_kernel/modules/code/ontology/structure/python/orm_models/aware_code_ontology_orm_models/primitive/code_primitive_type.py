from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Code Ontology Orm Models
from aware_code_ontology_orm_models.primitive.code_primitive_enums import CodePrimitiveBaseType

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_code_ontology_orm_models.primitive.code_primitive_type_element_type import CodePrimitiveTypeElementType
    from aware_code_ontology_orm_models.primitive.code_primitive_type_union_type import CodePrimitiveTypeUnionType


class CodePrimitiveType(ORMModel):
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
    item_type: CodePrimitiveType | None = Field(default=None, exclude=True)
    key_type: CodePrimitiveType | None = Field(default=None, exclude=True)
    value_type: CodePrimitiveType | None = Field(default=None, exclude=True)

    # Attributes
    signature: str
    base_type: CodePrimitiveBaseType
    constraints: JsonObject | None = Field(default=None)

    # Foreign Keys
    item_type_id: UUID | None = Field(default=None, description="Foreign key for CodePrimitiveType.item_type")
    key_type_id: UUID | None = Field(default=None, description="Foreign key for CodePrimitiveType.key_type")
    value_type_id: UUID | None = Field(default=None, description="Foreign key for CodePrimitiveType.value_type")

    # Edges
    code_primitive_type_element_types: list[CodePrimitiveTypeElementType] = Field(
        default_factory=list, exclude=True, description="Edge association helper for element_types"
    )
    code_primitive_type_union_types: list[CodePrimitiveTypeUnionType] = Field(
        default_factory=list, exclude=True, description="Edge association helper for union_types"
    )

    @property
    def element_types(self) -> list[CodePrimitiveType]:
        return [edge.element_type for edge in self.code_primitive_type_element_types if edge.element_type is not None]

    @property
    def union_types(self) -> list[CodePrimitiveType]:
        return [edge.union_type for edge in self.code_primitive_type_union_types if edge.union_type is not None]
