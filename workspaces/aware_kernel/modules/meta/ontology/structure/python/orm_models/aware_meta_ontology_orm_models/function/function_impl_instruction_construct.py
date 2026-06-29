from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.class_.class_config import ClassConfig
    from aware_meta_ontology_orm_models.function.function_impl_instruction_construct_assignment import (
        FunctionImplInstructionConstructAssignment,
    )


class FunctionImplInstructionConstruct(ORMModel):
    """
    Canonical explicit object-construction payload in function execution rail.
    Contract:
    - Represents direct object materialization intent (`construct ClassName(...)`).
    - Distinct from constructor invocation (`FunctionImplInstructionInvoke(kind=construct)`).
    """

    # Relationships
    target_class_config: ClassConfig | None = Field(default=None, exclude=True)
    assignments: list[FunctionImplInstructionConstructAssignment] = Field(default_factory=list)

    # Foreign Keys
    function_impl_instruction_id: UUID | None = Field(
        default=None, description="Foreign key for FunctionImplInstruction.instruction_construct"
    )
    target_class_config_id: UUID = Field(
        description="Foreign key for FunctionImplInstructionConstruct.target_class_config"
    )
