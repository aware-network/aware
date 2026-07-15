from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Meta Ontology Dto
from aware_meta_ontology_dto.function.function_impl_instruction_enums import FunctionImplInvokeKind

if TYPE_CHECKING:
    from aware_meta_ontology_dto.class_.class_config_relationship import ClassConfigRelationship
    from aware_meta_ontology_dto.function.function_config import FunctionConfig
    from aware_meta_ontology_dto.function.function_impl_instruction_invoke_attribute_config import (
        FunctionImplInstructionInvokeAttributeConfig,
    )


class FunctionImplInstructionInvoke(BaseModel):
    """
    Canonical invoke step in function execution rail.
    Contract:
    - Target function is resolved by relationship (`target_function_config`), not strings.
    - Argument bindings remain explicit through `attribute_configs`.
    """

    # Relationships
    target_function_config: FunctionConfig | None = Field(default=None)
    class_config_relationship: ClassConfigRelationship | None = Field(default=None)
    attribute_configs: list[FunctionImplInstructionInvokeAttributeConfig] = Field(default_factory=list)

    # Attributes
    kind: FunctionImplInvokeKind = Field(default=FunctionImplInvokeKind.call)
