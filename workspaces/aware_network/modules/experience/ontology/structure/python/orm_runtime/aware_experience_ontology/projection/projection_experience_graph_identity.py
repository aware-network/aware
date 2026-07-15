from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_experience_ontology.projection.projection_experience_graph_identity_profile import (
        ProjectionExperienceGraphIdentityProfile,
    )
    from aware_experience_ontology.projection.projection_experience_node_identity import (
        ProjectionExperienceNodeIdentity,
    )


class ProjectionExperienceGraphIdentity(ORMModel):
    """
    Graph occurrence identity under ProjectionExperienceGraph.
    Contract:
    - Binds one graph occurrence handle to one ProjectionExperienceNodeIdentity.
    - `is_root` marks the canonical root occurrence for deterministic path derivation.
    """

    # Relationships
    projection_experience_graph_identity_profile: ProjectionExperienceGraphIdentityProfile | None = Field(
        default=None, exclude=True
    )
    projection_experience_node_identity: ProjectionExperienceNodeIdentity | None = Field(default=None, exclude=True)

    # Attributes
    is_root: bool = Field(default=False)
    key: str

    # Foreign Keys
    projection_experience_graph_id: UUID = Field(
        description="Foreign key for ProjectionExperienceGraph.projection_experience_graph_identities"
    )
    projection_experience_node_identity_id: UUID = Field(
        description="Foreign key for ProjectionExperienceGraphIdentity.projection_experience_node_identity"
    )

    async def create_profile(
        self,
        review_label: str,
        resolution_prompts: list[str] = [],
        aliases: list[str] = [],
        summary: str | None = None,
        notes: str | None = None,
    ) -> ProjectionExperienceGraphIdentityProfile:
        """
        Attach the canonical graph-identity profile under this ProjectionExperienceGraphIdentity.

        Contract:
        - Graph occurrence identity is the canonical anchor for profile truth.
        - The profile remains Experience-owned and perception-agnostic.
        - Future API/Service rails should consume this profile rather than direct ontology search.
        """

        payload = {
            "review_label": review_label,
            "resolution_prompts": resolution_prompts,
            "aliases": aliases,
            "summary": summary,
            "notes": notes,
        }
        result = await invoke_instance(orm_model=self, function_name="create_profile", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.projection.projection_experience_graph_identity_profile import (
            ProjectionExperienceGraphIdentityProfile,
        )

        if isinstance(value, ProjectionExperienceGraphIdentityProfile):
            return value
        return ProjectionExperienceGraphIdentityProfile.validate_invocation_value(value)

    @classmethod
    async def build_via_projection_experience_graph(
        cls,
        projection_experience_graph_id: UUID,
        projection_experience_node_identity_id: UUID,
        key: str,
        is_root: bool = False,
    ) -> ProjectionExperienceGraphIdentity:
        """Create deterministic ProjectionExperienceGraphIdentity."""

        payload = {
            "projection_experience_graph_id": projection_experience_graph_id,
            "projection_experience_node_identity_id": projection_experience_node_identity_id,
            "key": key,
            "is_root": is_root,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_projection_experience_graph", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProjectionExperienceGraphIdentity):
            return value
        return ProjectionExperienceGraphIdentity.validate_invocation_value(value)


class ProjectionExperienceGraphIdentityCreateProfileInput(BaseModel):
    review_label: str
    resolution_prompts: list[str] = Field(default_factory=list)
    aliases: list[str] = Field(default_factory=list)
    summary: str | None = Field(default=None)
    notes: str | None = Field(default=None)


class ProjectionExperienceGraphIdentityCreateProfileOutput(BaseModel):
    value: ProjectionExperienceGraphIdentityProfile


class ProjectionExperienceGraphIdentityBuildViaProjectionExperienceGraphInput(BaseModel):
    projection_experience_graph_id: UUID = Field(
        description="Foreign key for ProjectionExperienceGraph.projection_experience_graph_identities"
    )
    projection_experience_node_identity_id: UUID
    key: str
    is_root: bool = Field(default=False)


class ProjectionExperienceGraphIdentityBuildViaProjectionExperienceGraphOutput(BaseModel):
    value: ProjectionExperienceGraphIdentity


FUNCTIONS = {
    "ProjectionExperienceGraphIdentity": {
        "create_profile": {
            "canonical": {
                "name": "create_profile",
                "description": "Attach the canonical graph-identity profile under this ProjectionExperienceGraphIdentity.\n\nContract:\n- Graph occurrence identity is the canonical anchor for profile truth.\n- The profile remains Experience-owned and perception-agnostic.\n- Future API/Service rails should consume this profile rather than direct ontology search.",
                "is_constructor": False,
            },
            "input": ProjectionExperienceGraphIdentityCreateProfileInput,
            "output": ProjectionExperienceGraphIdentityCreateProfileOutput,
        },
        "build_via_projection_experience_graph": {
            "canonical": {
                "name": "build_via_projection_experience_graph",
                "description": "Create deterministic ProjectionExperienceGraphIdentity.",
                "is_constructor": True,
            },
            "input": ProjectionExperienceGraphIdentityBuildViaProjectionExperienceGraphInput,
            "output": ProjectionExperienceGraphIdentityBuildViaProjectionExperienceGraphOutput,
        },
    },
}

__all__ = [
    "ProjectionExperienceGraphIdentity",
    "ProjectionExperienceGraphIdentityCreateProfileInput",
    "ProjectionExperienceGraphIdentityCreateProfileOutput",
    "ProjectionExperienceGraphIdentityBuildViaProjectionExperienceGraphInput",
    "ProjectionExperienceGraphIdentityBuildViaProjectionExperienceGraphOutput",
    "FUNCTIONS",
]
