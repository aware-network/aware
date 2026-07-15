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
    from aware_experience_ontology.program.impl.program_impl_instruction import ProgramImplInstruction
    from aware_experience_ontology.program.program_config import ProgramConfig


class ProgramImpl(ORMModel):
    # Relationships
    program_config: ProgramConfig | None = Field(default=None, exclude=True)
    instructions: list[ProgramImplInstruction] = Field(default_factory=list)

    # Attributes
    key: str

    # Foreign Keys
    program_config_id: UUID = Field(description="Foreign key for ProgramImpl.program_config")

    @classmethod
    async def build(cls, program_config_id: UUID, key: str) -> ProgramImpl:
        """Create a deterministic ProgramImpl."""

        payload = {"program_config_id": program_config_id, "key": key}
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProgramImpl):
            return value
        return ProgramImpl.validate_invocation_value(value)

    async def create_input_instruction(
        self, sequence: int, program_config_input_config_id: UUID
    ) -> ProgramImplInstruction:
        """Create one `input` instruction under this ProgramImpl."""

        payload = {"sequence": sequence, "program_config_input_config_id": program_config_input_config_id}
        result = await invoke_instance(orm_model=self, function_name="create_input_instruction", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.program.impl.program_impl_instruction import ProgramImplInstruction

        if isinstance(value, ProgramImplInstruction):
            return value
        return ProgramImplInstruction.validate_invocation_value(value)

    async def create_let_instruction(self, sequence: int, name: str, value_expr: JsonObject) -> ProgramImplInstruction:
        """Create one `let` instruction under this ProgramImpl."""

        payload = {"sequence": sequence, "name": name, "value_expr": value_expr}
        result = await invoke_instance(orm_model=self, function_name="create_let_instruction", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.program.impl.program_impl_instruction import ProgramImplInstruction

        if isinstance(value, ProgramImplInstruction):
            return value
        return ProgramImplInstruction.validate_invocation_value(value)

    async def create_bind_instruction(
        self, sequence: int, program_config_port_id: UUID, view_key: str, is_active: bool = True
    ) -> ProgramImplInstruction:
        """Create one `bind` instruction under this ProgramImpl."""

        payload = {
            "sequence": sequence,
            "program_config_port_id": program_config_port_id,
            "view_key": view_key,
            "is_active": is_active,
        }
        result = await invoke_instance(orm_model=self, function_name="create_bind_instruction", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.program.impl.program_impl_instruction import ProgramImplInstruction

        if isinstance(value, ProgramImplInstruction):
            return value
        return ProgramImplInstruction.validate_invocation_value(value)

    async def create_invoke_instruction(
        self,
        sequence: int,
        function_config_id: UUID,
        program_config_actor_config_id: UUID,
        program_config_port_projection_experience_node_id: UUID,
        target_kind: ProgramImplInvokeTargetKind = ProgramImplInvokeTargetKind.instance,
    ) -> ProgramImplInstruction:
        """Create one `invoke` instruction under this ProgramImpl."""

        payload = {
            "sequence": sequence,
            "function_config_id": function_config_id,
            "program_config_actor_config_id": program_config_actor_config_id,
            "program_config_port_projection_experience_node_id": program_config_port_projection_experience_node_id,
            "target_kind": target_kind,
        }
        result = await invoke_instance(orm_model=self, function_name="create_invoke_instruction", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.program.impl.program_impl_instruction import ProgramImplInstruction

        if isinstance(value, ProgramImplInstruction):
            return value
        return ProgramImplInstruction.validate_invocation_value(value)

    async def create_expect_instruction(
        self, sequence: int, event_config_id: UUID, required: bool = True
    ) -> ProgramImplInstruction:
        """Create one `expect` instruction under this ProgramImpl."""

        payload = {"sequence": sequence, "event_config_id": event_config_id, "required": required}
        result = await invoke_instance(orm_model=self, function_name="create_expect_instruction", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.program.impl.program_impl_instruction import ProgramImplInstruction

        if isinstance(value, ProgramImplInstruction):
            return value
        return ProgramImplInstruction.validate_invocation_value(value)

    async def create_intent_instruction(
        self, sequence: int, action_config_id: UUID, event_config_id: UUID
    ) -> ProgramImplInstruction:
        """Create one `intent` instruction under this ProgramImpl."""

        payload = {"sequence": sequence, "action_config_id": action_config_id, "event_config_id": event_config_id}
        result = await invoke_instance(orm_model=self, function_name="create_intent_instruction", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.program.impl.program_impl_instruction import ProgramImplInstruction

        if isinstance(value, ProgramImplInstruction):
            return value
        return ProgramImplInstruction.validate_invocation_value(value)


class ProgramImplBuildInput(BaseModel):
    program_config_id: UUID
    key: str


class ProgramImplBuildOutput(BaseModel):
    value: ProgramImpl


class ProgramImplCreateInputInstructionInput(BaseModel):
    sequence: int
    program_config_input_config_id: UUID


class ProgramImplCreateInputInstructionOutput(BaseModel):
    value: ProgramImplInstruction


class ProgramImplCreateLetInstructionInput(BaseModel):
    sequence: int
    name: str
    value_expr: JsonObject


class ProgramImplCreateLetInstructionOutput(BaseModel):
    value: ProgramImplInstruction


class ProgramImplCreateBindInstructionInput(BaseModel):
    sequence: int
    program_config_port_id: UUID
    view_key: str
    is_active: bool = Field(default=True)


class ProgramImplCreateBindInstructionOutput(BaseModel):
    value: ProgramImplInstruction


class ProgramImplCreateInvokeInstructionInput(BaseModel):
    sequence: int
    function_config_id: UUID
    program_config_actor_config_id: UUID
    program_config_port_projection_experience_node_id: UUID
    target_kind: ProgramImplInvokeTargetKind = Field(default=ProgramImplInvokeTargetKind.instance)


class ProgramImplCreateInvokeInstructionOutput(BaseModel):
    value: ProgramImplInstruction


class ProgramImplCreateExpectInstructionInput(BaseModel):
    sequence: int
    event_config_id: UUID
    required: bool = Field(default=True)


class ProgramImplCreateExpectInstructionOutput(BaseModel):
    value: ProgramImplInstruction


class ProgramImplCreateIntentInstructionInput(BaseModel):
    sequence: int
    action_config_id: UUID
    event_config_id: UUID


class ProgramImplCreateIntentInstructionOutput(BaseModel):
    value: ProgramImplInstruction


FUNCTIONS = {
    "ProgramImpl": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Create a deterministic ProgramImpl.",
                "is_constructor": True,
            },
            "input": ProgramImplBuildInput,
            "output": ProgramImplBuildOutput,
        },
        "create_input_instruction": {
            "canonical": {
                "name": "create_input_instruction",
                "description": "Create one `input` instruction under this ProgramImpl.",
                "is_constructor": False,
            },
            "input": ProgramImplCreateInputInstructionInput,
            "output": ProgramImplCreateInputInstructionOutput,
        },
        "create_let_instruction": {
            "canonical": {
                "name": "create_let_instruction",
                "description": "Create one `let` instruction under this ProgramImpl.",
                "is_constructor": False,
            },
            "input": ProgramImplCreateLetInstructionInput,
            "output": ProgramImplCreateLetInstructionOutput,
        },
        "create_bind_instruction": {
            "canonical": {
                "name": "create_bind_instruction",
                "description": "Create one `bind` instruction under this ProgramImpl.",
                "is_constructor": False,
            },
            "input": ProgramImplCreateBindInstructionInput,
            "output": ProgramImplCreateBindInstructionOutput,
        },
        "create_invoke_instruction": {
            "canonical": {
                "name": "create_invoke_instruction",
                "description": "Create one `invoke` instruction under this ProgramImpl.",
                "is_constructor": False,
            },
            "input": ProgramImplCreateInvokeInstructionInput,
            "output": ProgramImplCreateInvokeInstructionOutput,
        },
        "create_expect_instruction": {
            "canonical": {
                "name": "create_expect_instruction",
                "description": "Create one `expect` instruction under this ProgramImpl.",
                "is_constructor": False,
            },
            "input": ProgramImplCreateExpectInstructionInput,
            "output": ProgramImplCreateExpectInstructionOutput,
        },
        "create_intent_instruction": {
            "canonical": {
                "name": "create_intent_instruction",
                "description": "Create one `intent` instruction under this ProgramImpl.",
                "is_constructor": False,
            },
            "input": ProgramImplCreateIntentInstructionInput,
            "output": ProgramImplCreateIntentInstructionOutput,
        },
    },
}

__all__ = [
    "ProgramImpl",
    "ProgramImplBuildInput",
    "ProgramImplBuildOutput",
    "ProgramImplCreateInputInstructionInput",
    "ProgramImplCreateInputInstructionOutput",
    "ProgramImplCreateLetInstructionInput",
    "ProgramImplCreateLetInstructionOutput",
    "ProgramImplCreateBindInstructionInput",
    "ProgramImplCreateBindInstructionOutput",
    "ProgramImplCreateInvokeInstructionInput",
    "ProgramImplCreateInvokeInstructionOutput",
    "ProgramImplCreateExpectInstructionInput",
    "ProgramImplCreateExpectInstructionOutput",
    "ProgramImplCreateIntentInstructionInput",
    "ProgramImplCreateIntentInstructionOutput",
    "FUNCTIONS",
]
