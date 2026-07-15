from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_code_ontology_orm_models.code.code_test_framework import CodeTestFramework
    from aware_code_ontology_orm_models.code.code_test_unit import CodeTestUnit


class CodeTest(ORMModel):
    """
    Canonical test surface for one Code object.
    Contract:
    - Code owns test surfaces.
    - Framework identity is relational, not enum-backed.
    - Runnable test units live below this surface and point at concrete
    CodeSection truth.
    """

    # Relationships
    framework: CodeTestFramework | None = Field(default=None)
    units: list[CodeTestUnit] = Field(default_factory=list)

    # Attributes
    discovery_kind: str
    selector_prefix: str | None = Field(default=None)

    # Foreign Keys
    code_id: UUID = Field(description="Foreign key for Code.tests")
    framework_id: UUID = Field(description="Foreign key for CodeTest.framework")
