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
    from aware_api_ontology.api.api_package_language_package import ApiPackageLanguagePackage
    from aware_meta_ontology.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit


class ServicePackageProvidedApiPackage(ORMModel):
    # Relationships
    api_package: ApiPackage | None = Field(default=None)
    api_package_object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None)
    service_protocol_package: ApiPackageLanguagePackage | None = Field(default=None)

    # Attributes
    service_protocol_plan_hash_sha256: str
    description: str | None = Field(default=None)

    # Foreign Keys
    service_package_id: UUID = Field(description="Foreign key for ServicePackage.provided_api_packages")
    api_package_id: UUID = Field(description="Foreign key for ServicePackageProvidedApiPackage.api_package")
    api_package_object_instance_graph_commit_id: UUID = Field(
        description="Foreign key for ServicePackageProvidedApiPackage.api_package_object_instance_graph_commit"
    )
    service_protocol_package_id: UUID = Field(
        description="Foreign key for ServicePackageProvidedApiPackage.service_protocol_package"
    )

    @classmethod
    async def build_via_service_package(
        cls,
        service_package_id: UUID,
        api_package_id: UUID,
        service_protocol_package_id: UUID,
        service_protocol_plan_hash_sha256: str,
        api_package_object_instance_graph_commit_id: UUID,
        description: str | None = None,
    ) -> ServicePackageProvidedApiPackage:
        """
        Create one package-level Service provider bridge to one API package.

        Contract:
        - Parent `ServicePackage` scope is injected by propagation.
        - Identity is keyed by the attached `ApiPackage`.
        - This declares that the Service package provides/hosts this API package.
        - The API package commit, selected API-owned service-protocol language
          package, and normalized protocol-plan digest are materialized
          dependency-lock truth. They are not authored `aware.service.toml` pins.
        - The selected `ApiPackageLanguagePackage` owns the exact generated
          CodePackage commit pin.
        - Commit relationships may remain unresolved in this projection while
          their UUID pins preserve exact cross-graph replay identity.
        - It is the package-level counterpart to config-level `ServiceConfigApi` fulfillment.
        """

        payload = {
            "service_package_id": service_package_id,
            "api_package_id": api_package_id,
            "service_protocol_package_id": service_protocol_package_id,
            "service_protocol_plan_hash_sha256": service_protocol_plan_hash_sha256,
            "api_package_object_instance_graph_commit_id": api_package_object_instance_graph_commit_id,
            "description": description,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_service_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ServicePackageProvidedApiPackage):
            return value
        return ServicePackageProvidedApiPackage.validate_invocation_value(value)


class ServicePackageProvidedApiPackageBuildViaServicePackageInput(BaseModel):
    service_package_id: UUID = Field(description="Foreign key for ServicePackage.provided_api_packages")
    api_package_id: UUID
    service_protocol_package_id: UUID
    service_protocol_plan_hash_sha256: str
    api_package_object_instance_graph_commit_id: UUID
    description: str | None = Field(default=None)


class ServicePackageProvidedApiPackageBuildViaServicePackageOutput(BaseModel):
    value: ServicePackageProvidedApiPackage


FUNCTIONS = {
    "ServicePackageProvidedApiPackage": {
        "build_via_service_package": {
            "canonical": {
                "name": "build_via_service_package",
                "description": "Create one package-level Service provider bridge to one API package.\n\nContract:\n- Parent `ServicePackage` scope is injected by propagation.\n- Identity is keyed by the attached `ApiPackage`.\n- This declares that the Service package provides/hosts this API package.\n- The API package commit, selected API-owned service-protocol language\n  package, and normalized protocol-plan digest are materialized\n  dependency-lock truth. They are not authored `aware.service.toml` pins.\n- The selected `ApiPackageLanguagePackage` owns the exact generated\n  CodePackage commit pin.\n- Commit relationships may remain unresolved in this projection while\n  their UUID pins preserve exact cross-graph replay identity.\n- It is the package-level counterpart to config-level `ServiceConfigApi` fulfillment.",
                "is_constructor": True,
            },
            "input": ServicePackageProvidedApiPackageBuildViaServicePackageInput,
            "output": ServicePackageProvidedApiPackageBuildViaServicePackageOutput,
        },
    },
}

__all__ = [
    "ServicePackageProvidedApiPackage",
    "ServicePackageProvidedApiPackageBuildViaServicePackageInput",
    "ServicePackageProvidedApiPackageBuildViaServicePackageOutput",
    "FUNCTIONS",
]
