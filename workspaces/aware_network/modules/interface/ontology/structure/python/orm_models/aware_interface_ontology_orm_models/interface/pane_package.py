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
    from aware_code_ontology_orm_models.package.code_package import CodePackage
    from aware_interface_ontology_orm_models.interface.pane_config import PaneConfig
    from aware_interface_ontology_orm_models.interface.pane_package_experience_package import (
        PanePackageExperiencePackage,
    )
    from aware_interface_ontology_orm_models.interface.pane_package_render_component_package import (
        PanePackageRenderComponentPackage,
    )
    from aware_meta_ontology_orm_models.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit


class PanePackage(ORMModel):
    # Relationships
    source_code_package: CodePackage | None = Field(default=None)
    experience_packages: list[PanePackageExperiencePackage] = Field(default_factory=list)
    render_component_packages: list[PanePackageRenderComponentPackage] = Field(default_factory=list)
    pane_config: PaneConfig | None = Field(default=None)
    pane_config_object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None)

    # Attributes
    aware_pane_version: int = Field(default=1)
    dart: JsonObject = Field(default_factory=JsonObject)
    description: str | None = Field(default=None)
    exclude_paths: JsonArray = Field(default_factory=JsonArray)
    force_fresh_scan: bool = Field(default=True)
    fqn_prefix: str | None = Field(default=None)
    include_paths: JsonArray = Field(default_factory=JsonArray)
    manifest_relative_path: str | None = Field(default=None)
    name: str
    package_root: str = Field(default=".")
    pane_name: str | None = Field(default=None)
    python: JsonObject = Field(default_factory=JsonObject)
    sources_root: str = Field(default=".")
    title: str | None = Field(default=None)
    version_number: int = Field(default=1)

    # Foreign Keys
    source_code_package_id: UUID | None = Field(
        default=None, description="Foreign key for PanePackage.source_code_package"
    )
    pane_config_id: UUID = Field(description="Foreign key for PanePackage.pane_config")
    pane_config_object_instance_graph_commit_id: UUID | None = Field(
        default=None, description="Foreign key for PanePackage.pane_config_object_instance_graph_commit"
    )
