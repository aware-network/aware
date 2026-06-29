from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_code_ontology_dto.code.code_test import CodeTest
    from aware_code_ontology_dto.package.code_package_test_run import CodePackageTestRun


class CodePackageTest(BaseModel):
    """
    Package-level inventory object for one Code test surface.
    Contract:
    - CodePackageTest is a first-class object, not an association edge.
    - `code_test` is the direct target to Code-owned test identity.
    - Runs live only under this package-owned test surface.
    """

    # Relationships
    code_test: CodeTest
    runs: list[CodePackageTestRun] = Field(default_factory=list)

    # Attributes
    relative_path: str
