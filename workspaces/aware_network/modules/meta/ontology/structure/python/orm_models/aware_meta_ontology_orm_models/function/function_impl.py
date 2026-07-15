from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Meta Ontology Orm Models
from aware_meta_ontology_orm_models.function.function_impl_enums import FunctionImplKind

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.function.function_impl_instruction import FunctionImplInstruction


class FunctionImpl(ORMModel):
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

    # Foreign Keys
    function_config_id: UUID | None = Field(default=None, description="Foreign key for FunctionConfig.function_impl")
