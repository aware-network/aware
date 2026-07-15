from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor


class ProjectionExperienceViewStateProvider(ORMModel):
    """
    Experience-owned view-state provider binding.
    Contract:
    - There is one effective provider per ProjectionExperienceView.
    - The provider is a pure read transformation from host-owned materialized state to the view state model.
    - Runtime callables and SDK functions are implementation adapters selected by this canonical binding.
    """

    # Attributes
    provider_ref: str
    provider_kind: str = Field(default="runtime_callable")
    purity: str = Field(default="pure_read")

    # Foreign Keys
    projection_experience_view_id: UUID = Field(description="Foreign key for ProjectionExperienceView.state_providers")

    @classmethod
    async def build_via_projection_experience_view(
        cls,
        projection_experience_view_id: UUID,
        provider_ref: str,
        provider_kind: str = "runtime_callable",
        purity: str = "pure_read",
    ) -> ProjectionExperienceViewStateProvider:
        """
        Create the deterministic provider binding under one ProjectionExperienceView.

        Contract:
        - Parent ProjectionExperienceView scope is propagated by constructor lowering.
        - Identity is the parent view; changing provider_ref is a semantic migration.
        """

        payload = {
            "projection_experience_view_id": projection_experience_view_id,
            "provider_ref": provider_ref,
            "provider_kind": provider_kind,
            "purity": purity,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_projection_experience_view", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProjectionExperienceViewStateProvider):
            return value
        return ProjectionExperienceViewStateProvider.validate_invocation_value(value)


class ProjectionExperienceViewStateProviderBuildViaProjectionExperienceViewInput(BaseModel):
    projection_experience_view_id: UUID = Field(description="Foreign key for ProjectionExperienceView.state_providers")
    provider_ref: str
    provider_kind: str = Field(default="runtime_callable")
    purity: str = Field(default="pure_read")


class ProjectionExperienceViewStateProviderBuildViaProjectionExperienceViewOutput(BaseModel):
    value: ProjectionExperienceViewStateProvider


FUNCTIONS = {
    "ProjectionExperienceViewStateProvider": {
        "build_via_projection_experience_view": {
            "canonical": {
                "name": "build_via_projection_experience_view",
                "description": "Create the deterministic provider binding under one ProjectionExperienceView.\n\nContract:\n- Parent ProjectionExperienceView scope is propagated by constructor lowering.\n- Identity is the parent view; changing provider_ref is a semantic migration.",
                "is_constructor": True,
            },
            "input": ProjectionExperienceViewStateProviderBuildViaProjectionExperienceViewInput,
            "output": ProjectionExperienceViewStateProviderBuildViaProjectionExperienceViewOutput,
        },
    },
}

__all__ = [
    "ProjectionExperienceViewStateProvider",
    "ProjectionExperienceViewStateProviderBuildViaProjectionExperienceViewInput",
    "ProjectionExperienceViewStateProviderBuildViaProjectionExperienceViewOutput",
    "FUNCTIONS",
]
