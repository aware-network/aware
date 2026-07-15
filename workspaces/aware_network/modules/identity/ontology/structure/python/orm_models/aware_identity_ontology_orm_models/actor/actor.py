from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Identity Ontology Orm Models
from aware_identity_ontology_orm_models.actor.actor_enums import ActorType

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_history_ontology_orm_models.commit.commit import Commit
    from aware_identity_ontology_orm_models.actor.actor_commit import ActorCommit
    from aware_identity_ontology_orm_models.actor.actor_role import ActorRole
    from aware_identity_ontology_orm_models.actor.actor_subscription import ActorSubscription
    from aware_identity_ontology_orm_models.identity.identity import Identity


class Actor(ORMModel):
    # Relationships
    identity: Identity
    actor_roles: list[ActorRole] = Field(default_factory=list, exclude=True, description="Roles")
    actor_subscriptions: list[ActorSubscription] = Field(
        default_factory=list, exclude=True, description="Subscriptions"
    )
    authored_commits: list[Commit] = Field(default_factory=list, exclude=True, description="Commits")
    actor_commits: list[ActorCommit] = Field(default_factory=list, exclude=True)

    # Attributes
    key: str = Field(default="default")
    type: ActorType

    # Foreign Keys
    identity_id: UUID | None = Field(default=None, description="Foreign key for Actor.identity")
