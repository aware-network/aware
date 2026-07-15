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
    from aware_experience_ontology.projection.projection_experience_view import ProjectionExperienceView


class PaneConfig(ORMModel):
    # Relationships
    projection_experience_view: ProjectionExperienceView | None = Field(default=None, exclude=True)

    # Attributes
    name: str
    pane_kind: str
    view_ref: str | None = Field(default=None)
    description: str | None = Field(default=None)

    # Foreign Keys
    projection_experience_view_id: UUID = Field(description="Foreign key for PaneConfig.projection_experience_view")

    @classmethod
    async def build(
        cls,
        name: str,
        projection_experience_view_id: UUID,
        pane_kind: str,
        view_ref: str | None = None,
        description: str | None = None,
    ) -> PaneConfig:
        """
        Create one deterministic standalone pane-view adapter root.

        Contract:
        - PaneConfig is the Interface-owned render adapter for exactly one
          Experience projection view.
        - pane_kind is the stable cross-language implementation identity.
        - projection_experience_view is the stable pane-view identity key.
        - view_ref is authoring/debug metadata and must not become a second
          runtime identity rail.
        - A pane package must resolve its Experience view dependency without
          relying on a consuming InterfacePackage.
        - API/SDK invocation targets live on Experience projection-view invocation actions.
        - InterfaceConfig composes PaneConfig through `InterfaceConfigPaneConfig`; it does not
          permanently own pane identity.
        """

        payload = {
            "name": name,
            "projection_experience_view_id": projection_experience_view_id,
            "pane_kind": pane_kind,
            "view_ref": view_ref,
            "description": description,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, PaneConfig):
            return value
        return PaneConfig.validate_invocation_value(value)


class PaneConfigBuildInput(BaseModel):
    name: str
    projection_experience_view_id: UUID
    pane_kind: str
    view_ref: str | None = Field(default=None)
    description: str | None = Field(default=None)


class PaneConfigBuildOutput(BaseModel):
    value: PaneConfig


FUNCTIONS = {
    "PaneConfig": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Create one deterministic standalone pane-view adapter root.\n\nContract:\n- PaneConfig is the Interface-owned render adapter for exactly one\n  Experience projection view.\n- pane_kind is the stable cross-language implementation identity.\n- projection_experience_view is the stable pane-view identity key.\n- view_ref is authoring/debug metadata and must not become a second\n  runtime identity rail.\n- A pane package must resolve its Experience view dependency without\n  relying on a consuming InterfacePackage.\n- API/SDK invocation targets live on Experience projection-view invocation actions.\n- InterfaceConfig composes PaneConfig through `InterfaceConfigPaneConfig`; it does not\n  permanently own pane identity.",
                "is_constructor": True,
            },
            "input": PaneConfigBuildInput,
            "output": PaneConfigBuildOutput,
        },
    },
}

__all__ = [
    "PaneConfig",
    "PaneConfigBuildInput",
    "PaneConfigBuildOutput",
    "FUNCTIONS",
]
