from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_interface_ontology_dto.render.render_component_action_port import RenderComponentActionPort
    from aware_interface_ontology_dto.render.render_component_capability import RenderComponentCapability
    from aware_interface_ontology_dto.render.render_component_fallback_policy import RenderComponentFallbackPolicy
    from aware_interface_ontology_dto.render.render_component_input_port import RenderComponentInputPort


class RenderComponentContract(BaseModel):
    # Relationships
    input_ports: list[RenderComponentInputPort] = Field(default_factory=list)
    action_ports: list[RenderComponentActionPort] = Field(default_factory=list)
    capabilities: list[RenderComponentCapability] = Field(default_factory=list)
    fallback_policies: list[RenderComponentFallbackPolicy] = Field(default_factory=list)

    # Attributes
    component_ref: str
    contract_version: int = Field(default=1)
    display_name: str | None = Field(default=None)
    description: str | None = Field(default=None)
    surface_kind: str | None = Field(default=None)
