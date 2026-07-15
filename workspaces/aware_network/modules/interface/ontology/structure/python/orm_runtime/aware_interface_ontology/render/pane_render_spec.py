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
    PaneRenderCapabilityKind,
    PaneRenderNodeKind,
    PaneRenderSemanticRole,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_interface_ontology.interface.pane_config import PaneConfig
    from aware_interface_ontology.render.pane_render_node import PaneRenderNode
    from aware_interface_ontology.render.pane_renderer_capability_requirement import PaneRendererCapabilityRequirement
    from aware_meta_ontology.class_.class_config import ClassConfig


class PaneRenderSpec(ORMModel):
    # Relationships
    pane_config: PaneConfig | None = Field(default=None)
    nodes: list[PaneRenderNode] = Field(default_factory=list)
    renderer_requirements: list[PaneRendererCapabilityRequirement] = Field(default_factory=list)
    state_model: ClassConfig | None = Field(default=None, exclude=True)

    # Attributes
    name: str
    spec_version: str
    root_node_key: str
    view_ref: str | None = Field(default=None)
    projection_view_key: str | None = Field(default=None)
    description: str | None = Field(default=None)

    # Foreign Keys
    pane_config_id: UUID = Field(description="Foreign key for PaneRenderSpec.pane_config")
    state_model_id: UUID | None = Field(default=None, description="Foreign key for PaneRenderSpec.state_model")

    @classmethod
    async def create(
        cls,
        pane_config_id: UUID,
        name: str,
        spec_version: str,
        root_node_key: str,
        view_ref: str | None = None,
        projection_view_key: str | None = None,
        state_model_id: UUID | None = None,
        description: str | None = None,
    ) -> PaneRenderSpec:
        """
        Create one deterministic renderer-neutral render spec for a pane/view binding.

        Contract:
        - Pane remains the canonical UI unit.
        - This spec starts after PaneConfig and never replaces
          Attention, FocusScope, ProjectionView, or PaneConfig truth.
        - Nodes and bindings are declarative data so renderers can interpret the same
          visual, semantic, and command contract without dynamic code loading.
        """

        payload = {
            "pane_config_id": pane_config_id,
            "name": name,
            "spec_version": spec_version,
            "root_node_key": root_node_key,
            "view_ref": view_ref,
            "projection_view_key": projection_view_key,
            "state_model_id": state_model_id,
            "description": description,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, PaneRenderSpec):
            return value
        return PaneRenderSpec.validate_invocation_value(value)

    async def add_node(
        self,
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
        """Add one ordered semantic render node to this spec."""

        payload = {
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
        result = await invoke_instance(orm_model=self, function_name="add_node", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_interface_ontology.render.pane_render_node import PaneRenderNode

        if isinstance(value, PaneRenderNode):
            return value
        return PaneRenderNode.validate_invocation_value(value)

    async def require_renderer_capability(
        self, capability_kind: PaneRenderCapabilityKind, capability_key: str, is_required: bool = True
    ) -> PaneRendererCapabilityRequirement:
        """Declare one renderer capability required or preferred by this render spec."""

        payload = {"capability_kind": capability_kind, "capability_key": capability_key, "is_required": is_required}
        result = await invoke_instance(orm_model=self, function_name="require_renderer_capability", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_interface_ontology.render.pane_renderer_capability_requirement import (
            PaneRendererCapabilityRequirement,
        )

        if isinstance(value, PaneRendererCapabilityRequirement):
            return value
        return PaneRendererCapabilityRequirement.validate_invocation_value(value)


class PaneRenderSpecCreateInput(BaseModel):
    pane_config_id: UUID
    name: str
    spec_version: str
    root_node_key: str
    view_ref: str | None = Field(default=None)
    projection_view_key: str | None = Field(default=None)
    state_model_id: UUID | None = Field(default=None)
    description: str | None = Field(default=None)


class PaneRenderSpecCreateOutput(BaseModel):
    value: PaneRenderSpec


class PaneRenderSpecAddNodeInput(BaseModel):
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


class PaneRenderSpecAddNodeOutput(BaseModel):
    value: PaneRenderNode


class PaneRenderSpecRequireRendererCapabilityInput(BaseModel):
    capability_kind: PaneRenderCapabilityKind
    capability_key: str
    is_required: bool = Field(default=True)


class PaneRenderSpecRequireRendererCapabilityOutput(BaseModel):
    value: PaneRendererCapabilityRequirement


FUNCTIONS = {
    "PaneRenderSpec": {
        "create": {
            "canonical": {
                "name": "create",
                "description": "Create one deterministic renderer-neutral render spec for a pane/view binding.\n\nContract:\n- Pane remains the canonical UI unit.\n- This spec starts after PaneConfig and never replaces\n  Attention, FocusScope, ProjectionView, or PaneConfig truth.\n- Nodes and bindings are declarative data so renderers can interpret the same\n  visual, semantic, and command contract without dynamic code loading.",
                "is_constructor": True,
            },
            "input": PaneRenderSpecCreateInput,
            "output": PaneRenderSpecCreateOutput,
        },
        "add_node": {
            "canonical": {
                "name": "add_node",
                "description": "Add one ordered semantic render node to this spec.",
                "is_constructor": False,
            },
            "input": PaneRenderSpecAddNodeInput,
            "output": PaneRenderSpecAddNodeOutput,
        },
        "require_renderer_capability": {
            "canonical": {
                "name": "require_renderer_capability",
                "description": "Declare one renderer capability required or preferred by this render spec.",
                "is_constructor": False,
            },
            "input": PaneRenderSpecRequireRendererCapabilityInput,
            "output": PaneRenderSpecRequireRendererCapabilityOutput,
        },
    },
}

__all__ = [
    "PaneRenderSpec",
    "PaneRenderSpecCreateInput",
    "PaneRenderSpecCreateOutput",
    "PaneRenderSpecAddNodeInput",
    "PaneRenderSpecAddNodeOutput",
    "PaneRenderSpecRequireRendererCapabilityInput",
    "PaneRenderSpecRequireRendererCapabilityOutput",
    "FUNCTIONS",
]
