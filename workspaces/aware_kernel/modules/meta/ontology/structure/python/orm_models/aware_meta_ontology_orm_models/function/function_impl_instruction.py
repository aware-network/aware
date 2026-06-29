from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Meta Ontology Orm Models
from aware_meta_ontology_orm_models.function.function_impl_instruction_enums import FunctionImplInstructionType

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.function.function_impl_instruction_construct import (
        FunctionImplInstructionConstruct,
    )
    from aware_meta_ontology_orm_models.function.function_impl_instruction_delete import FunctionImplInstructionDelete
    from aware_meta_ontology_orm_models.function.function_impl_instruction_invoke import FunctionImplInstructionInvoke
    from aware_meta_ontology_orm_models.function.function_impl_instruction_let import FunctionImplInstructionLet
    from aware_meta_ontology_orm_models.function.function_impl_instruction_require import FunctionImplInstructionRequire
    from aware_meta_ontology_orm_models.function.function_impl_instruction_set import FunctionImplInstructionSet
    from aware_meta_ontology_orm_models.function.function_impl_value_source import FunctionImplValueSource


class FunctionImplInstruction(ORMModel):
    """Polymorphic instruction payload owned by `FunctionImpl`."""

    # Relationships
    instruction_let: FunctionImplInstructionLet | None = Field(default=None)
    instruction_invoke: FunctionImplInstructionInvoke | None = Field(default=None)
    instruction_construct: FunctionImplInstructionConstruct | None = Field(default=None)
    instruction_set: FunctionImplInstructionSet | None = Field(default=None)
    instruction_require: FunctionImplInstructionRequire | None = Field(default=None)
    instruction_delete: FunctionImplInstructionDelete | None = Field(default=None)
    value_sources: list[FunctionImplValueSource] = Field(default_factory=list)

    # Attributes
    type: FunctionImplInstructionType
    sequence: int

    # Foreign Keys
    function_impl_id: UUID = Field(description="Foreign key for FunctionImpl.instructions")
