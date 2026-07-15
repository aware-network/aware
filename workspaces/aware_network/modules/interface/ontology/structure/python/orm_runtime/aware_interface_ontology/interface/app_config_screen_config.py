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
    from aware_experience_ontology.projection.projection_experience_layout_graph_binding import (
        ProjectionExperienceLayoutGraphBinding,
    )


class AppConfigScreenConfig(ORMModel):
    # Relationships
    projection_experience: ProjectionExperience | None = Field(default=None)
    projection_experience_layout_graph_binding: ProjectionExperienceLayoutGraphBinding | None = Field(default=None)

    # Attributes
    screen_key: str

    # Foreign Keys
    app_config_id: UUID = Field(description="Foreign key for AppConfig.screen_configs")
    projection_experience_id: UUID = Field(description="Foreign key for AppConfigScreenConfig.projection_experience")
    projection_experience_layout_graph_binding_id: UUID = Field(
        description="Foreign key for AppConfigScreenConfig.projection_experience_layout_graph_binding"
    )

    @classmethod
    async def build_via_app_config(
        cls,
        app_config_id: UUID,
        screen_key: str,
        projection_experience_id: UUID,
        projection_experience_layout_graph_binding_id: UUID,
    ) -> AppConfigScreenConfig:
        """
        Create one app screen config under an AppConfig.

        Contract:
        - `screen_key` is the app-owned entry token.
        - `projection_experience` is the Experience entry point.
        - `projection_experience_layout_graph_binding` is the Experience-owned
          layout-level binding for the screen.
        - The app does not target Environment internals or pane defaults.
        """

        payload = {
            "app_config_id": app_config_id,
            "screen_key": screen_key,
            "projection_experience_id": projection_experience_id,
            "projection_experience_layout_graph_binding_id": projection_experience_layout_graph_binding_id,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_app_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, AppConfigScreenConfig):
            return value
        return AppConfigScreenConfig.validate_invocation_value(value)


class AppConfigScreenConfigBuildViaAppConfigInput(BaseModel):
    app_config_id: UUID = Field(description="Foreign key for AppConfig.screen_configs")
    screen_key: str
    projection_experience_id: UUID
    projection_experience_layout_graph_binding_id: UUID


class AppConfigScreenConfigBuildViaAppConfigOutput(BaseModel):
    value: AppConfigScreenConfig


FUNCTIONS = {
    "AppConfigScreenConfig": {
        "build_via_app_config": {
            "canonical": {
                "name": "build_via_app_config",
                "description": "Create one app screen config under an AppConfig.\n\nContract:\n- `screen_key` is the app-owned entry token.\n- `projection_experience` is the Experience entry point.\n- `projection_experience_layout_graph_binding` is the Experience-owned\n  layout-level binding for the screen.\n- The app does not target Environment internals or pane defaults.",
                "is_constructor": True,
            },
            "input": AppConfigScreenConfigBuildViaAppConfigInput,
            "output": AppConfigScreenConfigBuildViaAppConfigOutput,
        },
    },
}

__all__ = [
    "AppConfigScreenConfig",
    "AppConfigScreenConfigBuildViaAppConfigInput",
    "AppConfigScreenConfigBuildViaAppConfigOutput",
    "FUNCTIONS",
]
