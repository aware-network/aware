from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Interface Ontology
from aware_interface_ontology.interface.interface_enums import InterfaceOs

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_interface_ontology.interface.interface import Interface
    from aware_interface_ontology.interface.interface_config_pane_config import InterfaceConfigPaneConfig
    from aware_interface_ontology.interface.interface_config_window_config import InterfaceConfigWindowConfig
    from aware_interface_ontology.interface.pane_config import PaneConfig


class InterfaceConfig(ORMModel):
    # Relationships
    interfaces: list[Interface] = Field(default_factory=list, exclude=True)
    interface_config_window_configs: list[InterfaceConfigWindowConfig] = Field(default_factory=list, exclude=True)
    interface_config_pane_configs: list[InterfaceConfigPaneConfig] = Field(default_factory=list, exclude=True)

    # Attributes
    name: str
    description: str | None = Field(default=None)

    @classmethod
    async def build(cls, name: str, description: str | None = None) -> InterfaceConfig:
        """Create one deterministic InterfaceConfig."""

        payload = {"name": name, "description": description}
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, InterfaceConfig):
            return value
        return InterfaceConfig.validate_invocation_value(value)

    async def create_interface(self, os: InterfaceOs, version: str) -> Interface:
        """Create one runtime Interface instance under this InterfaceConfig."""

        payload = {"os": os, "version": version}
        result = await invoke_instance(orm_model=self, function_name="create_interface", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_interface_ontology.interface.interface import Interface

        if isinstance(value, Interface):
            return value
        return Interface.validate_invocation_value(value)

    async def attach_window_config(self, window_config_id: UUID) -> InterfaceConfigWindowConfig:
        """Attach one existing standalone WindowConfig beneath this InterfaceConfig."""

        payload = {"window_config_id": window_config_id}
        result = await invoke_instance(orm_model=self, function_name="attach_window_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_interface_ontology.interface.interface_config_window_config import InterfaceConfigWindowConfig

        if isinstance(value, InterfaceConfigWindowConfig):
            return value
        return InterfaceConfigWindowConfig.validate_invocation_value(value)

    async def attach_pane_config(
        self, pane_config_id: UUID, narrative_key: str | None = None
    ) -> InterfaceConfigPaneConfig:
        """Attach one existing standalone PaneConfig beneath this InterfaceConfig."""

        payload = {"pane_config_id": pane_config_id, "narrative_key": narrative_key}
        result = await invoke_instance(orm_model=self, function_name="attach_pane_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_interface_ontology.interface.interface_config_pane_config import InterfaceConfigPaneConfig

        if isinstance(value, InterfaceConfigPaneConfig):
            return value
        return InterfaceConfigPaneConfig.validate_invocation_value(value)

    async def create_pane_config(
        self,
        name: str,
        projection_experience_view_id: UUID,
        pane_kind: str,
        view_ref: str | None = None,
        description: str | None = None,
    ) -> PaneConfig:
        """
        Compatibility helper: create one standalone PaneConfig and attach it to this InterfaceConfig.

        Contract:
        - Pane semantic identity remains standalone.
        - This helper exists so current runtime/materialization rails can stay on one projection lane during
          the extraction.
        - Long-term authored `pane` / `interface` grammar should replace this convenience path.
        """

        payload = {
            "name": name,
            "projection_experience_view_id": projection_experience_view_id,
            "pane_kind": pane_kind,
            "view_ref": view_ref,
            "description": description,
        }
        result = await invoke_instance(orm_model=self, function_name="create_pane_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_interface_ontology.interface.pane_config import PaneConfig

        if isinstance(value, PaneConfig):
            return value
        return PaneConfig.validate_invocation_value(value)


class InterfaceConfigBuildInput(BaseModel):
    name: str
    description: str | None = Field(default=None)


class InterfaceConfigBuildOutput(BaseModel):
    value: InterfaceConfig


class InterfaceConfigCreateInterfaceInput(BaseModel):
    os: InterfaceOs
    version: str


class InterfaceConfigCreateInterfaceOutput(BaseModel):
    value: Interface


class InterfaceConfigAttachWindowConfigInput(BaseModel):
    window_config_id: UUID


class InterfaceConfigAttachWindowConfigOutput(BaseModel):
    value: InterfaceConfigWindowConfig


class InterfaceConfigAttachPaneConfigInput(BaseModel):
    pane_config_id: UUID
    narrative_key: str | None = Field(default=None)


class InterfaceConfigAttachPaneConfigOutput(BaseModel):
    value: InterfaceConfigPaneConfig


class InterfaceConfigCreatePaneConfigInput(BaseModel):
    name: str
    projection_experience_view_id: UUID
    pane_kind: str
    view_ref: str | None = Field(default=None)
    description: str | None = Field(default=None)


class InterfaceConfigCreatePaneConfigOutput(BaseModel):
    value: PaneConfig


FUNCTIONS = {
    "InterfaceConfig": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Create one deterministic InterfaceConfig.",
                "is_constructor": True,
            },
            "input": InterfaceConfigBuildInput,
            "output": InterfaceConfigBuildOutput,
        },
        "create_interface": {
            "canonical": {
                "name": "create_interface",
                "description": "Create one runtime Interface instance under this InterfaceConfig.",
                "is_constructor": False,
            },
            "input": InterfaceConfigCreateInterfaceInput,
            "output": InterfaceConfigCreateInterfaceOutput,
        },
        "attach_window_config": {
            "canonical": {
                "name": "attach_window_config",
                "description": "Attach one existing standalone WindowConfig beneath this InterfaceConfig.",
                "is_constructor": False,
            },
            "input": InterfaceConfigAttachWindowConfigInput,
            "output": InterfaceConfigAttachWindowConfigOutput,
        },
        "attach_pane_config": {
            "canonical": {
                "name": "attach_pane_config",
                "description": "Attach one existing standalone PaneConfig beneath this InterfaceConfig.",
                "is_constructor": False,
            },
            "input": InterfaceConfigAttachPaneConfigInput,
            "output": InterfaceConfigAttachPaneConfigOutput,
        },
        "create_pane_config": {
            "canonical": {
                "name": "create_pane_config",
                "description": "Compatibility helper: create one standalone PaneConfig and attach it to this InterfaceConfig.\n\nContract:\n- Pane semantic identity remains standalone.\n- This helper exists so current runtime/materialization rails can stay on one projection lane during\n  the extraction.\n- Long-term authored `pane` / `interface` grammar should replace this convenience path.",
                "is_constructor": False,
            },
            "input": InterfaceConfigCreatePaneConfigInput,
            "output": InterfaceConfigCreatePaneConfigOutput,
        },
    },
}

__all__ = [
    "InterfaceConfig",
    "InterfaceConfigBuildInput",
    "InterfaceConfigBuildOutput",
    "InterfaceConfigCreateInterfaceInput",
    "InterfaceConfigCreateInterfaceOutput",
    "InterfaceConfigAttachWindowConfigInput",
    "InterfaceConfigAttachWindowConfigOutput",
    "InterfaceConfigAttachPaneConfigInput",
    "InterfaceConfigAttachPaneConfigOutput",
    "InterfaceConfigCreatePaneConfigInput",
    "InterfaceConfigCreatePaneConfigOutput",
    "FUNCTIONS",
]
