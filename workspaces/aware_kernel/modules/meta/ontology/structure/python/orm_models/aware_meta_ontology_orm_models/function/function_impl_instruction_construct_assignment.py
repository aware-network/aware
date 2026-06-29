from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.class_.class_config_attribute_config import ClassConfigAttributeConfig
    from aware_meta_ontology_orm_models.function.function_impl_value_source import FunctionImplValueSource


class FunctionImplInstructionConstructAssignment(ORMModel):
    """Deterministic target/value assignment for explicit object-construction payloads."""

    # Relationships
    target_class_config_attribute_config: ClassConfigAttributeConfig
    value_source: FunctionImplValueSource

    # Attributes
    position: int | None = Field(default=None)

    # Foreign Keys
    function_impl_instruction_construct_id: UUID = Field(
        description="Foreign key for FunctionImplInstructionConstruct.assignments"
    )
    target_class_config_attribute_config_id: UUID | None = Field(
        default=None,
        description="Foreign key for FunctionImplInstructionConstructAssignment.target_class_config_attribute_config",
    )
    value_source_id: UUID | None = Field(
        default=None, description="Foreign key for FunctionImplInstructionConstructAssignment.value_source"
    )
