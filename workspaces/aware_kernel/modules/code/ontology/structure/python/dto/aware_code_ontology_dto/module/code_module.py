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
    from aware_code_ontology_dto.module.code_module_code_package import CodeModuleCodePackage
    from aware_code_ontology_dto.module.code_module_dependence import CodeModuleDependence
    from aware_code_ontology_dto.package.code_package import CodePackage


class CodeModule(BaseModel):
    # Relationships
    dependences: list[CodeModuleDependence] = Field(default_factory=list)

    # Attributes
    aware_module_version: int = Field(default=1)
    languages: list[CodeLanguage] = Field(default_factory=list)
    manifest_hash: str | None = Field(default=None)
    manifest_relative_path: str = Field(default="aware.module.toml")
    name: str
