from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Interface Ontology Dto
from aware_interface_ontology_dto.render.pane_render_enums import PaneActionEvent

if TYPE_CHECKING:
    from aware_experience_ontology_dto.projection.projection_experience_view_invocation_action import (
        ProjectionExperienceViewInvocationAction,
    )
    from aware_interface_ontology_dto.render.pane_input_binding import PaneInputBinding


class PaneActionBinding(BaseModel):
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
