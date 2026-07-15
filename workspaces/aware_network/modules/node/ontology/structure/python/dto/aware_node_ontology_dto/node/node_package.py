from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import JsonArray

if TYPE_CHECKING:
    from aware_code_ontology_dto.package.code_package import CodePackage
    from aware_node_ontology_dto.node.node_config import NodeConfig
    from aware_node_ontology_dto.node.node_package_included_node_package import NodePackageIncludedNodePackage


class NodePackage(BaseModel):
    # Relationships
    included_node_packages: list[NodePackageIncludedNodePackage] = Field(default_factory=list)
    source_code_package: CodePackage | None = Field(default=None)
    node_config: NodeConfig | None = Field(default=None)

    # Attributes
    aware_node_version: int = Field(default=1)
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
    sources_root: str = Field(default="nodes")
    title: str | None = Field(default=None)
    version_number: int = Field(default=1)
