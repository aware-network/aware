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
    from aware_experience_ontology.projection.projection_experience import ProjectionExperience
    from aware_skill_ontology.skill.skill_config_target import SkillConfigTarget


class SkillConfigExperience(ORMModel):
    # Relationships
    projection_experience: ProjectionExperience | None = Field(default=None)
    targets: list[SkillConfigTarget] = Field(default_factory=list)

    # Attributes
    description: str | None = Field(default=None)

    # Foreign Keys
    skill_config_id: UUID = Field(description="Foreign key for SkillConfig.experiences")
    projection_experience_id: UUID = Field(description="Foreign key for SkillConfigExperience.projection_experience")

    async def add_target(
        self, projection_experience_graph_identity_id: UUID, name: str, description: str | None = None
    ) -> SkillConfigTarget:
        """Add one reusable Skill target bound to an Experience graph identity."""

        payload = {
            "projection_experience_graph_identity_id": projection_experience_graph_identity_id,
            "name": name,
            "description": description,
        }
        result = await invoke_instance(orm_model=self, function_name="add_target", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_skill_ontology.skill.skill_config_target import SkillConfigTarget

        if isinstance(value, SkillConfigTarget):
            return value
        return SkillConfigTarget.validate_invocation_value(value)

    @classmethod
    async def build_via_skill_config(
        cls, skill_config_id: UUID, projection_experience_id: UUID, description: str | None = None
    ) -> SkillConfigExperience:
        """
        Create one Skill-owned bridge to an Experience projection namespace.

        Contract:
        - Skill owns that this SkillConfig may use the Experience namespace.
        - Experience owns graph identity/profile resolution under that namespace.
        """

        payload = {
            "skill_config_id": skill_config_id,
            "projection_experience_id": projection_experience_id,
            "description": description,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_skill_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, SkillConfigExperience):
            return value
        return SkillConfigExperience.validate_invocation_value(value)


class SkillConfigExperienceAddTargetInput(BaseModel):
    projection_experience_graph_identity_id: UUID
    name: str
    description: str | None = Field(default=None)


class SkillConfigExperienceAddTargetOutput(BaseModel):
    value: SkillConfigTarget


class SkillConfigExperienceBuildViaSkillConfigInput(BaseModel):
    skill_config_id: UUID = Field(description="Foreign key for SkillConfig.experiences")
    projection_experience_id: UUID
    description: str | None = Field(default=None)


class SkillConfigExperienceBuildViaSkillConfigOutput(BaseModel):
    value: SkillConfigExperience


FUNCTIONS = {
    "SkillConfigExperience": {
        "add_target": {
            "canonical": {
                "name": "add_target",
                "description": "Add one reusable Skill target bound to an Experience graph identity.",
                "is_constructor": False,
            },
            "input": SkillConfigExperienceAddTargetInput,
            "output": SkillConfigExperienceAddTargetOutput,
        },
        "build_via_skill_config": {
            "canonical": {
                "name": "build_via_skill_config",
                "description": "Create one Skill-owned bridge to an Experience projection namespace.\n\nContract:\n- Skill owns that this SkillConfig may use the Experience namespace.\n- Experience owns graph identity/profile resolution under that namespace.",
                "is_constructor": True,
            },
            "input": SkillConfigExperienceBuildViaSkillConfigInput,
            "output": SkillConfigExperienceBuildViaSkillConfigOutput,
        },
    },
}

__all__ = [
    "SkillConfigExperience",
    "SkillConfigExperienceAddTargetInput",
    "SkillConfigExperienceAddTargetOutput",
    "SkillConfigExperienceBuildViaSkillConfigInput",
    "SkillConfigExperienceBuildViaSkillConfigOutput",
    "FUNCTIONS",
]
