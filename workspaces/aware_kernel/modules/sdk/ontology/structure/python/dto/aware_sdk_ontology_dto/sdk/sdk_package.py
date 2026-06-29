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
    from aware_meta_ontology_dto.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit
    from aware_sdk_ontology_dto.sdk.sdk_config import SdkConfig
    from aware_sdk_ontology_dto.sdk.sdk_package_api_package import SdkPackageApiPackage
    from aware_sdk_ontology_dto.sdk.sdk_package_dependency import SdkPackageDependency
    from aware_sdk_ontology_dto.sdk.sdk_package_implementation_package import SdkPackageImplementationPackage
    from aware_sdk_ontology_dto.sdk.sdk_package_object_config_graph_package import SdkPackageObjectConfigGraphPackage


class SdkPackage(BaseModel):
    # Relationships
    source_code_package: CodePackage | None = Field(default=None)
    api_packages: list[SdkPackageApiPackage] = Field(default_factory=list)
    implementation_packages: list[SdkPackageImplementationPackage] = Field(default_factory=list)
    object_config_graph_packages: list[SdkPackageObjectConfigGraphPackage] = Field(default_factory=list)
    sdk_package_dependencies: list[SdkPackageDependency] = Field(default_factory=list)
    sdk_config: SdkConfig | None = Field(default=None)
    sdk_config_object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None)

    # Attributes
    aware_sdk_version: int = Field(default=1)
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
    sources_root: str = Field(default="sdks")
    targets: JsonObject = Field(default_factory=JsonObject)
    title: str | None = Field(default=None)
    version_number: int = Field(default=1)
