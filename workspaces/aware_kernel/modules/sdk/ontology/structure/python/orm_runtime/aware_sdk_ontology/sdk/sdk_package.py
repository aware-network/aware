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
    from aware_code_ontology.package.code_package import CodePackage
    from aware_meta_ontology.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit
    from aware_sdk_ontology.sdk.sdk_config import SdkConfig
    from aware_sdk_ontology.sdk.sdk_package_api_package import SdkPackageApiPackage
    from aware_sdk_ontology.sdk.sdk_package_dependency import SdkPackageDependency
    from aware_sdk_ontology.sdk.sdk_package_implementation_package import SdkPackageImplementationPackage
    from aware_sdk_ontology.sdk.sdk_package_object_config_graph_package import SdkPackageObjectConfigGraphPackage


class SdkPackage(ORMModel):
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

    # Foreign Keys
    source_code_package_id: UUID | None = Field(
        default=None, description="Foreign key for SdkPackage.source_code_package"
    )
    sdk_config_id: UUID = Field(description="Foreign key for SdkPackage.sdk_config")
    sdk_config_object_instance_graph_commit_id: UUID | None = Field(
        default=None, description="Foreign key for SdkPackage.sdk_config_object_instance_graph_commit"
    )

    @classmethod
    async def build(
        cls,
        name: str,
        sdk_config_id: UUID,
        sdk_config_object_instance_graph_commit_id: UUID | None = None,
        source_code_package_id: UUID | None = None,
        fqn_prefix: str | None = None,
        version_number: int = 1,
        title: str | None = None,
        description: str | None = None,
        aware_sdk_version: int = 1,
        manifest_relative_path: str | None = None,
        package_root: str = ".",
        sources_root: str = "sdks",
        include_paths: JsonArray = [],
        exclude_paths: JsonArray = [],
        force_fresh_scan: bool = True,
        compilation_mode: str = "raw_xor",
        dependencies: JsonArray = [],
        targets: JsonObject = {},
    ) -> SdkPackage:
        """
        Create the canonical SDK-owned package root over an existing `SdkConfig`.

        Contract:
        - Identity is keyed by SDK package `name`.
        - `SdkPackage` is the package/public root over an existing canonical `SdkConfig`.
        - `sdk_config_id` must point at the canonical SdkConfig stable id for this package root.
        - `sdk_config_object_instance_graph_commit_id` pins the historical ObjectInstanceGraphCommit
          for the semantic SdkConfig root so package consumers can replay exact SDK truth without
          resolving branch head or reopening authoring TOML.
        - `source_code_package_id` is explicit raw-source provenance for this semantic leaf package.
        - `SdkPackageApiPackage` declares which API packages are available to generated/runtime SDKs.
        - `SdkPackageImplementationPackage` declares concrete Python/Dart package roots owned by
          the SDK package for public install/runtime consumption.
        - `SdkPackageObjectConfigGraphPackage` declares SDK-owned OCG/state packages that travel
          with this SDK package rather than acting as external dependencies.
        - `SdkPackageDependency` declares package-level SDK dependencies; operation composition may only
          target SDK operations from this declared dependency closure.
        """

        payload = {
            "name": name,
            "sdk_config_id": sdk_config_id,
            "sdk_config_object_instance_graph_commit_id": sdk_config_object_instance_graph_commit_id,
            "source_code_package_id": source_code_package_id,
            "fqn_prefix": fqn_prefix,
            "version_number": version_number,
            "title": title,
            "description": description,
            "aware_sdk_version": aware_sdk_version,
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
        if isinstance(value, SdkPackage):
            return value
        return SdkPackage.validate_invocation_value(value)

    async def sync_manifest_truth(
        self,
        sdk_config_object_instance_graph_commit_id: UUID | None = None,
        source_code_package_id: UUID | None = None,
        fqn_prefix: str | None = None,
        version_number: int = 1,
        title: str | None = None,
        description: str | None = None,
        aware_sdk_version: int = 1,
        manifest_relative_path: str | None = None,
        package_root: str = ".",
        sources_root: str = "sdks",
        include_paths: JsonArray = [],
        exclude_paths: JsonArray = [],
        force_fresh_scan: bool = True,
        compilation_mode: str = "raw_xor",
        dependencies: JsonArray = [],
        targets: JsonObject = {},
    ) -> SdkPackage:
        """Sync mutable manifest/build/dependency/target truth onto an existing SdkPackage root."""

        payload = {
            "sdk_config_object_instance_graph_commit_id": sdk_config_object_instance_graph_commit_id,
            "source_code_package_id": source_code_package_id,
            "fqn_prefix": fqn_prefix,
            "version_number": version_number,
            "title": title,
            "description": description,
            "aware_sdk_version": aware_sdk_version,
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
        if isinstance(value, SdkPackage):
            return value
        return SdkPackage.validate_invocation_value(value)

    async def attach_api_package(self, api_package_id: UUID, description: str | None = None) -> SdkPackageApiPackage:
        """
        Attach one API package to this SdkPackage.

        Contract:
        - This is the package/import rail for authored/generated SDK source.
        - Operation-level endpoint bindings remain separate `SdkOperation -> ApiCapabilityEndpoint` truth.
        """

        payload = {"api_package_id": api_package_id, "description": description}
        result = await invoke_instance(orm_model=self, function_name="attach_api_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_sdk_ontology.sdk.sdk_package_api_package import SdkPackageApiPackage

        if isinstance(value, SdkPackageApiPackage):
            return value
        return SdkPackageApiPackage.validate_invocation_value(value)

    async def attach_implementation_package(
        self,
        code_package_id: UUID,
        package_name: str,
        language: CodeLanguage,
        import_root: str,
        manifest_relative_path: str,
        package_root: str = ".",
        entrypoint: str | None = None,
        role: str = "public_package",
        include_paths: JsonArray = [],
        exclude_paths: JsonArray = [],
    ) -> SdkPackageImplementationPackage:
        """
        Attach one concrete language implementation package owned by this SdkPackage.

        Contract:
        - The SDK package owns explicit language implementation packages as semantic package truth.
        - WorkspaceRevision checkout and SDK installers must resolve public package roots from this
          bridge, never from target JSON or workspace layout heuristics.
        - `code_package_id` points at the canonical CodePackage for the implementation package.
        - `package_root` and `manifest_relative_path` are workspace-revision relative contract payload.
        """

        payload = {
            "code_package_id": code_package_id,
            "package_name": package_name,
            "language": language,
            "import_root": import_root,
            "manifest_relative_path": manifest_relative_path,
            "package_root": package_root,
            "entrypoint": entrypoint,
            "role": role,
            "include_paths": include_paths,
            "exclude_paths": exclude_paths,
        }
        result = await invoke_instance(orm_model=self, function_name="attach_implementation_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_sdk_ontology.sdk.sdk_package_implementation_package import SdkPackageImplementationPackage

        if isinstance(value, SdkPackageImplementationPackage):
            return value
        return SdkPackageImplementationPackage.validate_invocation_value(value)

    async def attach_object_config_graph_package(
        self,
        object_config_graph_package_id: UUID,
        manifest_relative_path: str,
        role: str = "local_state",
        package_kind: str = "state",
        object_config_graph_package_object_instance_graph_commit_id: UUID | None = None,
        expected_hash_sha256: str | None = None,
        description: str | None = None,
    ) -> SdkPackageObjectConfigGraphPackage:
        """
        Attach one SDK-owned ObjectConfigGraphPackage to this SdkPackage.

        Contract:
        - This is SDK ownership truth, not SDK dependency truth.
        - The child package is declared by `aware.sdk.toml` and materialized through the
          canonical ObjectConfigGraphPackage rail.
        - WorkspaceRevision/Hub consumers can use the optional OIG commit pin to replay
          exact SDK-owned DB/schema truth without reopening local manifests.
        """

        payload = {
            "object_config_graph_package_id": object_config_graph_package_id,
            "manifest_relative_path": manifest_relative_path,
            "role": role,
            "package_kind": package_kind,
            "object_config_graph_package_object_instance_graph_commit_id": object_config_graph_package_object_instance_graph_commit_id,
            "expected_hash_sha256": expected_hash_sha256,
            "description": description,
        }
        result = await invoke_instance(
            orm_model=self, function_name="attach_object_config_graph_package", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_sdk_ontology.sdk.sdk_package_object_config_graph_package import SdkPackageObjectConfigGraphPackage

        if isinstance(value, SdkPackageObjectConfigGraphPackage):
            return value
        return SdkPackageObjectConfigGraphPackage.validate_invocation_value(value)

    async def attach_sdk_package_dependency(
        self,
        target_sdk_package_id: UUID,
        target_package_name: str,
        target_sdk_package_object_instance_graph_commit_id: UUID | None = None,
        target_version_number: int | None = None,
        expected_hash_sha256: str | None = None,
        description: str | None = None,
    ) -> SdkPackageDependency:
        """
        Attach one SDK package dependency to this SdkPackage.

        Contract:
        - This is package dependency truth, not operation invocation truth.
        - `target_version_number` is selector/compatibility metadata.
        - `target_sdk_package_object_instance_graph_commit_id` is the exact reproducibility authority
          when the dependency is locked or resolved through WorkspaceRevision/Hub evidence.
        - SDK operation composition must only target operations from the declared dependency closure.
        """

        payload = {
            "target_sdk_package_id": target_sdk_package_id,
            "target_package_name": target_package_name,
            "target_sdk_package_object_instance_graph_commit_id": target_sdk_package_object_instance_graph_commit_id,
            "target_version_number": target_version_number,
            "expected_hash_sha256": expected_hash_sha256,
            "description": description,
        }
        result = await invoke_instance(orm_model=self, function_name="attach_sdk_package_dependency", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_sdk_ontology.sdk.sdk_package_dependency import SdkPackageDependency

        if isinstance(value, SdkPackageDependency):
            return value
        return SdkPackageDependency.validate_invocation_value(value)


class SdkPackageBuildInput(BaseModel):
    name: str
    sdk_config_id: UUID
    sdk_config_object_instance_graph_commit_id: UUID | None = Field(default=None)
    source_code_package_id: UUID | None = Field(default=None)
    fqn_prefix: str | None = Field(default=None)
    version_number: int = Field(default=1)
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    aware_sdk_version: int = Field(default=1)
    manifest_relative_path: str | None = Field(default=None)
    package_root: str = Field(default=".")
    sources_root: str = Field(default="sdks")
    include_paths: JsonArray = Field(default_factory=JsonArray)
    exclude_paths: JsonArray = Field(default_factory=JsonArray)
    force_fresh_scan: bool = Field(default=True)
    compilation_mode: str = Field(default="raw_xor")
    dependencies: JsonArray = Field(default_factory=JsonArray)
    targets: JsonObject = Field(default_factory=JsonObject)


class SdkPackageBuildOutput(BaseModel):
    value: SdkPackage


class SdkPackageSyncManifestTruthInput(BaseModel):
    sdk_config_object_instance_graph_commit_id: UUID | None = Field(default=None)
    source_code_package_id: UUID | None = Field(default=None)
    fqn_prefix: str | None = Field(default=None)
    version_number: int = Field(default=1)
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    aware_sdk_version: int = Field(default=1)
    manifest_relative_path: str | None = Field(default=None)
    package_root: str = Field(default=".")
    sources_root: str = Field(default="sdks")
    include_paths: JsonArray = Field(default_factory=JsonArray)
    exclude_paths: JsonArray = Field(default_factory=JsonArray)
    force_fresh_scan: bool = Field(default=True)
    compilation_mode: str = Field(default="raw_xor")
    dependencies: JsonArray = Field(default_factory=JsonArray)
    targets: JsonObject = Field(default_factory=JsonObject)


class SdkPackageSyncManifestTruthOutput(BaseModel):
    value: SdkPackage


class SdkPackageAttachApiPackageInput(BaseModel):
    api_package_id: UUID
    description: str | None = Field(default=None)


class SdkPackageAttachApiPackageOutput(BaseModel):
    value: SdkPackageApiPackage


class SdkPackageAttachImplementationPackageInput(BaseModel):
    code_package_id: UUID
    package_name: str
    language: CodeLanguage
    import_root: str
    manifest_relative_path: str
    package_root: str = Field(default=".")
    entrypoint: str | None = Field(default=None)
    role: str = Field(default="public_package")
    include_paths: JsonArray = Field(default_factory=JsonArray)
    exclude_paths: JsonArray = Field(default_factory=JsonArray)


class SdkPackageAttachImplementationPackageOutput(BaseModel):
    value: SdkPackageImplementationPackage


class SdkPackageAttachObjectConfigGraphPackageInput(BaseModel):
    object_config_graph_package_id: UUID
    manifest_relative_path: str
    role: str = Field(default="local_state")
    package_kind: str = Field(default="state")
    object_config_graph_package_object_instance_graph_commit_id: UUID | None = Field(default=None)
    expected_hash_sha256: str | None = Field(default=None)
    description: str | None = Field(default=None)


class SdkPackageAttachObjectConfigGraphPackageOutput(BaseModel):
    value: SdkPackageObjectConfigGraphPackage


class SdkPackageAttachSdkPackageDependencyInput(BaseModel):
    target_sdk_package_id: UUID
    target_package_name: str
    target_sdk_package_object_instance_graph_commit_id: UUID | None = Field(default=None)
    target_version_number: int | None = Field(default=None)
    expected_hash_sha256: str | None = Field(default=None)
    description: str | None = Field(default=None)


class SdkPackageAttachSdkPackageDependencyOutput(BaseModel):
    value: SdkPackageDependency


FUNCTIONS = {
    "SdkPackage": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Create the canonical SDK-owned package root over an existing `SdkConfig`.\n\nContract:\n- Identity is keyed by SDK package `name`.\n- `SdkPackage` is the package/public root over an existing canonical `SdkConfig`.\n- `sdk_config_id` must point at the canonical SdkConfig stable id for this package root.\n- `sdk_config_object_instance_graph_commit_id` pins the historical ObjectInstanceGraphCommit\n  for the semantic SdkConfig root so package consumers can replay exact SDK truth without\n  resolving branch head or reopening authoring TOML.\n- `source_code_package_id` is explicit raw-source provenance for this semantic leaf package.\n- `SdkPackageApiPackage` declares which API packages are available to generated/runtime SDKs.\n- `SdkPackageImplementationPackage` declares concrete Python/Dart package roots owned by\n  the SDK package for public install/runtime consumption.\n- `SdkPackageObjectConfigGraphPackage` declares SDK-owned OCG/state packages that travel\n  with this SDK package rather than acting as external dependencies.\n- `SdkPackageDependency` declares package-level SDK dependencies; operation composition may only\n  target SDK operations from this declared dependency closure.",
                "is_constructor": True,
            },
            "input": SdkPackageBuildInput,
            "output": SdkPackageBuildOutput,
        },
        "sync_manifest_truth": {
            "canonical": {
                "name": "sync_manifest_truth",
                "description": "Sync mutable manifest/build/dependency/target truth onto an existing SdkPackage root.",
                "is_constructor": False,
            },
            "input": SdkPackageSyncManifestTruthInput,
            "output": SdkPackageSyncManifestTruthOutput,
        },
        "attach_api_package": {
            "canonical": {
                "name": "attach_api_package",
                "description": "Attach one API package to this SdkPackage.\n\nContract:\n- This is the package/import rail for authored/generated SDK source.\n- Operation-level endpoint bindings remain separate `SdkOperation -> ApiCapabilityEndpoint` truth.",
                "is_constructor": False,
            },
            "input": SdkPackageAttachApiPackageInput,
            "output": SdkPackageAttachApiPackageOutput,
        },
        "attach_implementation_package": {
            "canonical": {
                "name": "attach_implementation_package",
                "description": "Attach one concrete language implementation package owned by this SdkPackage.\n\nContract:\n- The SDK package owns explicit language implementation packages as semantic package truth.\n- WorkspaceRevision checkout and SDK installers must resolve public package roots from this\n  bridge, never from target JSON or workspace layout heuristics.\n- `code_package_id` points at the canonical CodePackage for the implementation package.\n- `package_root` and `manifest_relative_path` are workspace-revision relative contract payload.",
                "is_constructor": False,
            },
            "input": SdkPackageAttachImplementationPackageInput,
            "output": SdkPackageAttachImplementationPackageOutput,
        },
        "attach_object_config_graph_package": {
            "canonical": {
                "name": "attach_object_config_graph_package",
                "description": "Attach one SDK-owned ObjectConfigGraphPackage to this SdkPackage.\n\nContract:\n- This is SDK ownership truth, not SDK dependency truth.\n- The child package is declared by `aware.sdk.toml` and materialized through the\n  canonical ObjectConfigGraphPackage rail.\n- WorkspaceRevision/Hub consumers can use the optional OIG commit pin to replay\n  exact SDK-owned DB/schema truth without reopening local manifests.",
                "is_constructor": False,
            },
            "input": SdkPackageAttachObjectConfigGraphPackageInput,
            "output": SdkPackageAttachObjectConfigGraphPackageOutput,
        },
        "attach_sdk_package_dependency": {
            "canonical": {
                "name": "attach_sdk_package_dependency",
                "description": "Attach one SDK package dependency to this SdkPackage.\n\nContract:\n- This is package dependency truth, not operation invocation truth.\n- `target_version_number` is selector/compatibility metadata.\n- `target_sdk_package_object_instance_graph_commit_id` is the exact reproducibility authority\n  when the dependency is locked or resolved through WorkspaceRevision/Hub evidence.\n- SDK operation composition must only target operations from the declared dependency closure.",
                "is_constructor": False,
            },
            "input": SdkPackageAttachSdkPackageDependencyInput,
            "output": SdkPackageAttachSdkPackageDependencyOutput,
        },
    },
}

__all__ = [
    "SdkPackage",
    "SdkPackageBuildInput",
    "SdkPackageBuildOutput",
    "SdkPackageSyncManifestTruthInput",
    "SdkPackageSyncManifestTruthOutput",
    "SdkPackageAttachApiPackageInput",
    "SdkPackageAttachApiPackageOutput",
    "SdkPackageAttachImplementationPackageInput",
    "SdkPackageAttachImplementationPackageOutput",
    "SdkPackageAttachObjectConfigGraphPackageInput",
    "SdkPackageAttachObjectConfigGraphPackageOutput",
    "SdkPackageAttachSdkPackageDependencyInput",
    "SdkPackageAttachSdkPackageDependencyOutput",
    "FUNCTIONS",
]
