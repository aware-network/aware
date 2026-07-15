from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_experience_ontology.program.impl.program_impl_instruction_bind import ProgramImplInstructionBind
    from aware_experience_ontology.program.program_turn_instruction_bind_identity import (
        ProgramTurnInstructionBindIdentity,
    )
    from aware_experience_ontology.projection.projection_experience_view import ProjectionExperienceView
    from aware_meta_ontology.graph.instance.object_instance_graph_branch import ObjectInstanceGraphBranch


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

    async def add_resolved_node_identity(
        self,
        program_config_port_projection_experience_node_id: UUID,
        projection_experience_node_class_identity_id: UUID,
    ) -> ProgramTurnInstructionBindIdentity:
        """Record one deterministic alias->ClassInstanceIdentity resolution receipt."""

        payload = {
            "program_config_port_projection_experience_node_id": program_config_port_projection_experience_node_id,
            "projection_experience_node_class_identity_id": projection_experience_node_class_identity_id,
        }
        result = await invoke_instance(orm_model=self, function_name="add_resolved_node_identity", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.program.program_turn_instruction_bind_identity import (
            ProgramTurnInstructionBindIdentity,
        )

        if isinstance(value, ProgramTurnInstructionBindIdentity):
            return value
        return ProgramTurnInstructionBindIdentity.validate_invocation_value(value)

    @classmethod
    async def build_via_program_turn_instruction(
        cls,
        program_turn_instruction_id: UUID,
        program_impl_instruction_bind_id: UUID,
        object_instance_graph_branch_id: UUID,
        projection_experience_view_id: UUID,
    ) -> ProgramTurnInstructionBind:
        """Create deterministic ProgramTurnInstructionBind under ProgramTurnInstruction."""

        payload = {
            "program_turn_instruction_id": program_turn_instruction_id,
            "program_impl_instruction_bind_id": program_impl_instruction_bind_id,
            "object_instance_graph_branch_id": object_instance_graph_branch_id,
            "projection_experience_view_id": projection_experience_view_id,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_program_turn_instruction", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProgramTurnInstructionBind):
            return value
        return ProgramTurnInstructionBind.validate_invocation_value(value)


class ProgramTurnInstructionBindAddResolvedNodeIdentityInput(BaseModel):
    program_config_port_projection_experience_node_id: UUID
    projection_experience_node_class_identity_id: UUID


class ProgramTurnInstructionBindAddResolvedNodeIdentityOutput(BaseModel):
    value: ProgramTurnInstructionBindIdentity


class ProgramTurnInstructionBindBuildViaProgramTurnInstructionInput(BaseModel):
    program_turn_instruction_id: UUID = Field(description="Foreign key for ProgramTurnInstruction.bind_receipt")
    program_impl_instruction_bind_id: UUID
    object_instance_graph_branch_id: UUID
    projection_experience_view_id: UUID


class ProgramTurnInstructionBindBuildViaProgramTurnInstructionOutput(BaseModel):
    value: ProgramTurnInstructionBind


FUNCTIONS = {
    "ProgramTurnInstructionBind": {
        "add_resolved_node_identity": {
            "canonical": {
                "name": "add_resolved_node_identity",
                "description": "Record one deterministic alias->ClassInstanceIdentity resolution receipt.",
                "is_constructor": False,
            },
            "input": ProgramTurnInstructionBindAddResolvedNodeIdentityInput,
            "output": ProgramTurnInstructionBindAddResolvedNodeIdentityOutput,
        },
        "build_via_program_turn_instruction": {
            "canonical": {
                "name": "build_via_program_turn_instruction",
                "description": "Create deterministic ProgramTurnInstructionBind under ProgramTurnInstruction.",
                "is_constructor": True,
            },
            "input": ProgramTurnInstructionBindBuildViaProgramTurnInstructionInput,
            "output": ProgramTurnInstructionBindBuildViaProgramTurnInstructionOutput,
        },
    },
}

__all__ = [
    "ProgramTurnInstructionBind",
    "ProgramTurnInstructionBindAddResolvedNodeIdentityInput",
    "ProgramTurnInstructionBindAddResolvedNodeIdentityOutput",
    "ProgramTurnInstructionBindBuildViaProgramTurnInstructionInput",
    "ProgramTurnInstructionBindBuildViaProgramTurnInstructionOutput",
    "FUNCTIONS",
]
