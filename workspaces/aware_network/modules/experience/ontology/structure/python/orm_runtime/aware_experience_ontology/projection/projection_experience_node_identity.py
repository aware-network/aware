from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor


class ProjectionExperienceNodeIdentity(ORMModel):
    """
    ProjectionExperience node identity contract.
    Contract:
    - Declares one human-stable identity name under a ProjectionExperienceNode.
    - Parent->child identity traversal is declared via ProjectionExperienceNodeIdentityEdge.
    """

    # Attributes
    key: str

    # Foreign Keys
    projection_experience_node_id: UUID = Field(
        description="Foreign key for ProjectionExperienceNode.projection_experience_node_identities"
    )

    @classmethod
    async def build_via_projection_experience_node(
        cls, projection_experience_node_id: UUID, key: str
    ) -> ProjectionExperienceNodeIdentity:
        """Create deterministic ProjectionExperienceNodeIdentity association edge."""

        payload = {"projection_experience_node_id": projection_experience_node_id, "key": key}
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_projection_experience_node", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProjectionExperienceNodeIdentity):
            return value
        return ProjectionExperienceNodeIdentity.validate_invocation_value(value)


class ProjectionExperienceNodeIdentityBuildViaProjectionExperienceNodeInput(BaseModel):
    projection_experience_node_id: UUID = Field(
        description="Foreign key for ProjectionExperienceNode.projection_experience_node_identities"
    )
    key: str


class ProjectionExperienceNodeIdentityBuildViaProjectionExperienceNodeOutput(BaseModel):
    value: ProjectionExperienceNodeIdentity


FUNCTIONS = {
    "ProjectionExperienceNodeIdentity": {
        "build_via_projection_experience_node": {
            "canonical": {
                "name": "build_via_projection_experience_node",
                "description": "Create deterministic ProjectionExperienceNodeIdentity association edge.",
                "is_constructor": True,
            },
            "input": ProjectionExperienceNodeIdentityBuildViaProjectionExperienceNodeInput,
            "output": ProjectionExperienceNodeIdentityBuildViaProjectionExperienceNodeOutput,
        },
    },
}

__all__ = [
    "ProjectionExperienceNodeIdentity",
    "ProjectionExperienceNodeIdentityBuildViaProjectionExperienceNodeInput",
    "ProjectionExperienceNodeIdentityBuildViaProjectionExperienceNodeOutput",
    "FUNCTIONS",
]
