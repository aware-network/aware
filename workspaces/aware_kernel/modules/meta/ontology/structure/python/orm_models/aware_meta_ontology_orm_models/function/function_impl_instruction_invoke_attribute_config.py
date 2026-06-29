from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.attribute.attribute_config import AttributeConfig


class FunctionImplInstructionInvokeAttributeConfig(ORMModel):
    """Signature/value binding slot for `FunctionImplInstructionInvoke`."""

    # Relationships
    attribute_config: AttributeConfig | None = Field(default=None, exclude=True)

    # Attributes
    value_expr: JsonObject
    position: int | None = Field(default=None)

    # Foreign Keys
    function_impl_instruction_invoke_id: UUID = Field(
        description="Foreign key for FunctionImplInstructionInvoke.attribute_configs"
    )
    attribute_config_id: UUID = Field(
        description="Foreign key for FunctionImplInstructionInvokeAttributeConfig.attribute_config"
    )
