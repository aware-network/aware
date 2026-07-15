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
    from aware_interface_ontology.interface.app_config_screen_config import AppConfigScreenConfig


class AppConfig(ORMModel):
    # Relationships
    screen_configs: list[AppConfigScreenConfig] = Field(default_factory=list)

    # Attributes
    description: str | None = Field(default=None)
    name: str
    title: str | None = Field(default=None)

    @classmethod
    async def build(cls, name: str, title: str | None = None, description: str | None = None) -> AppConfig:
        """
        Create one reusable app configuration.

        Contract:
        - AppConfig owns app-level screen selection intent.
        - Screen rows select Experience layout graph bindings.
        - AppConfig does not own Environment profile/session/process/thread truth.
        """

        payload = {"name": name, "title": title, "description": description}
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, AppConfig):
            return value
        return AppConfig.validate_invocation_value(value)

    async def attach_screen_config(
        self, screen_key: str, projection_experience_id: UUID, projection_experience_layout_graph_binding_id: UUID
    ) -> AppConfigScreenConfig:
        """
        Attach one screen to this app config.

        Contract:
        - Parent AppConfig scope is injected by propagation.
        - The screen is a consumer entry point into Experience layout binding truth.
        - Runtime selection may activate Attention sessions later, but config does
          not mutate Attention or Environment state.
        """

        payload = {
            "screen_key": screen_key,
            "projection_experience_id": projection_experience_id,
            "projection_experience_layout_graph_binding_id": projection_experience_layout_graph_binding_id,
        }
        result = await invoke_instance(orm_model=self, function_name="attach_screen_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_interface_ontology.interface.app_config_screen_config import AppConfigScreenConfig

        if isinstance(value, AppConfigScreenConfig):
            return value
        return AppConfigScreenConfig.validate_invocation_value(value)


class AppConfigBuildInput(BaseModel):
    name: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)


class AppConfigBuildOutput(BaseModel):
    value: AppConfig


class AppConfigAttachScreenConfigInput(BaseModel):
    screen_key: str
    projection_experience_id: UUID
    projection_experience_layout_graph_binding_id: UUID


class AppConfigAttachScreenConfigOutput(BaseModel):
    value: AppConfigScreenConfig


FUNCTIONS = {
    "AppConfig": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Create one reusable app configuration.\n\nContract:\n- AppConfig owns app-level screen selection intent.\n- Screen rows select Experience layout graph bindings.\n- AppConfig does not own Environment profile/session/process/thread truth.",
                "is_constructor": True,
            },
            "input": AppConfigBuildInput,
            "output": AppConfigBuildOutput,
        },
        "attach_screen_config": {
            "canonical": {
                "name": "attach_screen_config",
                "description": "Attach one screen to this app config.\n\nContract:\n- Parent AppConfig scope is injected by propagation.\n- The screen is a consumer entry point into Experience layout binding truth.\n- Runtime selection may activate Attention sessions later, but config does\n  not mutate Attention or Environment state.",
                "is_constructor": False,
            },
            "input": AppConfigAttachScreenConfigInput,
            "output": AppConfigAttachScreenConfigOutput,
        },
    },
}

__all__ = [
    "AppConfig",
    "AppConfigBuildInput",
    "AppConfigBuildOutput",
    "AppConfigAttachScreenConfigInput",
    "AppConfigAttachScreenConfigOutput",
    "FUNCTIONS",
]
