from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_code_ontology_dto.code.code_section import CodeSection


class CodeTestUnit(BaseModel):
    """
    Runnable test unit resolved from CodeSection truth.
    Contract:
    - Identity is the target CodeSection under the parent CodeTest.
    - `selector` is execution/discovery payload, not file-path identity.
    """

    # Relationships
    code_section: CodeSection

    # Attributes
    unit_key: str
    selector: str
    kind: str = Field(default="function")
    name: str | None = Field(default=None)
