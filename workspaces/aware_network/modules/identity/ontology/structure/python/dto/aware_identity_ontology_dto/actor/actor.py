from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Identity Ontology Dto
from aware_identity_ontology_dto.actor.actor_enums import ActorType

if TYPE_CHECKING:
    from aware_history_ontology_dto.commit.commit import Commit
    from aware_identity_ontology_dto.actor.actor_commit import ActorCommit
    from aware_identity_ontology_dto.actor.actor_role import ActorRole
    from aware_identity_ontology_dto.actor.actor_subscription import ActorSubscription
    from aware_identity_ontology_dto.identity.identity import Identity


class Actor(BaseModel):
    # Relationships
    identity: Identity
    actor_roles: list[ActorRole] = Field(default_factory=list, description="Roles")
    actor_subscriptions: list[ActorSubscription] = Field(default_factory=list, description="Subscriptions")
    authored_commits: list[Commit] = Field(default_factory=list, description="Commits")
    actor_commits: list[ActorCommit] = Field(default_factory=list)

    # Attributes
    key: str = Field(default="default")
    type: ActorType
