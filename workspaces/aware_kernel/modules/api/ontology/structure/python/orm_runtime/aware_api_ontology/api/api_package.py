from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage

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
    from aware_api_ontology.api.api import Api
    from aware_api_ontology.api.api_package_language_package import ApiPackageLanguagePackage
    from aware_code_ontology.package.code_package import CodePackage
    from aware_meta_ontology.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit


class ApiPackage(ORMModel):
    # Relationships
    source_code_package: CodePackage | None = Field(default=None)
    api: Api | None = Field(default=None)
    api_object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None)
    language_packages: list[ApiPackageLanguagePackage] = Field(default_factory=list)

    # Attributes
    aware_api_version: int = Field(default=1)
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
    sources_root: str = Field(default="apis")
    targets: JsonObject = Field(default_factory=JsonObject)
    title: str | None = Field(default=None)
    version_number: int = Field(default=1)

    # Foreign Keys
    source_code_package_id: UUID | None = Field(
        default=None, description="Foreign key for ApiPackage.source_code_package"
    )
    api_id: UUID = Field(description="Foreign key for ApiPackage.api")
    api_object_instance_graph_commit_id: UUID | None = Field(
        default=None, description="Foreign key for ApiPackage.api_object_instance_graph_commit"
    )

    @classmethod
    async def build(
        cls,
        name: str,
        api_id: UUID,
        api_object_instance_graph_commit_id: UUID | None = None,
        source_code_package_id: UUID | None = None,
        fqn_prefix: str | None = None,
        version_number: int = 1,
        title: str | None = None,
        description: str | None = None,
        aware_api_version: int = 1,
        manifest_relative_path: str | None = None,
        package_root: str = ".",
        sources_root: str = "apis",
        include_paths: JsonArray = [],
        exclude_paths: JsonArray = [],
        force_fresh_scan: bool = True,
        compilation_mode: str = "raw_xor",
        dependencies: JsonArray = [],
        targets: JsonObject = {},
    ) -> ApiPackage:
        """
        Create the canonical API-owned package root over an existing `Api`.

        Contract:
        - Identity is keyed by API package `name`.
        - `ApiPackage` is the package/public root over an existing canonical `Api`.
        - `api_id` must point at the canonical Api stable id for this package root.
        - `api_object_instance_graph_commit_id` pins the historical ObjectInstanceGraphCommit for the
          semantic Api root so package consumers can replay the exact API truth without resolving branch
        head.
        - `source_code_package_id` is the explicit raw-source provenance link for this semantic leaf
        package.
        - Manifest/build/dependency/target attributes mirror `aware.api.toml` so committed package truth can
          drive Workspace, Service protocol, and runtime resolution without reopening authoring TOML.
        - Workspace will later mount `ApiPackage`, not raw `Api`.
        """

        payload = {
            "name": name,
            "api_id": api_id,
            "api_object_instance_graph_commit_id": api_object_instance_graph_commit_id,
            "source_code_package_id": source_code_package_id,
            "fqn_prefix": fqn_prefix,
            "version_number": version_number,
            "title": title,
            "description": description,
            "aware_api_version": aware_api_version,
            "manifest_relative_path": manifest_relative_path,
            "package_root": package_root,
            "sources_root": sources_root,
            "include_paths": include_paths,
            "exclude_paths": exclude_paths,
            "force_fresh_scan": force_fresh_scan,
            "compilation_mode": compilation_mode,
            "dependencies": dependencies,
            "targets": targets,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ApiPackage):
            return value
        return ApiPackage.validate_invocation_value(value)

    async def sync_manifest_truth(
        self,
        api_object_instance_graph_commit_id: UUID | None = None,
        source_code_package_id: UUID | None = None,
        fqn_prefix: str | None = None,
        version_number: int = 1,
        title: str | None = None,
        description: str | None = None,
        aware_api_version: int = 1,
        manifest_relative_path: str | None = None,
        package_root: str = ".",
        sources_root: str = "apis",
        include_paths: JsonArray = [],
        exclude_paths: JsonArray = [],
        force_fresh_scan: bool = True,
        compilation_mode: str = "raw_xor",
        dependencies: JsonArray = [],
        targets: JsonObject = {},
    ) -> ApiPackage:
        """
        Sync mutable manifest/build/dependency/target truth onto an existing ApiPackage root.

        This keeps `build` create-only for empty package lanes while allowing committed package truth to
        follow the latest parsed `aware.api.toml` snapshot and pinned semantic Api commit.
        """

        payload = {
            "api_object_instance_graph_commit_id": api_object_instance_graph_commit_id,
            "source_code_package_id": source_code_package_id,
            "fqn_prefix": fqn_prefix,
            "version_number": version_number,
            "title": title,
            "description": description,
            "aware_api_version": aware_api_version,
            "manifest_relative_path": manifest_relative_path,
            "package_root": package_root,
            "sources_root": sources_root,
            "include_paths": include_paths,
            "exclude_paths": exclude_paths,
            "force_fresh_scan": force_fresh_scan,
            "compilation_mode": compilation_mode,
            "dependencies": dependencies,
            "targets": targets,
        }
        result = await invoke_instance(orm_model=self, function_name="sync_manifest_truth", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ApiPackage):
            return value
        return ApiPackage.validate_invocation_value(value)

    async def attach_language_package(
        self,
        code_package_id: UUID,
        package_name: str,
        language: CodeLanguage,
        import_root: str,
        manifest_relative_path: str,
        package_root: str = ".",
        role: str = "public_package",
        output_key: str = "python.public_package",
        include_paths: JsonArray = [],
        exclude_paths: JsonArray = [],
    ) -> ApiPackageLanguagePackage:
        """
        Attach one generated language package owned by this ApiPackage.

        Contract:
        - API generated clients and service protocols are explicit package truth.
        - WorkspaceRevision checkout and SDK/service consumers must resolve API
          generated language roots from this bridge, not from target-table or
          filesystem inference.
        - `code_package_id` points at the canonical CodePackage for the generated
          package root.
        - `role` distinguishes API client and service protocol package outputs.
        """

        payload = {
            "code_package_id": code_package_id,
            "package_name": package_name,
            "language": language,
            "import_root": import_root,
            "manifest_relative_path": manifest_relative_path,
            "package_root": package_root,
            "role": role,
            "output_key": output_key,
            "include_paths": include_paths,
            "exclude_paths": exclude_paths,
        }
        result = await invoke_instance(orm_model=self, function_name="attach_language_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_api_ontology.api.api_package_language_package import ApiPackageLanguagePackage

        if isinstance(value, ApiPackageLanguagePackage):
            return value
        return ApiPackageLanguagePackage.validate_invocation_value(value)


class ApiPackageBuildInput(BaseModel):
    name: str
    api_id: UUID
    api_object_instance_graph_commit_id: UUID | None = Field(default=None)
    source_code_package_id: UUID | None = Field(default=None)
    fqn_prefix: str | None = Field(default=None)
    version_number: int = Field(default=1)
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    aware_api_version: int = Field(default=1)
    manifest_relative_path: str | None = Field(default=None)
    package_root: str = Field(default=".")
    sources_root: str = Field(default="apis")
    include_paths: JsonArray = Field(default_factory=JsonArray)
    exclude_paths: JsonArray = Field(default_factory=JsonArray)
    force_fresh_scan: bool = Field(default=True)
    compilation_mode: str = Field(default="raw_xor")
    dependencies: JsonArray = Field(default_factory=JsonArray)
    targets: JsonObject = Field(default_factory=JsonObject)


class ApiPackageBuildOutput(BaseModel):
    value: ApiPackage


class ApiPackageSyncManifestTruthInput(BaseModel):
    api_object_instance_graph_commit_id: UUID | None = Field(default=None)
    source_code_package_id: UUID | None = Field(default=None)
    fqn_prefix: str | None = Field(default=None)
    version_number: int = Field(default=1)
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    aware_api_version: int = Field(default=1)
    manifest_relative_path: str | None = Field(default=None)
    package_root: str = Field(default=".")
    sources_root: str = Field(default="apis")
    include_paths: JsonArray = Field(default_factory=JsonArray)
    exclude_paths: JsonArray = Field(default_factory=JsonArray)
    force_fresh_scan: bool = Field(default=True)
    compilation_mode: str = Field(default="raw_xor")
    dependencies: JsonArray = Field(default_factory=JsonArray)
    targets: JsonObject = Field(default_factory=JsonObject)


class ApiPackageSyncManifestTruthOutput(BaseModel):
    value: ApiPackage


class ApiPackageAttachLanguagePackageInput(BaseModel):
    code_package_id: UUID
    package_name: str
    language: CodeLanguage
    import_root: str
    manifest_relative_path: str
    package_root: str = Field(default=".")
    role: str = Field(default="public_package")
    output_key: str = Field(default="python.public_package")
    include_paths: JsonArray = Field(default_factory=JsonArray)
    exclude_paths: JsonArray = Field(default_factory=JsonArray)


class ApiPackageAttachLanguagePackageOutput(BaseModel):
    value: ApiPackageLanguagePackage


FUNCTIONS = {
    "ApiPackage": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Create the canonical API-owned package root over an existing `Api`.\n\nContract:\n- Identity is keyed by API package `name`.\n- `ApiPackage` is the package/public root over an existing canonical `Api`.\n- `api_id` must point at the canonical Api stable id for this package root.\n- `api_object_instance_graph_commit_id` pins the historical ObjectInstanceGraphCommit for the\n  semantic Api root so package consumers can replay the exact API truth without resolving branch head.\n- `source_code_package_id` is the explicit raw-source provenance link for this semantic leaf\npackage.\n- Manifest/build/dependency/target attributes mirror `aware.api.toml` so committed package truth can\n  drive Workspace, Service protocol, and runtime resolution without reopening authoring TOML.\n- Workspace will later mount `ApiPackage`, not raw `Api`.",
                "is_constructor": True,
            },
            "input": ApiPackageBuildInput,
            "output": ApiPackageBuildOutput,
        },
        "sync_manifest_truth": {
            "canonical": {
                "name": "sync_manifest_truth",
                "description": "Sync mutable manifest/build/dependency/target truth onto an existing ApiPackage root.\n\nThis keeps `build` create-only for empty package lanes while allowing committed package truth to\nfollow the latest parsed `aware.api.toml` snapshot and pinned semantic Api commit.",
                "is_constructor": False,
            },
            "input": ApiPackageSyncManifestTruthInput,
            "output": ApiPackageSyncManifestTruthOutput,
        },
        "attach_language_package": {
            "canonical": {
                "name": "attach_language_package",
                "description": "Attach one generated language package owned by this ApiPackage.\n\nContract:\n- API generated clients and service protocols are explicit package truth.\n- WorkspaceRevision checkout and SDK/service consumers must resolve API\n  generated language roots from this bridge, not from target-table or\n  filesystem inference.\n- `code_package_id` points at the canonical CodePackage for the generated\n  package root.\n- `role` distinguishes API client and service protocol package outputs.",
                "is_constructor": False,
            },
            "input": ApiPackageAttachLanguagePackageInput,
            "output": ApiPackageAttachLanguagePackageOutput,
        },
    },
}

__all__ = [
    "ApiPackage",
    "ApiPackageBuildInput",
    "ApiPackageBuildOutput",
    "ApiPackageSyncManifestTruthInput",
    "ApiPackageSyncManifestTruthOutput",
    "ApiPackageAttachLanguagePackageInput",
    "ApiPackageAttachLanguagePackageOutput",
    "FUNCTIONS",
]
