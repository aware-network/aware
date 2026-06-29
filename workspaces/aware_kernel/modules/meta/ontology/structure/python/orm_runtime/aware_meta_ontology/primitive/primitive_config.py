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
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_code_ontology.primitive.code_primitive_type import CodePrimitiveType


class PrimitiveConfig(ORMModel):
    # Relationships
    primitive_type: CodePrimitiveType

    # Foreign Keys
    primitive_type_id: UUID | None = Field(default=None, description="Foreign key for PrimitiveConfig.primitive_type")

    @classmethod
    async def create(
        cls, primitive_config_id: UUID, primitive_type_id: UUID, primitive_base_type: CodePrimitiveBaseType
    ) -> PrimitiveConfig:
        """Create deterministic PrimitiveConfig with explicit identity."""

        payload = {
            "primitive_config_id": primitive_config_id,
            "primitive_type_id": primitive_type_id,
            "primitive_base_type": primitive_base_type,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, PrimitiveConfig):
            return value
        return PrimitiveConfig.validate_invocation_value(value)


class PrimitiveConfigCreateInput(BaseModel):
    primitive_config_id: UUID
    primitive_type_id: UUID
    primitive_base_type: CodePrimitiveBaseType


class PrimitiveConfigCreateOutput(BaseModel):
    value: PrimitiveConfig


FUNCTIONS = {
    "PrimitiveConfig": {
        "create": {
            "canonical": {
                "name": "create",
                "description": "Create deterministic PrimitiveConfig with explicit identity.",
                "is_constructor": True,
            },
            "input": PrimitiveConfigCreateInput,
            "output": PrimitiveConfigCreateOutput,
        },
    },
}

__all__ = [
    "PrimitiveConfig",
    "PrimitiveConfigCreateInput",
    "PrimitiveConfigCreateOutput",
    "FUNCTIONS",
]
