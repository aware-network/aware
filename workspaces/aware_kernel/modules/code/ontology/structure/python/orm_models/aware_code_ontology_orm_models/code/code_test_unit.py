from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_code_ontology_orm_models.code.code_section import CodeSection


class CodeTestUnit(ORMModel):
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

    # Foreign Keys
    code_test_id: UUID = Field(description="Foreign key for CodeTest.units")
    code_section_id: UUID | None = Field(default=None, description="Foreign key for CodeTestUnit.code_section")
