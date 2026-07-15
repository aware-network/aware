from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.projection.projection_experience_section_graph_binding import (
        ProjectionExperienceSectionGraphBinding,
    )
    from aware_experience_ontology_orm_models.projection.projection_experience_view_invocation_action import (
        ProjectionExperienceViewInvocationAction,
    )
    from aware_meta_ontology_orm_models.graph.instance.object_instance_graph_branch import ObjectInstanceGraphBranch


class ProjectionExperienceViewInstance(ORMModel):
    """
    Concrete runtime/display instance of one ProjectionExperienceView.
    Contract:
    - `ProjectionExperienceView` remains configuration.
    - This object identifies one concrete fulfillment of a view for a
    section-graph binding and optional materialized branch.
    - Attention is not part of this object's identity. Attention selects
    Section -> FocusScope -> Observable; Experience resolves Section + Observable
    to this view instance through ProjectionExperienceSectionView.
    """

    # Relationships
    section_graph_binding: ProjectionExperienceSectionGraphBinding | None = Field(default=None)
    object_instance_graph_branch: ObjectInstanceGraphBranch | None = Field(default=None)
    invocation_actions: list[ProjectionExperienceViewInvocationAction] = Field(default_factory=list)

    # Attributes
    view_instance_key: str
    state_commit_id: UUID | None = Field(default=None)
    status: str = Field(default="active")

    # Foreign Keys
    projection_experience_view_id: UUID = Field(description="Foreign key for ProjectionExperienceView.view_instances")
    section_graph_binding_id: UUID = Field(
        description="Foreign key for ProjectionExperienceViewInstance.section_graph_binding"
    )
    object_instance_graph_branch_id: UUID | None = Field(
        default=None, description="Foreign key for ProjectionExperienceViewInstance.object_instance_graph_branch"
    )
