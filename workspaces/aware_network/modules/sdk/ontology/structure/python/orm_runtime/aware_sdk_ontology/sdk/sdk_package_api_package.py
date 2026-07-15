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


class SdkPackageApiPackage(ORMModel):
    # Relationships
    api_package: ApiPackage | None = Field(default=None)

    # Attributes
    description: str | None = Field(default=None)

    # Foreign Keys
    sdk_package_id: UUID = Field(description="Foreign key for SdkPackage.api_packages")
    api_package_id: UUID = Field(description="Foreign key for SdkPackageApiPackage.api_package")

    @classmethod
    async def build_via_sdk_package(
        cls, sdk_package_id: UUID, api_package_id: UUID, description: str | None = None
    ) -> SdkPackageApiPackage:
        """
        Create one package-level SDK bridge to one API package.

        Contract:
        - Parent `SdkPackage` scope is injected by propagation.
        - Identity is keyed by the attached `ApiPackage`.
        - This is package/import truth; operation endpoint routing remains operation-owned.
        """

        payload = {"sdk_package_id": sdk_package_id, "api_package_id": api_package_id, "description": description}
        result = await invoke_constructor(orm_class=cls, function_name="build_via_sdk_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, SdkPackageApiPackage):
            return value
        return SdkPackageApiPackage.validate_invocation_value(value)


class SdkPackageApiPackageBuildViaSdkPackageInput(BaseModel):
    sdk_package_id: UUID = Field(description="Foreign key for SdkPackage.api_packages")
    api_package_id: UUID
    description: str | None = Field(default=None)


class SdkPackageApiPackageBuildViaSdkPackageOutput(BaseModel):
    value: SdkPackageApiPackage


FUNCTIONS = {
    "SdkPackageApiPackage": {
        "build_via_sdk_package": {
            "canonical": {
                "name": "build_via_sdk_package",
                "description": "Create one package-level SDK bridge to one API package.\n\nContract:\n- Parent `SdkPackage` scope is injected by propagation.\n- Identity is keyed by the attached `ApiPackage`.\n- This is package/import truth; operation endpoint routing remains operation-owned.",
                "is_constructor": True,
            },
            "input": SdkPackageApiPackageBuildViaSdkPackageInput,
            "output": SdkPackageApiPackageBuildViaSdkPackageOutput,
        },
    },
}

__all__ = [
    "SdkPackageApiPackage",
    "SdkPackageApiPackageBuildViaSdkPackageInput",
    "SdkPackageApiPackageBuildViaSdkPackageOutput",
    "FUNCTIONS",
]
