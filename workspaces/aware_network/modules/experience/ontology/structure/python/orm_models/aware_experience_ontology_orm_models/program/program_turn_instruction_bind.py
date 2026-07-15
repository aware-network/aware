from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.program.impl.program_impl_instruction_bind import (
        ProgramImplInstructionBind,
    )
    from aware_experience_ontology_orm_models.program.program_turn_instruction_bind_identity import (
        ProgramTurnInstructionBindIdentity,
    )
    from aware_experience_ontology_orm_models.projection.projection_experience_view import ProjectionExperienceView
    from aware_meta_ontology_orm_models.graph.instance.object_instance_graph_branch import ObjectInstanceGraphBranch


class ProgramTurnInstructionBind(ORMModel):
    """
    Canonical bind execution receipt under one ProgramTurnInstruction.
    Contract:
    - Captures resolved branch/view bindings for one bind instruction execution.
    - Owns per-node alias resolution receipts (`resolved_node_identities`).
    """

    # Relationships
    program_impl_instruction_bind: ProgramImplInstructionBind | None = Field(default=None, exclude=True)
    object_instance_graph_branch: ObjectInstanceGraphBranch | None = Field(default=None, exclude=True)
    projection_experience_view: ProjectionExperienceView | None = Field(default=None, exclude=True)
    resolved_node_identities: list[ProgramTurnInstructionBindIdentity] = Field(default_factory=list, exclude=True)

    # Foreign Keys
    program_turn_instruction_id: UUID | None = Field(
        default=None, description="Foreign key for ProgramTurnInstruction.bind_receipt"
    )
    program_impl_instruction_bind_id: UUID = Field(
        description="Foreign key for ProgramTurnInstructionBind.program_impl_instruction_bind"
    )
    object_instance_graph_branch_id: UUID = Field(
        description="Foreign key for ProgramTurnInstructionBind.object_instance_graph_branch"
    )
    projection_experience_view_id: UUID = Field(
        description="Foreign key for ProgramTurnInstructionBind.projection_experience_view"
    )
