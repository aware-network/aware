from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_meta_ontology_dto.class_.class_config import ClassConfig
    from aware_meta_ontology_dto.function.function_impl_instruction_construct_assignment import (
        FunctionImplInstructionConstructAssignment,
    )


class FunctionImplInstructionConstruct(BaseModel):
    """
    Canonical explicit object-construction payload in function execution rail.
    Contract:
    - Represents direct object materialization intent (`construct ClassName(...)`).
    - Distinct from constructor invocation (`FunctionImplInstructionInvoke(kind=construct)`).
    """

    # Relationships
    target_class_config: ClassConfig | None = Field(default=None)
    assignments: list[FunctionImplInstructionConstructAssignment] = Field(default_factory=list)
