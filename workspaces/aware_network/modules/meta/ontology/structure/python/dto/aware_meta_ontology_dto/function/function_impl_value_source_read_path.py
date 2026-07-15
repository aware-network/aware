from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Meta Ontology Dto
from aware_meta_ontology_dto.function.function_impl_instruction_enums import FunctionImplValueSourceReadPathRootKind

if TYPE_CHECKING:
    from aware_meta_ontology_dto.class_.class_config_attribute_config import ClassConfigAttributeConfig
    from aware_meta_ontology_dto.function.function_config_attribute_config import FunctionConfigAttributeConfig
    from aware_meta_ontology_dto.function.function_impl_instruction_let import FunctionImplInstructionLet
    from aware_meta_ontology_dto.function.function_impl_value_source_read_path_segment import (
        FunctionImplValueSourceReadPathSegment,
    )


class FunctionImplValueSourceReadPath(BaseModel):
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
