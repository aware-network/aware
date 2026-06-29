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

# Types
from aware_types import JsonArray

if TYPE_CHECKING:
    from aware_code_ontology_orm_models.package.code_package import CodePackage


class SdkPackageImplementationPackage(ORMModel):
    # Relationships
    code_package: CodePackage | None = Field(default=None)

    # Attributes
    entrypoint: str | None = Field(default=None)
    exclude_paths: JsonArray = Field(default_factory=JsonArray)
    import_root: str
    include_paths: JsonArray = Field(default_factory=JsonArray)
    language: CodeLanguage
    manifest_relative_path: str
    package_name: str
    package_root: str = Field(default=".")
    role: str = Field(default="public_package")

    # Foreign Keys
    sdk_package_id: UUID = Field(description="Foreign key for SdkPackage.implementation_packages")
    code_package_id: UUID = Field(description="Foreign key for SdkPackageImplementationPackage.code_package")
