from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.class_.class_config_attribute_config import ClassConfigAttributeConfig
    from aware_meta_ontology_orm_models.function.function_impl_value_source import FunctionImplValueSource


class FunctionImplInstructionSet(ORMModel):
    """
    Deterministic mutation intent payload for function execution rail.
    Notes:
    - Grammar lowering for `set` is staged after this ontology contract.
    - Runtime must remain fail-closed until lowering/execution support is complete.
    """

    # Relationships
    target_class_config_attribute_config: ClassConfigAttributeConfig = Field(
        description="Canonical self-owned attribute declaration being mutated."
    )
    value_source: FunctionImplValueSource = Field(
        description="Deterministic assignment source (literal / function input ref / let ref)."
    )

    # Foreign Keys
    function_impl_instruction_id: UUID | None = Field(
        default=None, description="Foreign key for FunctionImplInstruction.instruction_set"
    )
    target_class_config_attribute_config_id: UUID | None = Field(
        default=None, description="Foreign key for FunctionImplInstructionSet.target_class_config_attribute_config"
    )
    value_source_id: UUID | None = Field(
        default=None, description="Foreign key for FunctionImplInstructionSet.value_source"
    )
