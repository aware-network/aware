from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_meta_ontology_dto.class_.class_config_attribute_config import ClassConfigAttributeConfig
    from aware_meta_ontology_dto.function.function_impl_value_source import FunctionImplValueSource


class FunctionImplInstructionConstructAssignment(BaseModel):
    """Deterministic target/value assignment for explicit object-construction payloads."""

    # Relationships
    target_class_config_attribute_config: ClassConfigAttributeConfig
    value_source: FunctionImplValueSource

    # Attributes
    position: int | None = Field(default=None)
