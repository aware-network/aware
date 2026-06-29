from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Meta Ontology
from aware_meta_ontology.function.function_impl_instruction_enums import FunctionImplDeleteTargetKind

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor


class FunctionImplInstructionDelete(ORMModel):
    """
    Deterministic self-owned graph lifecycle deletion payload.
    Contract:
    - `delete self` is the only v0 authored target.
    - Runtime deletes the invoked ClassInstance's self-owned closure only.
    - External parent/detach/cascade semantics are separate routed operations.
    """

    # Attributes
    target_kind: FunctionImplDeleteTargetKind = Field(default=FunctionImplDeleteTargetKind.self)

    # Foreign Keys
    function_impl_instruction_id: UUID | None = Field(
        default=None, description="Foreign key for FunctionImplInstruction.instruction_delete"
    )

    @classmethod
    async def build_via_function_impl_instruction(
        cls,
        function_impl_instruction_id: UUID,
        target_kind: FunctionImplDeleteTargetKind = FunctionImplDeleteTargetKind.self,
    ) -> FunctionImplInstructionDelete:
        """
        Create deterministic `delete self` payload for one FunctionImplInstruction.

        Contract:
        - Parent context (`function_impl_instruction_id`) is injected by parent-edge lowering.
        - v0 only accepts `target_kind = self`.
        """

        payload = {"function_impl_instruction_id": function_impl_instruction_id, "target_kind": target_kind}
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_function_impl_instruction", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, FunctionImplInstructionDelete):
            return value
        return FunctionImplInstructionDelete.validate_invocation_value(value)


class FunctionImplInstructionDeleteBuildViaFunctionImplInstructionInput(BaseModel):
    function_impl_instruction_id: UUID = Field(description="Foreign key for FunctionImplInstruction.instruction_delete")
    target_kind: FunctionImplDeleteTargetKind = Field(default=FunctionImplDeleteTargetKind.self)


class FunctionImplInstructionDeleteBuildViaFunctionImplInstructionOutput(BaseModel):
    value: FunctionImplInstructionDelete


FUNCTIONS = {
    "FunctionImplInstructionDelete": {
        "build_via_function_impl_instruction": {
            "canonical": {
                "name": "build_via_function_impl_instruction",
                "description": "Create deterministic `delete self` payload for one FunctionImplInstruction.\n\nContract:\n- Parent context (`function_impl_instruction_id`) is injected by parent-edge lowering.\n- v0 only accepts `target_kind = self`.",
                "is_constructor": True,
            },
            "input": FunctionImplInstructionDeleteBuildViaFunctionImplInstructionInput,
            "output": FunctionImplInstructionDeleteBuildViaFunctionImplInstructionOutput,
        },
    },
}

__all__ = [
    "FunctionImplInstructionDelete",
    "FunctionImplInstructionDeleteBuildViaFunctionImplInstructionInput",
    "FunctionImplInstructionDeleteBuildViaFunctionImplInstructionOutput",
    "FUNCTIONS",
]
