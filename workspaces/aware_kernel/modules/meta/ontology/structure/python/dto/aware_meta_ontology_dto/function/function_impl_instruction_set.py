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


class FunctionImplInstructionSet(BaseModel):
    """
    Deterministic mutation intent payload for function execution rail.
    Notes:
    - Grammar lowering for `set` is staged after this ontology contract.
    - Runtime must remain fail-closed until lowering/execution support is complete.
    """

    # Relationships
    target_class_config_attribute_config: ClassConfigAttributeConfig = Field(
        description="Canonical self-owned attribute declaration being mutated."
    )
    value_source: FunctionImplValueSource = Field(
        description="Deterministic assignment source (literal / function input ref / let ref)."
    )
