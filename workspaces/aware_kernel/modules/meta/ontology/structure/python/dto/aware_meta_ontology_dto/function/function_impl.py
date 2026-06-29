from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Meta Ontology Dto
from aware_meta_ontology_dto.function.function_impl_enums import FunctionImplKind

if TYPE_CHECKING:
    from aware_meta_ontology_dto.function.function_impl_instruction import FunctionImplInstruction


class FunctionImpl(BaseModel):
    """
    Canonical execution rail for one function body.
    Contract:
    - Runtime executes `FunctionImplInstruction*` payloads, not raw source text.
    - `kind` distinguishes executable instruction bodies from declarative auto constructors.
    - `FunctionConfig` remains signature/contract truth.
    """

    # Relationships
    instructions: list[FunctionImplInstruction] = Field(default_factory=list)

    # Attributes
    key: str
    kind: FunctionImplKind = Field(default=FunctionImplKind.instruction_body)
