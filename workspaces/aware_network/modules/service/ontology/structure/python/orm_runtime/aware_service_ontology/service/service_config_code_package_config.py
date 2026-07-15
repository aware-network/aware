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

# Service Ontology
from aware_service_ontology.service.service_enums import ServiceConfigCodePackageConfigCardinality

if TYPE_CHECKING:
    from aware_code_ontology.package.code_package_config import CodePackageConfig


class ServiceConfigCodePackageConfig(ORMModel):
    # Relationships
    code_package_config: CodePackageConfig | None = Field(default=None, exclude=True)

    # Attributes
    slot_key: str
    cardinality: ServiceConfigCodePackageConfigCardinality = Field(
        default=ServiceConfigCodePackageConfigCardinality.many
    )
    required: bool = Field(default=False)
    description: str | None = Field(default=None)

    # Foreign Keys
    service_config_id: UUID = Field(description="Foreign key for ServiceConfig.code_package_configs")
    code_package_config_id: UUID = Field(
        description="Foreign key for ServiceConfigCodePackageConfig.code_package_config"
    )

    @classmethod
    async def build_via_service_config(
        cls,
        service_config_id: UUID,
        slot_key: str,
        code_package_config_id: UUID,
        cardinality: ServiceConfigCodePackageConfigCardinality = ServiceConfigCodePackageConfigCardinality.many,
        required: bool = False,
        description: str | None = None,
    ) -> ServiceConfigCodePackageConfig:
        """
        Create one config-level bridge between a ServiceConfig and one hostable CodePackageConfig.

        Contract:
        - Parent ServiceConfig scope is injected by propagation.
        - The bridge declares service capability only.
        - Concrete CodePackage activation is Node/deployment-specific and must not be inferred here.
        """

        payload = {
            "service_config_id": service_config_id,
            "slot_key": slot_key,
            "code_package_config_id": code_package_config_id,
            "cardinality": cardinality,
            "required": required,
            "description": description,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_service_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ServiceConfigCodePackageConfig):
            return value
        return ServiceConfigCodePackageConfig.validate_invocation_value(value)


class ServiceConfigCodePackageConfigBuildViaServiceConfigInput(BaseModel):
    service_config_id: UUID = Field(description="Foreign key for ServiceConfig.code_package_configs")
    slot_key: str
    code_package_config_id: UUID
    cardinality: ServiceConfigCodePackageConfigCardinality = Field(
        default=ServiceConfigCodePackageConfigCardinality.many
    )
    required: bool = Field(default=False)
    description: str | None = Field(default=None)


class ServiceConfigCodePackageConfigBuildViaServiceConfigOutput(BaseModel):
    value: ServiceConfigCodePackageConfig


FUNCTIONS = {
    "ServiceConfigCodePackageConfig": {
        "build_via_service_config": {
            "canonical": {
                "name": "build_via_service_config",
                "description": "Create one config-level bridge between a ServiceConfig and one hostable CodePackageConfig.\n\nContract:\n- Parent ServiceConfig scope is injected by propagation.\n- The bridge declares service capability only.\n- Concrete CodePackage activation is Node/deployment-specific and must not be inferred here.",
                "is_constructor": True,
            },
            "input": ServiceConfigCodePackageConfigBuildViaServiceConfigInput,
            "output": ServiceConfigCodePackageConfigBuildViaServiceConfigOutput,
        },
    },
}

__all__ = [
    "ServiceConfigCodePackageConfig",
    "ServiceConfigCodePackageConfigBuildViaServiceConfigInput",
    "ServiceConfigCodePackageConfigBuildViaServiceConfigOutput",
    "FUNCTIONS",
]
