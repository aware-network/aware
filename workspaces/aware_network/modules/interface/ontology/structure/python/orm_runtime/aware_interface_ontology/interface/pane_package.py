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
    from aware_interface_ontology.interface.pane_config import PaneConfig
    from aware_interface_ontology.interface.pane_package_experience_package import PanePackageExperiencePackage
    from aware_interface_ontology.interface.pane_package_render_component_package import (
        PanePackageRenderComponentPackage,
    )
    from aware_meta_ontology.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit


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

    @classmethod
    async def build(
        cls,
        name: str,
        pane_config_id: UUID,
        pane_config_object_instance_graph_commit_id: UUID | None = None,
        source_code_package_id: UUID | None = None,
        fqn_prefix: str | None = None,
        pane_name: str | None = None,
        version_number: int = 1,
        title: str | None = None,
        description: str | None = None,
        aware_pane_version: int = 1,
        manifest_relative_path: str | None = None,
        package_root: str = ".",
        sources_root: str = ".",
        include_paths: JsonArray = [],
        exclude_paths: JsonArray = [],
        force_fresh_scan: bool = True,
        python: JsonObject = {},
        dart: JsonObject = {},
    ) -> PanePackage:
        """
        Create the canonical Pane-owned package root over an existing `PaneConfig`.

        Contract:
        - Identity is keyed by pane package `name`.
        - `PanePackage` is the package/public root over an existing canonical `PaneConfig`.
        - `pane_config_id` must point at the canonical standalone pane semantic id for this package root.
        - `pane_config_object_instance_graph_commit_id` pins the historical ObjectInstanceGraphCommit
          for the semantic PaneConfig root so package consumers can replay exact pane truth without
          resolving branch head or reopening authoring TOML.
        - `source_code_package_id` is the explicit raw-source provenance link for this semantic leaf
        package.
        - Manifest/build/python/dart attributes mirror `aware.pane.toml` so committed package truth
          can drive Interface and Workspace pane routing without reopening authoring TOML.
        - Interface packages and later Workspace mounts should depend on `PanePackage`, not raw
        `PaneConfig`.
        """

        payload = {
            "name": name,
            "pane_config_id": pane_config_id,
            "pane_config_object_instance_graph_commit_id": pane_config_object_instance_graph_commit_id,
            "source_code_package_id": source_code_package_id,
            "fqn_prefix": fqn_prefix,
            "pane_name": pane_name,
            "version_number": version_number,
            "title": title,
            "description": description,
            "aware_pane_version": aware_pane_version,
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
        if isinstance(value, PanePackage):
            return value
        return PanePackage.validate_invocation_value(value)

    async def sync_manifest_truth(
        self,
        pane_config_object_instance_graph_commit_id: UUID | None = None,
        source_code_package_id: UUID | None = None,
        fqn_prefix: str | None = None,
        pane_name: str | None = None,
        version_number: int = 1,
        title: str | None = None,
        description: str | None = None,
        aware_pane_version: int = 1,
        manifest_relative_path: str | None = None,
        package_root: str = ".",
        sources_root: str = ".",
        include_paths: JsonArray = [],
        exclude_paths: JsonArray = [],
        force_fresh_scan: bool = True,
        python: JsonObject = {},
        dart: JsonObject = {},
    ) -> PanePackage:
        """
        Sync mutable manifest/build/python/dart truth onto an existing PanePackage root.

        This keeps `build` create-only for empty package lanes while allowing committed package
        truth to follow the latest parsed `aware.pane.toml` snapshot and pinned semantic PaneConfig
        commit.
        """

        payload = {
            "pane_config_object_instance_graph_commit_id": pane_config_object_instance_graph_commit_id,
            "source_code_package_id": source_code_package_id,
            "fqn_prefix": fqn_prefix,
            "pane_name": pane_name,
            "version_number": version_number,
            "title": title,
            "description": description,
            "aware_pane_version": aware_pane_version,
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
        if isinstance(value, PanePackage):
            return value
        return PanePackage.validate_invocation_value(value)

    async def attach_experience_package(
        self, experience_package_id: UUID, description: str | None = None
    ) -> PanePackageExperiencePackage:
        """
        Attach one Experience package to this PanePackage.

        Contract:
        - This is the pane-local package/import rail for the one Experience view
          a PaneConfig adapts.
        - Pane packages resolve ProjectionExperienceView through this declared
          dependency before any Interface package consumes the pane.
        - Interface packages must not use their own Experience package
          dependencies to rescue unresolved pane view refs.
        """

        payload = {"experience_package_id": experience_package_id, "description": description}
        result = await invoke_instance(orm_model=self, function_name="attach_experience_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_interface_ontology.interface.pane_package_experience_package import PanePackageExperiencePackage

        if isinstance(value, PanePackageExperiencePackage):
            return value
        return PanePackageExperiencePackage.validate_invocation_value(value)

    async def attach_render_component_package(
        self, render_component_package_id: UUID, description: str | None = None
    ) -> PanePackageRenderComponentPackage:
        """
        Attach one render component package to this PanePackage.

        Contract:
        - This is the pane-local package/import rail for rich renderer component contracts.
        - It declares which reusable components authored PaneRenderSpec nodes may reference.
        - Components provide ports and renderer capability requirements; they do not own pane state
          or bypass canonical ActionBinding/API execution.
        """

        payload = {"render_component_package_id": render_component_package_id, "description": description}
        result = await invoke_instance(orm_model=self, function_name="attach_render_component_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_interface_ontology.interface.pane_package_render_component_package import (
            PanePackageRenderComponentPackage,
        )

        if isinstance(value, PanePackageRenderComponentPackage):
            return value
        return PanePackageRenderComponentPackage.validate_invocation_value(value)


class PanePackageBuildInput(BaseModel):
    name: str
    pane_config_id: UUID
    pane_config_object_instance_graph_commit_id: UUID | None = Field(default=None)
    source_code_package_id: UUID | None = Field(default=None)
    fqn_prefix: str | None = Field(default=None)
    pane_name: str | None = Field(default=None)
    version_number: int = Field(default=1)
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    aware_pane_version: int = Field(default=1)
    manifest_relative_path: str | None = Field(default=None)
    package_root: str = Field(default=".")
    sources_root: str = Field(default=".")
    include_paths: JsonArray = Field(default_factory=JsonArray)
    exclude_paths: JsonArray = Field(default_factory=JsonArray)
    force_fresh_scan: bool = Field(default=True)
    python: JsonObject = Field(default_factory=JsonObject)
    dart: JsonObject = Field(default_factory=JsonObject)


class PanePackageBuildOutput(BaseModel):
    value: PanePackage


class PanePackageSyncManifestTruthInput(BaseModel):
    pane_config_object_instance_graph_commit_id: UUID | None = Field(default=None)
    source_code_package_id: UUID | None = Field(default=None)
    fqn_prefix: str | None = Field(default=None)
    pane_name: str | None = Field(default=None)
    version_number: int = Field(default=1)
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    aware_pane_version: int = Field(default=1)
    manifest_relative_path: str | None = Field(default=None)
    package_root: str = Field(default=".")
    sources_root: str = Field(default=".")
    include_paths: JsonArray = Field(default_factory=JsonArray)
    exclude_paths: JsonArray = Field(default_factory=JsonArray)
    force_fresh_scan: bool = Field(default=True)
    python: JsonObject = Field(default_factory=JsonObject)
    dart: JsonObject = Field(default_factory=JsonObject)


class PanePackageSyncManifestTruthOutput(BaseModel):
    value: PanePackage


class PanePackageAttachExperiencePackageInput(BaseModel):
    experience_package_id: UUID
    description: str | None = Field(default=None)


class PanePackageAttachExperiencePackageOutput(BaseModel):
    value: PanePackageExperiencePackage


class PanePackageAttachRenderComponentPackageInput(BaseModel):
    render_component_package_id: UUID
    description: str | None = Field(default=None)


class PanePackageAttachRenderComponentPackageOutput(BaseModel):
    value: PanePackageRenderComponentPackage


FUNCTIONS = {
    "PanePackage": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Create the canonical Pane-owned package root over an existing `PaneConfig`.\n\nContract:\n- Identity is keyed by pane package `name`.\n- `PanePackage` is the package/public root over an existing canonical `PaneConfig`.\n- `pane_config_id` must point at the canonical standalone pane semantic id for this package root.\n- `pane_config_object_instance_graph_commit_id` pins the historical ObjectInstanceGraphCommit\n  for the semantic PaneConfig root so package consumers can replay exact pane truth without\n  resolving branch head or reopening authoring TOML.\n- `source_code_package_id` is the explicit raw-source provenance link for this semantic leaf package.\n- Manifest/build/python/dart attributes mirror `aware.pane.toml` so committed package truth\n  can drive Interface and Workspace pane routing without reopening authoring TOML.\n- Interface packages and later Workspace mounts should depend on `PanePackage`, not raw `PaneConfig`.",
                "is_constructor": True,
            },
            "input": PanePackageBuildInput,
            "output": PanePackageBuildOutput,
        },
        "sync_manifest_truth": {
            "canonical": {
                "name": "sync_manifest_truth",
                "description": "Sync mutable manifest/build/python/dart truth onto an existing PanePackage root.\n\nThis keeps `build` create-only for empty package lanes while allowing committed package\ntruth to follow the latest parsed `aware.pane.toml` snapshot and pinned semantic PaneConfig\ncommit.",
                "is_constructor": False,
            },
            "input": PanePackageSyncManifestTruthInput,
            "output": PanePackageSyncManifestTruthOutput,
        },
        "attach_experience_package": {
            "canonical": {
                "name": "attach_experience_package",
                "description": "Attach one Experience package to this PanePackage.\n\nContract:\n- This is the pane-local package/import rail for the one Experience view\n  a PaneConfig adapts.\n- Pane packages resolve ProjectionExperienceView through this declared\n  dependency before any Interface package consumes the pane.\n- Interface packages must not use their own Experience package\n  dependencies to rescue unresolved pane view refs.",
                "is_constructor": False,
            },
            "input": PanePackageAttachExperiencePackageInput,
            "output": PanePackageAttachExperiencePackageOutput,
        },
        "attach_render_component_package": {
            "canonical": {
                "name": "attach_render_component_package",
                "description": "Attach one render component package to this PanePackage.\n\nContract:\n- This is the pane-local package/import rail for rich renderer component contracts.\n- It declares which reusable components authored PaneRenderSpec nodes may reference.\n- Components provide ports and renderer capability requirements; they do not own pane state\n  or bypass canonical ActionBinding/API execution.",
                "is_constructor": False,
            },
            "input": PanePackageAttachRenderComponentPackageInput,
            "output": PanePackageAttachRenderComponentPackageOutput,
        },
    },
}

__all__ = [
    "PanePackage",
    "PanePackageBuildInput",
    "PanePackageBuildOutput",
    "PanePackageSyncManifestTruthInput",
    "PanePackageSyncManifestTruthOutput",
    "PanePackageAttachExperiencePackageInput",
    "PanePackageAttachExperiencePackageOutput",
    "PanePackageAttachRenderComponentPackageInput",
    "PanePackageAttachRenderComponentPackageOutput",
    "FUNCTIONS",
]
