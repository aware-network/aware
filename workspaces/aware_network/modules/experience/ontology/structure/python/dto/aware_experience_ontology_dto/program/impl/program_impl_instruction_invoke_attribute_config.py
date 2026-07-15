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


class ProgramImplInstructionInvokeAttributeConfig(BaseModel):
    """
    Signature/value binding slot for ProgramImplInstructionInvoke.
    Contract:
    - Keeps invoke argument lowering explicit and deterministic.
    - Association identity is deterministic from `(invoke_id, attribute_config_id)`.
    """

    # Relationships
    attribute_config: AttributeConfig | None = Field(default=None)

    # Attributes
    value_expr: JsonObject
    position: int | None = Field(default=None)
