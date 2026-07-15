from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import (
    JsonArray,
    JsonObject,
)

if TYPE_CHECKING:
    from aware_api_ontology_orm_models.api.api import Api
    from aware_api_ontology_orm_models.api.api_package_language_package import ApiPackageLanguagePackage
    from aware_code_ontology_orm_models.package.code_package import CodePackage
    from aware_meta_ontology_orm_models.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit


class ApiPackage(ORMModel):
    # Relationships
    source_code_package: CodePackage | None = Field(default=None)
    api: Api | None = Field(default=None)
    api_object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None)
    language_packages: list[ApiPackageLanguagePackage] = Field(default_factory=list)

    # Attributes
    aware_api_version: int = Field(default=1)
    compilation_mode: str = Field(default="raw_xor")
    dependencies: JsonArray = Field(default_factory=JsonArray)
    description: str | None = Field(default=None)
    exclude_paths: JsonArray = Field(default_factory=JsonArray)
    force_fresh_scan: bool = Field(default=True)
    fqn_prefix: str | None = Field(default=None)
    include_paths: JsonArray = Field(default_factory=JsonArray)
    manifest_relative_path: str | None = Field(default=None)
    name: str
    package_root: str = Field(default=".")
    sources_root: str = Field(default="apis")
    targets: JsonObject = Field(default_factory=JsonObject)
    title: str | None = Field(default=None)
    version_number: int = Field(default=1)

    # Foreign Keys
    source_code_package_id: UUID | None = Field(
        default=None, description="Foreign key for ApiPackage.source_code_package"
    )
    api_id: UUID = Field(description="Foreign key for ApiPackage.api")
    api_object_instance_graph_commit_id: UUID | None = Field(
        default=None, description="Foreign key for ApiPackage.api_object_instance_graph_commit"
    )
