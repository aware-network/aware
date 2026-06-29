from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_code_ontology_orm_models.code.code_test import CodeTest
    from aware_code_ontology_orm_models.package.code_package_test_run import CodePackageTestRun


class CodePackageTest(ORMModel):
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

    # Foreign Keys
    code_package_id: UUID = Field(description="Foreign key for CodePackage.tests")
    code_test_id: UUID | None = Field(default=None, description="Foreign key for CodePackageTest.code_test")
