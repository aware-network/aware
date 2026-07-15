from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_experience_ontology_dto.invocation.experience_invocation_action_commit_event import (
        ExperienceInvocationActionCommitEvent,
    )
    from aware_meta_ontology_dto.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit


class ExperienceInvocationActionCommit(BaseModel):
    """
    Commit provenance for one Experience invocation action.
    Contract:
    - `ExperienceInvocationAction` owns the causal relationship.
    - `ObjectInstanceGraphCommit` remains Meta-owned commit truth.
    - Events emitted from the commit are linked through
    `ExperienceInvocationActionCommitEvent`.
    """

    # Relationships
    object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None)
    events: list[ExperienceInvocationActionCommitEvent] = Field(default_factory=list)

    # Attributes
    commit_role: str = Field(default="mutation")
    description: str | None = Field(default=None)
