from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Code Ontology Dto
from aware_code_ontology_dto.code.code_enums import CodeLanguage

if TYPE_CHECKING:
    from aware_code_ontology_dto.code.code import Code
    from aware_code_ontology_dto.code.code_test_framework import CodeTestFramework
    from aware_code_ontology_dto.package.code_package_artifact import CodePackageArtifact
    from aware_code_ontology_dto.package.code_package_code import CodePackageCode
    from aware_code_ontology_dto.package.code_package_delta_producer import CodePackageDeltaProducer
    from aware_code_ontology_dto.package.code_package_test import CodePackageTest
    from aware_code_ontology_dto.package.code_package_test_framework import CodePackageTestFramework


class CodePackage(BaseModel):
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
