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
    from aware_meta_ontology_orm_models.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit


class OntologyPackageRuntimeCodePackage(ORMModel):
    """Runtime/implementation CodePackage attached to an OntologyPackage."""

    # Relationships
    code_package: CodePackage | None = Field(default=None)
    object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None)

    # Attributes
    exclude_paths: JsonArray = Field(default_factory=JsonArray)
    import_root: str
    include_paths: JsonArray = Field(default_factory=JsonArray)
    language: CodeLanguage
    manifest_relative_path: str
    package_name: str
    package_root: str = Field(default=".")
    role: str = Field(default="runtime")

    # Foreign Keys
    ontology_package_id: UUID = Field(description="Foreign key for OntologyPackage.runtime_code_packages")
    code_package_id: UUID = Field(description="Foreign key for OntologyPackageRuntimeCodePackage.code_package")
    object_instance_graph_commit_id: UUID | None = Field(
        default=None, description="Foreign key for OntologyPackageRuntimeCodePackage.object_instance_graph_commit"
    )
