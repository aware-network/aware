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


class AppPackageExperiencePackage(ORMModel):
    # Relationships
    experience_package: ExperiencePackage | None = Field(default=None)
    experience_package_object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None)

    # Attributes
    description: str | None = Field(default=None)
    role: str = Field(default="experience")

    # Foreign Keys
    app_package_id: UUID = Field(description="Foreign key for AppPackage.experience_packages")
    experience_package_id: UUID = Field(description="Foreign key for AppPackageExperiencePackage.experience_package")
    experience_package_object_instance_graph_commit_id: UUID | None = Field(
        default=None,
        description="Foreign key for AppPackageExperiencePackage.experience_package_object_instance_graph_commit",
    )

    @classmethod
    async def build_via_app_package(
        cls,
        app_package_id: UUID,
        experience_package_id: UUID,
        experience_package_object_instance_graph_commit_id: UUID | None = None,
        role: str = "experience",
        description: str | None = None,
    ) -> AppPackageExperiencePackage:
        """
        Create one app package dependency on an ExperiencePackage.

        Contract:
        - Parent AppPackage scope is injected by propagation.
        - Identity is keyed by the attached ExperiencePackage.
        - This is the app front door dependency: app screens resolve Experience
          layout graph bindings, not Environment internals.
        """

        payload = {
            "app_package_id": app_package_id,
            "experience_package_id": experience_package_id,
            "experience_package_object_instance_graph_commit_id": experience_package_object_instance_graph_commit_id,
            "role": role,
            "description": description,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_app_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, AppPackageExperiencePackage):
            return value
        return AppPackageExperiencePackage.validate_invocation_value(value)


class AppPackageExperiencePackageBuildViaAppPackageInput(BaseModel):
    app_package_id: UUID = Field(description="Foreign key for AppPackage.experience_packages")
    experience_package_id: UUID
    experience_package_object_instance_graph_commit_id: UUID | None = Field(default=None)
    role: str = Field(default="experience")
    description: str | None = Field(default=None)


class AppPackageExperiencePackageBuildViaAppPackageOutput(BaseModel):
    value: AppPackageExperiencePackage


FUNCTIONS = {
    "AppPackageExperiencePackage": {
        "build_via_app_package": {
            "canonical": {
                "name": "build_via_app_package",
                "description": "Create one app package dependency on an ExperiencePackage.\n\nContract:\n- Parent AppPackage scope is injected by propagation.\n- Identity is keyed by the attached ExperiencePackage.\n- This is the app front door dependency: app screens resolve Experience\n  layout graph bindings, not Environment internals.",
                "is_constructor": True,
            },
            "input": AppPackageExperiencePackageBuildViaAppPackageInput,
            "output": AppPackageExperiencePackageBuildViaAppPackageOutput,
        },
    },
}

__all__ = [
    "AppPackageExperiencePackage",
    "AppPackageExperiencePackageBuildViaAppPackageInput",
    "AppPackageExperiencePackageBuildViaAppPackageOutput",
    "FUNCTIONS",
]
