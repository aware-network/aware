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
    from aware_experience_ontology.environment.environment_experience_event import EnvironmentExperienceEvent
    from aware_experience_ontology.projection.projection_experience_section_graph_binding import (
        ProjectionExperienceSectionGraphBinding,
    )
    from aware_experience_ontology.projection.projection_experience_view import ProjectionExperienceView


class EnvironmentExperienceViewEventTransition(ORMModel):
    """
    Experience-owned View -> Event -> View transition policy.
    Contract:
    - Source view is the focused Experience projection view.
    - Trigger event is the profile-owned Reactivity event binding.
    - Target is the section-graph binding that resolves the next view + graph occurrence
    + Attention layout section.
    - This object never references Attention directly.
    """

    # Relationships
    source_view: ProjectionExperienceView | None = Field(default=None, exclude=True)
    trigger_event: EnvironmentExperienceEvent | None = Field(default=None, exclude=True)
    target_section_graph_binding: ProjectionExperienceSectionGraphBinding | None = Field(default=None, exclude=True)

    # Attributes
    transition_key: str
    name: str | None = Field(default=None)
    rationale: str | None = Field(default=None)
    idempotency_policy: str | None = Field(default=None)

    # Foreign Keys
    environment_experience_profile_config_id: UUID = Field(
        description="Foreign key for EnvironmentExperienceProfileConfig.view_event_transitions"
    )
    source_view_id: UUID = Field(description="Foreign key for EnvironmentExperienceViewEventTransition.source_view")
    trigger_event_id: UUID = Field(description="Foreign key for EnvironmentExperienceViewEventTransition.trigger_event")
    target_section_graph_binding_id: UUID = Field(
        description="Foreign key for EnvironmentExperienceViewEventTransition.target_section_graph_binding"
    )

    @classmethod
    async def build_via_environment_experience_profile_config(
        cls,
        environment_experience_profile_config_id: UUID,
        source_view_id: UUID,
        trigger_event_id: UUID,
        target_section_graph_binding_id: UUID,
        transition_key: str,
        name: str | None = None,
        rationale: str | None = None,
        idempotency_policy: str | None = None,
    ) -> EnvironmentExperienceViewEventTransition:
        """
        Construct one deterministic profile-owned ViewEventTransition.

        Notes:
        - Identity is derived from `(environment_experience_profile_config_id, source_view_id,
          trigger_event_id, target_section_graph_binding_id, transition_key)`.
        - `target_section_graph_binding` is the only transition target rail. Attention focus
          activation is resolved later through that binding.
        """

        payload = {
            "environment_experience_profile_config_id": environment_experience_profile_config_id,
            "source_view_id": source_view_id,
            "trigger_event_id": trigger_event_id,
            "target_section_graph_binding_id": target_section_graph_binding_id,
            "transition_key": transition_key,
            "name": name,
            "rationale": rationale,
            "idempotency_policy": idempotency_policy,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_environment_experience_profile_config", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, EnvironmentExperienceViewEventTransition):
            return value
        return EnvironmentExperienceViewEventTransition.validate_invocation_value(value)


class EnvironmentExperienceViewEventTransitionBuildViaEnvironmentExperienceProfileConfigInput(BaseModel):
    environment_experience_profile_config_id: UUID = Field(
        description="Foreign key for EnvironmentExperienceProfileConfig.view_event_transitions"
    )
    source_view_id: UUID
    trigger_event_id: UUID
    target_section_graph_binding_id: UUID
    transition_key: str
    name: str | None = Field(default=None)
    rationale: str | None = Field(default=None)
    idempotency_policy: str | None = Field(default=None)


class EnvironmentExperienceViewEventTransitionBuildViaEnvironmentExperienceProfileConfigOutput(BaseModel):
    value: EnvironmentExperienceViewEventTransition


FUNCTIONS = {
    "EnvironmentExperienceViewEventTransition": {
        "build_via_environment_experience_profile_config": {
            "canonical": {
                "name": "build_via_environment_experience_profile_config",
                "description": "Construct one deterministic profile-owned ViewEventTransition.\n\nNotes:\n- Identity is derived from `(environment_experience_profile_config_id, source_view_id,\n  trigger_event_id, target_section_graph_binding_id, transition_key)`.\n- `target_section_graph_binding` is the only transition target rail. Attention focus\n  activation is resolved later through that binding.",
                "is_constructor": True,
            },
            "input": EnvironmentExperienceViewEventTransitionBuildViaEnvironmentExperienceProfileConfigInput,
            "output": EnvironmentExperienceViewEventTransitionBuildViaEnvironmentExperienceProfileConfigOutput,
        },
    },
}

__all__ = [
    "EnvironmentExperienceViewEventTransition",
    "EnvironmentExperienceViewEventTransitionBuildViaEnvironmentExperienceProfileConfigInput",
    "EnvironmentExperienceViewEventTransitionBuildViaEnvironmentExperienceProfileConfigOutput",
    "FUNCTIONS",
]
