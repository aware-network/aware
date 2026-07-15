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
    from aware_api_ontology.api.api_package import ApiPackage


class ExperiencePackageApiPackage(ORMModel):
    # Relationships
    api_package: ApiPackage | None = Field(default=None)

    # Attributes
    description: str | None = Field(default=None)

    # Foreign Keys
    experience_package_id: UUID = Field(description="Foreign key for ExperiencePackage.api_packages")
    api_package_id: UUID = Field(description="Foreign key for ExperiencePackageApiPackage.api_package")

    @classmethod
    async def build_via_experience_package(
        cls, experience_package_id: UUID, api_package_id: UUID, description: str | None = None
    ) -> ExperiencePackageApiPackage:
        """
        Create one package-level Experience dependency bridge to one API package.

        Contract:
        - Parent `ExperiencePackage` scope is injected by propagation.
        - Identity is keyed by the attached `ApiPackage`.
        - This declares API capability availability for Experience-owned view invocation actions.
        - It does not imply that panes own or provide those API contracts.
        """

        payload = {
            "experience_package_id": experience_package_id,
            "api_package_id": api_package_id,
            "description": description,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_experience_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ExperiencePackageApiPackage):
            return value
        return ExperiencePackageApiPackage.validate_invocation_value(value)


class ExperiencePackageApiPackageBuildViaExperiencePackageInput(BaseModel):
    experience_package_id: UUID = Field(description="Foreign key for ExperiencePackage.api_packages")
    api_package_id: UUID
    description: str | None = Field(default=None)


class ExperiencePackageApiPackageBuildViaExperiencePackageOutput(BaseModel):
    value: ExperiencePackageApiPackage


FUNCTIONS = {
    "ExperiencePackageApiPackage": {
        "build_via_experience_package": {
            "canonical": {
                "name": "build_via_experience_package",
                "description": "Create one package-level Experience dependency bridge to one API package.\n\nContract:\n- Parent `ExperiencePackage` scope is injected by propagation.\n- Identity is keyed by the attached `ApiPackage`.\n- This declares API capability availability for Experience-owned view invocation actions.\n- It does not imply that panes own or provide those API contracts.",
                "is_constructor": True,
            },
            "input": ExperiencePackageApiPackageBuildViaExperiencePackageInput,
            "output": ExperiencePackageApiPackageBuildViaExperiencePackageOutput,
        },
    },
}

__all__ = [
    "ExperiencePackageApiPackage",
    "ExperiencePackageApiPackageBuildViaExperiencePackageInput",
    "ExperiencePackageApiPackageBuildViaExperiencePackageOutput",
    "FUNCTIONS",
]
