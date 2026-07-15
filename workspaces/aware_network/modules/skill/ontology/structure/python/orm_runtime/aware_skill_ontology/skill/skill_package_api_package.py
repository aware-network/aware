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


class SkillPackageApiPackage(ORMModel):
    # Relationships
    api_package: ApiPackage | None = Field(default=None)

    # Attributes
    description: str | None = Field(default=None)

    # Foreign Keys
    skill_package_id: UUID = Field(description="Foreign key for SkillPackage.api_packages")
    api_package_id: UUID = Field(description="Foreign key for SkillPackageApiPackage.api_package")

    @classmethod
    async def build_via_skill_package(
        cls, skill_package_id: UUID, api_package_id: UUID, description: str | None = None
    ) -> SkillPackageApiPackage:
        """
        Create one package-level Skill bridge to one API package.

        Contract:
        - Parent `SkillPackage` scope is injected by propagation.
        - Identity is keyed by the attached `ApiPackage`.
        - This is the package/import seam for authored Skill source resolution.
        - It does not replace config-level semantic API or endpoint resolution.
        """

        payload = {"skill_package_id": skill_package_id, "api_package_id": api_package_id, "description": description}
        result = await invoke_constructor(orm_class=cls, function_name="build_via_skill_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, SkillPackageApiPackage):
            return value
        return SkillPackageApiPackage.validate_invocation_value(value)


class SkillPackageApiPackageBuildViaSkillPackageInput(BaseModel):
    skill_package_id: UUID = Field(description="Foreign key for SkillPackage.api_packages")
    api_package_id: UUID
    description: str | None = Field(default=None)


class SkillPackageApiPackageBuildViaSkillPackageOutput(BaseModel):
    value: SkillPackageApiPackage


FUNCTIONS = {
    "SkillPackageApiPackage": {
        "build_via_skill_package": {
            "canonical": {
                "name": "build_via_skill_package",
                "description": "Create one package-level Skill bridge to one API package.\n\nContract:\n- Parent `SkillPackage` scope is injected by propagation.\n- Identity is keyed by the attached `ApiPackage`.\n- This is the package/import seam for authored Skill source resolution.\n- It does not replace config-level semantic API or endpoint resolution.",
                "is_constructor": True,
            },
            "input": SkillPackageApiPackageBuildViaSkillPackageInput,
            "output": SkillPackageApiPackageBuildViaSkillPackageOutput,
        },
    },
}

__all__ = [
    "SkillPackageApiPackage",
    "SkillPackageApiPackageBuildViaSkillPackageInput",
    "SkillPackageApiPackageBuildViaSkillPackageOutput",
    "FUNCTIONS",
]
