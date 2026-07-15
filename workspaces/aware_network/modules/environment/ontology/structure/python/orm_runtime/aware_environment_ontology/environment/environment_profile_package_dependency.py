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
    from aware_environment_ontology.environment.environment_profile_package import EnvironmentProfilePackage
    from aware_meta_ontology.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit


class EnvironmentProfilePackageDependency(ORMModel):
    """
    Direct dependency from one EnvironmentProfilePackage to another.
    This models reusable OS profile package composition as Environment semantic
    package truth. It is separate from concrete EnvironmentProfile session links.
    """

    # Relationships
    target_environment_profile_package: EnvironmentProfilePackage | None = Field(default=None)
    target_environment_profile_package_object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(
        default=None
    )
    environment_profile_package: EnvironmentProfilePackage | None = Field(
        default=None, exclude=True, description="Reverse view for EnvironmentProfilePackage.dependencies"
    )

    # Attributes
    description: str | None = Field(default=None)
    expected_hash_sha256: str | None = Field(default=None)
    target_package_name: str
    target_version_number: int | None = Field(default=None)

    # Foreign Keys
    environment_profile_package_id: UUID = Field(description="Foreign key for EnvironmentProfilePackage.dependencies")
    target_environment_profile_package_id: UUID = Field(
        description="Foreign key for EnvironmentProfilePackageDependency.target_environment_profile_package"
    )
    target_environment_profile_package_object_instance_graph_commit_id: UUID | None = Field(
        default=None,
        description="Foreign key for EnvironmentProfilePackageDependency.target_environment_profile_package_object_instance_graph_commit",
    )

    @classmethod
    async def build_via_environment_profile_package(
        cls,
        environment_profile_package_id: UUID,
        target_environment_profile_package_id: UUID,
        target_package_name: str,
        target_environment_profile_package_object_instance_graph_commit_id: UUID | None = None,
        target_version_number: int | None = None,
        expected_hash_sha256: str | None = None,
        description: str | None = None,
    ) -> EnvironmentProfilePackageDependency:
        """
        Create one package-level EnvironmentProfilePackage dependency edge.

        Contract:
        - Parent `EnvironmentProfilePackage` scope is injected by propagation.
        - Identity is keyed by the target package.
        - `target_package_name` is retained as authored selector text.
        - The optional OIG commit pin is the exact reproducibility authority for
          WorkspaceRevision and Hub consumers.
        """

        payload = {
            "environment_profile_package_id": environment_profile_package_id,
            "target_environment_profile_package_id": target_environment_profile_package_id,
            "target_package_name": target_package_name,
            "target_environment_profile_package_object_instance_graph_commit_id": target_environment_profile_package_object_instance_graph_commit_id,
            "target_version_number": target_version_number,
            "expected_hash_sha256": expected_hash_sha256,
            "description": description,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_environment_profile_package", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, EnvironmentProfilePackageDependency):
            return value
        return EnvironmentProfilePackageDependency.validate_invocation_value(value)


class EnvironmentProfilePackageDependencyBuildViaEnvironmentProfilePackageInput(BaseModel):
    environment_profile_package_id: UUID = Field(description="Foreign key for EnvironmentProfilePackage.dependencies")
    target_environment_profile_package_id: UUID
    target_package_name: str
    target_environment_profile_package_object_instance_graph_commit_id: UUID | None = Field(default=None)
    target_version_number: int | None = Field(default=None)
    expected_hash_sha256: str | None = Field(default=None)
    description: str | None = Field(default=None)


class EnvironmentProfilePackageDependencyBuildViaEnvironmentProfilePackageOutput(BaseModel):
    value: EnvironmentProfilePackageDependency


FUNCTIONS = {
    "EnvironmentProfilePackageDependency": {
        "build_via_environment_profile_package": {
            "canonical": {
                "name": "build_via_environment_profile_package",
                "description": "Create one package-level EnvironmentProfilePackage dependency edge.\n\nContract:\n- Parent `EnvironmentProfilePackage` scope is injected by propagation.\n- Identity is keyed by the target package.\n- `target_package_name` is retained as authored selector text.\n- The optional OIG commit pin is the exact reproducibility authority for\n  WorkspaceRevision and Hub consumers.",
                "is_constructor": True,
            },
            "input": EnvironmentProfilePackageDependencyBuildViaEnvironmentProfilePackageInput,
            "output": EnvironmentProfilePackageDependencyBuildViaEnvironmentProfilePackageOutput,
        },
    },
}

__all__ = [
    "EnvironmentProfilePackageDependency",
    "EnvironmentProfilePackageDependencyBuildViaEnvironmentProfilePackageInput",
    "EnvironmentProfilePackageDependencyBuildViaEnvironmentProfilePackageOutput",
    "FUNCTIONS",
]
