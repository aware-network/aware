from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_experience_ontology_dto.program.impl.program_impl_instruction_bind import ProgramImplInstructionBind
    from aware_experience_ontology_dto.program.program_turn_instruction_bind_identity import (
        ProgramTurnInstructionBindIdentity,
    )
    from aware_experience_ontology_dto.projection.projection_experience_view import ProjectionExperienceView
    from aware_meta_ontology_dto.graph.instance.object_instance_graph_branch import ObjectInstanceGraphBranch


class ProgramTurnInstructionBind(BaseModel):
    """
    Canonical bind execution receipt under one ProgramTurnInstruction.
    Contract:
    - Captures resolved branch/view bindings for one bind instruction execution.
    - Owns per-node alias resolution receipts (`resolved_node_identities`).
    """

    # Relationships
    program_impl_instruction_bind: ProgramImplInstructionBind | None = Field(default=None)
    object_instance_graph_branch: ObjectInstanceGraphBranch | None = Field(default=None)
    projection_experience_view: ProjectionExperienceView | None = Field(default=None)
    resolved_node_identities: list[ProgramTurnInstructionBindIdentity] = Field(default_factory=list)
