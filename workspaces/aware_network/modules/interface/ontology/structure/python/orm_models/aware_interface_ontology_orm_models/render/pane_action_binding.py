from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Interface Ontology Orm Models
from aware_interface_ontology_orm_models.render.pane_render_enums import PaneActionEvent

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.projection.projection_experience_view_invocation_action import (
        ProjectionExperienceViewInvocationAction,
    )
    from aware_interface_ontology_orm_models.render.pane_input_binding import PaneInputBinding


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
