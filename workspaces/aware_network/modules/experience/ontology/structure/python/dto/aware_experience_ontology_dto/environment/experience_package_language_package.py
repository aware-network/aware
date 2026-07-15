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

# Types
from aware_types import JsonArray

if TYPE_CHECKING:
    from aware_code_ontology_dto.package.code_package import CodePackage


class ExperiencePackageLanguagePackage(BaseModel):
    # Relationships
    code_package: CodePackage | None = Field(default=None)

    # Attributes
    exclude_paths: JsonArray = Field(default_factory=JsonArray)
    import_root: str
    include_paths: JsonArray = Field(default_factory=JsonArray)
    language: CodeLanguage
    manifest_relative_path: str
    output_key: str = Field(default="experience.language_contract.generated_code_packages")
    package_name: str
    package_root: str = Field(default=".")
    role: str = Field(default="view_model_package")
    sources_root: str | None = Field(default=None)
