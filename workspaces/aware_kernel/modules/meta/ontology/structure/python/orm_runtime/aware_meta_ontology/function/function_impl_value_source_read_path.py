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
from aware_meta_ontology.function.function_impl_instruction_enums import FunctionImplValueSourceReadPathRootKind

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_meta_ontology.class_.class_config_attribute_config import ClassConfigAttributeConfig
    from aware_meta_ontology.function.function_config_attribute_config import FunctionConfigAttributeConfig
    from aware_meta_ontology.function.function_impl_instruction_let import FunctionImplInstructionLet
    from aware_meta_ontology.function.function_impl_value_source_read_path_segment import (
        FunctionImplValueSourceReadPathSegment,
    )


class FunctionImplValueSourceReadPath(ORMModel):
    """
    Deterministic read-only member traversal payload for `FunctionImplValueSource`.
    Contract:
    - Parent `FunctionImplValueSource.kind` must be `read_path`.
    - The root is one of: function input, prior let binding, or invoked target attribute.
    - Segments are compiler-resolved `AttributeConfig` hops and are evaluated as JSON reads.
    - This payload never authorizes mutation outside the invoked target.
    """

    # Relationships
    root_function_config_attribute_config: FunctionConfigAttributeConfig | None = Field(
        default=None, description="Function contract attribute root when `root_kind == function_input`."
    )
    root_instruction_let: FunctionImplInstructionLet | None = Field(
        default=None, description="Prior deterministic let-binding root when `root_kind == let_binding`."
    )
    root_class_config_attribute_config: ClassConfigAttributeConfig | None = Field(
        default=None, description="Invoked target attribute root when `root_kind == target_attribute`."
    )
    segments: list[FunctionImplValueSourceReadPathSegment] = Field(
        default_factory=list, description="Ordered compiler-resolved member segments."
    )

    # Attributes
    root_kind: FunctionImplValueSourceReadPathRootKind

    # Foreign Keys
    function_impl_value_source_id: UUID | None = Field(
        default=None, description="Foreign key for FunctionImplValueSource.source_read_path"
    )
    root_function_config_attribute_config_id: UUID | None = Field(
        default=None,
        description="Foreign key for FunctionImplValueSourceReadPath.root_function_config_attribute_config",
    )
    root_instruction_let_id: UUID | None = Field(
        default=None, description="Foreign key for FunctionImplValueSourceReadPath.root_instruction_let"
    )
    root_class_config_attribute_config_id: UUID | None = Field(
        default=None, description="Foreign key for FunctionImplValueSourceReadPath.root_class_config_attribute_config"
    )

    async def add_segment(self, position: int, attribute_config_id: UUID) -> FunctionImplValueSourceReadPathSegment:
        """Add one deterministic member segment to the read-only traversal."""

        payload = {"position": position, "attribute_config_id": attribute_config_id}
        result = await invoke_instance(orm_model=self, function_name="add_segment", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.function.function_impl_value_source_read_path_segment import (
            FunctionImplValueSourceReadPathSegment,
        )

        if isinstance(value, FunctionImplValueSourceReadPathSegment):
            return value
        return FunctionImplValueSourceReadPathSegment.validate_invocation_value(value)

    @classmethod
    async def build_via_function_impl_value_source(
        cls,
        function_impl_value_source_id: UUID,
        root_kind: FunctionImplValueSourceReadPathRootKind,
        root_function_config_attribute_config_id: UUID | None = None,
        root_instruction_let_id: UUID | None = None,
        root_class_config_attribute_config_id: UUID | None = None,
    ) -> FunctionImplValueSourceReadPath:
        """
        Create deterministic read-path payload under one FunctionImplValueSource.

        Contract:
        - Parent context (`function_impl_value_source_id`) is injected by parent-edge lowering.
        - Exactly one root relationship must match `root_kind`.
        """

        payload = {
            "function_impl_value_source_id": function_impl_value_source_id,
            "root_kind": root_kind,
            "root_function_config_attribute_config_id": root_function_config_attribute_config_id,
            "root_instruction_let_id": root_instruction_let_id,
            "root_class_config_attribute_config_id": root_class_config_attribute_config_id,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_function_impl_value_source", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, FunctionImplValueSourceReadPath):
            return value
        return FunctionImplValueSourceReadPath.validate_invocation_value(value)


class FunctionImplValueSourceReadPathAddSegmentInput(BaseModel):
    position: int
    attribute_config_id: UUID


class FunctionImplValueSourceReadPathAddSegmentOutput(BaseModel):
    value: FunctionImplValueSourceReadPathSegment


class FunctionImplValueSourceReadPathBuildViaFunctionImplValueSourceInput(BaseModel):
    function_impl_value_source_id: UUID = Field(description="Foreign key for FunctionImplValueSource.source_read_path")
    root_kind: FunctionImplValueSourceReadPathRootKind
    root_function_config_attribute_config_id: UUID | None = Field(default=None)
    root_instruction_let_id: UUID | None = Field(default=None)
    root_class_config_attribute_config_id: UUID | None = Field(default=None)


class FunctionImplValueSourceReadPathBuildViaFunctionImplValueSourceOutput(BaseModel):
    value: FunctionImplValueSourceReadPath


FUNCTIONS = {
    "FunctionImplValueSourceReadPath": {
        "add_segment": {
            "canonical": {
                "name": "add_segment",
                "description": "Add one deterministic member segment to the read-only traversal.",
                "is_constructor": False,
            },
            "input": FunctionImplValueSourceReadPathAddSegmentInput,
            "output": FunctionImplValueSourceReadPathAddSegmentOutput,
        },
        "build_via_function_impl_value_source": {
            "canonical": {
                "name": "build_via_function_impl_value_source",
                "description": "Create deterministic read-path payload under one FunctionImplValueSource.\n\nContract:\n- Parent context (`function_impl_value_source_id`) is injected by parent-edge lowering.\n- Exactly one root relationship must match `root_kind`.",
                "is_constructor": True,
            },
            "input": FunctionImplValueSourceReadPathBuildViaFunctionImplValueSourceInput,
            "output": FunctionImplValueSourceReadPathBuildViaFunctionImplValueSourceOutput,
        },
    },
}

__all__ = [
    "FunctionImplValueSourceReadPath",
    "FunctionImplValueSourceReadPathAddSegmentInput",
    "FunctionImplValueSourceReadPathAddSegmentOutput",
    "FunctionImplValueSourceReadPathBuildViaFunctionImplValueSourceInput",
    "FunctionImplValueSourceReadPathBuildViaFunctionImplValueSourceOutput",
    "FUNCTIONS",
]
