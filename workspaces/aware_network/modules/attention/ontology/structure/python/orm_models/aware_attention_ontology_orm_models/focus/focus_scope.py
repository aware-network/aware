from __future__ import annotations

# Standard
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_attention_ontology_orm_models.focus.focus import Focus
    from aware_attention_ontology_orm_models.focus.focus_scope_commit import FocusScopeCommit
    from aware_attention_ontology_orm_models.focus.focus_scope_request import FocusScopeRequest
    from aware_meta_ontology_orm_models.graph.projection.object_projection_graph_observable import (
        ObjectProjectionGraphObservable,
    )


class FocusScope(ORMModel):
    """Attention abstraction that allows to set an scope over DYNAMIC FOCUS."""

    # Relationships
    focus: Focus | None = Field(default=None, exclude=True)
    observable: ObjectProjectionGraphObservable | None = Field(
        default=None,
        exclude=True,
        description="Selected observable for the current focus scope.\nContract:\n- This is a canonical, network-shared selector (commit-backed).\n- FocusScope never owns Experience views. It only owns ontology-backed\nobservable selection.\n- The observable must be an ObjectProjectionGraphObservable (meta) so it can be shared and replayed.",
    )
    requests: list[FocusScopeRequest] = Field(default_factory=list, exclude=True)
    commits: list[FocusScopeCommit] = Field(
        default_factory=list,
        exclude=True,
        description="Commit pins observed while this FocusScope is active.\nContract:\n- FocusScopeCommit is provenance, not a semantic change rail.\n- Each row links the active Focus and an existing Meta ObjectInstanceGraphCommit.\n- Observation time is the create commit time for the FocusScopeCommit itself.",
    )

    # Attributes
    title: str
    description: str | None = Field(default=None)
    rationale: str | None = Field(default=None)
    expires_at: datetime | None = Field(default=None)
    is_active: bool = Field(default=True)
    last_accessed: datetime | None = Field(default=None)

    # Foreign Keys
    focus_id: UUID | None = Field(default=None, description="Foreign key for FocusScope.focus")
    observable_id: UUID | None = Field(default=None, description="Foreign key for FocusScope.observable")
