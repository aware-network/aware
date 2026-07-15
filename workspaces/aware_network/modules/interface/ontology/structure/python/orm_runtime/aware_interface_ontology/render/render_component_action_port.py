from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Interface Ontology
from aware_interface_ontology.render.pane_render_enums import PaneActionEvent

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor


class RenderComponentActionPort(ORMModel):
    # Attributes
    port_key: str
    event: PaneActionEvent = Field(default=PaneActionEvent.activate)
    is_required: bool = Field(default=True)
    description: str | None = Field(default=None)

    # Foreign Keys
    render_component_contract_id: UUID = Field(description="Foreign key for RenderComponentContract.action_ports")

    @classmethod
    async def build_via_render_component_contract(
        cls,
        render_component_contract_id: UUID,
        port_key: str,
        event: PaneActionEvent = PaneActionEvent.activate,
        is_required: bool = True,
        description: str | None = None,
    ) -> RenderComponentActionPort:
        """
        Create one explicit component action port.

        Contract:
        - Ports describe user/agent events emitted by the component.
        - PaneRenderSpec ActionBinding maps the port to a canonical API capability endpoint.
        - Components do not call services directly.
        """

        payload = {
            "render_component_contract_id": render_component_contract_id,
            "port_key": port_key,
            "event": event,
            "is_required": is_required,
            "description": description,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_render_component_contract", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, RenderComponentActionPort):
            return value
        return RenderComponentActionPort.validate_invocation_value(value)


class RenderComponentActionPortBuildViaRenderComponentContractInput(BaseModel):
    render_component_contract_id: UUID = Field(description="Foreign key for RenderComponentContract.action_ports")
    port_key: str
    event: PaneActionEvent = Field(default=PaneActionEvent.activate)
    is_required: bool = Field(default=True)
    description: str | None = Field(default=None)


class RenderComponentActionPortBuildViaRenderComponentContractOutput(BaseModel):
    value: RenderComponentActionPort


FUNCTIONS = {
    "RenderComponentActionPort": {
        "build_via_render_component_contract": {
            "canonical": {
                "name": "build_via_render_component_contract",
                "description": "Create one explicit component action port.\n\nContract:\n- Ports describe user/agent events emitted by the component.\n- PaneRenderSpec ActionBinding maps the port to a canonical API capability endpoint.\n- Components do not call services directly.",
                "is_constructor": True,
            },
            "input": RenderComponentActionPortBuildViaRenderComponentContractInput,
            "output": RenderComponentActionPortBuildViaRenderComponentContractOutput,
        },
    },
}

__all__ = [
    "RenderComponentActionPort",
    "RenderComponentActionPortBuildViaRenderComponentContractInput",
    "RenderComponentActionPortBuildViaRenderComponentContractOutput",
    "FUNCTIONS",
]
