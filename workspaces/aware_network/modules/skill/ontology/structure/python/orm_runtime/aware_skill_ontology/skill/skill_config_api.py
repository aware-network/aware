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
    from aware_api_ontology.api.api import Api
    from aware_skill_ontology.skill.skill_config_api_endpoint import SkillConfigApiEndpoint


class SkillConfigApi(ORMModel):
    # Relationships
    api: Api | None = Field(default=None)
    api_endpoints: list[SkillConfigApiEndpoint] = Field(default_factory=list)

    # Attributes
    description: str | None = Field(default=None)

    # Foreign Keys
    skill_config_id: UUID = Field(description="Foreign key for SkillConfig.apis")
    api_id: UUID = Field(description="Foreign key for SkillConfigApi.api")

    async def add_api_endpoint(
        self, api_endpoint_id: UUID, capability_name: str, name: str, description: str | None = None
    ) -> SkillConfigApiEndpoint:
        """Add one Skill-owned API endpoint requirement under this API grouping."""

        payload = {
            "api_endpoint_id": api_endpoint_id,
            "capability_name": capability_name,
            "name": name,
            "description": description,
        }
        result = await invoke_instance(orm_model=self, function_name="add_api_endpoint", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_skill_ontology.skill.skill_config_api_endpoint import SkillConfigApiEndpoint

        if isinstance(value, SkillConfigApiEndpoint):
            return value
        return SkillConfigApiEndpoint.validate_invocation_value(value)

    @classmethod
    async def build_via_skill_config(
        cls, skill_config_id: UUID, api_id: UUID, description: str | None = None
    ) -> SkillConfigApi:
        """Create one Skill-level API grouping."""

        payload = {"skill_config_id": skill_config_id, "api_id": api_id, "description": description}
        result = await invoke_constructor(orm_class=cls, function_name="build_via_skill_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, SkillConfigApi):
            return value
        return SkillConfigApi.validate_invocation_value(value)


class SkillConfigApiAddApiEndpointInput(BaseModel):
    api_endpoint_id: UUID
    capability_name: str
    name: str
    description: str | None = Field(default=None)


class SkillConfigApiAddApiEndpointOutput(BaseModel):
    value: SkillConfigApiEndpoint


class SkillConfigApiBuildViaSkillConfigInput(BaseModel):
    skill_config_id: UUID = Field(description="Foreign key for SkillConfig.apis")
    api_id: UUID
    description: str | None = Field(default=None)


class SkillConfigApiBuildViaSkillConfigOutput(BaseModel):
    value: SkillConfigApi


FUNCTIONS = {
    "SkillConfigApi": {
        "add_api_endpoint": {
            "canonical": {
                "name": "add_api_endpoint",
                "description": "Add one Skill-owned API endpoint requirement under this API grouping.",
                "is_constructor": False,
            },
            "input": SkillConfigApiAddApiEndpointInput,
            "output": SkillConfigApiAddApiEndpointOutput,
        },
        "build_via_skill_config": {
            "canonical": {
                "name": "build_via_skill_config",
                "description": "Create one Skill-level API grouping.",
                "is_constructor": True,
            },
            "input": SkillConfigApiBuildViaSkillConfigInput,
            "output": SkillConfigApiBuildViaSkillConfigOutput,
        },
    },
}

__all__ = [
    "SkillConfigApi",
    "SkillConfigApiAddApiEndpointInput",
    "SkillConfigApiAddApiEndpointOutput",
    "SkillConfigApiBuildViaSkillConfigInput",
    "SkillConfigApiBuildViaSkillConfigOutput",
    "FUNCTIONS",
]
