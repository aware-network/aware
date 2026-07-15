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
    from aware_experience_ontology.environment.experience_package import ExperiencePackage
    from aware_meta_ontology.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit


class ExperiencePackageDependency(ORMModel):
    """
    Experience package to Experience package dependency bridge.
    The authored `aware.experience.toml` dependency row is selector truth. The
    resolved OIG commit pin, when present, is exact reproducibility authority for
    WorkspaceRevision/Hub consumers and cross-Experience transition linking.
    """

    # Relationships
    target_experience_package: ExperiencePackage | None = Field(default=None)
    target_experience_package_object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None)

    # Attributes
    target_package_name: str
    target_version_number: int | None = Field(default=None)
    expected_hash_sha256: str | None = Field(default=None)
    description: str | None = Field(default=None)

    # Foreign Keys
    experience_package_id: UUID = Field(description="Foreign key for ExperiencePackage.experience_package_dependencies")
    target_experience_package_id: UUID = Field(
        description="Foreign key for ExperiencePackageDependency.target_experience_package"
    )
    target_experience_package_object_instance_graph_commit_id: UUID | None = Field(
        default=None,
        description="Foreign key for ExperiencePackageDependency.target_experience_package_object_instance_graph_commit",
    )

    @classmethod
    async def build_via_experience_package(
        cls,
        experience_package_id: UUID,
        target_experience_package_id: UUID,
        target_package_name: str,
        target_experience_package_object_instance_graph_commit_id: UUID | None = None,
        target_version_number: int | None = None,
        expected_hash_sha256: str | None = None,
        description: str | None = None,
    ) -> ExperiencePackageDependency:
        """
        Create one package-level Experience dependency edge.

        Contract:
        - Parent `ExperiencePackage` scope is injected by propagation.
        - Identity is keyed by the target `ExperiencePackage`.
        - `target_package_name` is retained as authored selector text.
        - `target_version_number` is compatibility/selector metadata, not reproducibility authority.
        - `target_experience_package_object_instance_graph_commit_id`, when present, pins exact
          semantic package truth.
        - Cross-Experience transitions and profile composition may resolve only through this
          dependency closure.
        """

        payload = {
            "experience_package_id": experience_package_id,
            "target_experience_package_id": target_experience_package_id,
            "target_package_name": target_package_name,
            "target_experience_package_object_instance_graph_commit_id": target_experience_package_object_instance_graph_commit_id,
            "target_version_number": target_version_number,
            "expected_hash_sha256": expected_hash_sha256,
            "description": description,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_experience_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ExperiencePackageDependency):
            return value
        return ExperiencePackageDependency.validate_invocation_value(value)


class ExperiencePackageDependencyBuildViaExperiencePackageInput(BaseModel):
    experience_package_id: UUID = Field(description="Foreign key for ExperiencePackage.experience_package_dependencies")
    target_experience_package_id: UUID
    target_package_name: str
    target_experience_package_object_instance_graph_commit_id: UUID | None = Field(default=None)
    target_version_number: int | None = Field(default=None)
    expected_hash_sha256: str | None = Field(default=None)
    description: str | None = Field(default=None)


class ExperiencePackageDependencyBuildViaExperiencePackageOutput(BaseModel):
    value: ExperiencePackageDependency


FUNCTIONS = {
    "ExperiencePackageDependency": {
        "build_via_experience_package": {
            "canonical": {
                "name": "build_via_experience_package",
                "description": "Create one package-level Experience dependency edge.\n\nContract:\n- Parent `ExperiencePackage` scope is injected by propagation.\n- Identity is keyed by the target `ExperiencePackage`.\n- `target_package_name` is retained as authored selector text.\n- `target_version_number` is compatibility/selector metadata, not reproducibility authority.\n- `target_experience_package_object_instance_graph_commit_id`, when present, pins exact\n  semantic package truth.\n- Cross-Experience transitions and profile composition may resolve only through this\n  dependency closure.",
                "is_constructor": True,
            },
            "input": ExperiencePackageDependencyBuildViaExperiencePackageInput,
            "output": ExperiencePackageDependencyBuildViaExperiencePackageOutput,
        },
    },
}

__all__ = [
    "ExperiencePackageDependency",
    "ExperiencePackageDependencyBuildViaExperiencePackageInput",
    "ExperiencePackageDependencyBuildViaExperiencePackageOutput",
    "FUNCTIONS",
]
