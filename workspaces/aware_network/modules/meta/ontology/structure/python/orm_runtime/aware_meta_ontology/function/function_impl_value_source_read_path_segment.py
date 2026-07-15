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
    from aware_meta_ontology.attribute.attribute_config import AttributeConfig


class FunctionImplValueSourceReadPathSegment(ORMModel):
    """
    Ordered typed member segment for `FunctionImplValueSourceReadPath`.
    Contract:
    - `attribute_config` is compiler-resolved from the previous class-valued hop.
    - `position` is compiler-owned path order.
    """

    # Relationships
    attribute_config: AttributeConfig

    # Attributes
    position: int

    # Foreign Keys
    function_impl_value_source_read_path_id: UUID = Field(
        description="Foreign key for FunctionImplValueSourceReadPath.segments"
    )
    attribute_config_id: UUID | None = Field(
        default=None, description="Foreign key for FunctionImplValueSourceReadPathSegment.attribute_config"
    )

    @classmethod
    async def build_via_function_impl_value_source_read_path(
        cls, function_impl_value_source_read_path_id: UUID, position: int, attribute_config_id: UUID
    ) -> FunctionImplValueSourceReadPathSegment:
        """Create deterministic read-path segment under one read-path payload."""

        payload = {
            "function_impl_value_source_read_path_id": function_impl_value_source_read_path_id,
            "position": position,
            "attribute_config_id": attribute_config_id,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_function_impl_value_source_read_path", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, FunctionImplValueSourceReadPathSegment):
            return value
        return FunctionImplValueSourceReadPathSegment.validate_invocation_value(value)


class FunctionImplValueSourceReadPathSegmentBuildViaFunctionImplValueSourceReadPathInput(BaseModel):
    function_impl_value_source_read_path_id: UUID = Field(
        description="Foreign key for FunctionImplValueSourceReadPath.segments"
    )
    position: int
    attribute_config_id: UUID


class FunctionImplValueSourceReadPathSegmentBuildViaFunctionImplValueSourceReadPathOutput(BaseModel):
    value: FunctionImplValueSourceReadPathSegment


FUNCTIONS = {
    "FunctionImplValueSourceReadPathSegment": {
        "build_via_function_impl_value_source_read_path": {
            "canonical": {
                "name": "build_via_function_impl_value_source_read_path",
                "description": "Create deterministic read-path segment under one read-path payload.",
                "is_constructor": True,
            },
            "input": FunctionImplValueSourceReadPathSegmentBuildViaFunctionImplValueSourceReadPathInput,
            "output": FunctionImplValueSourceReadPathSegmentBuildViaFunctionImplValueSourceReadPathOutput,
        },
    },
}

__all__ = [
    "FunctionImplValueSourceReadPathSegment",
    "FunctionImplValueSourceReadPathSegmentBuildViaFunctionImplValueSourceReadPathInput",
    "FunctionImplValueSourceReadPathSegmentBuildViaFunctionImplValueSourceReadPathOutput",
    "FUNCTIONS",
]
