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
    from aware_interface_ontology.interface.interface_config import InterfaceConfig
    from aware_interface_ontology.interface.interface_package_experience_package import (
        InterfacePackageExperiencePackage,
    )
    from aware_interface_ontology.interface.interface_package_pane_package import InterfacePackagePanePackage
    from aware_interface_ontology.interface.interface_package_render_component_package import (
        InterfacePackageRenderComponentPackage,
    )
    from aware_meta_ontology.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit


class InterfacePackage(ORMModel):
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

    # Foreign Keys
    source_code_package_id: UUID | None = Field(
        default=None, description="Foreign key for InterfacePackage.source_code_package"
    )
    interface_config_id: UUID = Field(description="Foreign key for InterfacePackage.interface_config")
    interface_config_object_instance_graph_commit_id: UUID | None = Field(
        default=None, description="Foreign key for InterfacePackage.interface_config_object_instance_graph_commit"
    )

    @classmethod
    async def build(
        cls,
        name: str,
        interface_config_id: UUID,
        interface_config_object_instance_graph_commit_id: UUID | None = None,
        source_code_package_id: UUID | None = None,
        fqn_prefix: str | None = None,
        version_number: int = 1,
        title: str | None = None,
        description: str | None = None,
        aware_interface_version: int = 1,
        manifest_relative_path: str | None = None,
        package_root: str = ".",
        sources_root: str = ".",
        config_bundle_path: str | None = None,
        include_paths: JsonArray = [],
        exclude_paths: JsonArray = [],
        force_fresh_scan: bool = True,
        compilation_mode: str = "raw_xor",
        dependencies: JsonArray = [],
        dart: JsonObject = {},
    ) -> InterfacePackage:
        """
        Create the canonical Interface-owned package root over an existing `InterfaceConfig`.

        Contract:
        - Identity is keyed by Interface package `name`.
        - `InterfacePackage` is the package/public root over an existing canonical `InterfaceConfig`.
        - `interface_config_id` must point at the canonical InterfaceConfig stable id for this package root.
        - `interface_config_object_instance_graph_commit_id` pins the historical ObjectInstanceGraphCommit
          for the semantic InterfaceConfig root so package consumers can replay exact interface truth
          without resolving branch head or reopening authoring TOML.
        - `source_code_package_id` is the explicit raw-source provenance link for this semantic leaf
        package.
        - Manifest/build/dependency/dart attributes mirror `aware.interface.toml` so committed package
          truth can drive Workspace and UI runtime routing without reopening authoring TOML.
        - Workspace will later mount `InterfacePackage`, not raw `InterfaceConfig`.
        """

        payload = {
            "name": name,
            "interface_config_id": interface_config_id,
            "interface_config_object_instance_graph_commit_id": interface_config_object_instance_graph_commit_id,
            "source_code_package_id": source_code_package_id,
            "fqn_prefix": fqn_prefix,
            "version_number": version_number,
            "title": title,
            "description": description,
            "aware_interface_version": aware_interface_version,
            "manifest_relative_path": manifest_relative_path,
            "package_root": package_root,
            "sources_root": sources_root,
            "config_bundle_path": config_bundle_path,
            "include_paths": include_paths,
            "exclude_paths": exclude_paths,
            "force_fresh_scan": force_fresh_scan,
            "compilation_mode": compilation_mode,
            "dependencies": dependencies,
            "dart": dart,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, InterfacePackage):
            return value
        return InterfacePackage.validate_invocation_value(value)

    async def sync_manifest_truth(
        self,
        interface_config_object_instance_graph_commit_id: UUID | None = None,
        source_code_package_id: UUID | None = None,
        fqn_prefix: str | None = None,
        version_number: int = 1,
        title: str | None = None,
        description: str | None = None,
        aware_interface_version: int = 1,
        manifest_relative_path: str | None = None,
        package_root: str = ".",
        sources_root: str = ".",
        config_bundle_path: str | None = None,
        include_paths: JsonArray = [],
        exclude_paths: JsonArray = [],
        force_fresh_scan: bool = True,
        compilation_mode: str = "raw_xor",
        dependencies: JsonArray = [],
        dart: JsonObject = {},
    ) -> InterfacePackage:
        """
        Sync mutable manifest/build/dependency/dart truth onto an existing InterfacePackage root.

        This keeps `build` create-only for empty package lanes while allowing committed package
        truth to follow the latest parsed `aware.interface.toml` snapshot and pinned semantic
        InterfaceConfig commit.
        """

        payload = {
            "interface_config_object_instance_graph_commit_id": interface_config_object_instance_graph_commit_id,
            "source_code_package_id": source_code_package_id,
            "fqn_prefix": fqn_prefix,
            "version_number": version_number,
            "title": title,
            "description": description,
            "aware_interface_version": aware_interface_version,
            "manifest_relative_path": manifest_relative_path,
            "package_root": package_root,
            "sources_root": sources_root,
            "config_bundle_path": config_bundle_path,
            "include_paths": include_paths,
            "exclude_paths": exclude_paths,
            "force_fresh_scan": force_fresh_scan,
            "compilation_mode": compilation_mode,
            "dependencies": dependencies,
            "dart": dart,
        }
        result = await invoke_instance(orm_model=self, function_name="sync_manifest_truth", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, InterfacePackage):
            return value
        return InterfacePackage.validate_invocation_value(value)

    async def attach_experience_package(
        self, experience_package_id: UUID, description: str | None = None
    ) -> InterfacePackageExperiencePackage:
        """
        Attach one Experience package to this InterfacePackage.

        Contract:
        - This is the package/import rail for authored Interface view ownership.
        - It declares which Experience packages supply canonical observable/view contracts to this
          Interface package.
        - Runtime pane resolution remains a later `observable -> experience view -> pane` seam.
        """

        payload = {"experience_package_id": experience_package_id, "description": description}
        result = await invoke_instance(orm_model=self, function_name="attach_experience_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_interface_ontology.interface.interface_package_experience_package import (
            InterfacePackageExperiencePackage,
        )

        if isinstance(value, InterfacePackageExperiencePackage):
            return value
        return InterfacePackageExperiencePackage.validate_invocation_value(value)

    async def attach_pane_package(
        self, pane_package_id: UUID, description: str | None = None
    ) -> InterfacePackagePanePackage:
        """
        Attach one pane package to this InterfacePackage.

        Contract:
        - This is the package/import rail for canonical pane implementation ownership.
        - It lets Interface packages compose pane packages explicitly instead of guessing pane runtime
        packages.
        - Runtime registrar loading remains a later seam; this cut only establishes package dependency
        truth.
        """

        payload = {"pane_package_id": pane_package_id, "description": description}
        result = await invoke_instance(orm_model=self, function_name="attach_pane_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_interface_ontology.interface.interface_package_pane_package import InterfacePackagePanePackage

        if isinstance(value, InterfacePackagePanePackage):
            return value
        return InterfacePackagePanePackage.validate_invocation_value(value)

    async def attach_render_component_package(
        self, render_component_package_id: UUID, description: str | None = None
    ) -> InterfacePackageRenderComponentPackage:
        """
        Attach one render component package to this InterfacePackage.

        Contract:
        - This is the package/import rail for reusable rich renderer component contracts.
        - Interface packages declare component availability explicitly so renderers do not guess
          native capability registries from pane implementation details.
        - Pane packages still decide which components their PaneRenderSpec may reference.
        """

        payload = {"render_component_package_id": render_component_package_id, "description": description}
        result = await invoke_instance(orm_model=self, function_name="attach_render_component_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_interface_ontology.interface.interface_package_render_component_package import (
            InterfacePackageRenderComponentPackage,
        )

        if isinstance(value, InterfacePackageRenderComponentPackage):
            return value
        return InterfacePackageRenderComponentPackage.validate_invocation_value(value)


class InterfacePackageBuildInput(BaseModel):
    name: str
    interface_config_id: UUID
    interface_config_object_instance_graph_commit_id: UUID | None = Field(default=None)
    source_code_package_id: UUID | None = Field(default=None)
    fqn_prefix: str | None = Field(default=None)
    version_number: int = Field(default=1)
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    aware_interface_version: int = Field(default=1)
    manifest_relative_path: str | None = Field(default=None)
    package_root: str = Field(default=".")
    sources_root: str = Field(default=".")
    config_bundle_path: str | None = Field(default=None)
    include_paths: JsonArray = Field(default_factory=JsonArray)
    exclude_paths: JsonArray = Field(default_factory=JsonArray)
    force_fresh_scan: bool = Field(default=True)
    compilation_mode: str = Field(default="raw_xor")
    dependencies: JsonArray = Field(default_factory=JsonArray)
    dart: JsonObject = Field(default_factory=JsonObject)


class InterfacePackageBuildOutput(BaseModel):
    value: InterfacePackage


class InterfacePackageSyncManifestTruthInput(BaseModel):
    interface_config_object_instance_graph_commit_id: UUID | None = Field(default=None)
    source_code_package_id: UUID | None = Field(default=None)
    fqn_prefix: str | None = Field(default=None)
    version_number: int = Field(default=1)
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    aware_interface_version: int = Field(default=1)
    manifest_relative_path: str | None = Field(default=None)
    package_root: str = Field(default=".")
    sources_root: str = Field(default=".")
    config_bundle_path: str | None = Field(default=None)
    include_paths: JsonArray = Field(default_factory=JsonArray)
    exclude_paths: JsonArray = Field(default_factory=JsonArray)
    force_fresh_scan: bool = Field(default=True)
    compilation_mode: str = Field(default="raw_xor")
    dependencies: JsonArray = Field(default_factory=JsonArray)
    dart: JsonObject = Field(default_factory=JsonObject)


class InterfacePackageSyncManifestTruthOutput(BaseModel):
    value: InterfacePackage


class InterfacePackageAttachExperiencePackageInput(BaseModel):
    experience_package_id: UUID
    description: str | None = Field(default=None)


class InterfacePackageAttachExperiencePackageOutput(BaseModel):
    value: InterfacePackageExperiencePackage


class InterfacePackageAttachPanePackageInput(BaseModel):
    pane_package_id: UUID
    description: str | None = Field(default=None)


class InterfacePackageAttachPanePackageOutput(BaseModel):
    value: InterfacePackagePanePackage


class InterfacePackageAttachRenderComponentPackageInput(BaseModel):
    render_component_package_id: UUID
    description: str | None = Field(default=None)


class InterfacePackageAttachRenderComponentPackageOutput(BaseModel):
    value: InterfacePackageRenderComponentPackage


FUNCTIONS = {
    "InterfacePackage": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Create the canonical Interface-owned package root over an existing `InterfaceConfig`.\n\nContract:\n- Identity is keyed by Interface package `name`.\n- `InterfacePackage` is the package/public root over an existing canonical `InterfaceConfig`.\n- `interface_config_id` must point at the canonical InterfaceConfig stable id for this package root.\n- `interface_config_object_instance_graph_commit_id` pins the historical ObjectInstanceGraphCommit\n  for the semantic InterfaceConfig root so package consumers can replay exact interface truth\n  without resolving branch head or reopening authoring TOML.\n- `source_code_package_id` is the explicit raw-source provenance link for this semantic leaf package.\n- Manifest/build/dependency/dart attributes mirror `aware.interface.toml` so committed package\n  truth can drive Workspace and UI runtime routing without reopening authoring TOML.\n- Workspace will later mount `InterfacePackage`, not raw `InterfaceConfig`.",
                "is_constructor": True,
            },
            "input": InterfacePackageBuildInput,
            "output": InterfacePackageBuildOutput,
        },
        "sync_manifest_truth": {
            "canonical": {
                "name": "sync_manifest_truth",
                "description": "Sync mutable manifest/build/dependency/dart truth onto an existing InterfacePackage root.\n\nThis keeps `build` create-only for empty package lanes while allowing committed package\ntruth to follow the latest parsed `aware.interface.toml` snapshot and pinned semantic\nInterfaceConfig commit.",
                "is_constructor": False,
            },
            "input": InterfacePackageSyncManifestTruthInput,
            "output": InterfacePackageSyncManifestTruthOutput,
        },
        "attach_experience_package": {
            "canonical": {
                "name": "attach_experience_package",
                "description": "Attach one Experience package to this InterfacePackage.\n\nContract:\n- This is the package/import rail for authored Interface view ownership.\n- It declares which Experience packages supply canonical observable/view contracts to this\n  Interface package.\n- Runtime pane resolution remains a later `observable -> experience view -> pane` seam.",
                "is_constructor": False,
            },
            "input": InterfacePackageAttachExperiencePackageInput,
            "output": InterfacePackageAttachExperiencePackageOutput,
        },
        "attach_pane_package": {
            "canonical": {
                "name": "attach_pane_package",
                "description": "Attach one pane package to this InterfacePackage.\n\nContract:\n- This is the package/import rail for canonical pane implementation ownership.\n- It lets Interface packages compose pane packages explicitly instead of guessing pane runtime packages.\n- Runtime registrar loading remains a later seam; this cut only establishes package dependency truth.",
                "is_constructor": False,
            },
            "input": InterfacePackageAttachPanePackageInput,
            "output": InterfacePackageAttachPanePackageOutput,
        },
        "attach_render_component_package": {
            "canonical": {
                "name": "attach_render_component_package",
                "description": "Attach one render component package to this InterfacePackage.\n\nContract:\n- This is the package/import rail for reusable rich renderer component contracts.\n- Interface packages declare component availability explicitly so renderers do not guess\n  native capability registries from pane implementation details.\n- Pane packages still decide which components their PaneRenderSpec may reference.",
                "is_constructor": False,
            },
            "input": InterfacePackageAttachRenderComponentPackageInput,
            "output": InterfacePackageAttachRenderComponentPackageOutput,
        },
    },
}

__all__ = [
    "InterfacePackage",
    "InterfacePackageBuildInput",
    "InterfacePackageBuildOutput",
    "InterfacePackageSyncManifestTruthInput",
    "InterfacePackageSyncManifestTruthOutput",
    "InterfacePackageAttachExperiencePackageInput",
    "InterfacePackageAttachExperiencePackageOutput",
    "InterfacePackageAttachPanePackageInput",
    "InterfacePackageAttachPanePackageOutput",
    "InterfacePackageAttachRenderComponentPackageInput",
    "InterfacePackageAttachRenderComponentPackageOutput",
    "FUNCTIONS",
]
