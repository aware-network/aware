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
    FunctionImplValueSourceKind,
    FunctionImplValueSourceReadPathRootKind,
    FunctionImplValueTransformKind,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

# Types
from aware_types import Json

if TYPE_CHECKING:
    from aware_meta_ontology.function.function_config_attribute_config import FunctionConfigAttributeConfig
    from aware_meta_ontology.function.function_impl_instruction_let import FunctionImplInstructionLet
    from aware_meta_ontology.function.function_impl_value_source_literal_primitive import (
        FunctionImplValueSourceLiteralPrimitive,
    )
    from aware_meta_ontology.function.function_impl_value_source_read_path import FunctionImplValueSourceReadPath
    from aware_meta_ontology.function.function_impl_value_source_transform import FunctionImplValueSourceTransform


class FunctionImplValueSource(ORMModel):
    """
    Deterministic value-source payload for function instruction assignment rails.
    Contract:
    - `set` does not evaluate expressions; it assigns from a typed source.
    - Exactly one source payload must be populated according to `kind`.
    - Transforms are pure value-source payloads; they are not FunctionImpl instructions.
    - Read paths are typed, read-only value sources and never mutation targets.
    """

    # Relationships
    source_function_config_attribute_config: FunctionConfigAttributeConfig | None = Field(
        default=None, description="Function contract attribute source (must belong to FunctionImpl.function_config)."
    )
    source_instruction_let: FunctionImplInstructionLet | None = Field(
        default=None, description="Prior deterministic let-binding source."
    )
    source_literal_primitive: FunctionImplValueSourceLiteralPrimitive | None = Field(
        default=None, description="Typed primitive literal payload (used only when `kind == literal`)."
    )
    source_transform: FunctionImplValueSourceTransform | None = Field(
        default=None, description="Typed pure transform payload (used only when `kind == transform`)."
    )
    source_read_path: FunctionImplValueSourceReadPath | None = Field(
        default=None, description="Typed read-only member traversal payload (used only when `kind == read_path`)."
    )

    # Attributes
    key: str
    kind: FunctionImplValueSourceKind

    # Foreign Keys
    function_impl_instruction_id: UUID = Field(description="Foreign key for FunctionImplInstruction.value_sources")
    source_function_config_attribute_config_id: UUID | None = Field(
        default=None, description="Foreign key for FunctionImplValueSource.source_function_config_attribute_config"
    )
    source_instruction_let_id: UUID | None = Field(
        default=None, description="Foreign key for FunctionImplValueSource.source_instruction_let"
    )

    async def attach_literal_primitive(
        self, primitive_config_id: UUID, value: Json
    ) -> FunctionImplValueSourceLiteralPrimitive:
        """Attach deterministic primitive literal payload when `kind == literal`."""

        payload = {"primitive_config_id": primitive_config_id, "value": value}
        result = await invoke_instance(orm_model=self, function_name="attach_literal_primitive", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.function.function_impl_value_source_literal_primitive import (
            FunctionImplValueSourceLiteralPrimitive,
        )

        if isinstance(value, FunctionImplValueSourceLiteralPrimitive):
            return value
        return FunctionImplValueSourceLiteralPrimitive.validate_invocation_value(value)

    async def attach_transform(
        self, operation: FunctionImplValueTransformKind, output_primitive_config_id: UUID | None = None
    ) -> FunctionImplValueSourceTransform:
        """Attach deterministic pure-transform payload when `kind == transform`."""

        payload = {"operation": operation, "output_primitive_config_id": output_primitive_config_id}
        result = await invoke_instance(orm_model=self, function_name="attach_transform", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.function.function_impl_value_source_transform import FunctionImplValueSourceTransform

        if isinstance(value, FunctionImplValueSourceTransform):
            return value
        return FunctionImplValueSourceTransform.validate_invocation_value(value)

    async def attach_read_path(
        self,
        root_kind: FunctionImplValueSourceReadPathRootKind,
        root_function_config_attribute_config_id: UUID | None = None,
        root_instruction_let_id: UUID | None = None,
        root_class_config_attribute_config_id: UUID | None = None,
    ) -> FunctionImplValueSourceReadPath:
        """
        Attach deterministic read-only traversal payload when `kind == read_path`.

        Contract:
        - The read path only produces a JSON-like value for the owning instruction.
        - Dotted mutation targets remain unsupported; this payload is assignment-source only.
        """

        payload = {
            "root_kind": root_kind,
            "root_function_config_attribute_config_id": root_function_config_attribute_config_id,
            "root_instruction_let_id": root_instruction_let_id,
            "root_class_config_attribute_config_id": root_class_config_attribute_config_id,
        }
        result = await invoke_instance(orm_model=self, function_name="attach_read_path", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.function.function_impl_value_source_read_path import FunctionImplValueSourceReadPath

        if isinstance(value, FunctionImplValueSourceReadPath):
            return value
        return FunctionImplValueSourceReadPath.validate_invocation_value(value)

    async def update_function_input_ref(self, source_function_config_attribute_config_id: UUID) -> None:
        """
        Update an existing function-input value source to point at another input edge.

        Contract:
        - The value source identity and key remain stable.
        - Only `function_input_ref` sources are mutable on this rail.
        - Literal and let-ref replacement require their own explicit ontology functions.
        """

        payload = {"source_function_config_attribute_config_id": source_function_config_attribute_config_id}
        await invoke_instance(orm_model=self, function_name="update_function_input_ref", payload=payload)
        return None

    @classmethod
    async def build_via_function_impl_instruction(
        cls,
        function_impl_instruction_id: UUID,
        key: str,
        kind: FunctionImplValueSourceKind,
        source_function_config_attribute_config_id: UUID | None = None,
        source_instruction_let_id: UUID | None = None,
    ) -> FunctionImplValueSource:
        """
        Create deterministic value-source payload under one FunctionImplInstruction.

        Contract:
        - Parent context (`function_impl_instruction_id`) is injected by parent-edge lowering.
        - Identity is parent-scoped via stable `key`.
        """

        payload = {
            "function_impl_instruction_id": function_impl_instruction_id,
            "key": key,
            "kind": kind,
            "source_function_config_attribute_config_id": source_function_config_attribute_config_id,
            "source_instruction_let_id": source_instruction_let_id,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_function_impl_instruction", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, FunctionImplValueSource):
            return value
        return FunctionImplValueSource.validate_invocation_value(value)


class FunctionImplValueSourceAttachLiteralPrimitiveInput(BaseModel):
    primitive_config_id: UUID
    value: Json


class FunctionImplValueSourceAttachLiteralPrimitiveOutput(BaseModel):
    value: FunctionImplValueSourceLiteralPrimitive


class FunctionImplValueSourceAttachTransformInput(BaseModel):
    operation: FunctionImplValueTransformKind
    output_primitive_config_id: UUID | None = Field(default=None)


class FunctionImplValueSourceAttachTransformOutput(BaseModel):
    value: FunctionImplValueSourceTransform


class FunctionImplValueSourceAttachReadPathInput(BaseModel):
    root_kind: FunctionImplValueSourceReadPathRootKind
    root_function_config_attribute_config_id: UUID | None = Field(default=None)
    root_instruction_let_id: UUID | None = Field(default=None)
    root_class_config_attribute_config_id: UUID | None = Field(default=None)


class FunctionImplValueSourceAttachReadPathOutput(BaseModel):
    value: FunctionImplValueSourceReadPath


class FunctionImplValueSourceUpdateFunctionInputRefInput(BaseModel):
    source_function_config_attribute_config_id: UUID


class FunctionImplValueSourceUpdateFunctionInputRefOutput(BaseModel):
    pass


class FunctionImplValueSourceBuildViaFunctionImplInstructionInput(BaseModel):
    function_impl_instruction_id: UUID = Field(description="Foreign key for FunctionImplInstruction.value_sources")
    key: str
    kind: FunctionImplValueSourceKind
    source_function_config_attribute_config_id: UUID | None = Field(default=None)
    source_instruction_let_id: UUID | None = Field(default=None)


class FunctionImplValueSourceBuildViaFunctionImplInstructionOutput(BaseModel):
    value: FunctionImplValueSource


FUNCTIONS = {
    "FunctionImplValueSource": {
        "attach_literal_primitive": {
            "canonical": {
                "name": "attach_literal_primitive",
                "description": "Attach deterministic primitive literal payload when `kind == literal`.",
                "is_constructor": False,
            },
            "input": FunctionImplValueSourceAttachLiteralPrimitiveInput,
            "output": FunctionImplValueSourceAttachLiteralPrimitiveOutput,
        },
        "attach_transform": {
            "canonical": {
                "name": "attach_transform",
                "description": "Attach deterministic pure-transform payload when `kind == transform`.",
                "is_constructor": False,
            },
            "input": FunctionImplValueSourceAttachTransformInput,
            "output": FunctionImplValueSourceAttachTransformOutput,
        },
        "attach_read_path": {
            "canonical": {
                "name": "attach_read_path",
                "description": "Attach deterministic read-only traversal payload when `kind == read_path`.\n\nContract:\n- The read path only produces a JSON-like value for the owning instruction.\n- Dotted mutation targets remain unsupported; this payload is assignment-source only.",
                "is_constructor": False,
            },
            "input": FunctionImplValueSourceAttachReadPathInput,
            "output": FunctionImplValueSourceAttachReadPathOutput,
        },
        "update_function_input_ref": {
            "canonical": {
                "name": "update_function_input_ref",
                "description": "Update an existing function-input value source to point at another input edge.\n\nContract:\n- The value source identity and key remain stable.\n- Only `function_input_ref` sources are mutable on this rail.\n- Literal and let-ref replacement require their own explicit ontology functions.",
                "is_constructor": False,
            },
            "input": FunctionImplValueSourceUpdateFunctionInputRefInput,
            "output": FunctionImplValueSourceUpdateFunctionInputRefOutput,
        },
        "build_via_function_impl_instruction": {
            "canonical": {
                "name": "build_via_function_impl_instruction",
                "description": "Create deterministic value-source payload under one FunctionImplInstruction.\n\nContract:\n- Parent context (`function_impl_instruction_id`) is injected by parent-edge lowering.\n- Identity is parent-scoped via stable `key`.",
                "is_constructor": True,
            },
            "input": FunctionImplValueSourceBuildViaFunctionImplInstructionInput,
            "output": FunctionImplValueSourceBuildViaFunctionImplInstructionOutput,
        },
    },
}

__all__ = [
    "FunctionImplValueSource",
    "FunctionImplValueSourceAttachLiteralPrimitiveInput",
    "FunctionImplValueSourceAttachLiteralPrimitiveOutput",
    "FunctionImplValueSourceAttachTransformInput",
    "FunctionImplValueSourceAttachTransformOutput",
    "FunctionImplValueSourceAttachReadPathInput",
    "FunctionImplValueSourceAttachReadPathOutput",
    "FunctionImplValueSourceUpdateFunctionInputRefInput",
    "FunctionImplValueSourceUpdateFunctionInputRefOutput",
    "FunctionImplValueSourceBuildViaFunctionImplInstructionInput",
    "FunctionImplValueSourceBuildViaFunctionImplInstructionOutput",
    "FUNCTIONS",
]
