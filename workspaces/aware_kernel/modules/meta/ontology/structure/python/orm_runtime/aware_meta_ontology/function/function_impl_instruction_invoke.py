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
from aware_meta_ontology.function.function_impl_instruction_enums import FunctionImplInvokeKind

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship
    from aware_meta_ontology.function.function_config import FunctionConfig
    from aware_meta_ontology.function.function_impl_instruction_invoke_attribute_config import (
        FunctionImplInstructionInvokeAttributeConfig,
    )


class FunctionImplInstructionInvoke(ORMModel):
    """
    Canonical invoke step in function execution rail.
    Contract:
    - Target function is resolved by relationship (`target_function_config`), not strings.
    - Argument bindings remain explicit through `attribute_configs`.
    """

    # Relationships
    target_function_config: FunctionConfig | None = Field(default=None, exclude=True)
    class_config_relationship: ClassConfigRelationship | None = Field(default=None)
    attribute_configs: list[FunctionImplInstructionInvokeAttributeConfig] = Field(default_factory=list)

    # Attributes
    kind: FunctionImplInvokeKind = Field(default=FunctionImplInvokeKind.call)

    # Foreign Keys
    function_impl_instruction_id: UUID | None = Field(
        default=None, description="Foreign key for FunctionImplInstruction.instruction_invoke"
    )
    target_function_config_id: UUID = Field(
        description="Foreign key for FunctionImplInstructionInvoke.target_function_config"
    )
    class_config_relationship_id: UUID | None = Field(
        default=None, description="Foreign key for FunctionImplInstructionInvoke.class_config_relationship"
    )

    async def add_attribute_config(
        self, attribute_config_id: UUID, value_expr: JsonObject, position: int | None = None
    ) -> FunctionImplInstructionInvokeAttributeConfig:
        """Attach one deterministic invoke argument binding by AttributeConfig contract."""

        payload = {"attribute_config_id": attribute_config_id, "value_expr": value_expr, "position": position}
        result = await invoke_instance(orm_model=self, function_name="add_attribute_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.function.function_impl_instruction_invoke_attribute_config import (
            FunctionImplInstructionInvokeAttributeConfig,
        )

        if isinstance(value, FunctionImplInstructionInvokeAttributeConfig):
            return value
        return FunctionImplInstructionInvokeAttributeConfig.validate_invocation_value(value)

    @classmethod
    async def build_via_function_impl_instruction(
        cls,
        function_impl_instruction_id: UUID,
        target_function_config_id: UUID,
        class_config_relationship_id: UUID | None = None,
        kind: FunctionImplInvokeKind = FunctionImplInvokeKind.call,
    ) -> FunctionImplInstructionInvoke:
        """
        Create deterministic `invoke` payload for one FunctionImplInstruction.

        Contract:
        - Parent context (`function_impl_instruction_id`) is injected by parent-edge lowering.
        """

        payload = {
            "function_impl_instruction_id": function_impl_instruction_id,
            "target_function_config_id": target_function_config_id,
            "class_config_relationship_id": class_config_relationship_id,
            "kind": kind,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_function_impl_instruction", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, FunctionImplInstructionInvoke):
            return value
        return FunctionImplInstructionInvoke.validate_invocation_value(value)


class FunctionImplInstructionInvokeAddAttributeConfigInput(BaseModel):
    attribute_config_id: UUID
    value_expr: JsonObject
    position: int | None = Field(default=None)


class FunctionImplInstructionInvokeAddAttributeConfigOutput(BaseModel):
    value: FunctionImplInstructionInvokeAttributeConfig


class FunctionImplInstructionInvokeBuildViaFunctionImplInstructionInput(BaseModel):
    function_impl_instruction_id: UUID = Field(description="Foreign key for FunctionImplInstruction.instruction_invoke")
    target_function_config_id: UUID
    class_config_relationship_id: UUID | None = Field(default=None)
    kind: FunctionImplInvokeKind = Field(default=FunctionImplInvokeKind.call)


class FunctionImplInstructionInvokeBuildViaFunctionImplInstructionOutput(BaseModel):
    value: FunctionImplInstructionInvoke


FUNCTIONS = {
    "FunctionImplInstructionInvoke": {
        "add_attribute_config": {
            "canonical": {
                "name": "add_attribute_config",
                "description": "Attach one deterministic invoke argument binding by AttributeConfig contract.",
                "is_constructor": False,
            },
            "input": FunctionImplInstructionInvokeAddAttributeConfigInput,
            "output": FunctionImplInstructionInvokeAddAttributeConfigOutput,
        },
        "build_via_function_impl_instruction": {
            "canonical": {
                "name": "build_via_function_impl_instruction",
                "description": "Create deterministic `invoke` payload for one FunctionImplInstruction.\n\nContract:\n- Parent context (`function_impl_instruction_id`) is injected by parent-edge lowering.",
                "is_constructor": True,
            },
            "input": FunctionImplInstructionInvokeBuildViaFunctionImplInstructionInput,
            "output": FunctionImplInstructionInvokeBuildViaFunctionImplInstructionOutput,
        },
    },
}

__all__ = [
    "FunctionImplInstructionInvoke",
    "FunctionImplInstructionInvokeAddAttributeConfigInput",
    "FunctionImplInstructionInvokeAddAttributeConfigOutput",
    "FunctionImplInstructionInvokeBuildViaFunctionImplInstructionInput",
    "FunctionImplInstructionInvokeBuildViaFunctionImplInstructionOutput",
    "FUNCTIONS",
]
