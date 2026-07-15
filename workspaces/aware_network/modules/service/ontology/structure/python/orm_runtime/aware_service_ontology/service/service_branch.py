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
    from aware_meta_ontology.graph.instance.object_instance_graph_branch import ObjectInstanceGraphBranch
    from aware_service_ontology.service.service_config_api_projection import ServiceConfigApiProjection


class ServiceBranch(ORMModel):
    # Relationships
    service_config_api_projection: ServiceConfigApiProjection | None = Field(default=None, exclude=True)
    object_instance_graph_branch: ObjectInstanceGraphBranch | None = Field(default=None, exclude=True)

    # Attributes
    description: str | None = Field(default=None)

    # Foreign Keys
    service_id: UUID = Field(description="Foreign key for Service.branches")
    service_config_api_projection_id: UUID = Field(
        description="Foreign key for ServiceBranch.service_config_api_projection"
    )
    object_instance_graph_branch_id: UUID = Field(
        description="Foreign key for ServiceBranch.object_instance_graph_branch"
    )

    @classmethod
    async def build_via_service(
        cls,
        service_id: UUID,
        service_config_api_projection_id: UUID,
        object_instance_graph_branch_id: UUID,
        description: str | None = None,
    ) -> ServiceBranch:
        """Create one concrete service-instance branch binding for one subscribed API projection lane."""

        payload = {
            "service_id": service_id,
            "service_config_api_projection_id": service_config_api_projection_id,
            "object_instance_graph_branch_id": object_instance_graph_branch_id,
            "description": description,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_service", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ServiceBranch):
            return value
        return ServiceBranch.validate_invocation_value(value)


class ServiceBranchBuildViaServiceInput(BaseModel):
    service_id: UUID = Field(description="Foreign key for Service.branches")
    service_config_api_projection_id: UUID
    object_instance_graph_branch_id: UUID
    description: str | None = Field(default=None)


class ServiceBranchBuildViaServiceOutput(BaseModel):
    value: ServiceBranch


FUNCTIONS = {
    "ServiceBranch": {
        "build_via_service": {
            "canonical": {
                "name": "build_via_service",
                "description": "Create one concrete service-instance branch binding for one subscribed API projection lane.",
                "is_constructor": True,
            },
            "input": ServiceBranchBuildViaServiceInput,
            "output": ServiceBranchBuildViaServiceOutput,
        },
    },
}

__all__ = [
    "ServiceBranch",
    "ServiceBranchBuildViaServiceInput",
    "ServiceBranchBuildViaServiceOutput",
    "FUNCTIONS",
]
