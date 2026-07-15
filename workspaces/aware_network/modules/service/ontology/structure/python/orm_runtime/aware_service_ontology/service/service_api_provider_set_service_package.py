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
    from aware_service_ontology.service.service_package import ServicePackage


class ServiceApiProviderSetServicePackage(ORMModel):
    # Relationships
    service_package: ServicePackage | None = Field(default=None)

    # Attributes
    description: str | None = Field(default=None)
    membership_key: str | None = Field(default=None)

    # Foreign Keys
    service_api_provider_set_id: UUID = Field(description="Foreign key for ServiceApiProviderSet.service_packages")
    service_package_id: UUID = Field(description="Foreign key for ServiceApiProviderSetServicePackage.service_package")

    @classmethod
    async def build_via_service_api_provider_set(
        cls,
        service_api_provider_set_id: UUID,
        service_package_id: UUID,
        membership_key: str | None = None,
        description: str | None = None,
    ) -> ServiceApiProviderSetServicePackage:
        """
        Create one provider-set membership bridge to a committed ServicePackage.

        Contract:
        - Parent `ServiceApiProviderSet` scope is injected by propagation.
        - Identity is keyed by the attached `ServicePackage`.
        - The optional `membership_key` is descriptive routing provenance, not identity.
        """

        payload = {
            "service_api_provider_set_id": service_api_provider_set_id,
            "service_package_id": service_package_id,
            "membership_key": membership_key,
            "description": description,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_service_api_provider_set", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ServiceApiProviderSetServicePackage):
            return value
        return ServiceApiProviderSetServicePackage.validate_invocation_value(value)


class ServiceApiProviderSetServicePackageBuildViaServiceApiProviderSetInput(BaseModel):
    service_api_provider_set_id: UUID = Field(description="Foreign key for ServiceApiProviderSet.service_packages")
    service_package_id: UUID
    membership_key: str | None = Field(default=None)
    description: str | None = Field(default=None)


class ServiceApiProviderSetServicePackageBuildViaServiceApiProviderSetOutput(BaseModel):
    value: ServiceApiProviderSetServicePackage


FUNCTIONS = {
    "ServiceApiProviderSetServicePackage": {
        "build_via_service_api_provider_set": {
            "canonical": {
                "name": "build_via_service_api_provider_set",
                "description": "Create one provider-set membership bridge to a committed ServicePackage.\n\nContract:\n- Parent `ServiceApiProviderSet` scope is injected by propagation.\n- Identity is keyed by the attached `ServicePackage`.\n- The optional `membership_key` is descriptive routing provenance, not identity.",
                "is_constructor": True,
            },
            "input": ServiceApiProviderSetServicePackageBuildViaServiceApiProviderSetInput,
            "output": ServiceApiProviderSetServicePackageBuildViaServiceApiProviderSetOutput,
        },
    },
}

__all__ = [
    "ServiceApiProviderSetServicePackage",
    "ServiceApiProviderSetServicePackageBuildViaServiceApiProviderSetInput",
    "ServiceApiProviderSetServicePackageBuildViaServiceApiProviderSetOutput",
    "FUNCTIONS",
]
