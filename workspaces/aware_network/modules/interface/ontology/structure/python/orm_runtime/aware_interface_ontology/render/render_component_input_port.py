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


class RenderComponentInputPort(ORMModel):
    # Attributes
    port_key: str
    value_kind: str
    is_required: bool = Field(default=True)
    description: str | None = Field(default=None)

    # Foreign Keys
    render_component_contract_id: UUID = Field(description="Foreign key for RenderComponentContract.input_ports")

    @classmethod
    async def build_via_render_component_contract(
        cls,
        render_component_contract_id: UUID,
        port_key: str,
        value_kind: str,
        is_required: bool = True,
        description: str | None = None,
    ) -> RenderComponentInputPort:
        """
        Create one explicit component input port.

        Contract:
        - Ports are component-local names, not view-state paths.
        - PaneRenderSpec StateBinding supplies the data bound into each port.
        - Renderers must not infer missing input values from underlying pane state.
        """

        payload = {
            "render_component_contract_id": render_component_contract_id,
            "port_key": port_key,
            "value_kind": value_kind,
            "is_required": is_required,
            "description": description,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_render_component_contract", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, RenderComponentInputPort):
            return value
        return RenderComponentInputPort.validate_invocation_value(value)


class RenderComponentInputPortBuildViaRenderComponentContractInput(BaseModel):
    render_component_contract_id: UUID = Field(description="Foreign key for RenderComponentContract.input_ports")
    port_key: str
    value_kind: str
    is_required: bool = Field(default=True)
    description: str | None = Field(default=None)


class RenderComponentInputPortBuildViaRenderComponentContractOutput(BaseModel):
    value: RenderComponentInputPort


FUNCTIONS = {
    "RenderComponentInputPort": {
        "build_via_render_component_contract": {
            "canonical": {
                "name": "build_via_render_component_contract",
                "description": "Create one explicit component input port.\n\nContract:\n- Ports are component-local names, not view-state paths.\n- PaneRenderSpec StateBinding supplies the data bound into each port.\n- Renderers must not infer missing input values from underlying pane state.",
                "is_constructor": True,
            },
            "input": RenderComponentInputPortBuildViaRenderComponentContractInput,
            "output": RenderComponentInputPortBuildViaRenderComponentContractOutput,
        },
    },
}

__all__ = [
    "RenderComponentInputPort",
    "RenderComponentInputPortBuildViaRenderComponentContractInput",
    "RenderComponentInputPortBuildViaRenderComponentContractOutput",
    "FUNCTIONS",
]
