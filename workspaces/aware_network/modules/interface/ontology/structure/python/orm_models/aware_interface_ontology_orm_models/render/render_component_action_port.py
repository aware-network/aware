from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import Field

# Interface Ontology Orm Models
from aware_interface_ontology_orm_models.render.pane_render_enums import PaneActionEvent

# Orm
from aware_orm.models.orm_model import ORMModel


class RenderComponentActionPort(ORMModel):
    # Attributes
    port_key: str
    event: PaneActionEvent = Field(default=PaneActionEvent.activate)
    is_required: bool = Field(default=True)
    description: str | None = Field(default=None)

    # Foreign Keys
    render_component_contract_id: UUID = Field(description="Foreign key for RenderComponentContract.action_ports")
