from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import (
    JsonArray,
    JsonObject,
)

if TYPE_CHECKING:
    from aware_code_ontology_dto.package.code_package import CodePackage
    from aware_interface_ontology_dto.interface.app_config import AppConfig
    from aware_interface_ontology_dto.interface.app_package_experience_package import AppPackageExperiencePackage
    from aware_interface_ontology_dto.interface.app_package_interface_package import AppPackageInterfacePackage
    from aware_meta_ontology_dto.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit


class AppPackage(BaseModel):
    # Relationships
    source_code_package: CodePackage | None = Field(default=None)
    app_config: AppConfig | None = Field(default=None)
    app_config_object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None)
    experience_packages: list[AppPackageExperiencePackage] = Field(default_factory=list)
    interface_packages: list[AppPackageInterfacePackage] = Field(default_factory=list)

    # Attributes
    aware_app_version: int = Field(default=1)
    dart: JsonObject = Field(default_factory=JsonObject)
    dependencies: JsonArray = Field(default_factory=JsonArray)
    description: str | None = Field(default=None)
    manifest_relative_path: str | None = Field(default=None)
    metadata_json: JsonObject = Field(default_factory=JsonObject)
    name: str
    package_root: str = Field(default=".")
    title: str | None = Field(default=None)
    version_number: int = Field(default=1)
