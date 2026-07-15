from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_code_ontology.primitive.code_primitive_type import CodePrimitiveType


class CodePrimitiveTypeElementType(ORMModel):
    """
    Edge linking a tuple-like CodePrimitiveType to its element types.
    Modeled as an explicit edge to support:
    - self-referential element lists without ambiguous FK names
    - sharing element nodes across multiple parents (M2M semantics)
    - stable ordering via `position`
    """

    # Relationships
    element_type: CodePrimitiveType = Field(description="Association target reference to CodePrimitiveType")

    # Attributes
    position: int

    # Foreign Keys
    element_type_id: UUID | None = Field(default=None, description="Join FK to CodePrimitiveType")
    code_primitive_type_id: UUID = Field(description="Join FK to CodePrimitiveType")

    @classmethod
    async def build_via_code_primitive_type(
        cls, code_primitive_type_id: UUID, position: int
    ) -> CodePrimitiveTypeElementType:
        """Create one ordered tuple element slot under a CodePrimitiveType."""

        payload = {"code_primitive_type_id": code_primitive_type_id, "position": position}
        result = await invoke_constructor(orm_class=cls, function_name="build_via_code_primitive_type", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CodePrimitiveTypeElementType):
            return value
        return CodePrimitiveTypeElementType.validate_invocation_value(value)


class CodePrimitiveTypeElementTypeBuildViaCodePrimitiveTypeInput(BaseModel):
    code_primitive_type_id: UUID = Field(description="Join FK to CodePrimitiveType")
    position: int


class CodePrimitiveTypeElementTypeBuildViaCodePrimitiveTypeOutput(BaseModel):
    value: CodePrimitiveTypeElementType


FUNCTIONS = {
    "CodePrimitiveTypeElementType": {
        "build_via_code_primitive_type": {
            "canonical": {
                "name": "build_via_code_primitive_type",
                "description": "Create one ordered tuple element slot under a CodePrimitiveType.",
                "is_constructor": True,
            },
            "input": CodePrimitiveTypeElementTypeBuildViaCodePrimitiveTypeInput,
            "output": CodePrimitiveTypeElementTypeBuildViaCodePrimitiveTypeOutput,
        },
    },
}

__all__ = [
    "CodePrimitiveTypeElementType",
    "CodePrimitiveTypeElementTypeBuildViaCodePrimitiveTypeInput",
    "CodePrimitiveTypeElementTypeBuildViaCodePrimitiveTypeOutput",
    "FUNCTIONS",
]
