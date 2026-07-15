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
    from aware_experience_ontology.projection.projection_experience import ProjectionExperience


class ServiceConfigExperience(ORMModel):
    # Relationships
    projection_experience: ProjectionExperience | None = Field(default=None, exclude=True)

    # Attributes
    description: str | None = Field(default=None)

    # Foreign Keys
    service_config_id: UUID = Field(description="Foreign key for ServiceConfig.experiences")
    projection_experience_id: UUID = Field(description="Foreign key for ServiceConfigExperience.projection_experience")

    @classmethod
    async def build_via_service_config(
        cls, service_config_id: UUID, projection_experience_id: UUID, description: str | None = None
    ) -> ServiceConfigExperience:
        """Create one config-level bridge between a ServiceConfig and one shared ProjectionExperience."""

        payload = {
            "service_config_id": service_config_id,
            "projection_experience_id": projection_experience_id,
            "description": description,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_service_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ServiceConfigExperience):
            return value
        return ServiceConfigExperience.validate_invocation_value(value)


class ServiceConfigExperienceBuildViaServiceConfigInput(BaseModel):
    service_config_id: UUID = Field(description="Foreign key for ServiceConfig.experiences")
    projection_experience_id: UUID
    description: str | None = Field(default=None)


class ServiceConfigExperienceBuildViaServiceConfigOutput(BaseModel):
    value: ServiceConfigExperience


FUNCTIONS = {
    "ServiceConfigExperience": {
        "build_via_service_config": {
            "canonical": {
                "name": "build_via_service_config",
                "description": "Create one config-level bridge between a ServiceConfig and one shared ProjectionExperience.",
                "is_constructor": True,
            },
            "input": ServiceConfigExperienceBuildViaServiceConfigInput,
            "output": ServiceConfigExperienceBuildViaServiceConfigOutput,
        },
    },
}

__all__ = [
    "ServiceConfigExperience",
    "ServiceConfigExperienceBuildViaServiceConfigInput",
    "ServiceConfigExperienceBuildViaServiceConfigOutput",
    "FUNCTIONS",
]
