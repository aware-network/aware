from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Identity Ontology
from aware_identity_ontology.actor.actor_enums import ActorType
from aware_identity_ontology.actor.actor_subscription_enums import (
    SubscriptionAddressingPolicy,
    SubscriptionFilterMode,
    SubscriptionStatus,
)
from aware_identity_ontology.actor.actor import Actor
from aware_identity_ontology.actor.actor_commit import ActorCommit
from aware_identity_ontology.actor.actor_role import ActorRole
from aware_identity_ontology.actor.actor_subscription import ActorSubscription

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_identity_ontology.stable_ids import (
    stable_actor_id,
)
from aware_identity_ontology.identity.identity import Identity

# --- AWARE: USER_IMPORTS END


async def create_actor(type: ActorType, identity_id: UUID, key: str = "default") -> Actor:
    """
    Create an actor bound to an identity.

    v0: used by `Identity.signup` to build the minimal Identity→Actor graph
    while preserving the hard mutation boundary (mutate-self-only).
    """

    # --- AWARE: LOGIC START create_actor
    identity = Identity.by_id_cached(identity_id)
    if identity is None:
        raise ValueError(f"Identity not available in write context for Actor.create_actor (identity_id={identity_id})")

    key_norm = (key or "").strip().casefold() or "default"
    actor_id = stable_actor_id(identity_id=identity_id, key=key_norm)
    existing = Actor.by_id_cached(actor_id)
    if existing is not None:
        if existing.identity_id != identity.id:
            raise ValueError(
                "Actor.create_actor identity mismatch for deterministic actor id: "
                f"actor_id={actor_id} expected_identity_id={identity.id} got_identity_id={existing.identity_id}"
            )
        if existing.type != type:
            raise ValueError(
                "Actor.create_actor type mismatch for deterministic actor id: "
                f"actor_id={actor_id} expected_type={type} got_type={existing.type}"
            )
        return existing

    return Actor(
        id=actor_id,
        key=key_norm,
        type=type,
        identity=identity,
        identity_id=identity.id,
    )
    # --- AWARE: LOGIC END create_actor


async def add_role(actor: Actor, role_id: UUID) -> ActorRole:
    """
    Adds a role binding to this actor.
    """

    # --- AWARE: LOGIC START add_role
    actor_role = await ActorRole.create_via_actor(
        actor_id=actor.id,
        role_id=role_id,
    )
    if all(x.id != actor_role.id for x in actor.actor_roles):
        actor.actor_roles.append(actor_role)
    return actor_role
    # --- AWARE: LOGIC END add_role


async def remove_role(actor: Actor, role_id: UUID) -> None:
    """
    Remove a role binding from this actor.

    Contract:
    - Actor owns the actor_roles containment rail.
    - Missing role bindings are a no-op.
    - Deletion occurs through the contained ActorRole delete handler so
      mutation remains parent-owned.
    """

    # --- AWARE: LOGIC START remove_role
    target: ActorRole | None = None
    for existing in list(actor.actor_roles):
        if existing.role_id == role_id:
            target = existing
            break

    if target is None:
        return

    await target.delete()
    actor.actor_roles[:] = [existing for existing in actor.actor_roles if existing.id != target.id]
    # --- AWARE: LOGIC END remove_role


async def add_subscription(
    actor: Actor,
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
    """
    Adds a subscription policy to this actor.
    """

    # --- AWARE: LOGIC START add_subscription
    subscription = await ActorSubscription.create_via_actor(
        actor_id=actor.id,
        event_config_condition_config_scope_id=event_config_condition_config_scope_id,
        name=name,
        description=description,
        action_type=action_type,
        event_config_action_config_ids=list(event_config_action_config_ids or []),
        addressing_policy=addressing_policy,
        is_enabled=is_enabled,
        status=status,
        filter_mode=filter_mode,
        filter_config=filter_config,
        priority=priority,
        batch_mode=batch_mode,
        batch_window_ms=batch_window_ms,
        max_batch_size=max_batch_size,
        require_read_access=require_read_access,
        check_ownership=check_ownership,
        rate_limit_per_minute=rate_limit_per_minute,
        rate_limit_per_hour=rate_limit_per_hour,
    )
    if all(x.id != subscription.id for x in actor.actor_subscriptions):
        actor.actor_subscriptions.append(subscription)
    return subscription
    # --- AWARE: LOGIC END add_subscription


async def ensure_commit(
    actor: Actor,
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

    # --- AWARE: LOGIC START ensure_commit
    actor_commit = await ActorCommit.create_via_actor(
        actor_id=actor.id,
        domain_branch_id=domain_branch_id,
        domain_projection_hash=domain_projection_hash,
        domain_commit_id=domain_commit_id,
        object_instance_graph_commit_id=object_instance_graph_commit_id,
        environment_id=environment_id,
        process_id=process_id,
        thread_id=thread_id,
        receipt_actor_id=receipt_actor_id,
        created_at_unix_ms=created_at_unix_ms,
        operation_label=operation_label,
        call_target=call_target,
        function_id=function_id,
        object_id=object_id,
        class_instance_identity_id=class_instance_identity_id,
        graph_hash_post=graph_hash_post,
        object_instance_graph_id=object_instance_graph_id,
        root_object_id=root_object_id,
        head_version=head_version,
        source=source,
    )
    if all(existing.id != actor_commit.id for existing in actor.actor_commits):
        actor.actor_commits.append(actor_commit)
    return actor_commit
    # --- AWARE: LOGIC END ensure_commit
