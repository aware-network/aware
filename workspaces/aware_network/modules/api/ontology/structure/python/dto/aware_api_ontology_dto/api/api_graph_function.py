from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_meta_ontology_dto.class_.class_config_function_config import ClassConfigFunctionConfig


class ApiGraphFunction(BaseModel):
    # Relationships
    class_config_function_config: ClassConfigFunctionConfig | None = Field(default=None)

    # Attributes
    description: str | None = Field(default=None)
