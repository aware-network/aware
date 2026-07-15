from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import Field

# Interface Ontology Orm Models
from aware_interface_ontology_orm_models.render.pane_render_enums import PaneRenderNodeKind

# Orm
from aware_orm.models.orm_model import ORMModel


class RenderComponentFallbackPolicy(ORMModel):
    # Attributes
    policy_key: str
    fallback_kind: str
    fallback_component_ref: str | None = Field(default=None)
    fallback_node_kind: PaneRenderNodeKind | None = Field(default=None)
    description: str | None = Field(default=None)

    # Foreign Keys
    render_component_contract_id: UUID = Field(description="Foreign key for RenderComponentContract.fallback_policies")
