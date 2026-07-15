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


class InterfacePackageExperiencePackage(ORMModel):
    # Relationships
    experience_package: ExperiencePackage | None = Field(default=None)

    # Attributes
    description: str | None = Field(default=None)

    # Foreign Keys
    interface_package_id: UUID = Field(description="Foreign key for InterfacePackage.experience_packages")
    experience_package_id: UUID = Field(
        description="Foreign key for InterfacePackageExperiencePackage.experience_package"
    )

    @classmethod
    async def build_via_interface_package(
        cls, interface_package_id: UUID, experience_package_id: UUID, description: str | None = None
    ) -> InterfacePackageExperiencePackage:
        """
        Create one package-level Interface bridge to one ExperiencePackage.

        Contract:
        - Parent `InterfacePackage` scope is injected by propagation.
        - Identity is keyed by the attached `ExperiencePackage`.
        - This is the package/import seam for authored Interface observable/view ownership.
        - It does not replace pane-level `ProjectionExperienceView` binding inside `InterfaceConfig`.
        """

        payload = {
            "interface_package_id": interface_package_id,
            "experience_package_id": experience_package_id,
            "description": description,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_interface_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, InterfacePackageExperiencePackage):
            return value
        return InterfacePackageExperiencePackage.validate_invocation_value(value)


class InterfacePackageExperiencePackageBuildViaInterfacePackageInput(BaseModel):
    interface_package_id: UUID = Field(description="Foreign key for InterfacePackage.experience_packages")
    experience_package_id: UUID
    description: str | None = Field(default=None)


class InterfacePackageExperiencePackageBuildViaInterfacePackageOutput(BaseModel):
    value: InterfacePackageExperiencePackage


FUNCTIONS = {
    "InterfacePackageExperiencePackage": {
        "build_via_interface_package": {
            "canonical": {
                "name": "build_via_interface_package",
                "description": "Create one package-level Interface bridge to one ExperiencePackage.\n\nContract:\n- Parent `InterfacePackage` scope is injected by propagation.\n- Identity is keyed by the attached `ExperiencePackage`.\n- This is the package/import seam for authored Interface observable/view ownership.\n- It does not replace pane-level `ProjectionExperienceView` binding inside `InterfaceConfig`.",
                "is_constructor": True,
            },
            "input": InterfacePackageExperiencePackageBuildViaInterfacePackageInput,
            "output": InterfacePackageExperiencePackageBuildViaInterfacePackageOutput,
        },
    },
}

__all__ = [
    "InterfacePackageExperiencePackage",
    "InterfacePackageExperiencePackageBuildViaInterfacePackageInput",
    "InterfacePackageExperiencePackageBuildViaInterfacePackageOutput",
    "FUNCTIONS",
]
