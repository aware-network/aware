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
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_meta_ontology.graph.config.object_config_graph_package import ObjectConfigGraphPackage
    from aware_meta_ontology.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit


class SdkPackageObjectConfigGraphPackage(ORMModel):
    """
    SDK package to owned ObjectConfigGraphPackage bridge.
    This records OCG/state packages declared by `aware.sdk.toml` as SDK-owned
    package surfaces. These are not package dependencies; they are part of the
    SDK package truth and should travel with WorkspaceRevision/Hub receipts.
    """

    # Relationships
    object_config_graph_package: ObjectConfigGraphPackage | None = Field(default=None)
    object_config_graph_package_object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None)

    # Attributes
    role: str = Field(default="local_state")
    manifest_relative_path: str
    package_kind: str = Field(default="state")
    expected_hash_sha256: str | None = Field(default=None)
    description: str | None = Field(default=None)

    # Foreign Keys
    sdk_package_id: UUID = Field(description="Foreign key for SdkPackage.object_config_graph_packages")
    object_config_graph_package_id: UUID = Field(
        description="Foreign key for SdkPackageObjectConfigGraphPackage.object_config_graph_package"
    )
    object_config_graph_package_object_instance_graph_commit_id: UUID | None = Field(
        default=None,
        description="Foreign key for SdkPackageObjectConfigGraphPackage.object_config_graph_package_object_instance_graph_commit",
    )

    @classmethod
    async def build_via_sdk_package(
        cls,
        sdk_package_id: UUID,
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
        - Parent `SdkPackage` scope is injected by propagation.
        - Identity is keyed by the owned ObjectConfigGraphPackage.
        - `manifest_relative_path` preserves the SDK-authored child package manifest path.
        - `object_config_graph_package_object_instance_graph_commit_id`, when present,
          pins the exact committed OCG package truth included in a WorkspaceRevision.
        """

        payload = {
            "sdk_package_id": sdk_package_id,
            "object_config_graph_package_id": object_config_graph_package_id,
            "manifest_relative_path": manifest_relative_path,
            "role": role,
            "package_kind": package_kind,
            "object_config_graph_package_object_instance_graph_commit_id": object_config_graph_package_object_instance_graph_commit_id,
            "expected_hash_sha256": expected_hash_sha256,
            "description": description,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_sdk_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, SdkPackageObjectConfigGraphPackage):
            return value
        return SdkPackageObjectConfigGraphPackage.validate_invocation_value(value)


class SdkPackageObjectConfigGraphPackageBuildViaSdkPackageInput(BaseModel):
    sdk_package_id: UUID = Field(description="Foreign key for SdkPackage.object_config_graph_packages")
    object_config_graph_package_id: UUID
    manifest_relative_path: str
    role: str = Field(default="local_state")
    package_kind: str = Field(default="state")
    object_config_graph_package_object_instance_graph_commit_id: UUID | None = Field(default=None)
    expected_hash_sha256: str | None = Field(default=None)
    description: str | None = Field(default=None)


class SdkPackageObjectConfigGraphPackageBuildViaSdkPackageOutput(BaseModel):
    value: SdkPackageObjectConfigGraphPackage


FUNCTIONS = {
    "SdkPackageObjectConfigGraphPackage": {
        "build_via_sdk_package": {
            "canonical": {
                "name": "build_via_sdk_package",
                "description": "Attach one SDK-owned ObjectConfigGraphPackage to this SdkPackage.\n\nContract:\n- Parent `SdkPackage` scope is injected by propagation.\n- Identity is keyed by the owned ObjectConfigGraphPackage.\n- `manifest_relative_path` preserves the SDK-authored child package manifest path.\n- `object_config_graph_package_object_instance_graph_commit_id`, when present,\n  pins the exact committed OCG package truth included in a WorkspaceRevision.",
                "is_constructor": True,
            },
            "input": SdkPackageObjectConfigGraphPackageBuildViaSdkPackageInput,
            "output": SdkPackageObjectConfigGraphPackageBuildViaSdkPackageOutput,
        },
    },
}

__all__ = [
    "SdkPackageObjectConfigGraphPackage",
    "SdkPackageObjectConfigGraphPackageBuildViaSdkPackageInput",
    "SdkPackageObjectConfigGraphPackageBuildViaSdkPackageOutput",
    "FUNCTIONS",
]
