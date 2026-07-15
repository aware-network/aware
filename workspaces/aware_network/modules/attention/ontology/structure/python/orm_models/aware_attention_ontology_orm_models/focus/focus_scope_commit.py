from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_attention_ontology_orm_models.focus.focus import Focus
    from aware_meta_ontology_orm_models.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit


class FocusScopeCommit(ORMModel):
    """
    Provenance pin for a Meta OIG commit observed under one FocusScope.
    Contract:
    - Attention owns this context pointer.
    - Meta remains the commit authority through ObjectInstanceGraphCommit.
    - This is not a semantic `Change` object; consumers reconstruct meaning from
    the pinned commit deltas.
    - Observation time is the create commit time of this FocusScopeCommit.
    """

    # Relationships
    focus: Focus | None = Field(default=None)
    object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None)

    # Foreign Keys
    focus_scope_id: UUID = Field(description="Foreign key for FocusScope.commits")
    focus_id: UUID = Field(description="Foreign key for FocusScopeCommit.focus")
    object_instance_graph_commit_id: UUID = Field(
        description="Foreign key for FocusScopeCommit.object_instance_graph_commit"
    )
