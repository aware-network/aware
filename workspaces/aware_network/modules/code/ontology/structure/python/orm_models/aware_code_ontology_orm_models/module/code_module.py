from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import Field

# Code Ontology Orm Models
from aware_code_ontology_orm_models.code.code_enums import CodeLanguage

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_code_ontology_orm_models.module.code_module_code_package import CodeModuleCodePackage
    from aware_code_ontology_orm_models.module.code_module_dependence import CodeModuleDependence
    from aware_code_ontology_orm_models.package.code_package import CodePackage


class CodeModule(ORMModel):
    # Relationships
    dependences: list[CodeModuleDependence] = Field(default_factory=list, exclude=True)

    # Attributes
    aware_module_version: int = Field(default=1)
    languages: list[CodeLanguage] = Field(default_factory=list)
    manifest_hash: str | None = Field(default=None)
    manifest_relative_path: str = Field(default="aware.module.toml")
    name: str

    # Edges
    code_module_code_packages: list[CodeModuleCodePackage] = Field(
        default_factory=list, description="Edge association helper for packages"
    )

    @property
    def packages(self) -> list[CodePackage]:
        return [edge.code_package for edge in self.code_module_code_packages if edge.code_package is not None]
