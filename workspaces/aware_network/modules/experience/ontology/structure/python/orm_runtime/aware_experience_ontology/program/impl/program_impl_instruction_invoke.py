from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Experience Ontology
from aware_experience_ontology.program.impl.program_impl_instruction_enums import ProgramImplInvokeTargetKind

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_experience_ontology.program.impl.program_impl_instruction_invoke_attribute_config import (
        ProgramImplInstructionInvokeAttributeConfig,
    )
    from aware_experience_ontology.program.program_config_actor_config import ProgramConfigActorConfig
    from aware_experience_ontology.program.program_config_port_projection_experience_node import (
        ProgramConfigPortProjectionExperienceNode,
    )
    from aware_meta_ontology.function.function_config import FunctionConfig


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

    async def add_attribute_config(
        self, attribute_config_id: UUID, value_expr: JsonObject, position: int | None = None
    ) -> ProgramImplInstructionInvokeAttributeConfig:
        """Attach one deterministic invoke argument binding by AttributeConfig contract."""

        payload = {"attribute_config_id": attribute_config_id, "value_expr": value_expr, "position": position}
        result = await invoke_instance(orm_model=self, function_name="add_attribute_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.program.impl.program_impl_instruction_invoke_attribute_config import (
            ProgramImplInstructionInvokeAttributeConfig,
        )

        if isinstance(value, ProgramImplInstructionInvokeAttributeConfig):
            return value
        return ProgramImplInstructionInvokeAttributeConfig.validate_invocation_value(value)

    @classmethod
    async def build_via_program_impl_instruction(
        cls,
        program_impl_instruction_id: UUID,
        function_config_id: UUID,
        program_config_actor_config_id: UUID,
        program_config_port_projection_experience_node_id: UUID,
        target_kind: ProgramImplInvokeTargetKind = ProgramImplInvokeTargetKind.instance,
    ) -> ProgramImplInstructionInvoke:
        """
        Create deterministic invoke payload for one ProgramImplInstruction.

        Contract:
        - Parent context (`program_impl_instruction_id`) is injected by parent-edge lowering.
        """

        payload = {
            "program_impl_instruction_id": program_impl_instruction_id,
            "function_config_id": function_config_id,
            "program_config_actor_config_id": program_config_actor_config_id,
            "program_config_port_projection_experience_node_id": program_config_port_projection_experience_node_id,
            "target_kind": target_kind,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_program_impl_instruction", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProgramImplInstructionInvoke):
            return value
        return ProgramImplInstructionInvoke.validate_invocation_value(value)


class ProgramImplInstructionInvokeAddAttributeConfigInput(BaseModel):
    attribute_config_id: UUID
    value_expr: JsonObject
    position: int | None = Field(default=None)


class ProgramImplInstructionInvokeAddAttributeConfigOutput(BaseModel):
    value: ProgramImplInstructionInvokeAttributeConfig


class ProgramImplInstructionInvokeBuildViaProgramImplInstructionInput(BaseModel):
    program_impl_instruction_id: UUID = Field(description="Foreign key for ProgramImplInstruction.instruction_invoke")
    function_config_id: UUID
    program_config_actor_config_id: UUID
    program_config_port_projection_experience_node_id: UUID
    target_kind: ProgramImplInvokeTargetKind = Field(default=ProgramImplInvokeTargetKind.instance)


class ProgramImplInstructionInvokeBuildViaProgramImplInstructionOutput(BaseModel):
    value: ProgramImplInstructionInvoke


FUNCTIONS = {
    "ProgramImplInstructionInvoke": {
        "add_attribute_config": {
            "canonical": {
                "name": "add_attribute_config",
                "description": "Attach one deterministic invoke argument binding by AttributeConfig contract.",
                "is_constructor": False,
            },
            "input": ProgramImplInstructionInvokeAddAttributeConfigInput,
            "output": ProgramImplInstructionInvokeAddAttributeConfigOutput,
        },
        "build_via_program_impl_instruction": {
            "canonical": {
                "name": "build_via_program_impl_instruction",
                "description": "Create deterministic invoke payload for one ProgramImplInstruction.\n\nContract:\n- Parent context (`program_impl_instruction_id`) is injected by parent-edge lowering.",
                "is_constructor": True,
            },
            "input": ProgramImplInstructionInvokeBuildViaProgramImplInstructionInput,
            "output": ProgramImplInstructionInvokeBuildViaProgramImplInstructionOutput,
        },
    },
}

__all__ = [
    "ProgramImplInstructionInvoke",
    "ProgramImplInstructionInvokeAddAttributeConfigInput",
    "ProgramImplInstructionInvokeAddAttributeConfigOutput",
    "ProgramImplInstructionInvokeBuildViaProgramImplInstructionInput",
    "ProgramImplInstructionInvokeBuildViaProgramImplInstructionOutput",
    "FUNCTIONS",
]
