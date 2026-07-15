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
    from aware_environment_ontology.environment.environment_config_package import EnvironmentConfigPackage
    from aware_meta_ontology.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit


class EnvironmentConfigPackageDependency(ORMModel):
    """
    A direct dependency from one EnvironmentConfigPackage to another.
    This models environment config composition as semantic package truth. The
    current kernel base is just one dependency role/value, not a special module
    dependency copied into product environments.
    """

    # Relationships
    target_environment_config_package: EnvironmentConfigPackage | None = Field(default=None)
    target_environment_config_package_object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(
        default=None
    )
    environment_config_package: EnvironmentConfigPackage | None = Field(
        default=None, exclude=True, description="Reverse view for EnvironmentConfigPackage.dependencies"
    )

    # Attributes
    dependency_role: str
    dependency_index: int
    target_handle: str

    # Foreign Keys
    environment_config_package_id: UUID = Field(description="Foreign key for EnvironmentConfigPackage.dependencies")
    target_environment_config_package_id: UUID = Field(
        description="Foreign key for EnvironmentConfigPackageDependency.target_environment_config_package"
    )
    target_environment_config_package_object_instance_graph_commit_id: UUID = Field(
        description="Foreign key for EnvironmentConfigPackageDependency.target_environment_config_package_object_instance_graph_commit"
    )

    @classmethod
    async def build_via_environment_config_package(
        cls,
        environment_config_package_id: UUID,
        dependency_role: str,
        dependency_index: int,
        target_handle: str,
        target_environment_config_package_id: UUID,
        target_environment_config_package_object_instance_graph_commit_id: UUID,
    ) -> EnvironmentConfigPackageDependency:
        """
        Create one deterministic environment package dependency edge.

        Contract:
        - Parent EnvironmentConfigPackage scope is injected by propagation.
        - `target_handle` mirrors the target package handle for readable
          receipts and deterministic root selection.
        - `target_environment_config_package_object_instance_graph_commit_id`
          is required; dependency resolution must be commit-pinned.
        """

        payload = {
            "environment_config_package_id": environment_config_package_id,
            "dependency_role": dependency_role,
            "dependency_index": dependency_index,
            "target_handle": target_handle,
            "target_environment_config_package_id": target_environment_config_package_id,
            "target_environment_config_package_object_instance_graph_commit_id": target_environment_config_package_object_instance_graph_commit_id,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_environment_config_package", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, EnvironmentConfigPackageDependency):
            return value
        return EnvironmentConfigPackageDependency.validate_invocation_value(value)


class EnvironmentConfigPackageDependencyBuildViaEnvironmentConfigPackageInput(BaseModel):
    environment_config_package_id: UUID = Field(description="Foreign key for EnvironmentConfigPackage.dependencies")
    dependency_role: str
    dependency_index: int
    target_handle: str
    target_environment_config_package_id: UUID
    target_environment_config_package_object_instance_graph_commit_id: UUID


class EnvironmentConfigPackageDependencyBuildViaEnvironmentConfigPackageOutput(BaseModel):
    value: EnvironmentConfigPackageDependency


FUNCTIONS = {
    "EnvironmentConfigPackageDependency": {
        "build_via_environment_config_package": {
            "canonical": {
                "name": "build_via_environment_config_package",
                "description": "Create one deterministic environment package dependency edge.\n\nContract:\n- Parent EnvironmentConfigPackage scope is injected by propagation.\n- `target_handle` mirrors the target package handle for readable\n  receipts and deterministic root selection.\n- `target_environment_config_package_object_instance_graph_commit_id`\n  is required; dependency resolution must be commit-pinned.",
                "is_constructor": True,
            },
            "input": EnvironmentConfigPackageDependencyBuildViaEnvironmentConfigPackageInput,
            "output": EnvironmentConfigPackageDependencyBuildViaEnvironmentConfigPackageOutput,
        },
    },
}

__all__ = [
    "EnvironmentConfigPackageDependency",
    "EnvironmentConfigPackageDependencyBuildViaEnvironmentConfigPackageInput",
    "EnvironmentConfigPackageDependencyBuildViaEnvironmentConfigPackageOutput",
    "FUNCTIONS",
]
