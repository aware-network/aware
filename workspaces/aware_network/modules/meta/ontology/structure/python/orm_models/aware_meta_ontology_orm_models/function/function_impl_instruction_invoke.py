from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Meta Ontology Orm Models
from aware_meta_ontology_orm_models.function.function_impl_instruction_enums import FunctionImplInvokeKind

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.class_.class_config_relationship import ClassConfigRelationship
    from aware_meta_ontology_orm_models.function.function_config import FunctionConfig
    from aware_meta_ontology_orm_models.function.function_impl_instruction_invoke_attribute_config import (
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
