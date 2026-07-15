from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Experience Ontology Dto
from aware_experience_ontology_dto.program.impl.program_impl_instruction_enums import ProgramImplInvokeTargetKind

if TYPE_CHECKING:
    from aware_experience_ontology_dto.program.impl.program_impl_instruction_invoke_attribute_config import (
        ProgramImplInstructionInvokeAttributeConfig,
    )
    from aware_experience_ontology_dto.program.program_config_actor_config import ProgramConfigActorConfig
    from aware_experience_ontology_dto.program.program_config_port_projection_experience_node import (
        ProgramConfigPortProjectionExperienceNode,
    )
    from aware_meta_ontology_dto.function.function_config import FunctionConfig


class ProgramImplInstructionInvoke(BaseModel):
    """
    Program effectful invocation step.
    Contract:
    - Canonical target is `function_config` (no string-dispatched calls).
    - Runtime must fail-closed when invoked without active branch context.
    """

    # Relationships
    function_config: FunctionConfig | None = Field(default=None)
    program_config_actor_config: ProgramConfigActorConfig | None = Field(default=None)
    program_config_port_projection_experience_node: ProgramConfigPortProjectionExperienceNode | None = Field(
        default=None
    )
    attribute_configs: list[ProgramImplInstructionInvokeAttributeConfig] = Field(default_factory=list)

    # Attributes
    target_kind: ProgramImplInvokeTargetKind = Field(default=ProgramImplInvokeTargetKind.instance)
