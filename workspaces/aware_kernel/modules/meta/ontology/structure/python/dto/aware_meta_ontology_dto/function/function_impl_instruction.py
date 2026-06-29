from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Meta Ontology Dto
from aware_meta_ontology_dto.function.function_impl_instruction_enums import FunctionImplInstructionType

if TYPE_CHECKING:
    from aware_meta_ontology_dto.function.function_impl_instruction_construct import FunctionImplInstructionConstruct
    from aware_meta_ontology_dto.function.function_impl_instruction_delete import FunctionImplInstructionDelete
    from aware_meta_ontology_dto.function.function_impl_instruction_invoke import FunctionImplInstructionInvoke
    from aware_meta_ontology_dto.function.function_impl_instruction_let import FunctionImplInstructionLet
    from aware_meta_ontology_dto.function.function_impl_instruction_require import FunctionImplInstructionRequire
    from aware_meta_ontology_dto.function.function_impl_instruction_set import FunctionImplInstructionSet
    from aware_meta_ontology_dto.function.function_impl_value_source import FunctionImplValueSource


class FunctionImplInstruction(BaseModel):
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
