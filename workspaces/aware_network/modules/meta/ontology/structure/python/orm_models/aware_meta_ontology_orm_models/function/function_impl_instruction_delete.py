from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import Field

# Meta Ontology Orm Models
from aware_meta_ontology_orm_models.function.function_impl_instruction_enums import FunctionImplDeleteTargetKind

# Orm
from aware_orm.models.orm_model import ORMModel


class FunctionImplInstructionDelete(ORMModel):
    """
    Deterministic self-owned graph lifecycle deletion payload.
    Contract:
    - `delete self` is the only v0 authored target.
    - Runtime deletes the invoked ClassInstance's self-owned closure only.
    - External parent/detach/cascade semantics are separate routed operations.
    """

    # Attributes
    target_kind: FunctionImplDeleteTargetKind = Field(default=FunctionImplDeleteTargetKind.self)

    # Foreign Keys
    function_impl_instruction_id: UUID | None = Field(
        default=None, description="Foreign key for FunctionImplInstruction.instruction_delete"
    )
