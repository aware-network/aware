from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Experience Ontology Orm Models
from aware_experience_ontology_orm_models.program.impl.program_impl_instruction_enums import ProgramImplInvokeTargetKind

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.program.impl.program_impl_instruction_invoke_attribute_config import (
        ProgramImplInstructionInvokeAttributeConfig,
    )
    from aware_experience_ontology_orm_models.program.program_config_actor_config import ProgramConfigActorConfig
    from aware_experience_ontology_orm_models.program.program_config_port_projection_experience_node import (
        ProgramConfigPortProjectionExperienceNode,
    )
    from aware_meta_ontology_orm_models.function.function_config import FunctionConfig


class ProgramImplInstructionInvoke(ORMModel):
    """
    Program effectful invocation step.
    Contract:
    - Canonical target is `function_config` (no string-dispatched calls).
    - Runtime must fail-closed when invoked without active branch context.
    """

    # Relationships
    function_config: FunctionConfig | None = Field(default=None, exclude=True)
    program_config_actor_config: ProgramConfigActorConfig | None = Field(default=None, exclude=True)
    program_config_port_projection_experience_node: ProgramConfigPortProjectionExperienceNode | None = Field(
        default=None, exclude=True
    )
    attribute_configs: list[ProgramImplInstructionInvokeAttributeConfig] = Field(default_factory=list, exclude=True)

    # Attributes
    target_kind: ProgramImplInvokeTargetKind = Field(default=ProgramImplInvokeTargetKind.instance)

    # Foreign Keys
    program_impl_instruction_id: UUID | None = Field(
        default=None, description="Foreign key for ProgramImplInstruction.instruction_invoke"
    )
    function_config_id: UUID = Field(description="Foreign key for ProgramImplInstructionInvoke.function_config")
    program_config_actor_config_id: UUID = Field(
        description="Foreign key for ProgramImplInstructionInvoke.program_config_actor_config"
    )
    program_config_port_projection_experience_node_id: UUID = Field(
        description="Foreign key for ProgramImplInstructionInvoke.program_config_port_projection_experience_node"
    )
