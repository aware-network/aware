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
    from aware_api_ontology.api.api_capability_endpoint import ApiCapabilityEndpoint


class SkillConfigApiEndpoint(ORMModel):
    # Relationships
    api_endpoint: ApiCapabilityEndpoint | None = Field(default=None)

    # Attributes
    capability_name: str
    description: str | None = Field(default=None)
    name: str

    # Foreign Keys
    skill_config_api_id: UUID = Field(description="Foreign key for SkillConfigApi.api_endpoints")
    api_endpoint_id: UUID = Field(description="Foreign key for SkillConfigApiEndpoint.api_endpoint")

    @classmethod
    async def build_via_skill_config_api(
        cls,
        skill_config_api_id: UUID,
        api_endpoint_id: UUID,
        capability_name: str,
        name: str,
        description: str | None = None,
    ) -> SkillConfigApiEndpoint:
        """
        Create one Skill-owned API endpoint requirement.

        Contract:
        - This object is Skill-owned endpoint requirement truth.
        - `capability_name` and `name` preserve Skill-owned selection identity.
        - It targets API-owned `ApiCapabilityEndpoint` invocation truth.
        - Projection routes the target through API's `Api` projection.
        """

        payload = {
            "skill_config_api_id": skill_config_api_id,
            "api_endpoint_id": api_endpoint_id,
            "capability_name": capability_name,
            "name": name,
            "description": description,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_skill_config_api", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, SkillConfigApiEndpoint):
            return value
        return SkillConfigApiEndpoint.validate_invocation_value(value)


class SkillConfigApiEndpointBuildViaSkillConfigApiInput(BaseModel):
    skill_config_api_id: UUID = Field(description="Foreign key for SkillConfigApi.api_endpoints")
    api_endpoint_id: UUID
    capability_name: str
    name: str
    description: str | None = Field(default=None)


class SkillConfigApiEndpointBuildViaSkillConfigApiOutput(BaseModel):
    value: SkillConfigApiEndpoint


FUNCTIONS = {
    "SkillConfigApiEndpoint": {
        "build_via_skill_config_api": {
            "canonical": {
                "name": "build_via_skill_config_api",
                "description": "Create one Skill-owned API endpoint requirement.\n\nContract:\n- This object is Skill-owned endpoint requirement truth.\n- `capability_name` and `name` preserve Skill-owned selection identity.\n- It targets API-owned `ApiCapabilityEndpoint` invocation truth.\n- Projection routes the target through API's `Api` projection.",
                "is_constructor": True,
            },
            "input": SkillConfigApiEndpointBuildViaSkillConfigApiInput,
            "output": SkillConfigApiEndpointBuildViaSkillConfigApiOutput,
        },
    },
}

__all__ = [
    "SkillConfigApiEndpoint",
    "SkillConfigApiEndpointBuildViaSkillConfigApiInput",
    "SkillConfigApiEndpointBuildViaSkillConfigApiOutput",
    "FUNCTIONS",
]
