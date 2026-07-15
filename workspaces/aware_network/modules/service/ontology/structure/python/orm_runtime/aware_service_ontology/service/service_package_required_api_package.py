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


class ServicePackageRequiredApiPackage(ORMModel):
    # Relationships
    api_package: ApiPackage | None = Field(default=None)

    # Attributes
    description: str | None = Field(default=None)

    # Foreign Keys
    service_package_id: UUID = Field(description="Foreign key for ServicePackage.required_api_packages")
    api_package_id: UUID = Field(description="Foreign key for ServicePackageRequiredApiPackage.api_package")

    @classmethod
    async def build_via_service_package(
        cls, service_package_id: UUID, api_package_id: UUID, description: str | None = None
    ) -> ServicePackageRequiredApiPackage:
        """
        Create one package-level Service consumer bridge to one API package.

        Contract:
        - Parent `ServicePackage` scope is injected by propagation.
        - Identity is keyed by the attached `ApiPackage`.
        - This declares that the Service package requires/invokes this API package.
        - It does not imply this Service package provides or hosts the API.
        """

        payload = {
            "service_package_id": service_package_id,
            "api_package_id": api_package_id,
            "description": description,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_service_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ServicePackageRequiredApiPackage):
            return value
        return ServicePackageRequiredApiPackage.validate_invocation_value(value)


class ServicePackageRequiredApiPackageBuildViaServicePackageInput(BaseModel):
    service_package_id: UUID = Field(description="Foreign key for ServicePackage.required_api_packages")
    api_package_id: UUID
    description: str | None = Field(default=None)


class ServicePackageRequiredApiPackageBuildViaServicePackageOutput(BaseModel):
    value: ServicePackageRequiredApiPackage


FUNCTIONS = {
    "ServicePackageRequiredApiPackage": {
        "build_via_service_package": {
            "canonical": {
                "name": "build_via_service_package",
                "description": "Create one package-level Service consumer bridge to one API package.\n\nContract:\n- Parent `ServicePackage` scope is injected by propagation.\n- Identity is keyed by the attached `ApiPackage`.\n- This declares that the Service package requires/invokes this API package.\n- It does not imply this Service package provides or hosts the API.",
                "is_constructor": True,
            },
            "input": ServicePackageRequiredApiPackageBuildViaServicePackageInput,
            "output": ServicePackageRequiredApiPackageBuildViaServicePackageOutput,
        },
    },
}

__all__ = [
    "ServicePackageRequiredApiPackage",
    "ServicePackageRequiredApiPackageBuildViaServicePackageInput",
    "ServicePackageRequiredApiPackageBuildViaServicePackageOutput",
    "FUNCTIONS",
]
