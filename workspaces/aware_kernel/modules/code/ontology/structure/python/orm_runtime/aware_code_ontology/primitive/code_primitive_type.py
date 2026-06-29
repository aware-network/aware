from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Code Ontology
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_code_ontology.primitive.code_primitive_type_element_type import CodePrimitiveTypeElementType
    from aware_code_ontology.primitive.code_primitive_type_union_type import CodePrimitiveTypeUnionType


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

    @classmethod
    async def create(
        cls, signature: str, base_type: CodePrimitiveBaseType, constraints: JsonObject | None = None
    ) -> CodePrimitiveType:
        """Create deterministic primitive type root from canonical structural signature."""

        payload = {"signature": signature, "base_type": base_type, "constraints": constraints}
        result = await invoke_constructor(orm_class=cls, function_name="create", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CodePrimitiveType):
            return value
        return CodePrimitiveType.validate_invocation_value(value)

    async def create_item_type(
        self, signature: str, base_type: CodePrimitiveBaseType, constraints: JsonObject | None = None
    ) -> CodePrimitiveType:
        """Create the item type for array/set-like primitive shapes."""

        payload = {"signature": signature, "base_type": base_type, "constraints": constraints}
        result = await invoke_instance(orm_model=self, function_name="create_item_type", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CodePrimitiveType):
            return value
        return CodePrimitiveType.validate_invocation_value(value)

    async def create_key_type(
        self, signature: str, base_type: CodePrimitiveBaseType, constraints: JsonObject | None = None
    ) -> CodePrimitiveType:
        """Create the key type for dict-like primitive shapes."""

        payload = {"signature": signature, "base_type": base_type, "constraints": constraints}
        result = await invoke_instance(orm_model=self, function_name="create_key_type", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CodePrimitiveType):
            return value
        return CodePrimitiveType.validate_invocation_value(value)

    async def create_value_type(
        self, signature: str, base_type: CodePrimitiveBaseType, constraints: JsonObject | None = None
    ) -> CodePrimitiveType:
        """Create the value type for dict-like primitive shapes."""

        payload = {"signature": signature, "base_type": base_type, "constraints": constraints}
        result = await invoke_instance(orm_model=self, function_name="create_value_type", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CodePrimitiveType):
            return value
        return CodePrimitiveType.validate_invocation_value(value)

    async def create_element_slot(self, position: int) -> CodePrimitiveTypeElementType:
        """Create one ordered tuple element slot under this primitive type."""

        payload = {"position": position}
        result = await invoke_instance(orm_model=self, function_name="create_element_slot", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_code_ontology.primitive.code_primitive_type_element_type import CodePrimitiveTypeElementType

        if isinstance(value, CodePrimitiveTypeElementType):
            return value
        return CodePrimitiveTypeElementType.validate_invocation_value(value)

    async def create_union_slot(self, position: int) -> CodePrimitiveTypeUnionType:
        """Create one ordered union member slot under this primitive type."""

        payload = {"position": position}
        result = await invoke_instance(orm_model=self, function_name="create_union_slot", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_code_ontology.primitive.code_primitive_type_union_type import CodePrimitiveTypeUnionType

        if isinstance(value, CodePrimitiveTypeUnionType):
            return value
        return CodePrimitiveTypeUnionType.validate_invocation_value(value)


class CodePrimitiveTypeCreateInput(BaseModel):
    signature: str
    base_type: CodePrimitiveBaseType
    constraints: JsonObject | None = Field(default=None)


class CodePrimitiveTypeCreateOutput(BaseModel):
    value: CodePrimitiveType


class CodePrimitiveTypeCreateItemTypeInput(BaseModel):
    signature: str
    base_type: CodePrimitiveBaseType
    constraints: JsonObject | None = Field(default=None)


class CodePrimitiveTypeCreateItemTypeOutput(BaseModel):
    value: CodePrimitiveType


class CodePrimitiveTypeCreateKeyTypeInput(BaseModel):
    signature: str
    base_type: CodePrimitiveBaseType
    constraints: JsonObject | None = Field(default=None)


class CodePrimitiveTypeCreateKeyTypeOutput(BaseModel):
    value: CodePrimitiveType


class CodePrimitiveTypeCreateValueTypeInput(BaseModel):
    signature: str
    base_type: CodePrimitiveBaseType
    constraints: JsonObject | None = Field(default=None)


class CodePrimitiveTypeCreateValueTypeOutput(BaseModel):
    value: CodePrimitiveType


class CodePrimitiveTypeCreateElementSlotInput(BaseModel):
    position: int


class CodePrimitiveTypeCreateElementSlotOutput(BaseModel):
    value: CodePrimitiveTypeElementType


class CodePrimitiveTypeCreateUnionSlotInput(BaseModel):
    position: int


class CodePrimitiveTypeCreateUnionSlotOutput(BaseModel):
    value: CodePrimitiveTypeUnionType


FUNCTIONS = {
    "CodePrimitiveType": {
        "create": {
            "canonical": {
                "name": "create",
                "description": "Create deterministic primitive type root from canonical structural signature.",
                "is_constructor": True,
            },
            "input": CodePrimitiveTypeCreateInput,
            "output": CodePrimitiveTypeCreateOutput,
        },
        "create_item_type": {
            "canonical": {
                "name": "create_item_type",
                "description": "Create the item type for array/set-like primitive shapes.",
                "is_constructor": False,
            },
            "input": CodePrimitiveTypeCreateItemTypeInput,
            "output": CodePrimitiveTypeCreateItemTypeOutput,
        },
        "create_key_type": {
            "canonical": {
                "name": "create_key_type",
                "description": "Create the key type for dict-like primitive shapes.",
                "is_constructor": False,
            },
            "input": CodePrimitiveTypeCreateKeyTypeInput,
            "output": CodePrimitiveTypeCreateKeyTypeOutput,
        },
        "create_value_type": {
            "canonical": {
                "name": "create_value_type",
                "description": "Create the value type for dict-like primitive shapes.",
                "is_constructor": False,
            },
            "input": CodePrimitiveTypeCreateValueTypeInput,
            "output": CodePrimitiveTypeCreateValueTypeOutput,
        },
        "create_element_slot": {
            "canonical": {
                "name": "create_element_slot",
                "description": "Create one ordered tuple element slot under this primitive type.",
                "is_constructor": False,
            },
            "input": CodePrimitiveTypeCreateElementSlotInput,
            "output": CodePrimitiveTypeCreateElementSlotOutput,
        },
        "create_union_slot": {
            "canonical": {
                "name": "create_union_slot",
                "description": "Create one ordered union member slot under this primitive type.",
                "is_constructor": False,
            },
            "input": CodePrimitiveTypeCreateUnionSlotInput,
            "output": CodePrimitiveTypeCreateUnionSlotOutput,
        },
    },
}

__all__ = [
    "CodePrimitiveType",
    "CodePrimitiveTypeCreateInput",
    "CodePrimitiveTypeCreateOutput",
    "CodePrimitiveTypeCreateItemTypeInput",
    "CodePrimitiveTypeCreateItemTypeOutput",
    "CodePrimitiveTypeCreateKeyTypeInput",
    "CodePrimitiveTypeCreateKeyTypeOutput",
    "CodePrimitiveTypeCreateValueTypeInput",
    "CodePrimitiveTypeCreateValueTypeOutput",
    "CodePrimitiveTypeCreateElementSlotInput",
    "CodePrimitiveTypeCreateElementSlotOutput",
    "CodePrimitiveTypeCreateUnionSlotInput",
    "CodePrimitiveTypeCreateUnionSlotOutput",
    "FUNCTIONS",
]
