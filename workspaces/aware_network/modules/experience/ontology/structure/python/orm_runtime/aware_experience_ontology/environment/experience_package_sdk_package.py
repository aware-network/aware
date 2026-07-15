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
    from aware_sdk_ontology.sdk.sdk_package import SdkPackage


class ExperiencePackageSdkPackage(ORMModel):
    # Relationships
    sdk_package: SdkPackage | None = Field(default=None)

    # Attributes
    description: str | None = Field(default=None)

    # Foreign Keys
    experience_package_id: UUID = Field(description="Foreign key for ExperiencePackage.sdk_packages")
    sdk_package_id: UUID = Field(description="Foreign key for ExperiencePackageSdkPackage.sdk_package")

    @classmethod
    async def build_via_experience_package(
        cls, experience_package_id: UUID, sdk_package_id: UUID, description: str | None = None
    ) -> ExperiencePackageSdkPackage:
        """
        Create one package-level Experience dependency bridge to one SDK package.

        Contract:
        - Parent `ExperiencePackage` scope is injected by propagation.
        - Identity is keyed by the attached `SdkPackage`.
        - This declares SDK operation availability for Experience-owned view invocation actions.
        - SDK operation expansion remains SDK/API-owned; Experience owns the view action contract.
        """

        payload = {
            "experience_package_id": experience_package_id,
            "sdk_package_id": sdk_package_id,
            "description": description,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_experience_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ExperiencePackageSdkPackage):
            return value
        return ExperiencePackageSdkPackage.validate_invocation_value(value)


class ExperiencePackageSdkPackageBuildViaExperiencePackageInput(BaseModel):
    experience_package_id: UUID = Field(description="Foreign key for ExperiencePackage.sdk_packages")
    sdk_package_id: UUID
    description: str | None = Field(default=None)


class ExperiencePackageSdkPackageBuildViaExperiencePackageOutput(BaseModel):
    value: ExperiencePackageSdkPackage


FUNCTIONS = {
    "ExperiencePackageSdkPackage": {
        "build_via_experience_package": {
            "canonical": {
                "name": "build_via_experience_package",
                "description": "Create one package-level Experience dependency bridge to one SDK package.\n\nContract:\n- Parent `ExperiencePackage` scope is injected by propagation.\n- Identity is keyed by the attached `SdkPackage`.\n- This declares SDK operation availability for Experience-owned view invocation actions.\n- SDK operation expansion remains SDK/API-owned; Experience owns the view action contract.",
                "is_constructor": True,
            },
            "input": ExperiencePackageSdkPackageBuildViaExperiencePackageInput,
            "output": ExperiencePackageSdkPackageBuildViaExperiencePackageOutput,
        },
    },
}

__all__ = [
    "ExperiencePackageSdkPackage",
    "ExperiencePackageSdkPackageBuildViaExperiencePackageInput",
    "ExperiencePackageSdkPackageBuildViaExperiencePackageOutput",
    "FUNCTIONS",
]
