from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Meta Ontology Orm Models
from aware_meta_ontology_orm_models.function.function_impl_instruction_enums import FunctionImplValueSourceKind

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.function.function_config_attribute_config import FunctionConfigAttributeConfig
    from aware_meta_ontology_orm_models.function.function_impl_instruction_let import FunctionImplInstructionLet
    from aware_meta_ontology_orm_models.function.function_impl_value_source_literal_primitive import (
        FunctionImplValueSourceLiteralPrimitive,
    )
    from aware_meta_ontology_orm_models.function.function_impl_value_source_read_path import (
        FunctionImplValueSourceReadPath,
    )
    from aware_meta_ontology_orm_models.function.function_impl_value_source_transform import (
        FunctionImplValueSourceTransform,
    )


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
