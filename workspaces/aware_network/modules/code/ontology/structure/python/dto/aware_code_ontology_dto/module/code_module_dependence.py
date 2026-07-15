from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_code_ontology_dto.module.code_module import CodeModule


class CodeModuleDependence(BaseModel):
    # Relationships
    dependence: CodeModule | None = Field(default=None)

    # Attributes
    name: str
