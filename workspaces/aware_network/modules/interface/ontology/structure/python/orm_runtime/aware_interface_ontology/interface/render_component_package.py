from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

# Types
from aware_types import (
    JsonArray,
    JsonObject,
)

if TYPE_CHECKING:
    from aware_code_ontology.package.code_package import CodePackage
    from aware_interface_ontology.render.render_component_config import RenderComponentConfig
    from aware_meta_ontology.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit


class RenderComponentPackage(ORMModel):
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

    # Foreign Keys
    source_code_package_id: UUID | None = Field(
        default=None, description="Foreign key for RenderComponentPackage.source_code_package"
    )
    render_component_config_id: UUID | None = Field(
        default=None, description="Foreign key for RenderComponentPackage.render_component_config"
    )
    render_component_config_object_instance_graph_commit_id: UUID | None = Field(
        default=None,
        description="Foreign key for RenderComponentPackage.render_component_config_object_instance_graph_commit",
    )

    @classmethod
    async def build(
        cls,
        name: str,
        render_component_config_id: UUID,
        render_component_config_object_instance_graph_commit_id: UUID | None = None,
        source_code_package_id: UUID | None = None,
        fqn_prefix: str | None = None,
        version_number: int = 1,
        title: str | None = None,
        description: str | None = None,
        aware_render_component_version: int = 1,
        manifest_relative_path: str | None = None,
        package_root: str = ".",
        sources_root: str = ".",
        include_paths: JsonArray = [],
        exclude_paths: JsonArray = [],
        force_fresh_scan: bool = True,
        python: JsonObject = {},
        dart: JsonObject = {},
    ) -> RenderComponentPackage:
        """
        Create the canonical Interface-owned package root over an existing `RenderComponentConfig`.

        Contract:
        - Identity is keyed by render component package `name`.
        - `RenderComponentPackage` is the package/public root over reusable rich renderer
          component contracts.
        - `render_component_config_id` must point at the canonical component contract root.
        - `render_component_config_object_instance_graph_commit_id` pins the historical
          ObjectInstanceGraphCommit for replayable component package truth.
        - `source_code_package_id` is the explicit raw-source provenance link for renderer
          implementation packages.
        - Manifest/build/python/dart attributes mirror `aware.render_component.toml` so committed
          package truth can drive Interface and Pane render component routing without reopening
          authoring TOML.
        - Panes may depend on this package, but components never own pane state or call services.
        """

        payload = {
            "name": name,
            "render_component_config_id": render_component_config_id,
            "render_component_config_object_instance_graph_commit_id": render_component_config_object_instance_graph_commit_id,
            "source_code_package_id": source_code_package_id,
            "fqn_prefix": fqn_prefix,
            "version_number": version_number,
            "title": title,
            "description": description,
            "aware_render_component_version": aware_render_component_version,
            "manifest_relative_path": manifest_relative_path,
            "package_root": package_root,
            "sources_root": sources_root,
            "include_paths": include_paths,
            "exclude_paths": exclude_paths,
            "force_fresh_scan": force_fresh_scan,
            "python": python,
            "dart": dart,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, RenderComponentPackage):
            return value
        return RenderComponentPackage.validate_invocation_value(value)

    async def sync_manifest_truth(
        self,
        render_component_config_object_instance_graph_commit_id: UUID | None = None,
        source_code_package_id: UUID | None = None,
        fqn_prefix: str | None = None,
        version_number: int = 1,
        title: str | None = None,
        description: str | None = None,
        aware_render_component_version: int = 1,
        manifest_relative_path: str | None = None,
        package_root: str = ".",
        sources_root: str = ".",
        include_paths: JsonArray = [],
        exclude_paths: JsonArray = [],
        force_fresh_scan: bool = True,
        python: JsonObject = {},
        dart: JsonObject = {},
    ) -> RenderComponentPackage:
        """
        Sync mutable manifest/build/python/dart truth onto an existing RenderComponentPackage root.

        This keeps `build` create-only while allowing committed package truth to follow the latest
        parsed `aware.render_component.toml` snapshot and pinned semantic RenderComponentConfig commit.
        """

        payload = {
            "render_component_config_object_instance_graph_commit_id": render_component_config_object_instance_graph_commit_id,
            "source_code_package_id": source_code_package_id,
            "fqn_prefix": fqn_prefix,
            "version_number": version_number,
            "title": title,
            "description": description,
            "aware_render_component_version": aware_render_component_version,
            "manifest_relative_path": manifest_relative_path,
            "package_root": package_root,
            "sources_root": sources_root,
            "include_paths": include_paths,
            "exclude_paths": exclude_paths,
            "force_fresh_scan": force_fresh_scan,
            "python": python,
            "dart": dart,
        }
        result = await invoke_instance(orm_model=self, function_name="sync_manifest_truth", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, RenderComponentPackage):
            return value
        return RenderComponentPackage.validate_invocation_value(value)


class RenderComponentPackageBuildInput(BaseModel):
    name: str
    render_component_config_id: UUID
    render_component_config_object_instance_graph_commit_id: UUID | None = Field(default=None)
    source_code_package_id: UUID | None = Field(default=None)
    fqn_prefix: str | None = Field(default=None)
    version_number: int = Field(default=1)
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    aware_render_component_version: int = Field(default=1)
    manifest_relative_path: str | None = Field(default=None)
    package_root: str = Field(default=".")
    sources_root: str = Field(default=".")
    include_paths: JsonArray = Field(default_factory=JsonArray)
    exclude_paths: JsonArray = Field(default_factory=JsonArray)
    force_fresh_scan: bool = Field(default=True)
    python: JsonObject = Field(default_factory=JsonObject)
    dart: JsonObject = Field(default_factory=JsonObject)


class RenderComponentPackageBuildOutput(BaseModel):
    value: RenderComponentPackage


class RenderComponentPackageSyncManifestTruthInput(BaseModel):
    render_component_config_object_instance_graph_commit_id: UUID | None = Field(default=None)
    source_code_package_id: UUID | None = Field(default=None)
    fqn_prefix: str | None = Field(default=None)
    version_number: int = Field(default=1)
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    aware_render_component_version: int = Field(default=1)
    manifest_relative_path: str | None = Field(default=None)
    package_root: str = Field(default=".")
    sources_root: str = Field(default=".")
    include_paths: JsonArray = Field(default_factory=JsonArray)
    exclude_paths: JsonArray = Field(default_factory=JsonArray)
    force_fresh_scan: bool = Field(default=True)
    python: JsonObject = Field(default_factory=JsonObject)
    dart: JsonObject = Field(default_factory=JsonObject)


class RenderComponentPackageSyncManifestTruthOutput(BaseModel):
    value: RenderComponentPackage


FUNCTIONS = {
    "RenderComponentPackage": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Create the canonical Interface-owned package root over an existing `RenderComponentConfig`.\n\nContract:\n- Identity is keyed by render component package `name`.\n- `RenderComponentPackage` is the package/public root over reusable rich renderer\n  component contracts.\n- `render_component_config_id` must point at the canonical component contract root.\n- `render_component_config_object_instance_graph_commit_id` pins the historical\n  ObjectInstanceGraphCommit for replayable component package truth.\n- `source_code_package_id` is the explicit raw-source provenance link for renderer\n  implementation packages.\n- Manifest/build/python/dart attributes mirror `aware.render_component.toml` so committed\n  package truth can drive Interface and Pane render component routing without reopening\n  authoring TOML.\n- Panes may depend on this package, but components never own pane state or call services.",
                "is_constructor": True,
            },
            "input": RenderComponentPackageBuildInput,
            "output": RenderComponentPackageBuildOutput,
        },
        "sync_manifest_truth": {
            "canonical": {
                "name": "sync_manifest_truth",
                "description": "Sync mutable manifest/build/python/dart truth onto an existing RenderComponentPackage root.\n\nThis keeps `build` create-only while allowing committed package truth to follow the latest\nparsed `aware.render_component.toml` snapshot and pinned semantic RenderComponentConfig commit.",
                "is_constructor": False,
            },
            "input": RenderComponentPackageSyncManifestTruthInput,
            "output": RenderComponentPackageSyncManifestTruthOutput,
        },
    },
}

__all__ = [
    "RenderComponentPackage",
    "RenderComponentPackageBuildInput",
    "RenderComponentPackageBuildOutput",
    "RenderComponentPackageSyncManifestTruthInput",
    "RenderComponentPackageSyncManifestTruthOutput",
    "FUNCTIONS",
]
