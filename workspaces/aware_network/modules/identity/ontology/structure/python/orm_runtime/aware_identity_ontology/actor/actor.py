from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Identity Ontology
from aware_identity_ontology.actor.actor_enums import ActorType
from aware_identity_ontology.actor.actor_subscription_enums import (
    SubscriptionAddressingPolicy,
    SubscriptionFilterMode,
    SubscriptionStatus,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_history_ontology.commit.commit import Commit
    from aware_identity_ontology.actor.actor_commit import ActorCommit
    from aware_identity_ontology.actor.actor_role import ActorRole
    from aware_identity_ontology.actor.actor_subscription import ActorSubscription
    from aware_identity_ontology.identity.identity import Identity


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

    @classmethod
    async def create_actor(cls, type: ActorType, identity_id: UUID, key: str = "default") -> Actor:
        """
        Create an actor bound to an identity.

        v0: used by `Identity.signup` to build the minimal Identity→Actor graph
        while preserving the hard mutation boundary (mutate-self-only).
        """

        payload = {"type": type, "identity_id": identity_id, "key": key}
        result = await invoke_constructor(orm_class=cls, function_name="create_actor", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, Actor):
            return value
        return Actor.validate_invocation_value(value)

    async def add_role(self, role_id: UUID) -> ActorRole:
        """Adds a role binding to this actor."""

        payload = {"role_id": role_id}
        result = await invoke_instance(orm_model=self, function_name="add_role", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_identity_ontology.actor.actor_role import ActorRole

        if isinstance(value, ActorRole):
            return value
        return ActorRole.validate_invocation_value(value)

    async def remove_role(self, role_id: UUID) -> None:
        """
        Remove a role binding from this actor.

        Contract:
        - Actor owns the actor_roles containment rail.
        - Missing role bindings are a no-op.
        - Deletion occurs through the contained ActorRole delete handler so
          mutation remains parent-owned.
        """

        payload = {"role_id": role_id}
        await invoke_instance(orm_model=self, function_name="remove_role", payload=payload)
        return None

    async def add_subscription(
        self,
        event_config_condition_config_scope_id: UUID,
        name: str,
        description: str | None = None,
        action_type: str | None = None,
        event_config_action_config_ids: list[UUID] = [],
        addressing_policy: SubscriptionAddressingPolicy = SubscriptionAddressingPolicy.any,
        is_enabled: bool = True,
        status: SubscriptionStatus = SubscriptionStatus.active,
        filter_mode: SubscriptionFilterMode = SubscriptionFilterMode.all_instances,
        filter_config: JsonObject | None = None,
        priority: int = 0,
        batch_mode: bool = False,
        batch_window_ms: int = 1000,
        max_batch_size: int = 100,
        require_read_access: bool = True,
        check_ownership: bool = True,
        rate_limit_per_minute: int | None = None,
        rate_limit_per_hour: int | None = None,
    ) -> ActorSubscription:
        """Adds a subscription policy to this actor."""

        payload = {
            "event_config_condition_config_scope_id": event_config_condition_config_scope_id,
            "name": name,
            "description": description,
            "action_type": action_type,
            "event_config_action_config_ids": event_config_action_config_ids,
            "addressing_policy": addressing_policy,
            "is_enabled": is_enabled,
            "status": status,
            "filter_mode": filter_mode,
            "filter_config": filter_config,
            "priority": priority,
            "batch_mode": batch_mode,
            "batch_window_ms": batch_window_ms,
            "max_batch_size": max_batch_size,
            "require_read_access": require_read_access,
            "check_ownership": check_ownership,
            "rate_limit_per_minute": rate_limit_per_minute,
            "rate_limit_per_hour": rate_limit_per_hour,
        }
        result = await invoke_instance(orm_model=self, function_name="add_subscription", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_identity_ontology.actor.actor_subscription import ActorSubscription

        if isinstance(value, ActorSubscription):
            return value
        return ActorSubscription.validate_invocation_value(value)

    async def ensure_commit(
        self,
        domain_branch_id: UUID,
        domain_projection_hash: str,
        domain_commit_id: UUID,
        object_instance_graph_commit_id: UUID,
        environment_id: UUID | None = None,
        process_id: UUID | None = None,
        thread_id: UUID | None = None,
        receipt_actor_id: UUID | None = None,
        created_at_unix_ms: int | None = None,
        operation_label: str | None = None,
        call_target: str | None = None,
        function_id: UUID | None = None,
        object_id: UUID | None = None,
        class_instance_identity_id: UUID | None = None,
        graph_hash_post: str | None = None,
        object_instance_graph_id: UUID | None = None,
        root_object_id: UUID | None = None,
        head_version: int | None = None,
        source: str = "environment_lane_commit_receipt",
    ) -> ActorCommit:
        """
        Ensure an ActorCommit personal-history binding for one durable lane commit.

        Canonical v0:
        - Called by the Identity Environment-fanout reaction after a lane head commit receipt.
        - Idempotent by Actor plus domain lane commit coordinate.
        - Preserves receipt actor separately from the bound personal-history actor, which allows
          admission to attach the first commit even when the receipt author was pre-auth/system.
        """

        payload = {
            "domain_branch_id": domain_branch_id,
            "domain_projection_hash": domain_projection_hash,
            "domain_commit_id": domain_commit_id,
            "object_instance_graph_commit_id": object_instance_graph_commit_id,
            "environment_id": environment_id,
            "process_id": process_id,
            "thread_id": thread_id,
            "receipt_actor_id": receipt_actor_id,
            "created_at_unix_ms": created_at_unix_ms,
            "operation_label": operation_label,
            "call_target": call_target,
            "function_id": function_id,
            "object_id": object_id,
            "class_instance_identity_id": class_instance_identity_id,
            "graph_hash_post": graph_hash_post,
            "object_instance_graph_id": object_instance_graph_id,
            "root_object_id": root_object_id,
            "head_version": head_version,
            "source": source,
        }
        result = await invoke_instance(orm_model=self, function_name="ensure_commit", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_identity_ontology.actor.actor_commit import ActorCommit

        if isinstance(value, ActorCommit):
            return value
        return ActorCommit.validate_invocation_value(value)


class ActorCreateActorInput(BaseModel):
    type: ActorType
    identity_id: UUID
    key: str = Field(default="default")


class ActorCreateActorOutput(BaseModel):
    value: Actor


class ActorAddRoleInput(BaseModel):
    role_id: UUID


class ActorAddRoleOutput(BaseModel):
    value: ActorRole


class ActorRemoveRoleInput(BaseModel):
    role_id: UUID


class ActorRemoveRoleOutput(BaseModel):
    pass


class ActorAddSubscriptionInput(BaseModel):
    event_config_condition_config_scope_id: UUID
    name: str
    description: str | None = Field(default=None)
    action_type: str | None = Field(default=None)
    event_config_action_config_ids: list[UUID] = Field(default_factory=list)
    addressing_policy: SubscriptionAddressingPolicy = Field(default=SubscriptionAddressingPolicy.any)
    is_enabled: bool = Field(default=True)
    status: SubscriptionStatus = Field(default=SubscriptionStatus.active)
    filter_mode: SubscriptionFilterMode = Field(default=SubscriptionFilterMode.all_instances)
    filter_config: JsonObject | None = Field(default=None)
    priority: int = Field(default=0)
    batch_mode: bool = Field(default=False)
    batch_window_ms: int = Field(default=1000)
    max_batch_size: int = Field(default=100)
    require_read_access: bool = Field(default=True)
    check_ownership: bool = Field(default=True)
    rate_limit_per_minute: int | None = Field(default=None)
    rate_limit_per_hour: int | None = Field(default=None)


class ActorAddSubscriptionOutput(BaseModel):
    value: ActorSubscription


class ActorEnsureCommitInput(BaseModel):
    domain_branch_id: UUID
    domain_projection_hash: str
    domain_commit_id: UUID
    object_instance_graph_commit_id: UUID
    environment_id: UUID | None = Field(default=None)
    process_id: UUID | None = Field(default=None)
    thread_id: UUID | None = Field(default=None)
    receipt_actor_id: UUID | None = Field(default=None)
    created_at_unix_ms: int | None = Field(default=None)
    operation_label: str | None = Field(default=None)
    call_target: str | None = Field(default=None)
    function_id: UUID | None = Field(default=None)
    object_id: UUID | None = Field(default=None)
    class_instance_identity_id: UUID | None = Field(default=None)
    graph_hash_post: str | None = Field(default=None)
    object_instance_graph_id: UUID | None = Field(default=None)
    root_object_id: UUID | None = Field(default=None)
    head_version: int | None = Field(default=None)
    source: str = Field(default="environment_lane_commit_receipt")


class ActorEnsureCommitOutput(BaseModel):
    value: ActorCommit


FUNCTIONS = {
    "Actor": {
        "create_actor": {
            "canonical": {
                "name": "create_actor",
                "description": "Create an actor bound to an identity.\n\nv0: used by `Identity.signup` to build the minimal Identity→Actor graph\nwhile preserving the hard mutation boundary (mutate-self-only).",
                "is_constructor": True,
            },
            "input": ActorCreateActorInput,
            "output": ActorCreateActorOutput,
        },
        "add_role": {
            "canonical": {
                "name": "add_role",
                "description": "Adds a role binding to this actor.",
                "is_constructor": False,
            },
            "input": ActorAddRoleInput,
            "output": ActorAddRoleOutput,
        },
        "remove_role": {
            "canonical": {
                "name": "remove_role",
                "description": "Remove a role binding from this actor.\n\nContract:\n- Actor owns the actor_roles containment rail.\n- Missing role bindings are a no-op.\n- Deletion occurs through the contained ActorRole delete handler so\n  mutation remains parent-owned.",
                "is_constructor": False,
            },
            "input": ActorRemoveRoleInput,
            "output": ActorRemoveRoleOutput,
        },
        "add_subscription": {
            "canonical": {
                "name": "add_subscription",
                "description": "Adds a subscription policy to this actor.",
                "is_constructor": False,
            },
            "input": ActorAddSubscriptionInput,
            "output": ActorAddSubscriptionOutput,
        },
        "ensure_commit": {
            "canonical": {
                "name": "ensure_commit",
                "description": "Ensure an ActorCommit personal-history binding for one durable lane commit.\n\nCanonical v0:\n- Called by the Identity Environment-fanout reaction after a lane head commit receipt.\n- Idempotent by Actor plus domain lane commit coordinate.\n- Preserves receipt actor separately from the bound personal-history actor, which allows\n  admission to attach the first commit even when the receipt author was pre-auth/system.",
                "is_constructor": False,
            },
            "input": ActorEnsureCommitInput,
            "output": ActorEnsureCommitOutput,
        },
    },
}

__all__ = [
    "Actor",
    "ActorCreateActorInput",
    "ActorCreateActorOutput",
    "ActorAddRoleInput",
    "ActorAddRoleOutput",
    "ActorRemoveRoleInput",
    "ActorRemoveRoleOutput",
    "ActorAddSubscriptionInput",
    "ActorAddSubscriptionOutput",
    "ActorEnsureCommitInput",
    "ActorEnsureCommitOutput",
    "FUNCTIONS",
]
