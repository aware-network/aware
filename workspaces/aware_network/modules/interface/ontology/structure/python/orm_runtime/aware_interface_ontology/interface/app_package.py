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
    from aware_interface_ontology.interface.app_config import AppConfig
    from aware_interface_ontology.interface.app_package_experience_package import AppPackageExperiencePackage
    from aware_interface_ontology.interface.app_package_interface_package import AppPackageInterfacePackage
    from aware_meta_ontology.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit


class AppPackage(ORMModel):
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

    # Foreign Keys
    source_code_package_id: UUID | None = Field(
        default=None, description="Foreign key for AppPackage.source_code_package"
    )
    app_config_id: UUID = Field(description="Foreign key for AppPackage.app_config")
    app_config_object_instance_graph_commit_id: UUID | None = Field(
        default=None, description="Foreign key for AppPackage.app_config_object_instance_graph_commit"
    )

    @classmethod
    async def build(
        cls,
        name: str,
        app_config_id: UUID,
        app_config_object_instance_graph_commit_id: UUID | None = None,
        source_code_package_id: UUID | None = None,
        version_number: int = 1,
        title: str | None = None,
        description: str | None = None,
        aware_app_version: int = 1,
        manifest_relative_path: str | None = None,
        package_root: str = ".",
        dependencies: JsonArray = [],
        dart: JsonObject = {},
        metadata_json: JsonObject = {},
    ) -> AppPackage:
        """
        Create the canonical app package root over an AppConfig.

        Contract:
        - AppPackage is the installable app package boundary.
        - AppConfig owns screen composition intent.
        - Apps depend on ExperiencePackage and InterfacePackage truth; they do not
          target Environment profile/session/process/thread coordinates directly.
        - `app_config_object_instance_graph_commit_id`, when present, pins exact
          AppConfig replay truth for WorkspaceRevision consumers.
        - `source_code_package_id` is raw-source provenance only.
        """

        payload = {
            "name": name,
            "app_config_id": app_config_id,
            "app_config_object_instance_graph_commit_id": app_config_object_instance_graph_commit_id,
            "source_code_package_id": source_code_package_id,
            "version_number": version_number,
            "title": title,
            "description": description,
            "aware_app_version": aware_app_version,
            "manifest_relative_path": manifest_relative_path,
            "package_root": package_root,
            "dependencies": dependencies,
            "dart": dart,
            "metadata_json": metadata_json,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, AppPackage):
            return value
        return AppPackage.validate_invocation_value(value)

    async def sync_manifest_truth(
        self,
        app_config_object_instance_graph_commit_id: UUID | None = None,
        source_code_package_id: UUID | None = None,
        version_number: int = 1,
        title: str | None = None,
        description: str | None = None,
        aware_app_version: int = 1,
        manifest_relative_path: str | None = None,
        package_root: str = ".",
        dependencies: JsonArray = [],
        dart: JsonObject = {},
        metadata_json: JsonObject = {},
    ) -> AppPackage:
        """
        Sync mutable app manifest truth onto an existing AppPackage root.

        Contract:
        - Manifest evidence is replay metadata, not dependency authority.
        - Typed package dependencies remain represented through child portal rows.
        - Environment admission remains resolved by Experience/Interface services.
        """

        payload = {
            "app_config_object_instance_graph_commit_id": app_config_object_instance_graph_commit_id,
            "source_code_package_id": source_code_package_id,
            "version_number": version_number,
            "title": title,
            "description": description,
            "aware_app_version": aware_app_version,
            "manifest_relative_path": manifest_relative_path,
            "package_root": package_root,
            "dependencies": dependencies,
            "dart": dart,
            "metadata_json": metadata_json,
        }
        result = await invoke_instance(orm_model=self, function_name="sync_manifest_truth", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, AppPackage):
            return value
        return AppPackage.validate_invocation_value(value)

    async def attach_experience_package(
        self,
        experience_package_id: UUID,
        experience_package_object_instance_graph_commit_id: UUID | None = None,
        role: str = "experience",
        description: str | None = None,
    ) -> AppPackageExperiencePackage:
        """
        Attach one ExperiencePackage dependency to this app.

        Contract:
        - The app selects Experience entry points and layout bindings through
          AppConfigScreenConfig.
        - Environment package/profile/session targets must remain behind
          Experience resolution, not on AppPackage.
        """

        payload = {
            "experience_package_id": experience_package_id,
            "experience_package_object_instance_graph_commit_id": experience_package_object_instance_graph_commit_id,
            "role": role,
            "description": description,
        }
        result = await invoke_instance(orm_model=self, function_name="attach_experience_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_interface_ontology.interface.app_package_experience_package import AppPackageExperiencePackage

        if isinstance(value, AppPackageExperiencePackage):
            return value
        return AppPackageExperiencePackage.validate_invocation_value(value)

    async def attach_interface_package(
        self,
        interface_package_id: UUID,
        interface_package_object_instance_graph_commit_id: UUID | None = None,
        role: str = "interface",
        description: str | None = None,
    ) -> AppPackageInterfacePackage:
        """
        Attach one InterfacePackage dependency to this app.

        Contract:
        - InterfacePackage supplies reusable shell/pane/render composition truth.
        - It does not authorize app-owned Environment targets or app-specific
          pane defaults.
        """

        payload = {
            "interface_package_id": interface_package_id,
            "interface_package_object_instance_graph_commit_id": interface_package_object_instance_graph_commit_id,
            "role": role,
            "description": description,
        }
        result = await invoke_instance(orm_model=self, function_name="attach_interface_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_interface_ontology.interface.app_package_interface_package import AppPackageInterfacePackage

        if isinstance(value, AppPackageInterfacePackage):
            return value
        return AppPackageInterfacePackage.validate_invocation_value(value)


class AppPackageBuildInput(BaseModel):
    name: str
    app_config_id: UUID
    app_config_object_instance_graph_commit_id: UUID | None = Field(default=None)
    source_code_package_id: UUID | None = Field(default=None)
    version_number: int = Field(default=1)
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    aware_app_version: int = Field(default=1)
    manifest_relative_path: str | None = Field(default=None)
    package_root: str = Field(default=".")
    dependencies: JsonArray = Field(default_factory=JsonArray)
    dart: JsonObject = Field(default_factory=JsonObject)
    metadata_json: JsonObject = Field(default_factory=JsonObject)


class AppPackageBuildOutput(BaseModel):
    value: AppPackage


class AppPackageSyncManifestTruthInput(BaseModel):
    app_config_object_instance_graph_commit_id: UUID | None = Field(default=None)
    source_code_package_id: UUID | None = Field(default=None)
    version_number: int = Field(default=1)
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    aware_app_version: int = Field(default=1)
    manifest_relative_path: str | None = Field(default=None)
    package_root: str = Field(default=".")
    dependencies: JsonArray = Field(default_factory=JsonArray)
    dart: JsonObject = Field(default_factory=JsonObject)
    metadata_json: JsonObject = Field(default_factory=JsonObject)


class AppPackageSyncManifestTruthOutput(BaseModel):
    value: AppPackage


class AppPackageAttachExperiencePackageInput(BaseModel):
    experience_package_id: UUID
    experience_package_object_instance_graph_commit_id: UUID | None = Field(default=None)
    role: str = Field(default="experience")
    description: str | None = Field(default=None)


class AppPackageAttachExperiencePackageOutput(BaseModel):
    value: AppPackageExperiencePackage


class AppPackageAttachInterfacePackageInput(BaseModel):
    interface_package_id: UUID
    interface_package_object_instance_graph_commit_id: UUID | None = Field(default=None)
    role: str = Field(default="interface")
    description: str | None = Field(default=None)


class AppPackageAttachInterfacePackageOutput(BaseModel):
    value: AppPackageInterfacePackage


FUNCTIONS = {
    "AppPackage": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Create the canonical app package root over an AppConfig.\n\nContract:\n- AppPackage is the installable app package boundary.\n- AppConfig owns screen composition intent.\n- Apps depend on ExperiencePackage and InterfacePackage truth; they do not\n  target Environment profile/session/process/thread coordinates directly.\n- `app_config_object_instance_graph_commit_id`, when present, pins exact\n  AppConfig replay truth for WorkspaceRevision consumers.\n- `source_code_package_id` is raw-source provenance only.",
                "is_constructor": True,
            },
            "input": AppPackageBuildInput,
            "output": AppPackageBuildOutput,
        },
        "sync_manifest_truth": {
            "canonical": {
                "name": "sync_manifest_truth",
                "description": "Sync mutable app manifest truth onto an existing AppPackage root.\n\nContract:\n- Manifest evidence is replay metadata, not dependency authority.\n- Typed package dependencies remain represented through child portal rows.\n- Environment admission remains resolved by Experience/Interface services.",
                "is_constructor": False,
            },
            "input": AppPackageSyncManifestTruthInput,
            "output": AppPackageSyncManifestTruthOutput,
        },
        "attach_experience_package": {
            "canonical": {
                "name": "attach_experience_package",
                "description": "Attach one ExperiencePackage dependency to this app.\n\nContract:\n- The app selects Experience entry points and layout bindings through\n  AppConfigScreenConfig.\n- Environment package/profile/session targets must remain behind\n  Experience resolution, not on AppPackage.",
                "is_constructor": False,
            },
            "input": AppPackageAttachExperiencePackageInput,
            "output": AppPackageAttachExperiencePackageOutput,
        },
        "attach_interface_package": {
            "canonical": {
                "name": "attach_interface_package",
                "description": "Attach one InterfacePackage dependency to this app.\n\nContract:\n- InterfacePackage supplies reusable shell/pane/render composition truth.\n- It does not authorize app-owned Environment targets or app-specific\n  pane defaults.",
                "is_constructor": False,
            },
            "input": AppPackageAttachInterfacePackageInput,
            "output": AppPackageAttachInterfacePackageOutput,
        },
    },
}

__all__ = [
    "AppPackage",
    "AppPackageBuildInput",
    "AppPackageBuildOutput",
    "AppPackageSyncManifestTruthInput",
    "AppPackageSyncManifestTruthOutput",
    "AppPackageAttachExperiencePackageInput",
    "AppPackageAttachExperiencePackageOutput",
    "AppPackageAttachInterfacePackageInput",
    "AppPackageAttachInterfacePackageOutput",
    "FUNCTIONS",
]
