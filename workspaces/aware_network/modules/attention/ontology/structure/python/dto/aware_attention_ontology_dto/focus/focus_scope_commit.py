from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_attention_ontology_dto.focus.focus import Focus
    from aware_meta_ontology_dto.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit


class FocusScopeCommit(BaseModel):
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
