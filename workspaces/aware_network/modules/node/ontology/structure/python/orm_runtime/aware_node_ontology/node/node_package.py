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
from aware_types import JsonArray

if TYPE_CHECKING:
    from aware_code_ontology.package.code_package import CodePackage
    from aware_node_ontology.node.node_config import NodeConfig
    from aware_node_ontology.node.node_package_included_node_package import NodePackageIncludedNodePackage


class NodePackage(ORMModel):
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

    # Foreign Keys
    source_code_package_id: UUID | None = Field(
        default=None, description="Foreign key for NodePackage.source_code_package"
    )
    node_config_id: UUID = Field(description="Foreign key for NodePackage.node_config")

    @classmethod
    async def build(
        cls,
        name: str,
        node_config_id: UUID,
        source_code_package_id: UUID | None = None,
        fqn_prefix: str | None = None,
        version_number: int = 1,
        title: str | None = None,
        description: str | None = None,
        aware_node_version: int = 1,
        manifest_relative_path: str | None = None,
        package_root: str = ".",
        sources_root: str = "nodes",
        include_paths: JsonArray = [],
        exclude_paths: JsonArray = [],
        force_fresh_scan: bool = True,
        compilation_mode: str = "raw_xor",
        dependencies: JsonArray = [],
    ) -> NodePackage:
        """
        Create the canonical Node-owned package root over an existing `NodeConfig`.

        Contract:
        - Identity is keyed by Node package `name`.
        - `NodePackage` is the package/public root over an existing canonical `NodeConfig`.
        - `node_config_id` must point at the canonical NodeConfig stable id for this package root.
        - `source_code_package_id` is the explicit raw-source provenance link for this semantic
          leaf package.
        - Manifest/build/dependency attributes mirror `aware.node.toml` so committed package truth
          can drive Workspace and Node runtime resolution without reopening authoring TOML.
        - Workspace will later mount `NodePackage`, not raw `NodeConfig`.
        """

        payload = {
            "name": name,
            "node_config_id": node_config_id,
            "source_code_package_id": source_code_package_id,
            "fqn_prefix": fqn_prefix,
            "version_number": version_number,
            "title": title,
            "description": description,
            "aware_node_version": aware_node_version,
            "manifest_relative_path": manifest_relative_path,
            "package_root": package_root,
            "sources_root": sources_root,
            "include_paths": include_paths,
            "exclude_paths": exclude_paths,
            "force_fresh_scan": force_fresh_scan,
            "compilation_mode": compilation_mode,
            "dependencies": dependencies,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, NodePackage):
            return value
        return NodePackage.validate_invocation_value(value)

    async def sync_manifest_truth(
        self,
        source_code_package_id: UUID | None = None,
        fqn_prefix: str | None = None,
        version_number: int = 1,
        title: str | None = None,
        description: str | None = None,
        aware_node_version: int = 1,
        manifest_relative_path: str | None = None,
        package_root: str = ".",
        sources_root: str = "nodes",
        include_paths: JsonArray = [],
        exclude_paths: JsonArray = [],
        force_fresh_scan: bool = True,
        compilation_mode: str = "raw_xor",
        dependencies: JsonArray = [],
    ) -> NodePackage:
        """
        Sync mutable manifest/build/dependency truth onto an existing NodePackage root.

        This keeps `build` create-only for empty package lanes while allowing committed package
        truth to follow the latest parsed `aware.node.toml` snapshot.
        """

        payload = {
            "source_code_package_id": source_code_package_id,
            "fqn_prefix": fqn_prefix,
            "version_number": version_number,
            "title": title,
            "description": description,
            "aware_node_version": aware_node_version,
            "manifest_relative_path": manifest_relative_path,
            "package_root": package_root,
            "sources_root": sources_root,
            "include_paths": include_paths,
            "exclude_paths": exclude_paths,
            "force_fresh_scan": force_fresh_scan,
            "compilation_mode": compilation_mode,
            "dependencies": dependencies,
        }
        result = await invoke_instance(orm_model=self, function_name="sync_manifest_truth", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, NodePackage):
            return value
        return NodePackage.validate_invocation_value(value)

    async def attach_included_node_package(
        self, included_package_name: str, include_key: str | None = None, description: str | None = None
    ) -> NodePackageIncludedNodePackage:
        """
        Attach one package-level Node composition include.

        Contract:
        - Parent `NodePackage` scope is injected by propagation.
        - Identity is keyed by the included package's semantic package name.
        - The bridge resolves and stores the canonical included `NodePackage` relationship.
        - Includes select composition participants only; ServicePackage API bridge truth still
          drives route requirements.
        """

        payload = {
            "included_package_name": included_package_name,
            "include_key": include_key,
            "description": description,
        }
        result = await invoke_instance(orm_model=self, function_name="attach_included_node_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_node_ontology.node.node_package_included_node_package import NodePackageIncludedNodePackage

        if isinstance(value, NodePackageIncludedNodePackage):
            return value
        return NodePackageIncludedNodePackage.validate_invocation_value(value)


class NodePackageBuildInput(BaseModel):
    name: str
    node_config_id: UUID
    source_code_package_id: UUID | None = Field(default=None)
    fqn_prefix: str | None = Field(default=None)
    version_number: int = Field(default=1)
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    aware_node_version: int = Field(default=1)
    manifest_relative_path: str | None = Field(default=None)
    package_root: str = Field(default=".")
    sources_root: str = Field(default="nodes")
    include_paths: JsonArray = Field(default_factory=JsonArray)
    exclude_paths: JsonArray = Field(default_factory=JsonArray)
    force_fresh_scan: bool = Field(default=True)
    compilation_mode: str = Field(default="raw_xor")
    dependencies: JsonArray = Field(default_factory=JsonArray)


class NodePackageBuildOutput(BaseModel):
    value: NodePackage


class NodePackageSyncManifestTruthInput(BaseModel):
    source_code_package_id: UUID | None = Field(default=None)
    fqn_prefix: str | None = Field(default=None)
    version_number: int = Field(default=1)
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    aware_node_version: int = Field(default=1)
    manifest_relative_path: str | None = Field(default=None)
    package_root: str = Field(default=".")
    sources_root: str = Field(default="nodes")
    include_paths: JsonArray = Field(default_factory=JsonArray)
    exclude_paths: JsonArray = Field(default_factory=JsonArray)
    force_fresh_scan: bool = Field(default=True)
    compilation_mode: str = Field(default="raw_xor")
    dependencies: JsonArray = Field(default_factory=JsonArray)


class NodePackageSyncManifestTruthOutput(BaseModel):
    value: NodePackage


class NodePackageAttachIncludedNodePackageInput(BaseModel):
    included_package_name: str
    include_key: str | None = Field(default=None)
    description: str | None = Field(default=None)


class NodePackageAttachIncludedNodePackageOutput(BaseModel):
    value: NodePackageIncludedNodePackage


FUNCTIONS = {
    "NodePackage": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Create the canonical Node-owned package root over an existing `NodeConfig`.\n\nContract:\n- Identity is keyed by Node package `name`.\n- `NodePackage` is the package/public root over an existing canonical `NodeConfig`.\n- `node_config_id` must point at the canonical NodeConfig stable id for this package root.\n- `source_code_package_id` is the explicit raw-source provenance link for this semantic\n  leaf package.\n- Manifest/build/dependency attributes mirror `aware.node.toml` so committed package truth\n  can drive Workspace and Node runtime resolution without reopening authoring TOML.\n- Workspace will later mount `NodePackage`, not raw `NodeConfig`.",
                "is_constructor": True,
            },
            "input": NodePackageBuildInput,
            "output": NodePackageBuildOutput,
        },
        "sync_manifest_truth": {
            "canonical": {
                "name": "sync_manifest_truth",
                "description": "Sync mutable manifest/build/dependency truth onto an existing NodePackage root.\n\nThis keeps `build` create-only for empty package lanes while allowing committed package\ntruth to follow the latest parsed `aware.node.toml` snapshot.",
                "is_constructor": False,
            },
            "input": NodePackageSyncManifestTruthInput,
            "output": NodePackageSyncManifestTruthOutput,
        },
        "attach_included_node_package": {
            "canonical": {
                "name": "attach_included_node_package",
                "description": "Attach one package-level Node composition include.\n\nContract:\n- Parent `NodePackage` scope is injected by propagation.\n- Identity is keyed by the included package's semantic package name.\n- The bridge resolves and stores the canonical included `NodePackage` relationship.\n- Includes select composition participants only; ServicePackage API bridge truth still\n  drives route requirements.",
                "is_constructor": False,
            },
            "input": NodePackageAttachIncludedNodePackageInput,
            "output": NodePackageAttachIncludedNodePackageOutput,
        },
    },
}

__all__ = [
    "NodePackage",
    "NodePackageBuildInput",
    "NodePackageBuildOutput",
    "NodePackageSyncManifestTruthInput",
    "NodePackageSyncManifestTruthOutput",
    "NodePackageAttachIncludedNodePackageInput",
    "NodePackageAttachIncludedNodePackageOutput",
    "FUNCTIONS",
]
