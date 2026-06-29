from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Code Ontology Orm Models
from aware_code_ontology_orm_models.code.code_enums import CodeLanguage

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_code_ontology_orm_models.code.code import Code
    from aware_code_ontology_orm_models.code.code_test_framework import CodeTestFramework
    from aware_code_ontology_orm_models.package.code_package_artifact import CodePackageArtifact
    from aware_code_ontology_orm_models.package.code_package_code import CodePackageCode
    from aware_code_ontology_orm_models.package.code_package_delta_producer import CodePackageDeltaProducer
    from aware_code_ontology_orm_models.package.code_package_test import CodePackageTest
    from aware_code_ontology_orm_models.package.code_package_test_framework import CodePackageTestFramework


class CodePackage(ORMModel):
    # Relationships
    delta_producers: list[CodePackageDeltaProducer] = Field(default_factory=list)
    artifacts: list[CodePackageArtifact] = Field(default_factory=list)
    tests: list[CodePackageTest] = Field(default_factory=list)

    # Attributes
    manifest_relative_path: str
    package_name: str
    package_root: str
    sources_root: str | None = Field(default=None)
    fqn_prefix: str | None = Field(default=None)
    language: CodeLanguage
    surface: str | None = Field(default=None)

    # Foreign Keys
    code_package_config_id: UUID = Field(description="Foreign key for CodePackageConfig.packages")

    # Edges
    code_package_codes: list[CodePackageCode] = Field(
        default_factory=list, description="Edge association helper for codes"
    )
    code_package_test_frameworks: list[CodePackageTestFramework] = Field(
        default_factory=list, description="Edge association helper for test_frameworks"
    )

    @property
    def codes(self) -> list[Code]:
        return [edge.code for edge in self.code_package_codes if edge.code is not None]

    @property
    def test_frameworks(self) -> list[CodeTestFramework]:
        return [
            edge.code_test_framework
            for edge in self.code_package_test_frameworks
            if edge.code_test_framework is not None
        ]
