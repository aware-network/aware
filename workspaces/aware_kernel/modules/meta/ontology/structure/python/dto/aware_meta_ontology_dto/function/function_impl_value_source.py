from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Meta Ontology Dto
from aware_meta_ontology_dto.function.function_impl_instruction_enums import FunctionImplValueSourceKind

if TYPE_CHECKING:
    from aware_meta_ontology_dto.function.function_config_attribute_config import FunctionConfigAttributeConfig
    from aware_meta_ontology_dto.function.function_impl_instruction_let import FunctionImplInstructionLet
    from aware_meta_ontology_dto.function.function_impl_value_source_literal_primitive import (
        FunctionImplValueSourceLiteralPrimitive,
    )
    from aware_meta_ontology_dto.function.function_impl_value_source_read_path import FunctionImplValueSourceReadPath
    from aware_meta_ontology_dto.function.function_impl_value_source_transform import FunctionImplValueSourceTransform


class FunctionImplValueSource(BaseModel):
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
