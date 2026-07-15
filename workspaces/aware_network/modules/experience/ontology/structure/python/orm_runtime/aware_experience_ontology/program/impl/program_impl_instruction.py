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
from aware_experience_ontology.program.impl.program_impl_instruction_enums import (
    ProgramImplInstructionType,
    ProgramImplInvokeTargetKind,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_experience_ontology.program.impl.program_impl_instruction_bind import ProgramImplInstructionBind
    from aware_experience_ontology.program.impl.program_impl_instruction_expect import ProgramImplInstructionExpect
    from aware_experience_ontology.program.impl.program_impl_instruction_input import ProgramImplInstructionInput
    from aware_experience_ontology.program.impl.program_impl_instruction_intent import ProgramImplInstructionIntent
    from aware_experience_ontology.program.impl.program_impl_instruction_invoke import ProgramImplInstructionInvoke
    from aware_experience_ontology.program.impl.program_impl_instruction_let import ProgramImplInstructionLet


class ProgramImplInstruction(ORMModel):
    """Polymorphic instruction for program impl construction."""

    # Relationships
    instruction_input: ProgramImplInstructionInput | None = Field(default=None)
    instruction_let: ProgramImplInstructionLet | None = Field(default=None)
    instruction_bind: ProgramImplInstructionBind | None = Field(default=None)
    instruction_invoke: ProgramImplInstructionInvoke | None = Field(default=None)
    instruction_expect: ProgramImplInstructionExpect | None = Field(default=None)
    instruction_intent: ProgramImplInstructionIntent | None = Field(default=None)

    # Attributes
    type: ProgramImplInstructionType
    sequence: int

    # Foreign Keys
    program_impl_id: UUID = Field(description="Foreign key for ProgramImpl.instructions")

    @classmethod
    async def create_bind_via_program_impl(
        cls, program_impl_id: UUID, sequence: int, program_config_port_id: UUID, view_key: str, is_active: bool = True
    ) -> ProgramImplInstruction:
        """Create one `bind` ProgramImplInstruction with its typed payload."""

        payload = {
            "program_impl_id": program_impl_id,
            "sequence": sequence,
            "program_config_port_id": program_config_port_id,
            "view_key": view_key,
            "is_active": is_active,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_bind_via_program_impl", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProgramImplInstruction):
            return value
        return ProgramImplInstruction.validate_invocation_value(value)

    @classmethod
    async def create_expect_via_program_impl(
        cls, program_impl_id: UUID, sequence: int, event_config_id: UUID, required: bool = True
    ) -> ProgramImplInstruction:
        """Create one `expect` ProgramImplInstruction with its typed payload."""

        payload = {
            "program_impl_id": program_impl_id,
            "sequence": sequence,
            "event_config_id": event_config_id,
            "required": required,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="create_expect_via_program_impl", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProgramImplInstruction):
            return value
        return ProgramImplInstruction.validate_invocation_value(value)

    @classmethod
    async def create_input_via_program_impl(
        cls, program_impl_id: UUID, sequence: int, program_config_input_config_id: UUID
    ) -> ProgramImplInstruction:
        """Create one `input` ProgramImplInstruction with its typed payload."""

        payload = {
            "program_impl_id": program_impl_id,
            "sequence": sequence,
            "program_config_input_config_id": program_config_input_config_id,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_input_via_program_impl", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProgramImplInstruction):
            return value
        return ProgramImplInstruction.validate_invocation_value(value)

    @classmethod
    async def create_intent_via_program_impl(
        cls, program_impl_id: UUID, sequence: int, action_config_id: UUID, event_config_id: UUID
    ) -> ProgramImplInstruction:
        """Create one `intent` ProgramImplInstruction with its typed payload."""

        payload = {
            "program_impl_id": program_impl_id,
            "sequence": sequence,
            "action_config_id": action_config_id,
            "event_config_id": event_config_id,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="create_intent_via_program_impl", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProgramImplInstruction):
            return value
        return ProgramImplInstruction.validate_invocation_value(value)

    @classmethod
    async def create_invoke_via_program_impl(
        cls,
        program_impl_id: UUID,
        sequence: int,
        function_config_id: UUID,
        program_config_actor_config_id: UUID,
        program_config_port_projection_experience_node_id: UUID,
        target_kind: ProgramImplInvokeTargetKind = ProgramImplInvokeTargetKind.instance,
    ) -> ProgramImplInstruction:
        """Create one `invoke` ProgramImplInstruction with its typed payload."""

        payload = {
            "program_impl_id": program_impl_id,
            "sequence": sequence,
            "function_config_id": function_config_id,
            "program_config_actor_config_id": program_config_actor_config_id,
            "program_config_port_projection_experience_node_id": program_config_port_projection_experience_node_id,
            "target_kind": target_kind,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="create_invoke_via_program_impl", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProgramImplInstruction):
            return value
        return ProgramImplInstruction.validate_invocation_value(value)

    @classmethod
    async def create_let_via_program_impl(
        cls, program_impl_id: UUID, sequence: int, name: str, value_expr: JsonObject
    ) -> ProgramImplInstruction:
        """Create one `let` ProgramImplInstruction with its typed payload."""

        payload = {"program_impl_id": program_impl_id, "sequence": sequence, "name": name, "value_expr": value_expr}
        result = await invoke_constructor(orm_class=cls, function_name="create_let_via_program_impl", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProgramImplInstruction):
            return value
        return ProgramImplInstruction.validate_invocation_value(value)


class ProgramImplInstructionCreateBindViaProgramImplInput(BaseModel):
    program_impl_id: UUID = Field(description="Foreign key for ProgramImpl.instructions")
    sequence: int
    program_config_port_id: UUID
    view_key: str
    is_active: bool = Field(default=True)


class ProgramImplInstructionCreateBindViaProgramImplOutput(BaseModel):
    value: ProgramImplInstruction


class ProgramImplInstructionCreateExpectViaProgramImplInput(BaseModel):
    program_impl_id: UUID = Field(description="Foreign key for ProgramImpl.instructions")
    sequence: int
    event_config_id: UUID
    required: bool = Field(default=True)


class ProgramImplInstructionCreateExpectViaProgramImplOutput(BaseModel):
    value: ProgramImplInstruction


class ProgramImplInstructionCreateInputViaProgramImplInput(BaseModel):
    program_impl_id: UUID = Field(description="Foreign key for ProgramImpl.instructions")
    sequence: int
    program_config_input_config_id: UUID


class ProgramImplInstructionCreateInputViaProgramImplOutput(BaseModel):
    value: ProgramImplInstruction


class ProgramImplInstructionCreateIntentViaProgramImplInput(BaseModel):
    program_impl_id: UUID = Field(description="Foreign key for ProgramImpl.instructions")
    sequence: int
    action_config_id: UUID
    event_config_id: UUID


class ProgramImplInstructionCreateIntentViaProgramImplOutput(BaseModel):
    value: ProgramImplInstruction


class ProgramImplInstructionCreateInvokeViaProgramImplInput(BaseModel):
    program_impl_id: UUID = Field(description="Foreign key for ProgramImpl.instructions")
    sequence: int
    function_config_id: UUID
    program_config_actor_config_id: UUID
    program_config_port_projection_experience_node_id: UUID
    target_kind: ProgramImplInvokeTargetKind = Field(default=ProgramImplInvokeTargetKind.instance)


class ProgramImplInstructionCreateInvokeViaProgramImplOutput(BaseModel):
    value: ProgramImplInstruction


class ProgramImplInstructionCreateLetViaProgramImplInput(BaseModel):
    program_impl_id: UUID = Field(description="Foreign key for ProgramImpl.instructions")
    sequence: int
    name: str
    value_expr: JsonObject


class ProgramImplInstructionCreateLetViaProgramImplOutput(BaseModel):
    value: ProgramImplInstruction


FUNCTIONS = {
    "ProgramImplInstruction": {
        "create_bind_via_program_impl": {
            "canonical": {
                "name": "create_bind_via_program_impl",
                "description": "Create one `bind` ProgramImplInstruction with its typed payload.",
                "is_constructor": True,
            },
            "input": ProgramImplInstructionCreateBindViaProgramImplInput,
            "output": ProgramImplInstructionCreateBindViaProgramImplOutput,
        },
        "create_expect_via_program_impl": {
            "canonical": {
                "name": "create_expect_via_program_impl",
                "description": "Create one `expect` ProgramImplInstruction with its typed payload.",
                "is_constructor": True,
            },
            "input": ProgramImplInstructionCreateExpectViaProgramImplInput,
            "output": ProgramImplInstructionCreateExpectViaProgramImplOutput,
        },
        "create_input_via_program_impl": {
            "canonical": {
                "name": "create_input_via_program_impl",
                "description": "Create one `input` ProgramImplInstruction with its typed payload.",
                "is_constructor": True,
            },
            "input": ProgramImplInstructionCreateInputViaProgramImplInput,
            "output": ProgramImplInstructionCreateInputViaProgramImplOutput,
        },
        "create_intent_via_program_impl": {
            "canonical": {
                "name": "create_intent_via_program_impl",
                "description": "Create one `intent` ProgramImplInstruction with its typed payload.",
                "is_constructor": True,
            },
            "input": ProgramImplInstructionCreateIntentViaProgramImplInput,
            "output": ProgramImplInstructionCreateIntentViaProgramImplOutput,
        },
        "create_invoke_via_program_impl": {
            "canonical": {
                "name": "create_invoke_via_program_impl",
                "description": "Create one `invoke` ProgramImplInstruction with its typed payload.",
                "is_constructor": True,
            },
            "input": ProgramImplInstructionCreateInvokeViaProgramImplInput,
            "output": ProgramImplInstructionCreateInvokeViaProgramImplOutput,
        },
        "create_let_via_program_impl": {
            "canonical": {
                "name": "create_let_via_program_impl",
                "description": "Create one `let` ProgramImplInstruction with its typed payload.",
                "is_constructor": True,
            },
            "input": ProgramImplInstructionCreateLetViaProgramImplInput,
            "output": ProgramImplInstructionCreateLetViaProgramImplOutput,
        },
    },
}

__all__ = [
    "ProgramImplInstruction",
    "ProgramImplInstructionCreateBindViaProgramImplInput",
    "ProgramImplInstructionCreateBindViaProgramImplOutput",
    "ProgramImplInstructionCreateExpectViaProgramImplInput",
    "ProgramImplInstructionCreateExpectViaProgramImplOutput",
    "ProgramImplInstructionCreateInputViaProgramImplInput",
    "ProgramImplInstructionCreateInputViaProgramImplOutput",
    "ProgramImplInstructionCreateIntentViaProgramImplInput",
    "ProgramImplInstructionCreateIntentViaProgramImplOutput",
    "ProgramImplInstructionCreateInvokeViaProgramImplInput",
    "ProgramImplInstructionCreateInvokeViaProgramImplOutput",
    "ProgramImplInstructionCreateLetViaProgramImplInput",
    "ProgramImplInstructionCreateLetViaProgramImplOutput",
    "FUNCTIONS",
]
