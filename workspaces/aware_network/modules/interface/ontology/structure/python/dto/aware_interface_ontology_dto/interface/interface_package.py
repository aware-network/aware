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
    from aware_interface_ontology_dto.interface.interface_config import InterfaceConfig
    from aware_interface_ontology_dto.interface.interface_package_experience_package import (
        InterfacePackageExperiencePackage,
    )
    from aware_interface_ontology_dto.interface.interface_package_pane_package import InterfacePackagePanePackage
    from aware_interface_ontology_dto.interface.interface_package_render_component_package import (
        InterfacePackageRenderComponentPackage,
    )
    from aware_meta_ontology_dto.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit


class InterfacePackage(BaseModel):
    # Relationships
    source_code_package: CodePackage | None = Field(default=None)
    experience_packages: list[InterfacePackageExperiencePackage] = Field(default_factory=list)
    pane_packages: list[InterfacePackagePanePackage] = Field(default_factory=list)
    render_component_packages: list[InterfacePackageRenderComponentPackage] = Field(default_factory=list)
    interface_config: InterfaceConfig | None = Field(default=None)
    interface_config_object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None)

    # Attributes
    aware_interface_version: int = Field(default=1)
    compilation_mode: str = Field(default="raw_xor")
    config_bundle_path: str | None = Field(default=None)
    dart: JsonObject = Field(default_factory=JsonObject)
    dependencies: JsonArray = Field(default_factory=JsonArray)
    description: str | None = Field(default=None)
    exclude_paths: JsonArray = Field(default_factory=JsonArray)
    force_fresh_scan: bool = Field(default=True)
    fqn_prefix: str | None = Field(default=None)
    include_paths: JsonArray = Field(default_factory=JsonArray)
    manifest_relative_path: str | None = Field(default=None)
    name: str
    package_root: str = Field(default=".")
    sources_root: str = Field(default=".")
    title: str | None = Field(default=None)
    version_number: int = Field(default=1)
