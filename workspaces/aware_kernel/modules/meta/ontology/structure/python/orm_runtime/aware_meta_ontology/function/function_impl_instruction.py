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
from aware_meta_ontology.function.function_impl_instruction_enums import (
    FunctionImplDeleteTargetKind,
    FunctionImplInstructionType,
    FunctionImplInvokeKind,
    FunctionImplRequireCompareOperator,
    FunctionImplRequireKind,
    FunctionImplValueSourceKind,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_meta_ontology.function.function_impl_instruction_construct import FunctionImplInstructionConstruct
    from aware_meta_ontology.function.function_impl_instruction_delete import FunctionImplInstructionDelete
    from aware_meta_ontology.function.function_impl_instruction_invoke import FunctionImplInstructionInvoke
    from aware_meta_ontology.function.function_impl_instruction_let import FunctionImplInstructionLet
    from aware_meta_ontology.function.function_impl_instruction_require import FunctionImplInstructionRequire
    from aware_meta_ontology.function.function_impl_instruction_set import FunctionImplInstructionSet
    from aware_meta_ontology.function.function_impl_value_source import FunctionImplValueSource


class FunctionImplInstruction(ORMModel):
    """Polymorphic instruction payload owned by `FunctionImpl`."""

    # Relationships
    instruction_let: FunctionImplInstructionLet | None = Field(default=None)
    instruction_invoke: FunctionImplInstructionInvoke | None = Field(default=None)
    instruction_construct: FunctionImplInstructionConstruct | None = Field(default=None)
    instruction_set: FunctionImplInstructionSet | None = Field(default=None)
    instruction_require: FunctionImplInstructionRequire | None = Field(default=None)
    instruction_delete: FunctionImplInstructionDelete | None = Field(default=None)
    value_sources: list[FunctionImplValueSource] = Field(default_factory=list)

    # Attributes
    type: FunctionImplInstructionType
    sequence: int

    # Foreign Keys
    function_impl_id: UUID = Field(description="Foreign key for FunctionImpl.instructions")

    async def attach_let(self, name: str, value_expr: JsonObject) -> FunctionImplInstructionLet:
        """Attach deterministic `let` payload under this instruction."""

        payload = {"name": name, "value_expr": value_expr}
        result = await invoke_instance(orm_model=self, function_name="attach_let", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.function.function_impl_instruction_let import FunctionImplInstructionLet

        if isinstance(value, FunctionImplInstructionLet):
            return value
        return FunctionImplInstructionLet.validate_invocation_value(value)

    async def attach_invoke(
        self,
        target_function_config_id: UUID,
        class_config_relationship_id: UUID | None = None,
        kind: FunctionImplInvokeKind = FunctionImplInvokeKind.call,
    ) -> FunctionImplInstructionInvoke:
        """Attach deterministic `invoke` payload under this instruction."""

        payload = {
            "target_function_config_id": target_function_config_id,
            "class_config_relationship_id": class_config_relationship_id,
            "kind": kind,
        }
        result = await invoke_instance(orm_model=self, function_name="attach_invoke", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.function.function_impl_instruction_invoke import FunctionImplInstructionInvoke

        if isinstance(value, FunctionImplInstructionInvoke):
            return value
        return FunctionImplInstructionInvoke.validate_invocation_value(value)

    async def attach_construct(self, target_class_config_id: UUID) -> FunctionImplInstructionConstruct:
        """Attach deterministic object-construction payload under this instruction."""

        payload = {"target_class_config_id": target_class_config_id}
        result = await invoke_instance(orm_model=self, function_name="attach_construct", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.function.function_impl_instruction_construct import FunctionImplInstructionConstruct

        if isinstance(value, FunctionImplInstructionConstruct):
            return value
        return FunctionImplInstructionConstruct.validate_invocation_value(value)

    async def attach_set(
        self, target_class_config_attribute_config_id: UUID, value_source_id: UUID
    ) -> FunctionImplInstructionSet:
        """Attach deterministic `set` payload under this instruction."""

        payload = {
            "target_class_config_attribute_config_id": target_class_config_attribute_config_id,
            "value_source_id": value_source_id,
        }
        result = await invoke_instance(orm_model=self, function_name="attach_set", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.function.function_impl_instruction_set import FunctionImplInstructionSet

        if isinstance(value, FunctionImplInstructionSet):
            return value
        return FunctionImplInstructionSet.validate_invocation_value(value)

    async def attach_require(
        self,
        kind: FunctionImplRequireKind,
        compare_operator: FunctionImplRequireCompareOperator | None = None,
        expected_count: int | None = None,
        message: str | None = None,
    ) -> FunctionImplInstructionRequire:
        """Attach deterministic `require` payload under this instruction."""

        payload = {
            "kind": kind,
            "compare_operator": compare_operator,
            "expected_count": expected_count,
            "message": message,
        }
        result = await invoke_instance(orm_model=self, function_name="attach_require", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.function.function_impl_instruction_require import FunctionImplInstructionRequire

        if isinstance(value, FunctionImplInstructionRequire):
            return value
        return FunctionImplInstructionRequire.validate_invocation_value(value)

    async def attach_delete(
        self, target_kind: FunctionImplDeleteTargetKind = FunctionImplDeleteTargetKind.self
    ) -> FunctionImplInstructionDelete:
        """Attach deterministic `delete self` payload under this instruction."""

        payload = {"target_kind": target_kind}
        result = await invoke_instance(orm_model=self, function_name="attach_delete", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.function.function_impl_instruction_delete import FunctionImplInstructionDelete

        if isinstance(value, FunctionImplInstructionDelete):
            return value
        return FunctionImplInstructionDelete.validate_invocation_value(value)

    async def create_value_source(
        self,
        key: str,
        kind: FunctionImplValueSourceKind,
        source_function_config_attribute_config_id: UUID | None = None,
        source_instruction_let_id: UUID | None = None,
    ) -> FunctionImplValueSource:
        """Create one deterministic value source local to this instruction."""

        payload = {
            "key": key,
            "kind": kind,
            "source_function_config_attribute_config_id": source_function_config_attribute_config_id,
            "source_instruction_let_id": source_instruction_let_id,
        }
        result = await invoke_instance(orm_model=self, function_name="create_value_source", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.function.function_impl_value_source import FunctionImplValueSource

        if isinstance(value, FunctionImplValueSource):
            return value
        return FunctionImplValueSource.validate_invocation_value(value)

    @classmethod
    async def build_via_function_impl(
        cls, function_impl_id: UUID, type: FunctionImplInstructionType, sequence: int
    ) -> FunctionImplInstruction:
        """
        Create deterministic FunctionImplInstruction under one FunctionImpl parent path.

        Contract:
        - Parent context (`function_impl_id`) is injected by parent-edge lowering.
        - Constructor identity keys are `(type, sequence)` plus propagated parent scope.
        """

        payload = {"function_impl_id": function_impl_id, "type": type, "sequence": sequence}
        result = await invoke_constructor(orm_class=cls, function_name="build_via_function_impl", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, FunctionImplInstruction):
            return value
        return FunctionImplInstruction.validate_invocation_value(value)


class FunctionImplInstructionAttachLetInput(BaseModel):
    name: str
    value_expr: JsonObject


class FunctionImplInstructionAttachLetOutput(BaseModel):
    value: FunctionImplInstructionLet


class FunctionImplInstructionAttachInvokeInput(BaseModel):
    target_function_config_id: UUID
    class_config_relationship_id: UUID | None = Field(default=None)
    kind: FunctionImplInvokeKind = Field(default=FunctionImplInvokeKind.call)


class FunctionImplInstructionAttachInvokeOutput(BaseModel):
    value: FunctionImplInstructionInvoke


class FunctionImplInstructionAttachConstructInput(BaseModel):
    target_class_config_id: UUID


class FunctionImplInstructionAttachConstructOutput(BaseModel):
    value: FunctionImplInstructionConstruct


class FunctionImplInstructionAttachSetInput(BaseModel):
    target_class_config_attribute_config_id: UUID
    value_source_id: UUID


class FunctionImplInstructionAttachSetOutput(BaseModel):
    value: FunctionImplInstructionSet


class FunctionImplInstructionAttachRequireInput(BaseModel):
    kind: FunctionImplRequireKind
    compare_operator: FunctionImplRequireCompareOperator | None = Field(default=None)
    expected_count: int | None = Field(default=None)
    message: str | None = Field(default=None)


class FunctionImplInstructionAttachRequireOutput(BaseModel):
    value: FunctionImplInstructionRequire


class FunctionImplInstructionAttachDeleteInput(BaseModel):
    target_kind: FunctionImplDeleteTargetKind = Field(default=FunctionImplDeleteTargetKind.self)


class FunctionImplInstructionAttachDeleteOutput(BaseModel):
    value: FunctionImplInstructionDelete


class FunctionImplInstructionCreateValueSourceInput(BaseModel):
    key: str
    kind: FunctionImplValueSourceKind
    source_function_config_attribute_config_id: UUID | None = Field(default=None)
    source_instruction_let_id: UUID | None = Field(default=None)


class FunctionImplInstructionCreateValueSourceOutput(BaseModel):
    value: FunctionImplValueSource


class FunctionImplInstructionBuildViaFunctionImplInput(BaseModel):
    function_impl_id: UUID = Field(description="Foreign key for FunctionImpl.instructions")
    type: FunctionImplInstructionType
    sequence: int


class FunctionImplInstructionBuildViaFunctionImplOutput(BaseModel):
    value: FunctionImplInstruction


FUNCTIONS = {
    "FunctionImplInstruction": {
        "attach_let": {
            "canonical": {
                "name": "attach_let",
                "description": "Attach deterministic `let` payload under this instruction.",
                "is_constructor": False,
            },
            "input": FunctionImplInstructionAttachLetInput,
            "output": FunctionImplInstructionAttachLetOutput,
        },
        "attach_invoke": {
            "canonical": {
                "name": "attach_invoke",
                "description": "Attach deterministic `invoke` payload under this instruction.",
                "is_constructor": False,
            },
            "input": FunctionImplInstructionAttachInvokeInput,
            "output": FunctionImplInstructionAttachInvokeOutput,
        },
        "attach_construct": {
            "canonical": {
                "name": "attach_construct",
                "description": "Attach deterministic object-construction payload under this instruction.",
                "is_constructor": False,
            },
            "input": FunctionImplInstructionAttachConstructInput,
            "output": FunctionImplInstructionAttachConstructOutput,
        },
        "attach_set": {
            "canonical": {
                "name": "attach_set",
                "description": "Attach deterministic `set` payload under this instruction.",
                "is_constructor": False,
            },
            "input": FunctionImplInstructionAttachSetInput,
            "output": FunctionImplInstructionAttachSetOutput,
        },
        "attach_require": {
            "canonical": {
                "name": "attach_require",
                "description": "Attach deterministic `require` payload under this instruction.",
                "is_constructor": False,
            },
            "input": FunctionImplInstructionAttachRequireInput,
            "output": FunctionImplInstructionAttachRequireOutput,
        },
        "attach_delete": {
            "canonical": {
                "name": "attach_delete",
                "description": "Attach deterministic `delete self` payload under this instruction.",
                "is_constructor": False,
            },
            "input": FunctionImplInstructionAttachDeleteInput,
            "output": FunctionImplInstructionAttachDeleteOutput,
        },
        "create_value_source": {
            "canonical": {
                "name": "create_value_source",
                "description": "Create one deterministic value source local to this instruction.",
                "is_constructor": False,
            },
            "input": FunctionImplInstructionCreateValueSourceInput,
            "output": FunctionImplInstructionCreateValueSourceOutput,
        },
        "build_via_function_impl": {
            "canonical": {
                "name": "build_via_function_impl",
                "description": "Create deterministic FunctionImplInstruction under one FunctionImpl parent path.\n\nContract:\n- Parent context (`function_impl_id`) is injected by parent-edge lowering.\n- Constructor identity keys are `(type, sequence)` plus propagated parent scope.",
                "is_constructor": True,
            },
            "input": FunctionImplInstructionBuildViaFunctionImplInput,
            "output": FunctionImplInstructionBuildViaFunctionImplOutput,
        },
    },
}

__all__ = [
    "FunctionImplInstruction",
    "FunctionImplInstructionAttachLetInput",
    "FunctionImplInstructionAttachLetOutput",
    "FunctionImplInstructionAttachInvokeInput",
    "FunctionImplInstructionAttachInvokeOutput",
    "FunctionImplInstructionAttachConstructInput",
    "FunctionImplInstructionAttachConstructOutput",
    "FunctionImplInstructionAttachSetInput",
    "FunctionImplInstructionAttachSetOutput",
    "FunctionImplInstructionAttachRequireInput",
    "FunctionImplInstructionAttachRequireOutput",
    "FunctionImplInstructionAttachDeleteInput",
    "FunctionImplInstructionAttachDeleteOutput",
    "FunctionImplInstructionCreateValueSourceInput",
    "FunctionImplInstructionCreateValueSourceOutput",
    "FunctionImplInstructionBuildViaFunctionImplInput",
    "FunctionImplInstructionBuildViaFunctionImplOutput",
    "FUNCTIONS",
]
