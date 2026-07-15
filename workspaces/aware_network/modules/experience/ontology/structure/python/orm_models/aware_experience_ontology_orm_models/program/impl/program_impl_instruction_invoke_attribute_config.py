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


class ProgramImplInstructionInvokeAttributeConfig(ORMModel):
    """
    Signature/value binding slot for ProgramImplInstructionInvoke.
    Contract:
    - Keeps invoke argument lowering explicit and deterministic.
    - Association identity is deterministic from `(invoke_id, attribute_config_id)`.
    """

    # Relationships
    attribute_config: AttributeConfig | None = Field(default=None, exclude=True)

    # Attributes
    value_expr: JsonObject
    position: int | None = Field(default=None)

    # Foreign Keys
    program_impl_instruction_invoke_id: UUID = Field(
        description="Foreign key for ProgramImplInstructionInvoke.attribute_configs"
    )
    attribute_config_id: UUID = Field(
        description="Foreign key for ProgramImplInstructionInvokeAttributeConfig.attribute_config"
    )
