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
    from aware_interface_ontology_dto.render.render_component_config import RenderComponentConfig
    from aware_meta_ontology_dto.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit


class RenderComponentPackage(BaseModel):
    # Relationships
    source_code_package: CodePackage | None = Field(default=None)
    render_component_config: RenderComponentConfig
    render_component_config_object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None)

    # Attributes
    aware_render_component_version: int = Field(default=1)
    dart: JsonObject = Field(default_factory=JsonObject)
    description: str | None = Field(default=None)
    exclude_paths: JsonArray = Field(default_factory=JsonArray)
    force_fresh_scan: bool = Field(default=True)
    fqn_prefix: str | None = Field(default=None)
    include_paths: JsonArray = Field(default_factory=JsonArray)
    manifest_relative_path: str | None = Field(default=None)
    name: str
    package_root: str = Field(default=".")
    python: JsonObject = Field(default_factory=JsonObject)
    sources_root: str = Field(default=".")
    title: str | None = Field(default=None)
    version_number: int = Field(default=1)
