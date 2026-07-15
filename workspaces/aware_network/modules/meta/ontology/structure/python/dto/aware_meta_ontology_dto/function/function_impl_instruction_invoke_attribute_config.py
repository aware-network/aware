from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_meta_ontology_dto.attribute.attribute_config import AttributeConfig


class FunctionImplInstructionInvokeAttributeConfig(BaseModel):
    """Signature/value binding slot for `FunctionImplInstructionInvoke`."""

    # Relationships
    attribute_config: AttributeConfig | None = Field(default=None)

    # Attributes
    value_expr: JsonObject
    position: int | None = Field(default=None)
