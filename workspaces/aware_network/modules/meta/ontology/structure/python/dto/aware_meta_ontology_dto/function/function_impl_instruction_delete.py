from __future__ import annotations

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Meta Ontology Dto
from aware_meta_ontology_dto.function.function_impl_instruction_enums import FunctionImplDeleteTargetKind


class FunctionImplInstructionDelete(BaseModel):
    """
    Deterministic self-owned graph lifecycle deletion payload.
    Contract:
    - `delete self` is the only v0 authored target.
    - Runtime deletes the invoked ClassInstance's self-owned closure only.
    - External parent/detach/cascade semantics are separate routed operations.
    """

    # Attributes
    target_kind: FunctionImplDeleteTargetKind = Field(default=FunctionImplDeleteTargetKind.self)
