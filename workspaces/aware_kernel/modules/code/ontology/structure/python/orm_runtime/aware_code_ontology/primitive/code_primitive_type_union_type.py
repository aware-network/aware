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


class CodePrimitiveTypeUnionType(ORMModel):
    """
    Edge linking a union-like CodePrimitiveType to its member types.
    Modeled as an explicit edge to support:
    - self-referential unions without ambiguous FK names
    - sharing member nodes across multiple parents (M2M semantics)
    - stable ordering for deterministic renders via `position` (optional)
    """

    # Relationships
    union_type: CodePrimitiveType = Field(description="Association target reference to CodePrimitiveType")

    # Attributes
    position: int

    # Foreign Keys
    union_type_id: UUID | None = Field(default=None, description="Join FK to CodePrimitiveType")
    code_primitive_type_id: UUID = Field(description="Join FK to CodePrimitiveType")

    @classmethod
    async def build_via_code_primitive_type(
        cls, code_primitive_type_id: UUID, position: int
    ) -> CodePrimitiveTypeUnionType:
        """Create one ordered union member slot under a CodePrimitiveType."""

        payload = {"code_primitive_type_id": code_primitive_type_id, "position": position}
        result = await invoke_constructor(orm_class=cls, function_name="build_via_code_primitive_type", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CodePrimitiveTypeUnionType):
            return value
        return CodePrimitiveTypeUnionType.validate_invocation_value(value)


class CodePrimitiveTypeUnionTypeBuildViaCodePrimitiveTypeInput(BaseModel):
    code_primitive_type_id: UUID = Field(description="Join FK to CodePrimitiveType")
    position: int


class CodePrimitiveTypeUnionTypeBuildViaCodePrimitiveTypeOutput(BaseModel):
    value: CodePrimitiveTypeUnionType


FUNCTIONS = {
    "CodePrimitiveTypeUnionType": {
        "build_via_code_primitive_type": {
            "canonical": {
                "name": "build_via_code_primitive_type",
                "description": "Create one ordered union member slot under a CodePrimitiveType.",
                "is_constructor": True,
            },
            "input": CodePrimitiveTypeUnionTypeBuildViaCodePrimitiveTypeInput,
            "output": CodePrimitiveTypeUnionTypeBuildViaCodePrimitiveTypeOutput,
        },
    },
}

__all__ = [
    "CodePrimitiveTypeUnionType",
    "CodePrimitiveTypeUnionTypeBuildViaCodePrimitiveTypeInput",
    "CodePrimitiveTypeUnionTypeBuildViaCodePrimitiveTypeOutput",
    "FUNCTIONS",
]
