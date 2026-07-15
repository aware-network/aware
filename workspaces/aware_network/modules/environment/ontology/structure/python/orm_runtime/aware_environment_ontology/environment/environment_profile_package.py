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

if TYPE_CHECKING:
    from aware_code_ontology.package.code_package import CodePackage
    from aware_environment_ontology.environment.environment_config_package import EnvironmentConfigPackage
    from aware_environment_ontology.environment.environment_profile_config import EnvironmentProfileConfig
    from aware_environment_ontology.environment.environment_profile_package_dependency import (
        EnvironmentProfilePackageDependency,
    )
    from aware_meta_ontology.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit


class EnvironmentProfilePackage(ORMModel):
    """
    Semantic package root for one reusable EnvironmentProfileConfig.
    Contract:
    - EnvironmentProfilePackage is Environment-owned OS profile package truth.
    - The package root points at reusable EnvironmentProfileConfig, not applied
    EnvironmentProfile runtime state.
    - EnvironmentProfileConfig owns ProcessConfig, ThreadConfig, provider, and
    actor eligibility topology.
    - EnvironmentSessionConfig belongs to EnvironmentConfig and may reference
    profile/process/thread config defaults through portals.
    - EnvironmentProfile stays the concrete Environment-applied bridge to
    running EnvironmentSessions.
    """

    # Relationships
    source_code_package: CodePackage | None = Field(default=None)
    environment_config_package: EnvironmentConfigPackage | None = Field(default=None)
    environment_config_package_object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None)
    environment_profile_config: EnvironmentProfileConfig | None = Field(default=None)
    environment_profile_config_object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None)
    dependencies: list[EnvironmentProfilePackageDependency] = Field(default_factory=list)

    # Attributes
    description: str | None = Field(default=None)
    environment_handle: str | None = Field(default=None)
    manifest_relative_path: str | None = Field(default=None)
    name: str
    package_root: str = Field(default=".")
    profile_key: str | None = Field(default=None)
    sources_root: str = Field(default="profiles")
    title: str | None = Field(default=None)
    version_number: int = Field(default=1)

    # Foreign Keys
    source_code_package_id: UUID | None = Field(
        default=None, description="Foreign key for EnvironmentProfilePackage.source_code_package"
    )
    environment_config_package_id: UUID | None = Field(
        default=None, description="Foreign key for EnvironmentProfilePackage.environment_config_package"
    )
    environment_config_package_object_instance_graph_commit_id: UUID | None = Field(
        default=None,
        description="Foreign key for EnvironmentProfilePackage.environment_config_package_object_instance_graph_commit",
    )
    environment_profile_config_id: UUID = Field(
        description="Foreign key for EnvironmentProfilePackage.environment_profile_config"
    )
    environment_profile_config_object_instance_graph_commit_id: UUID | None = Field(
        default=None,
        description="Foreign key for EnvironmentProfilePackage.environment_profile_config_object_instance_graph_commit",
    )

    @classmethod
    async def build(
        cls,
        name: str,
        environment_profile_config_id: UUID,
        environment_profile_config_object_instance_graph_commit_id: UUID | None = None,
        environment_config_package_id: UUID | None = None,
        environment_config_package_object_instance_graph_commit_id: UUID | None = None,
        source_code_package_id: UUID | None = None,
        profile_key: str | None = None,
        environment_handle: str | None = None,
        version_number: int = 1,
        title: str | None = None,
        description: str | None = None,
        manifest_relative_path: str | None = None,
        package_root: str = ".",
        sources_root: str = "profiles",
    ) -> EnvironmentProfilePackage:
        """
        Create the canonical Environment package root over EnvironmentProfileConfig.

        Contract:
        - Identity is keyed by package `name`.
        - `environment_profile_config_id` points to reusable OS profile config
          truth, never a concrete EnvironmentProfile application.
        - OIG commit pins let WorkspaceRevision/Environment consumers replay
          exact profile config and dependency truth without reopening source
          profile manifests.
        - `environment_config_package_id` is optional package-level Environment
          composition provenance; EnvironmentConfig is Environment-owned.
        """

        payload = {
            "name": name,
            "environment_profile_config_id": environment_profile_config_id,
            "environment_profile_config_object_instance_graph_commit_id": environment_profile_config_object_instance_graph_commit_id,
            "environment_config_package_id": environment_config_package_id,
            "environment_config_package_object_instance_graph_commit_id": environment_config_package_object_instance_graph_commit_id,
            "source_code_package_id": source_code_package_id,
            "profile_key": profile_key,
            "environment_handle": environment_handle,
            "version_number": version_number,
            "title": title,
            "description": description,
            "manifest_relative_path": manifest_relative_path,
            "package_root": package_root,
            "sources_root": sources_root,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, EnvironmentProfilePackage):
            return value
        return EnvironmentProfilePackage.validate_invocation_value(value)

    async def attach_dependency(
        self,
        target_environment_profile_package_id: UUID,
        target_package_name: str,
        target_environment_profile_package_object_instance_graph_commit_id: UUID | None = None,
        target_version_number: int | None = None,
        expected_hash_sha256: str | None = None,
        description: str | None = None,
    ) -> EnvironmentProfilePackageDependency:
        """
        Attach one EnvironmentProfilePackage dependency.

        Contract:
        - Parent `EnvironmentProfilePackage` scope is injected by propagation.
        - Dependencies are package-level profile dependencies, not applied
          EnvironmentProfile session links.
        - Optional OIG commit pin is exact replay truth for WorkspaceRevision
          and Hub consumers.
        """

        payload = {
            "target_environment_profile_package_id": target_environment_profile_package_id,
            "target_package_name": target_package_name,
            "target_environment_profile_package_object_instance_graph_commit_id": target_environment_profile_package_object_instance_graph_commit_id,
            "target_version_number": target_version_number,
            "expected_hash_sha256": expected_hash_sha256,
            "description": description,
        }
        result = await invoke_instance(orm_model=self, function_name="attach_dependency", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_environment_ontology.environment.environment_profile_package_dependency import (
            EnvironmentProfilePackageDependency,
        )

        if isinstance(value, EnvironmentProfilePackageDependency):
            return value
        return EnvironmentProfilePackageDependency.validate_invocation_value(value)


class EnvironmentProfilePackageBuildInput(BaseModel):
    name: str
    environment_profile_config_id: UUID
    environment_profile_config_object_instance_graph_commit_id: UUID | None = Field(default=None)
    environment_config_package_id: UUID | None = Field(default=None)
    environment_config_package_object_instance_graph_commit_id: UUID | None = Field(default=None)
    source_code_package_id: UUID | None = Field(default=None)
    profile_key: str | None = Field(default=None)
    environment_handle: str | None = Field(default=None)
    version_number: int = Field(default=1)
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    manifest_relative_path: str | None = Field(default=None)
    package_root: str = Field(default=".")
    sources_root: str = Field(default="profiles")


class EnvironmentProfilePackageBuildOutput(BaseModel):
    value: EnvironmentProfilePackage


class EnvironmentProfilePackageAttachDependencyInput(BaseModel):
    target_environment_profile_package_id: UUID
    target_package_name: str
    target_environment_profile_package_object_instance_graph_commit_id: UUID | None = Field(default=None)
    target_version_number: int | None = Field(default=None)
    expected_hash_sha256: str | None = Field(default=None)
    description: str | None = Field(default=None)


class EnvironmentProfilePackageAttachDependencyOutput(BaseModel):
    value: EnvironmentProfilePackageDependency


FUNCTIONS = {
    "EnvironmentProfilePackage": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Create the canonical Environment package root over EnvironmentProfileConfig.\n\nContract:\n- Identity is keyed by package `name`.\n- `environment_profile_config_id` points to reusable OS profile config\n  truth, never a concrete EnvironmentProfile application.\n- OIG commit pins let WorkspaceRevision/Environment consumers replay\n  exact profile config and dependency truth without reopening source\n  profile manifests.\n- `environment_config_package_id` is optional package-level Environment\n  composition provenance; EnvironmentConfig is Environment-owned.",
                "is_constructor": True,
            },
            "input": EnvironmentProfilePackageBuildInput,
            "output": EnvironmentProfilePackageBuildOutput,
        },
        "attach_dependency": {
            "canonical": {
                "name": "attach_dependency",
                "description": "Attach one EnvironmentProfilePackage dependency.\n\nContract:\n- Parent `EnvironmentProfilePackage` scope is injected by propagation.\n- Dependencies are package-level profile dependencies, not applied\n  EnvironmentProfile session links.\n- Optional OIG commit pin is exact replay truth for WorkspaceRevision\n  and Hub consumers.",
                "is_constructor": False,
            },
            "input": EnvironmentProfilePackageAttachDependencyInput,
            "output": EnvironmentProfilePackageAttachDependencyOutput,
        },
    },
}

__all__ = [
    "EnvironmentProfilePackage",
    "EnvironmentProfilePackageBuildInput",
    "EnvironmentProfilePackageBuildOutput",
    "EnvironmentProfilePackageAttachDependencyInput",
    "EnvironmentProfilePackageAttachDependencyOutput",
    "FUNCTIONS",
]
