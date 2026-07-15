from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.invocation.experience_invocation_action_commit_event import (
        ExperienceInvocationActionCommitEvent,
    )
    from aware_meta_ontology_orm_models.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit


class ExperienceInvocationActionCommit(ORMModel):
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

    # Foreign Keys
    experience_invocation_action_id: UUID = Field(description="Foreign key for ExperienceInvocationAction.commits")
    object_instance_graph_commit_id: UUID = Field(
        description="Foreign key for ExperienceInvocationActionCommit.object_instance_graph_commit"
    )
