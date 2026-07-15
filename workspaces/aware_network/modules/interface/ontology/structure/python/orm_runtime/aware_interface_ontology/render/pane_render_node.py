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
from aware_interface_ontology.render.pane_render_enums import (
    PaneActionEvent,
    PaneRenderNodeKind,
    PaneRenderSemanticRole,
    PaneStateBindingTargetProperty,
    PaneStateBindingTransform,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_interface_ontology.render.pane_action_binding import PaneActionBinding
    from aware_interface_ontology.render.pane_state_binding import PaneStateBinding
    from aware_interface_ontology.render.pane_style_token_ref import PaneStyleTokenRef
    from aware_interface_ontology.render.render_component_contract import RenderComponentContract


class PaneRenderNode(ORMModel):
    # Relationships
    state_bindings: list[PaneStateBinding] = Field(default_factory=list)
    action_bindings: list[PaneActionBinding] = Field(default_factory=list)
    style_tokens: list[PaneStyleTokenRef] = Field(default_factory=list)
    component_contract: RenderComponentContract | None = Field(default=None)

    # Attributes
    node_key: str
    parent_node_key: str | None = Field(default=None)
    node_kind: PaneRenderNodeKind
    semantic_role: PaneRenderSemanticRole | None = Field(default=None)
    slot_key: str | None = Field(default=None)
    order: int = Field(default=0)
    label: str | None = Field(default=None)
    text: str | None = Field(default=None)
    placeholder: str | None = Field(default=None)
    component_ref: str | None = Field(default=None)
    fallback_node_kind: PaneRenderNodeKind | None = Field(default=None)
    fallback_text: str | None = Field(default=None)

    # Foreign Keys
    pane_render_spec_id: UUID = Field(description="Foreign key for PaneRenderSpec.nodes")
    component_contract_id: UUID | None = Field(
        default=None, description="Foreign key for PaneRenderNode.component_contract"
    )

    async def bind_state(
        self,
        binding_key: str,
        target_property: PaneStateBindingTargetProperty,
        json_path: str,
        state_model_id: UUID | None = None,
        state_attribute_config_id: UUID | None = None,
        component_input_port_key: str | None = None,
        transform: PaneStateBindingTransform = PaneStateBindingTransform.raw,
        fallback_value: str | None = None,
    ) -> PaneStateBinding:
        """Bind one canonical view-state value to one render-node property."""

        payload = {
            "binding_key": binding_key,
            "target_property": target_property,
            "json_path": json_path,
            "state_model_id": state_model_id,
            "state_attribute_config_id": state_attribute_config_id,
            "component_input_port_key": component_input_port_key,
            "transform": transform,
            "fallback_value": fallback_value,
        }
        result = await invoke_instance(orm_model=self, function_name="bind_state", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_interface_ontology.render.pane_state_binding import PaneStateBinding

        if isinstance(value, PaneStateBinding):
            return value
        return PaneStateBinding.validate_invocation_value(value)

    async def bind_action(
        self,
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
        """Bind a node event to one Experience view invocation action."""

        payload = {
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
        result = await invoke_instance(orm_model=self, function_name="bind_action", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_interface_ontology.render.pane_action_binding import PaneActionBinding

        if isinstance(value, PaneActionBinding):
            return value
        return PaneActionBinding.validate_invocation_value(value)

    async def add_style_token(self, token_key: str, token_value: str | None = None) -> PaneStyleTokenRef:
        """Attach one semantic style token to this node."""

        payload = {"token_key": token_key, "token_value": token_value}
        result = await invoke_instance(orm_model=self, function_name="add_style_token", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_interface_ontology.render.pane_style_token_ref import PaneStyleTokenRef

        if isinstance(value, PaneStyleTokenRef):
            return value
        return PaneStyleTokenRef.validate_invocation_value(value)

    @classmethod
    async def create_via_pane_render_spec(
        cls,
        pane_render_spec_id: UUID,
        node_key: str,
        node_kind: PaneRenderNodeKind,
        semantic_role: PaneRenderSemanticRole | None = None,
        parent_node_key: str | None = None,
        slot_key: str | None = None,
        order: int = 0,
        label: str | None = None,
        text: str | None = None,
        placeholder: str | None = None,
        component_ref: str | None = None,
        component_contract_id: UUID | None = None,
        fallback_node_kind: PaneRenderNodeKind | None = None,
        fallback_text: str | None = None,
    ) -> PaneRenderNode:
        """
        Create one semantic render node inside its owning PaneRenderSpec.

        Contract:
        - `node_kind` is renderer-neutral intent, not a Flutter/HTML class.
        - `parent_node_key` keeps the materialized tree relational and commit-friendly.
        - Exact state and action truth is attached through bindings, not local scripts.
        - Component nodes use `component_ref` to select a RenderComponentContract.
          They still receive state/actions only through explicit bindings.
        """

        payload = {
            "pane_render_spec_id": pane_render_spec_id,
            "node_key": node_key,
            "node_kind": node_kind,
            "semantic_role": semantic_role,
            "parent_node_key": parent_node_key,
            "slot_key": slot_key,
            "order": order,
            "label": label,
            "text": text,
            "placeholder": placeholder,
            "component_ref": component_ref,
            "component_contract_id": component_contract_id,
            "fallback_node_kind": fallback_node_kind,
            "fallback_text": fallback_text,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_via_pane_render_spec", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, PaneRenderNode):
            return value
        return PaneRenderNode.validate_invocation_value(value)


class PaneRenderNodeBindStateInput(BaseModel):
    binding_key: str
    target_property: PaneStateBindingTargetProperty
    json_path: str
    state_model_id: UUID | None = Field(default=None)
    state_attribute_config_id: UUID | None = Field(default=None)
    component_input_port_key: str | None = Field(default=None)
    transform: PaneStateBindingTransform = Field(default=PaneStateBindingTransform.raw)
    fallback_value: str | None = Field(default=None)


class PaneRenderNodeBindStateOutput(BaseModel):
    value: PaneStateBinding


class PaneRenderNodeBindActionInput(BaseModel):
    binding_key: str
    event: PaneActionEvent
    action_key: str
    projection_experience_view_invocation_action_id: UUID | None = Field(default=None)
    component_action_port_key: str | None = Field(default=None)
    label: str | None = Field(default=None)
    confirmation_policy: str | None = Field(default=None)
    optimistic_policy: str | None = Field(default=None)
    receipt_policy: str | None = Field(default=None)


class PaneRenderNodeBindActionOutput(BaseModel):
    value: PaneActionBinding


class PaneRenderNodeAddStyleTokenInput(BaseModel):
    token_key: str
    token_value: str | None = Field(default=None)


class PaneRenderNodeAddStyleTokenOutput(BaseModel):
    value: PaneStyleTokenRef


class PaneRenderNodeCreateViaPaneRenderSpecInput(BaseModel):
    pane_render_spec_id: UUID = Field(description="Foreign key for PaneRenderSpec.nodes")
    node_key: str
    node_kind: PaneRenderNodeKind
    semantic_role: PaneRenderSemanticRole | None = Field(default=None)
    parent_node_key: str | None = Field(default=None)
    slot_key: str | None = Field(default=None)
    order: int = Field(default=0)
    label: str | None = Field(default=None)
    text: str | None = Field(default=None)
    placeholder: str | None = Field(default=None)
    component_ref: str | None = Field(default=None)
    component_contract_id: UUID | None = Field(default=None)
    fallback_node_kind: PaneRenderNodeKind | None = Field(default=None)
    fallback_text: str | None = Field(default=None)


class PaneRenderNodeCreateViaPaneRenderSpecOutput(BaseModel):
    value: PaneRenderNode


FUNCTIONS = {
    "PaneRenderNode": {
        "bind_state": {
            "canonical": {
                "name": "bind_state",
                "description": "Bind one canonical view-state value to one render-node property.",
                "is_constructor": False,
            },
            "input": PaneRenderNodeBindStateInput,
            "output": PaneRenderNodeBindStateOutput,
        },
        "bind_action": {
            "canonical": {
                "name": "bind_action",
                "description": "Bind a node event to one Experience view invocation action.",
                "is_constructor": False,
            },
            "input": PaneRenderNodeBindActionInput,
            "output": PaneRenderNodeBindActionOutput,
        },
        "add_style_token": {
            "canonical": {
                "name": "add_style_token",
                "description": "Attach one semantic style token to this node.",
                "is_constructor": False,
            },
            "input": PaneRenderNodeAddStyleTokenInput,
            "output": PaneRenderNodeAddStyleTokenOutput,
        },
        "create_via_pane_render_spec": {
            "canonical": {
                "name": "create_via_pane_render_spec",
                "description": "Create one semantic render node inside its owning PaneRenderSpec.\n\nContract:\n- `node_kind` is renderer-neutral intent, not a Flutter/HTML class.\n- `parent_node_key` keeps the materialized tree relational and commit-friendly.\n- Exact state and action truth is attached through bindings, not local scripts.\n- Component nodes use `component_ref` to select a RenderComponentContract.\n  They still receive state/actions only through explicit bindings.",
                "is_constructor": True,
            },
            "input": PaneRenderNodeCreateViaPaneRenderSpecInput,
            "output": PaneRenderNodeCreateViaPaneRenderSpecOutput,
        },
    },
}

__all__ = [
    "PaneRenderNode",
    "PaneRenderNodeBindStateInput",
    "PaneRenderNodeBindStateOutput",
    "PaneRenderNodeBindActionInput",
    "PaneRenderNodeBindActionOutput",
    "PaneRenderNodeAddStyleTokenInput",
    "PaneRenderNodeAddStyleTokenOutput",
    "PaneRenderNodeCreateViaPaneRenderSpecInput",
    "PaneRenderNodeCreateViaPaneRenderSpecOutput",
    "FUNCTIONS",
]
