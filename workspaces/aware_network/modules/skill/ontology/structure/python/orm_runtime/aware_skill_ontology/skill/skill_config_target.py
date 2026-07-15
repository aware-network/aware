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
    from aware_experience_ontology.projection.projection_experience_graph_identity import (
        ProjectionExperienceGraphIdentity,
    )


class SkillConfigTarget(ORMModel):
    # Relationships
    projection_experience_graph_identity: ProjectionExperienceGraphIdentity | None = Field(default=None)

    # Attributes
    description: str | None = Field(default=None)
    name: str

    # Foreign Keys
    skill_config_experience_id: UUID = Field(description="Foreign key for SkillConfigExperience.targets")
    projection_experience_graph_identity_id: UUID = Field(
        description="Foreign key for SkillConfigTarget.projection_experience_graph_identity"
    )

    @classmethod
    async def build_via_skill_config_experience(
        cls,
        skill_config_experience_id: UUID,
        projection_experience_graph_identity_id: UUID,
        name: str,
        description: str | None = None,
    ) -> SkillConfigTarget:
        """
        Create one Skill-owned target alias over an Experience graph identity.

        Contract:
        - `name` is the Skill-local alias used by authored steps.
        - `projection_experience_graph_identity` is Experience-owned semantic target truth.
        """

        payload = {
            "skill_config_experience_id": skill_config_experience_id,
            "projection_experience_graph_identity_id": projection_experience_graph_identity_id,
            "name": name,
            "description": description,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_skill_config_experience", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, SkillConfigTarget):
            return value
        return SkillConfigTarget.validate_invocation_value(value)


class SkillConfigTargetBuildViaSkillConfigExperienceInput(BaseModel):
    skill_config_experience_id: UUID = Field(description="Foreign key for SkillConfigExperience.targets")
    projection_experience_graph_identity_id: UUID
    name: str
    description: str | None = Field(default=None)


class SkillConfigTargetBuildViaSkillConfigExperienceOutput(BaseModel):
    value: SkillConfigTarget


FUNCTIONS = {
    "SkillConfigTarget": {
        "build_via_skill_config_experience": {
            "canonical": {
                "name": "build_via_skill_config_experience",
                "description": "Create one Skill-owned target alias over an Experience graph identity.\n\nContract:\n- `name` is the Skill-local alias used by authored steps.\n- `projection_experience_graph_identity` is Experience-owned semantic target truth.",
                "is_constructor": True,
            },
            "input": SkillConfigTargetBuildViaSkillConfigExperienceInput,
            "output": SkillConfigTargetBuildViaSkillConfigExperienceOutput,
        },
    },
}

__all__ = [
    "SkillConfigTarget",
    "SkillConfigTargetBuildViaSkillConfigExperienceInput",
    "SkillConfigTargetBuildViaSkillConfigExperienceOutput",
    "FUNCTIONS",
]
