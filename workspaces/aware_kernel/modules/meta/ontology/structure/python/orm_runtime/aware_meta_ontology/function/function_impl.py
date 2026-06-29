from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Meta Ontology
from aware_meta_ontology.function.function_impl_enums import FunctionImplKind
from aware_meta_ontology.function.function_impl_instruction_enums import FunctionImplInstructionType

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_meta_ontology.function.function_impl_instruction import FunctionImplInstruction


class FunctionImpl(ORMModel):
    """
    Canonical execution rail for one function body.
    Contract:
    - Runtime executes `FunctionImplInstruction*` payloads, not raw source text.
    - `kind` distinguishes executable instruction bodies from declarative auto constructors.
    - `FunctionConfig` remains signature/contract truth.
    """

    # Relationships
    instructions: list[FunctionImplInstruction] = Field(default_factory=list)

    # Attributes
    key: str
    kind: FunctionImplKind = Field(default=FunctionImplKind.instruction_body)

    # Foreign Keys
    function_config_id: UUID | None = Field(default=None, description="Foreign key for FunctionConfig.function_impl")

    async def create_instruction(self, type: FunctionImplInstructionType, sequence: int) -> FunctionImplInstruction:
        """Create one deterministic instruction under this FunctionImpl."""

        payload = {"type": type, "sequence": sequence}
        result = await invoke_instance(orm_model=self, function_name="create_instruction", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.function.function_impl_instruction import FunctionImplInstruction

        if isinstance(value, FunctionImplInstruction):
            return value
        return FunctionImplInstruction.validate_invocation_value(value)

    async def remove_instruction(self, type: FunctionImplInstructionType, sequence: int) -> None:
        """Remove one deterministic instruction from this FunctionImpl."""

        payload = {"type": type, "sequence": sequence}
        await invoke_instance(orm_model=self, function_name="remove_instruction", payload=payload)
        return None

    @classmethod
    async def build_via_function_config(
        cls, function_config_id: UUID, key: str = "default", kind: FunctionImplKind = FunctionImplKind.instruction_body
    ) -> FunctionImpl:
        """
        Create deterministic FunctionImpl under one FunctionConfig parent path.

        Contract:
        - `instruction_body` means the implementation owns executable instruction payloads.
        - `auto_constructor` means a bodyless construct declaration materializes through constructor
        identity rails.
        """

        payload = {"function_config_id": function_config_id, "key": key, "kind": kind}
        result = await invoke_constructor(orm_class=cls, function_name="build_via_function_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, FunctionImpl):
            return value
        return FunctionImpl.validate_invocation_value(value)


class FunctionImplCreateInstructionInput(BaseModel):
    type: FunctionImplInstructionType
    sequence: int


class FunctionImplCreateInstructionOutput(BaseModel):
    value: FunctionImplInstruction


class FunctionImplRemoveInstructionInput(BaseModel):
    type: FunctionImplInstructionType
    sequence: int


class FunctionImplRemoveInstructionOutput(BaseModel):
    pass


class FunctionImplBuildViaFunctionConfigInput(BaseModel):
    function_config_id: UUID = Field(description="Foreign key for FunctionConfig.function_impl")
    key: str = Field(default="default")
    kind: FunctionImplKind = Field(default=FunctionImplKind.instruction_body)


class FunctionImplBuildViaFunctionConfigOutput(BaseModel):
    value: FunctionImpl


FUNCTIONS = {
    "FunctionImpl": {
        "create_instruction": {
            "canonical": {
                "name": "create_instruction",
                "description": "Create one deterministic instruction under this FunctionImpl.",
                "is_constructor": False,
            },
            "input": FunctionImplCreateInstructionInput,
            "output": FunctionImplCreateInstructionOutput,
        },
        "remove_instruction": {
            "canonical": {
                "name": "remove_instruction",
                "description": "Remove one deterministic instruction from this FunctionImpl.",
                "is_constructor": False,
            },
            "input": FunctionImplRemoveInstructionInput,
            "output": FunctionImplRemoveInstructionOutput,
        },
        "build_via_function_config": {
            "canonical": {
                "name": "build_via_function_config",
                "description": "Create deterministic FunctionImpl under one FunctionConfig parent path.\n\nContract:\n- `instruction_body` means the implementation owns executable instruction payloads.\n- `auto_constructor` means a bodyless construct declaration materializes through constructor identity rails.",
                "is_constructor": True,
            },
            "input": FunctionImplBuildViaFunctionConfigInput,
            "output": FunctionImplBuildViaFunctionConfigOutput,
        },
    },
}

__all__ = [
    "FunctionImpl",
    "FunctionImplCreateInstructionInput",
    "FunctionImplCreateInstructionOutput",
    "FunctionImplRemoveInstructionInput",
    "FunctionImplRemoveInstructionOutput",
    "FunctionImplBuildViaFunctionConfigInput",
    "FunctionImplBuildViaFunctionConfigOutput",
    "FUNCTIONS",
]
