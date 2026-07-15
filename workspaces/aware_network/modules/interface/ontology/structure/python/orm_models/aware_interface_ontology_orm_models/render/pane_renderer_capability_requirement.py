from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import Field

# Interface Ontology Orm Models
from aware_interface_ontology_orm_models.render.pane_render_enums import PaneRenderCapabilityKind

# Orm
from aware_orm.models.orm_model import ORMModel


class PaneRendererCapabilityRequirement(ORMModel):
    # Attributes
    capability_kind: PaneRenderCapabilityKind
    capability_key: str
    is_required: bool = Field(default=True)

    # Foreign Keys
    pane_render_spec_id: UUID = Field(description="Foreign key for PaneRenderSpec.renderer_requirements")
