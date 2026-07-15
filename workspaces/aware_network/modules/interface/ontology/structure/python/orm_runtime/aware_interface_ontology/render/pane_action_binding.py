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
from aware_interface_ontology.render.pane_render_enums import PaneActionEvent

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_experience_ontology.projection.projection_experience_view_invocation_action import (
        ProjectionExperienceViewInvocationAction,
    )
    from aware_interface_ontology.render.pane_input_binding import PaneInputBinding


class PaneActionBinding(ORMModel):
    # Relationships
    projection_experience_view_invocation_action: ProjectionExperienceViewInvocationAction | None = Field(default=None)
    input_bindings: list[PaneInputBinding] = Field(default_factory=list)

    # Attributes
    binding_key: str
    event: PaneActionEvent
    action_key: str
    label: str | None = Field(default=None)
    confirmation_policy: str | None = Field(default=None)
    optimistic_policy: str | None = Field(default=None)
    receipt_policy: str | None = Field(default=None)
    component_action_port_key: str | None = Field(default=None)

    # Foreign Keys
    pane_render_node_id: UUID = Field(description="Foreign key for PaneRenderNode.action_bindings")
    projection_experience_view_invocation_action_id: UUID | None = Field(
        default=None, description="Foreign key for PaneActionBinding.projection_experience_view_invocation_action"
    )

    async def bind_input(
        self,
        payload_path: str,
        source_node_key: str | None = None,
        source_json_path: str | None = None,
        literal_value: str | None = None,
    ) -> PaneInputBinding:
        """Map local control values or canonical state into an action payload field."""

        payload = {
            "payload_path": payload_path,
            "source_node_key": source_node_key,
            "source_json_path": source_json_path,
            "literal_value": literal_value,
        }
        result = await invoke_instance(orm_model=self, function_name="bind_input", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_interface_ontology.render.pane_input_binding import PaneInputBinding

        if isinstance(value, PaneInputBinding):
            return value
        return PaneInputBinding.validate_invocation_value(value)

    @classmethod
    async def create_via_pane_render_node(
        cls,
        pane_render_node_id: UUID,
        binding_key: str,
        event: PaneActionEvent,
        action_key: str,
        projection_experience_view_invocation_action_id: UUID | None = None,
        component_action_port_key: str | None = None,
        label: str | None = None,
        confirmation_policy: str | None = None,
        optimistic_policy: str | None = None,
        receipt_policy: str | None = None,
    ) -> PaneActionBinding:
        """
        Create one declarative action affordance binding.

        Contract:
        - `action_key` is the renderer-facing key for one Experience view invocation action.
        - `projection_experience_view_invocation_action` is canonical dispatch truth.
        - `component_action_port_key` names the component-emitted action port when this
          binding is attached to a component node.
        - Renderers may display this as a button, command, menu item, shortcut, or agent command.
        """

        payload = {
            "pane_render_node_id": pane_render_node_id,
            "binding_key": binding_key,
            "event": event,
            "action_key": action_key,
            "projection_experience_view_invocation_action_id": projection_experience_view_invocation_action_id,
            "component_action_port_key": component_action_port_key,
            "label": label,
            "confirmation_policy": confirmation_policy,
            "optimistic_policy": optimistic_policy,
            "receipt_policy": receipt_policy,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_via_pane_render_node", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, PaneActionBinding):
            return value
        return PaneActionBinding.validate_invocation_value(value)


class PaneActionBindingBindInputInput(BaseModel):
    payload_path: str
    source_node_key: str | None = Field(default=None)
    source_json_path: str | None = Field(default=None)
    literal_value: str | None = Field(default=None)


class PaneActionBindingBindInputOutput(BaseModel):
    value: PaneInputBinding


class PaneActionBindingCreateViaPaneRenderNodeInput(BaseModel):
    pane_render_node_id: UUID = Field(description="Foreign key for PaneRenderNode.action_bindings")
    binding_key: str
    event: PaneActionEvent
    action_key: str
    projection_experience_view_invocation_action_id: UUID | None = Field(default=None)
    component_action_port_key: str | None = Field(default=None)
    label: str | None = Field(default=None)
    confirmation_policy: str | None = Field(default=None)
    optimistic_policy: str | None = Field(default=None)
    receipt_policy: str | None = Field(default=None)


class PaneActionBindingCreateViaPaneRenderNodeOutput(BaseModel):
    value: PaneActionBinding


FUNCTIONS = {
    "PaneActionBinding": {
        "bind_input": {
            "canonical": {
                "name": "bind_input",
                "description": "Map local control values or canonical state into an action payload field.",
                "is_constructor": False,
            },
            "input": PaneActionBindingBindInputInput,
            "output": PaneActionBindingBindInputOutput,
        },
        "create_via_pane_render_node": {
            "canonical": {
                "name": "create_via_pane_render_node",
                "description": "Create one declarative action affordance binding.\n\nContract:\n- `action_key` is the renderer-facing key for one Experience view invocation action.\n- `projection_experience_view_invocation_action` is canonical dispatch truth.\n- `component_action_port_key` names the component-emitted action port when this\n  binding is attached to a component node.\n- Renderers may display this as a button, command, menu item, shortcut, or agent command.",
                "is_constructor": True,
            },
            "input": PaneActionBindingCreateViaPaneRenderNodeInput,
            "output": PaneActionBindingCreateViaPaneRenderNodeOutput,
        },
    },
}

__all__ = [
    "PaneActionBinding",
    "PaneActionBindingBindInputInput",
    "PaneActionBindingBindInputOutput",
    "PaneActionBindingCreateViaPaneRenderNodeInput",
    "PaneActionBindingCreateViaPaneRenderNodeOutput",
    "FUNCTIONS",
]
