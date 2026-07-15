from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Interface Ontology
from aware_interface_ontology.render.pane_render_enums import PaneRenderCapabilityKind

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor


class PaneRendererCapabilityRequirement(ORMModel):
    # Attributes
    capability_kind: PaneRenderCapabilityKind
    capability_key: str
    is_required: bool = Field(default=True)

    # Foreign Keys
    pane_render_spec_id: UUID = Field(description="Foreign key for PaneRenderSpec.renderer_requirements")

    @classmethod
    async def create_via_pane_render_spec(
        cls,
        pane_render_spec_id: UUID,
        capability_kind: PaneRenderCapabilityKind,
        capability_key: str,
        is_required: bool = True,
    ) -> PaneRendererCapabilityRequirement:
        """
        Declare one required or preferred renderer capability.

        Contract:
        - Renderers decide whether they can satisfy a PaneRenderSpec before attempting render.
        - Fallback remains a renderer/package policy until the spec grows explicit fallback nodes.
        """

        payload = {
            "pane_render_spec_id": pane_render_spec_id,
            "capability_kind": capability_kind,
            "capability_key": capability_key,
            "is_required": is_required,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_via_pane_render_spec", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, PaneRendererCapabilityRequirement):
            return value
        return PaneRendererCapabilityRequirement.validate_invocation_value(value)


class PaneRendererCapabilityRequirementCreateViaPaneRenderSpecInput(BaseModel):
    pane_render_spec_id: UUID = Field(description="Foreign key for PaneRenderSpec.renderer_requirements")
    capability_kind: PaneRenderCapabilityKind
    capability_key: str
    is_required: bool = Field(default=True)


class PaneRendererCapabilityRequirementCreateViaPaneRenderSpecOutput(BaseModel):
    value: PaneRendererCapabilityRequirement


FUNCTIONS = {
    "PaneRendererCapabilityRequirement": {
        "create_via_pane_render_spec": {
            "canonical": {
                "name": "create_via_pane_render_spec",
                "description": "Declare one required or preferred renderer capability.\n\nContract:\n- Renderers decide whether they can satisfy a PaneRenderSpec before attempting render.\n- Fallback remains a renderer/package policy until the spec grows explicit fallback nodes.",
                "is_constructor": True,
            },
            "input": PaneRendererCapabilityRequirementCreateViaPaneRenderSpecInput,
            "output": PaneRendererCapabilityRequirementCreateViaPaneRenderSpecOutput,
        },
    },
}

__all__ = [
    "PaneRendererCapabilityRequirement",
    "PaneRendererCapabilityRequirementCreateViaPaneRenderSpecInput",
    "PaneRendererCapabilityRequirementCreateViaPaneRenderSpecOutput",
    "FUNCTIONS",
]
