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


class PanePackageExperiencePackage(ORMModel):
    # Relationships
    experience_package: ExperiencePackage | None = Field(default=None)

    # Attributes
    description: str | None = Field(default=None)

    # Foreign Keys
    pane_package_id: UUID = Field(description="Foreign key for PanePackage.experience_packages")
    experience_package_id: UUID = Field(description="Foreign key for PanePackageExperiencePackage.experience_package")

    @classmethod
    async def build_via_pane_package(
        cls, pane_package_id: UUID, experience_package_id: UUID, description: str | None = None
    ) -> PanePackageExperiencePackage:
        """
        Create one package-level Pane bridge to one ExperiencePackage.

        Contract:
        - Parent `PanePackage` scope is injected by propagation.
        - Identity is keyed by the attached `ExperiencePackage`.
        - This is the pane-local import seam for resolving the PaneConfig
          ProjectionExperienceView key.
        - Interface packages consume the resolved PanePackage; they do not
          declare Experience packages to resolve pane views.
        """

        payload = {
            "pane_package_id": pane_package_id,
            "experience_package_id": experience_package_id,
            "description": description,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_pane_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, PanePackageExperiencePackage):
            return value
        return PanePackageExperiencePackage.validate_invocation_value(value)


class PanePackageExperiencePackageBuildViaPanePackageInput(BaseModel):
    pane_package_id: UUID = Field(description="Foreign key for PanePackage.experience_packages")
    experience_package_id: UUID
    description: str | None = Field(default=None)


class PanePackageExperiencePackageBuildViaPanePackageOutput(BaseModel):
    value: PanePackageExperiencePackage


FUNCTIONS = {
    "PanePackageExperiencePackage": {
        "build_via_pane_package": {
            "canonical": {
                "name": "build_via_pane_package",
                "description": "Create one package-level Pane bridge to one ExperiencePackage.\n\nContract:\n- Parent `PanePackage` scope is injected by propagation.\n- Identity is keyed by the attached `ExperiencePackage`.\n- This is the pane-local import seam for resolving the PaneConfig\n  ProjectionExperienceView key.\n- Interface packages consume the resolved PanePackage; they do not\n  declare Experience packages to resolve pane views.",
                "is_constructor": True,
            },
            "input": PanePackageExperiencePackageBuildViaPanePackageInput,
            "output": PanePackageExperiencePackageBuildViaPanePackageOutput,
        },
    },
}

__all__ = [
    "PanePackageExperiencePackage",
    "PanePackageExperiencePackageBuildViaPanePackageInput",
    "PanePackageExperiencePackageBuildViaPanePackageOutput",
    "FUNCTIONS",
]
