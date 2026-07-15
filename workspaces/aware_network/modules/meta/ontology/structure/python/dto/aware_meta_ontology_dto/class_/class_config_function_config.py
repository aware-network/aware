from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_meta_ontology_dto.function.function_config import FunctionConfig


class ClassConfigFunctionConfig(BaseModel):
    # Relationships
    function_config: FunctionConfig

    # Attributes
    is_public: bool = Field(default=True)
    is_constructor: bool = Field(default=False)
    position: int = Field(default=0)
