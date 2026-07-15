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
    PaneStateBindingTargetProperty,
    PaneStateBindingTransform,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_meta_ontology.attribute.attribute_config import AttributeConfig
    from aware_meta_ontology.class_.class_config import ClassConfig


class PaneStateBinding(ORMModel):
    # Relationships
    state_model: ClassConfig | None = Field(default=None)
    state_attribute_config: AttributeConfig | None = Field(default=None)

    # Attributes
    binding_key: str
    target_property: PaneStateBindingTargetProperty
    json_path: str
    transform: PaneStateBindingTransform = Field(default=PaneStateBindingTransform.raw)
    fallback_value: str | None = Field(default=None)
    component_input_port_key: str | None = Field(default=None)

    # Foreign Keys
    pane_render_node_id: UUID = Field(description="Foreign key for PaneRenderNode.state_bindings")
    state_model_id: UUID | None = Field(default=None, description="Foreign key for PaneStateBinding.state_model")
    state_attribute_config_id: UUID | None = Field(
        default=None, description="Foreign key for PaneStateBinding.state_attribute_config"
    )

    @classmethod
    async def create_via_pane_render_node(
        cls,
        pane_render_node_id: UUID,
        binding_key: str,
        target_property: PaneStateBindingTargetProperty,
        json_path: str,
        state_model_id: UUID | None = None,
        state_attribute_config_id: UUID | None = None,
        component_input_port_key: str | None = None,
        transform: PaneStateBindingTransform = PaneStateBindingTransform.raw,
        fallback_value: str | None = None,
    ) -> PaneStateBinding:
        """
        Create one relational binding from canonical Experience view state to a render property.

        Contract:
        - `state_model` points to ProjectionExperienceView.state_model when known.
        - `state_attribute_config` identifies the exact DTO attribute when available.
        - `json_path` is the materialized renderer path, not the source of semantic truth.
        - `target_property` is a bounded pane render target; `media_ref` carries
          StorageMediaRef pointers supplied by canonical view state.
        - `component_input_port_key` names the component input port this binding feeds;
          renderers must not infer unbound component inputs from pane state.
        - Transforms stay bounded and deterministic; complex behavior belongs in state providers.
        """

        payload = {
            "pane_render_node_id": pane_render_node_id,
            "binding_key": binding_key,
            "target_property": target_property,
            "json_path": json_path,
            "state_model_id": state_model_id,
            "state_attribute_config_id": state_attribute_config_id,
            "component_input_port_key": component_input_port_key,
            "transform": transform,
            "fallback_value": fallback_value,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_via_pane_render_node", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, PaneStateBinding):
            return value
        return PaneStateBinding.validate_invocation_value(value)


class PaneStateBindingCreateViaPaneRenderNodeInput(BaseModel):
    pane_render_node_id: UUID = Field(description="Foreign key for PaneRenderNode.state_bindings")
    binding_key: str
    target_property: PaneStateBindingTargetProperty
    json_path: str
    state_model_id: UUID | None = Field(default=None)
    state_attribute_config_id: UUID | None = Field(default=None)
    component_input_port_key: str | None = Field(default=None)
    transform: PaneStateBindingTransform = Field(default=PaneStateBindingTransform.raw)
    fallback_value: str | None = Field(default=None)


class PaneStateBindingCreateViaPaneRenderNodeOutput(BaseModel):
    value: PaneStateBinding


FUNCTIONS = {
    "PaneStateBinding": {
        "create_via_pane_render_node": {
            "canonical": {
                "name": "create_via_pane_render_node",
                "description": "Create one relational binding from canonical Experience view state to a render property.\n\nContract:\n- `state_model` points to ProjectionExperienceView.state_model when known.\n- `state_attribute_config` identifies the exact DTO attribute when available.\n- `json_path` is the materialized renderer path, not the source of semantic truth.\n- `target_property` is a bounded pane render target; `media_ref` carries\n  StorageMediaRef pointers supplied by canonical view state.\n- `component_input_port_key` names the component input port this binding feeds;\n  renderers must not infer unbound component inputs from pane state.\n- Transforms stay bounded and deterministic; complex behavior belongs in state providers.",
                "is_constructor": True,
            },
            "input": PaneStateBindingCreateViaPaneRenderNodeInput,
            "output": PaneStateBindingCreateViaPaneRenderNodeOutput,
        },
    },
}

__all__ = [
    "PaneStateBinding",
    "PaneStateBindingCreateViaPaneRenderNodeInput",
    "PaneStateBindingCreateViaPaneRenderNodeOutput",
    "FUNCTIONS",
]
