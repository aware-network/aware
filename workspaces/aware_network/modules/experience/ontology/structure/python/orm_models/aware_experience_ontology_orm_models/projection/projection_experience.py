from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.contract.experience_contract_actor_role_grant import (
        ExperienceContractActorRoleGrant,
    )
    from aware_experience_ontology_orm_models.invocation.experience_invocation_action_config import (
        ExperienceInvocationActionConfig,
    )
    from aware_experience_ontology_orm_models.projection.projection_experience_branch import ProjectionExperienceBranch
    from aware_experience_ontology_orm_models.projection.projection_experience_graph import ProjectionExperienceGraph
    from aware_experience_ontology_orm_models.projection.projection_experience_layout_graph_binding import (
        ProjectionExperienceLayoutGraphBinding,
    )
    from aware_experience_ontology_orm_models.projection.projection_experience_node import ProjectionExperienceNode
    from aware_experience_ontology_orm_models.projection.projection_experience_oigi import ProjectionExperienceOIGI
    from aware_experience_ontology_orm_models.projection.projection_experience_section import (
        ProjectionExperienceSection,
    )
    from aware_experience_ontology_orm_models.projection.projection_experience_section_graph_binding import (
        ProjectionExperienceSectionGraphBinding,
    )
    from aware_experience_ontology_orm_models.projection.projection_experience_view import ProjectionExperienceView
    from aware_experience_ontology_orm_models.provider.experience_provider import ExperienceProvider
    from aware_meta_ontology_orm_models.graph.projection.object_projection_graph_identity import (
        ObjectProjectionGraphIdentity,
    )


class ProjectionExperience(ORMModel):
    # Relationships
    object_projection_graph_identity: ObjectProjectionGraphIdentity | None = Field(default=None, exclude=True)
    projection_experience_branches: list[ProjectionExperienceBranch] = Field(default_factory=list, exclude=True)
    projection_experience_graphs: list[ProjectionExperienceGraph] = Field(default_factory=list, exclude=True)
    projection_experience_layout_graph_bindings: list[ProjectionExperienceLayoutGraphBinding] = Field(
        default_factory=list, exclude=True
    )
    projection_experience_nodes: list[ProjectionExperienceNode] = Field(default_factory=list, exclude=True)
    projection_experience_oigis: list[ProjectionExperienceOIGI] = Field(default_factory=list, exclude=True)
    projection_experience_sections: list[ProjectionExperienceSection] = Field(default_factory=list, exclude=True)
    projection_experience_section_graph_bindings: list[ProjectionExperienceSectionGraphBinding] = Field(
        default_factory=list, exclude=True
    )
    projection_experience_views: list[ProjectionExperienceView] = Field(default_factory=list, exclude=True)
    providers: list[ExperienceProvider] = Field(default_factory=list)
    contract_actor_role_grants: list[ExperienceContractActorRoleGrant] = Field(default_factory=list)
    invocation_action_configs: list[ExperienceInvocationActionConfig] = Field(default_factory=list)

    # Attributes
    name: str

    # Foreign Keys
    object_projection_graph_identity_id: UUID = Field(
        description="Foreign key for ProjectionExperience.object_projection_graph_identity"
    )
