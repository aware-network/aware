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
    from aware_meta_ontology.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit
    from aware_sdk_ontology.sdk.sdk_package import SdkPackage


class SdkPackageDependency(ORMModel):
    """
    SDK package to SDK package dependency bridge.
    The authored `aware.sdk.toml` dependency row is selector truth. The resolved
    OIG commit pin, when present, is exact reproducibility authority for Hub and
    WorkspaceRevision consumers.
    """

    # Relationships
    target_sdk_package: SdkPackage | None = Field(default=None)
    target_sdk_package_object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None)

    # Attributes
    target_package_name: str
    target_version_number: int | None = Field(default=None)
    expected_hash_sha256: str | None = Field(default=None)
    description: str | None = Field(default=None)

    # Foreign Keys
    sdk_package_id: UUID = Field(description="Foreign key for SdkPackage.sdk_package_dependencies")
    target_sdk_package_id: UUID = Field(description="Foreign key for SdkPackageDependency.target_sdk_package")
    target_sdk_package_object_instance_graph_commit_id: UUID | None = Field(
        default=None, description="Foreign key for SdkPackageDependency.target_sdk_package_object_instance_graph_commit"
    )

    @classmethod
    async def build_via_sdk_package(
        cls,
        sdk_package_id: UUID,
        target_sdk_package_id: UUID,
        target_package_name: str,
        target_sdk_package_object_instance_graph_commit_id: UUID | None = None,
        target_version_number: int | None = None,
        expected_hash_sha256: str | None = None,
        description: str | None = None,
    ) -> SdkPackageDependency:
        """
        Create one package-level SDK dependency edge.

        Contract:
        - Parent `SdkPackage` scope is injected by propagation.
        - Identity is keyed by the target `SdkPackage`; package name is retained as authored selector text.
        - `target_version_number` is compatibility/selector metadata, not reproducibility authority.
        - `target_sdk_package_object_instance_graph_commit_id`, when present, pins exact semantic package
        truth.
        - This bridge enables later SDK operation composition without turning API endpoints into
        orchestration truth.
        """

        payload = {
            "sdk_package_id": sdk_package_id,
            "target_sdk_package_id": target_sdk_package_id,
            "target_package_name": target_package_name,
            "target_sdk_package_object_instance_graph_commit_id": target_sdk_package_object_instance_graph_commit_id,
            "target_version_number": target_version_number,
            "expected_hash_sha256": expected_hash_sha256,
            "description": description,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_sdk_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, SdkPackageDependency):
            return value
        return SdkPackageDependency.validate_invocation_value(value)


class SdkPackageDependencyBuildViaSdkPackageInput(BaseModel):
    sdk_package_id: UUID = Field(description="Foreign key for SdkPackage.sdk_package_dependencies")
    target_sdk_package_id: UUID
    target_package_name: str
    target_sdk_package_object_instance_graph_commit_id: UUID | None = Field(default=None)
    target_version_number: int | None = Field(default=None)
    expected_hash_sha256: str | None = Field(default=None)
    description: str | None = Field(default=None)


class SdkPackageDependencyBuildViaSdkPackageOutput(BaseModel):
    value: SdkPackageDependency


FUNCTIONS = {
    "SdkPackageDependency": {
        "build_via_sdk_package": {
            "canonical": {
                "name": "build_via_sdk_package",
                "description": "Create one package-level SDK dependency edge.\n\nContract:\n- Parent `SdkPackage` scope is injected by propagation.\n- Identity is keyed by the target `SdkPackage`; package name is retained as authored selector text.\n- `target_version_number` is compatibility/selector metadata, not reproducibility authority.\n- `target_sdk_package_object_instance_graph_commit_id`, when present, pins exact semantic package truth.\n- This bridge enables later SDK operation composition without turning API endpoints into orchestration truth.",
                "is_constructor": True,
            },
            "input": SdkPackageDependencyBuildViaSdkPackageInput,
            "output": SdkPackageDependencyBuildViaSdkPackageOutput,
        },
    },
}

__all__ = [
    "SdkPackageDependency",
    "SdkPackageDependencyBuildViaSdkPackageInput",
    "SdkPackageDependencyBuildViaSdkPackageOutput",
    "FUNCTIONS",
]
