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
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_service_ontology.service.service_api_provider_set_service_package import (
        ServiceApiProviderSetServicePackage,
    )


class ServiceApiProviderSet(ORMModel):
    # Relationships
    service_packages: list[ServiceApiProviderSetServicePackage] = Field(default_factory=list)

    # Attributes
    description: str | None = Field(default=None)
    key: str
    title: str | None = Field(default=None)
    version_number: int = Field(default=1)

    @classmethod
    async def build(
        cls, key: str, title: str | None = None, description: str | None = None, version_number: int = 1
    ) -> ServiceApiProviderSet:
        """
        Create one Service-owned API provider set.

        Contract:
        - Identity is keyed by a stable provider-set key, for example `kernel.global_services.v1`.
        - A provider set groups committed ServicePackage roots that may fulfill API calls remotely.
        - Deployment artifacts may project this object into runtime provider refs, but the semantic
          truth is the committed provider-set object and its ServicePackage memberships.
        """

        payload = {"key": key, "title": title, "description": description, "version_number": version_number}
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ServiceApiProviderSet):
            return value
        return ServiceApiProviderSet.validate_invocation_value(value)

    async def attach_service_package(
        self, service_package_id: UUID, membership_key: str | None = None, description: str | None = None
    ) -> ServiceApiProviderSetServicePackage:
        """
        Attach one committed ServicePackage to this API provider set.

        Contract:
        - Parent `ServiceApiProviderSet` scope is injected by propagation.
        - Identity is keyed by the attached `ServicePackage`.
        - This declares provider-set membership only; API fulfillment still comes from the
          ServicePackage provided-api bridges.
        """

        payload = {
            "service_package_id": service_package_id,
            "membership_key": membership_key,
            "description": description,
        }
        result = await invoke_instance(orm_model=self, function_name="attach_service_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_service_ontology.service.service_api_provider_set_service_package import (
            ServiceApiProviderSetServicePackage,
        )

        if isinstance(value, ServiceApiProviderSetServicePackage):
            return value
        return ServiceApiProviderSetServicePackage.validate_invocation_value(value)


class ServiceApiProviderSetBuildInput(BaseModel):
    key: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    version_number: int = Field(default=1)


class ServiceApiProviderSetBuildOutput(BaseModel):
    value: ServiceApiProviderSet


class ServiceApiProviderSetAttachServicePackageInput(BaseModel):
    service_package_id: UUID
    membership_key: str | None = Field(default=None)
    description: str | None = Field(default=None)


class ServiceApiProviderSetAttachServicePackageOutput(BaseModel):
    value: ServiceApiProviderSetServicePackage


FUNCTIONS = {
    "ServiceApiProviderSet": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Create one Service-owned API provider set.\n\nContract:\n- Identity is keyed by a stable provider-set key, for example `kernel.global_services.v1`.\n- A provider set groups committed ServicePackage roots that may fulfill API calls remotely.\n- Deployment artifacts may project this object into runtime provider refs, but the semantic\n  truth is the committed provider-set object and its ServicePackage memberships.",
                "is_constructor": True,
            },
            "input": ServiceApiProviderSetBuildInput,
            "output": ServiceApiProviderSetBuildOutput,
        },
        "attach_service_package": {
            "canonical": {
                "name": "attach_service_package",
                "description": "Attach one committed ServicePackage to this API provider set.\n\nContract:\n- Parent `ServiceApiProviderSet` scope is injected by propagation.\n- Identity is keyed by the attached `ServicePackage`.\n- This declares provider-set membership only; API fulfillment still comes from the\n  ServicePackage provided-api bridges.",
                "is_constructor": False,
            },
            "input": ServiceApiProviderSetAttachServicePackageInput,
            "output": ServiceApiProviderSetAttachServicePackageOutput,
        },
    },
}

__all__ = [
    "ServiceApiProviderSet",
    "ServiceApiProviderSetBuildInput",
    "ServiceApiProviderSetBuildOutput",
    "ServiceApiProviderSetAttachServicePackageInput",
    "ServiceApiProviderSetAttachServicePackageOutput",
    "FUNCTIONS",
]
